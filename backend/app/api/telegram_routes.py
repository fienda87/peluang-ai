import uuid
from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.infrastructure.database import get_session
from app.modules.identity.auth_service import AuthService

router = APIRouter(prefix="/telegram", tags=["telegram"])


@router.get("/link")
async def telegram_link(
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    """JWT pendek sebagai deep-link token untuk /start <token> di bot."""
    token = AuthService.create_access_token(str(user_id), expires_delta=timedelta(minutes=30))
    return {
        "token": token,
        "url": f"https://t.me/peluang_ai_bot?start={token}",
        "expires_minutes": 30,
    }
