import logging

import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(user_data:dict, expiry: timedelta = None, refresh: bool = False) -> str:
    payload = {
        "user": user_data,
        "exp": datetime.utcnow() + (expiry if expiry else timedelta(minutes=15)),
        "jti": str(user_data.get("uid")),
        "refresh": refresh
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token

def decode_access_token(token: str) -> dict:
    try:
        decoded_token = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return decoded_token
    except jwt.PyJWTError as e:
        logging.exception(f"Token decoding error: {e}")
        return None
    


def create_refresh_token(user_data: dict, expiry: timedelta = None, refresh: bool = True) -> str:
    expiry = datetime.utcnow() + ( expiry or timedelta(days=7))
    payload = {
        "user": user_data,
        "exp": expiry,
        "jti": str(user_data.get("uid")),
        "refresh": refresh
    }
    refresh_token =jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return refresh_token