from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Request, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.Auth.utils import decode_access_token
from app.core.redis import is_token_revoked
from app.modules.User.service import UserService
from app.main import get_db


class Bearer(HTTPBearer):

    async def __call__(self, request: Request):

        creds: HTTPAuthorizationCredentials = await super().__call__(request)

        token_data = decode_access_token(creds.credentials)

        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )

        jti = token_data.get("jti")

        if jti and await is_token_revoked(jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked"
            )

        self.verify_token(token_data)

        return token_data

    def verify_token(self, token_data: dict):
        raise NotImplementedError()


class RefreshToken(Bearer):

    def verify_token(self, token_data: dict):

        if not token_data.get("refresh"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )


class AccessToken(Bearer):

    def verify_token(self, token_data: dict):

        if token_data.get("refresh"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access token"
            )


async def get_current_user(
    token_data: dict = Depends(AccessToken()),
    session: AsyncSession = Depends(get_db)
):

    user_id = token_data["sub"]

    service = UserService()

    user = await service.get_user_by_id(user_id, session)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    return user


class RoleChecker:

    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    async def __call__(self, current_user = Depends(get_current_user)):

        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )

        return current_user