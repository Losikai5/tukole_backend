import logging
import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from app.core.config import settings
import uuid


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)



def create_access_token(user_data: dict, expiry: timedelta = None) -> str:

    expire = datetime.utcnow() + (expiry or timedelta(minutes=15))

    payload = {
        "sub": user_data["uid"],
        "role": user_data["role"],
        "jti": str(uuid.uuid4()),
        "refresh": False,
        "iat": datetime.utcnow(),
        "exp": expire
    }

    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    return token


def create_refresh_token(user_data: dict, expiry: timedelta = None) -> str:

    expire = datetime.utcnow() + (expiry or timedelta(days=7))

    payload = {
        "sub": user_data["uid"],
        "role": user_data["role"],
        "jti": str(uuid.uuid4()),
        "refresh": True,
        "iat": datetime.utcnow(),
        "exp": expire
    }

    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    return token


def decode_access_token(token: str) -> dict | None:
    try:
        decoded = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        return decoded

    except jwt.ExpiredSignatureError:
        logging.warning("Token expired")
        return None

    except jwt.PyJWTError as e:
        logging.exception(f"Token decoding error: {e}")
        return None