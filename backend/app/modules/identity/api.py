from pydantic import BaseModel, EmailStr
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.auth_service import AuthService
from app.shared.logging import get_logger

logger = get_logger("identity.api")


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str | None = None
    last_name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthAPI:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.auth_service = AuthService()

    async def register(self, req: RegisterRequest) -> dict:
        result = await self.session.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": req.email},
        )
        if result.scalar_one_or_none():
            return {"error": "email_already_exists"}

        import uuid

        user_id = uuid.uuid4()
        hashed_pwd = self.auth_service.hash_password(req.password)

        await self.session.execute(
            text(
                "INSERT INTO users (id, email, first_name, last_name, password_hash, auth_provider) "
                "VALUES (:id, :email, :first_name, :last_name, :pwd, 'local')"
            ),
            {
                "id": user_id,
                "email": req.email,
                "first_name": req.first_name,
                "last_name": req.last_name,
                "pwd": hashed_pwd,
            },
        )
        await self.session.commit()

        access_token = self.auth_service.create_access_token(str(user_id))
        refresh_token = self.auth_service.create_refresh_token(str(user_id))

        logger.info("user_registered", user_id=str(user_id), email=req.email)
        return {"user_id": str(user_id), "access_token": access_token, "refresh_token": refresh_token}

    async def login(self, req: LoginRequest) -> dict:
        result = await self.session.execute(
            text("SELECT id, password_hash FROM users WHERE email = :email"),
            {"email": req.email},
        )
        row = result.one_or_none()

        if not row or not self.auth_service.verify_password(req.password, row[1]):
            logger.warning("login_failed", email=req.email)
            return {"error": "invalid_credentials"}

        user_id = str(row[0])
        access_token = self.auth_service.create_access_token(user_id)
        refresh_token = self.auth_service.create_refresh_token(user_id)

        logger.info("user_login", user_id=user_id, email=req.email)
        return {"user_id": user_id, "access_token": access_token, "refresh_token": refresh_token}

    async def refresh(self, refresh_token: str) -> dict:
        user_id = self.auth_service.verify_token(refresh_token)
        if not user_id:
            return {"error": "invalid_token"}

        access_token = self.auth_service.create_access_token(user_id)
        logger.info("token_refreshed", user_id=user_id)
        return {"access_token": access_token}
