from fastapi.security import HTTPAuthorizationCredentials,HTTPBearer
from fastapi import Depends,requests,HTTPException,status  
class AuthDependencies(HTTPBearer):
    pass