from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials
from fastapi import Request, HTTPException, status
from app.modules.Auth.utils import decode_access_token


class Bearer(HTTPBearer):
     def __init__ (auto_error: bool = True):
          super().__init__(auto_error=auto_error)
     async def __call__(self, request:Request) -> HTTPAuthorizationCredentials:
           creds = await super().__call__(request)   
           token_data = decode_access_token(creds.credentials)
           if token_data is None:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid or expired token")
           
           self.verify_token(token_data)
           
          
           return token_data
     def verify_token(self, token_data:dict) -> None:
          raise NotImplementedError("Subclasses must implement the verify_token method")
     
class RefreshToken(Bearer): 
        def verify_token(self, token_data:dict) -> None:
              if token_data and not token_data['refresh']:
                  raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid token type")
     
         
          
class AccessToken(Bearer):
        def verify_token(self, token_data:dict) -> None:
            if token_data and not token_data['refresh']:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid token type")
