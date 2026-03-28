from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from .service import Auth_service
from app.modules.User.service import UserService
from app.modules.User.schemes import UserCreate
from .schemes import SignUpScheme, UserResponseScheme, SignInScheme, ResendVerificationRequest
from .utils import (
    verify_password,
    create_refresh_token,
    create_access_token,
    hash_password,
    create_url_safe_token,
    decode_url_safe_token,
)
from fastapi.responses import JSONResponse
from app.core.dependencies import RefreshToken, AccessToken, get_current_user
from app.core.redis import add_token_to_blocklist, acquire_verification_resend_slot
from app.core.config import settings
from app.email import send_verification_email
from app.celery_task import send_verification_email_task
from app.modules.Notifications.service import NotificationService



auth_router = APIRouter()
auth_service = Auth_service()
user_service = UserService()
notification_service = NotificationService()
refresh_token_dependency = RefreshToken()
access_token_dependency = AccessToken()


async def _send_verification_email(email: str) -> str:
    token = create_url_safe_token({"email": email})
    link = f"http://{settings.DOMAIN}/api/v2/auth/verify/{token}"

    # Prefer Celery for non-blocking email delivery; fallback keeps flow resilient
    # if broker/workers are temporarily unavailable.
    try:
        send_verification_email_task.delay(email, link)
    except Exception:
        await send_verification_email(email, link)

    return token


async def _safe_create_auth_notification(user_id, title: str, message: str, session: AsyncSession, event_type: str, payload: dict):
    try:
        await notification_service.create_notification(
            user_id=user_id,
            title=title,
            message=message,
            session=session,
            event_type=event_type,
            entity_type="user",
            entity_id=user_id,
            payload=payload,
        )
    except Exception:
        # Email verification flow should not fail because in-app notification failed.
        pass

@auth_router.post("/login")
async def login(user_data: SignInScheme, session: AsyncSession = Depends(get_db)):

    user = await auth_service.get_user_by_email(user_data.email, session)

    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not verified. Please verify your email first"
        )

    payload = {
        "uid": str(user.uid),
        "role": user.role
    }

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
            "role": user.role
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
    
    # Create user via User service
    new_user = await user_service.create_user(user_create_data, hashed_pwd, session)

    await _send_verification_email(new_user.email)

    await _safe_create_auth_notification(
        user_id=new_user.uid,
        title="Verification Email Sent",
        message="A verification email has been sent to your address.",
        session=session,
        event_type="auth.verification_email_sent",
        payload={"email": new_user.email},
    )

    return new_user


@auth_router.get("/verify/{token}")
async def verify_user_account(token: str, session: AsyncSession = Depends(get_db)):
    token_data = decode_url_safe_token(token)
    user_email = token_data.get("email")

    if not user_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token payload"
        )

    user = await auth_service.get_user_by_email(user_email, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.is_active:
        return {"message": "Account already verified"}

    user.is_active = True
    await session.commit()
    await session.refresh(user)

    await _safe_create_auth_notification(
        user_id=user.uid,
        title="Account Verified",
        message="Your account has been verified successfully.",
        session=session,
        event_type="auth.account_verified",
        payload={"email": user.email},
    )

    return {"message": "Account verified successfully"}


@auth_router.post("/resend-verification")
async def resend_verification_email(payload: ResendVerificationRequest, session: AsyncSession = Depends(get_db)):
    user = await auth_service.get_user_by_email(payload.email, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.is_active:
        return {"message": "Account already verified"}

    slot_acquired = await acquire_verification_resend_slot(user.email, cooldown_seconds=60)
    if not slot_acquired:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Please wait before requesting another verification email"
        )

    await _send_verification_email(user.email)

    await _safe_create_auth_notification(
        user_id=user.uid,
        title="Verification Email Resent",
        message="A new verification email has been sent to your address.",
        session=session,
        event_type="auth.verification_email_resent",
        payload={"email": user.email},
    )

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
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    return {"user": current_user }
