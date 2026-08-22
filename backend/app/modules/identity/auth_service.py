from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from pydantic import BaseModel

from app.shared.config import get_settings

settings = get_settings()


class TokenData(BaseModel):
    user_id: str
    exp: datetime
    iat: datetime


class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        try:
            return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
        except ValueError:
            return False

    @staticmethod
    def create_access_token(user_id: str, expires_delta: timedelta | None = None) -> str:
        if expires_delta is None:
            expires_delta = timedelta(minutes=settings.jwt_access_expire_minutes)

        expire = datetime.now(timezone.utc) + expires_delta
        to_encode = {
            "user_id": user_id,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
        }
        encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)
        return encoded_jwt

    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_expire_days)
        to_encode = {
            "user_id": user_id,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh",
        }
        encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> str | None:
        try:
            payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
            user_id: str = payload.get("user_id")
            if user_id is None:
                return None
            return user_id
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
