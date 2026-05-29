import logging
from types import SimpleNamespace
import bcrypt
import jwt
from itsdangerous import URLSafeTimedSerializer
from itsdangerous.exc import BadSignature, SignatureExpired
from fastapi import HTTPException, status
from passlib.context import CryptContext
from datetime import datetime, timedelta
from app.core.config import settings
import uuid

# Passlib expects bcrypt.__about__.__version__, but newer bcrypt releases
# expose the version at module level instead.
if not hasattr(bcrypt, "__about__"):
    bcrypt.__about__ = SimpleNamespace(__version__=bcrypt.__version__)


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
EMAIL_TOKEN_SALT = "email-verification"
serializer = URLSafeTimedSerializer(settings.JWT_SECRET_KEY)


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


def create_url_safe_token(data: dict) -> str:
    return serializer.dumps(data, salt=EMAIL_TOKEN_SALT)


def decode_url_safe_token(token: str, max_age: int = 3600) -> dict:
    try:
        return serializer.loads(token, salt=EMAIL_TOKEN_SALT, max_age=max_age)
    except SignatureExpired as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification link has expired",
        ) from exc
    except BadSignature as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token",
        ) from exc
