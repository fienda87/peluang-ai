import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.infrastructure.database import get_session
from app.modules.recommendation.service import RecommendationService

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("")
async def get_feed(
    limit: int = 20,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    return await RecommendationService(session).get_feed(user_id, limit=limit)


@router.post("/generate")
async def generate(
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    return await RecommendationService(session).generate(user_id, trigger="on_demand")
