import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.auth_service import AuthService
from app.shared.logging import get_logger

logger = get_logger("identity.telegram")


class TelegramLinkService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.auth_service = AuthService()

    async def link_telegram(
        self,
        telegram_id: int,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> dict:
        result = await self.session.execute(
            text("SELECT id FROM users WHERE telegram_id = :tg_id"),
            {"telegram_id": telegram_id},
        )
        existing = result.scalar_one_or_none()

        if existing:
            access_token = self.auth_service.create_access_token(str(existing))
            refresh_token = self.auth_service.create_refresh_token(str(existing))
            logger.info("telegram_link_existing", telegram_id=telegram_id)
            return {
                "user_id": str(existing),
                "access_token": access_token,
                "refresh_token": refresh_token,
                "is_new": False,
            }

        user_id = uuid.uuid4()
        await self.session.execute(
            text(
                "INSERT INTO users (id, telegram_id, first_name, last_name, auth_provider) "
                "VALUES (:id, :tg_id, :first_name, :last_name, 'telegram')"
            ),
            {
                "id": user_id,
                "tg_id": telegram_id,
                "first_name": first_name,
                "last_name": last_name,
            },
        )
        await self.session.commit()

        access_token = self.auth_service.create_access_token(str(user_id))
        refresh_token = self.auth_service.create_refresh_token(str(user_id))

        logger.info("telegram_link_new", user_id=str(user_id), telegram_id=telegram_id)
        return {
            "user_id": str(user_id),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "is_new": True,
        }
