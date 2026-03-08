from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials
from fastapi import Request, HTTPException, status
from app.modules.Auth.utils import decode_access_token
from app.core.redis import is_token_revoked
from fastapi import Depends
from app.modules.User.service import UserService
from app.main import get_db
from sqlalchemy.ext.asyncio import AsyncSession

service = UserService()

class Bearer(HTTPBearer):
     def __init__ (self, auto_error: bool = True):
          super().__init__(auto_error=auto_error)
     async def __call__(self, request:Request) -> HTTPAuthorizationCredentials:
           creds = await super().__call__(request)   
           token_data = decode_access_token(creds.credentials)
           if not token_data:
               raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid or expired token")
          # Check token revocation
           jti = token_data.get("jti")

           if jti and await is_token_revoked(jti):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Token has been revoked")
           
           self.verify_token(token_data)
           
          
           return token_data
     def verify_token(self, token_data:dict) -> None:
          raise NotImplementedError("Subclasses must implement the verify_token method")
     
class RefreshToken(Bearer):
    """
    Security dependency for refresh tokens.
    """

    def verify_token(self, token_data: dict) -> None:
        if not token_data.get("refresh", False):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid refresh token")


class AccessToken(Bearer):
    """
    Security dependency for access tokens.
    """

    def verify_token(self, token_data: dict) -> None:
        if token_data.get("refresh", False):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid access token")
        
async def get_current_user(token_data: dict = Depends(AccessToken()), session: AsyncSession = Depends(get_db)) -> dict:
          user_email = token_data["user"]["email"]
          user = await service.get_user_by_email(user_email, session)
          if user is None:
               raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid token payload")
          return user


class RoleChecker:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    async def __call__(self, current_user: dict = Depends(get_current_user)):
        if current_user.role not in self.allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return True
    


  