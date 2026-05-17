from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from typing import Dict
from .service import Auth_service
from app.modules.User.service import UserService
from app.modules.User.schemes import UserCreate, UserResponse
from .schemes import SignUpScheme, UserResponseScheme, SignInScheme, ResendVerificationRequest
from .utils import (
    verify_password,
    create_refresh_token,
    create_access_token,
    hash_password,
    create_url_safe_token,
    decode_url_safe_token,
)
from app.core.dependencies import RefreshToken, AccessToken, get_current_user
from app.core.redis import add_token_to_blocklist
from app.core.config import settings
from app.core.models import NotificationType
from app.modules.Notifications.service import NotificationService
from app.celery_task import send_verification_email


auth_router = APIRouter()
auth_service = Auth_service()
user_service = UserService()
notification_service = NotificationService()
refresh_token_dependency = RefreshToken()
access_token_dependency = AccessToken()

_verification_resend_slots: Dict[str, float] = {}


async def _send_verification_email(email: str):
    token = create_url_safe_token({"email": email})
    link = f"http://{settings.DOMAIN}/api/v2/auth/verify/{token}"
    send_verification_email.delay(recipient=email, verification_link=link)


async def _safe_create_auth_notification(*, event_type: str, user_uid, session: AsyncSession, message: str):
    await notification_service.create_notification(
        user_uid=user_uid,
        message=message,
        notification_type=NotificationType.ACCOUNT_VERIFICATION,
        session=session,
    )


async def acquire_verification_resend_slot(email: str, cooldown_seconds: int = 60):
    now = datetime.now(timezone.utc).timestamp()
    last_sent = _verification_resend_slots.get(email)
    if last_sent is not None and now - last_sent < cooldown_seconds:
        return False
    _verification_resend_slots[email] = now
    return True

@auth_router.post("/login")
async def login(user_data: SignInScheme, session: AsyncSession = Depends(get_db)):
    try:
        user = await auth_service.authenticate_user(user_data.email, user_data.password, session)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    payload = {"uid": str(user.uid), "role":user.role}
    access_token = create_access_token(payload)
    refresh_token = create_refresh_token(payload)

    return {
        "message": "Login successful",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "uid": str(user.uid),
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_active": user.is_active,
        }
    }

@auth_router.post("/register", response_model=UserResponseScheme, status_code=status.HTTP_201_CREATED)
async def register(user_data: SignUpScheme, session: AsyncSession = Depends(get_db)):
    # Check if user already exists
    user_exists = await auth_service.user_exists(user_data.email, session)
    if user_exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")
    
    # Hash the password
    hashed_pwd = hash_password(user_data.password)
    
    # Prepare user data (exclude password from SignUpScheme)
    user_create_data = UserCreate(
        username=user_data.username,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        email=user_data.email,
        is_active=False,
        role=user_data.role
    )
    
    new_user = await user_service.create_user(user_create_data, hashed_pwd, session)

    try:
        await _send_verification_email(new_user.email)
    except Exception:
        pass  # Non-fatal: registration succeeds even if the broker is down

    try:
        await _safe_create_auth_notification(
            event_type="auth.verification_email_sent",
            user_uid=new_user.uid,
            session=session,
            message="Verification email sent",
        )
    except Exception:
        pass

    return new_user

   


@auth_router.get("/verify/{token}")
async def verify_user_account(token: str, session: AsyncSession = Depends(get_db)):
    token_data = decode_url_safe_token(token)
    user_email = token_data.get("email")
    if not user_email:
        raise HTTPException(status_code=400, detail="Invalid verification token payload")
    
    try:
        await auth_service.verify_user(user_email, session)
        user = await auth_service.get_user_by_email(user_email, session)
        if user:
            await _safe_create_auth_notification(
                event_type="auth.account_verified",
                user_uid=user.uid,
                session=session,
                message="Account verified successfully",
            )
        return {"message": "Account verified successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@auth_router.post("/resend-verification")
async def resend_verification(request: ResendVerificationRequest, session: AsyncSession = Depends(get_db)):
    user = await auth_service.get_user_by_email(request.email, session)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.is_active:
        return {"message": "Account already verified"}

    allowed = await acquire_verification_resend_slot(request.email, cooldown_seconds=60)
    if not allowed:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Please wait before requesting another verification email")

    try:
        await _send_verification_email(request.email)
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send verification email")

    try:
        await _safe_create_auth_notification(
            event_type="auth.verification_email_resent",
            user_uid=user.uid,
            session=session,
            message="Verification email resent",
        )
    except Exception:
        pass

    return {"message": "Verification email sent"}

@auth_router.post("/refresh-token")
async def refresh_token(token_data: dict = Depends(RefreshToken())):

    user_payload = {
        "uid": token_data["sub"],
        "role": token_data["role"]
    }

    new_access_token = create_access_token(user_payload)

    return {"access_token": new_access_token}

@auth_router.post("/logout")
async def logout(token_data: dict = Depends(AccessToken())):

    jti = token_data["jti"]

    await add_token_to_blocklist(jti)

    return {"message": "Logout successful"}


@auth_router.get("/me")
async def get_current_user_info(current_user = Depends(get_current_user)):
    return {
        "user": {
            "uid": str(current_user.uid),
            "username": current_user.username,
            "email": current_user.email,
            "role": current_user.role,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "is_active": current_user.is_active,
        }
    }
