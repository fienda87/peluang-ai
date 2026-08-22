import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.infrastructure.database import get_session
from app.modules.behavior.service import BehaviorService

router = APIRouter(prefix="/events", tags=["behavior"])


class EventRequest(BaseModel):
    event_type: str
    opportunity_id: str | None = None
    recommendation_id: str | None = None
    metadata: dict | None = None


@router.post("")
async def record_event(
    req: EventRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    svc = BehaviorService(session)
    event_id = await svc.record_event(
        user_id=user_id,
        event_type=req.event_type,
        opportunity_id=uuid.UUID(req.opportunity_id) if req.opportunity_id else None,
        recommendation_id=uuid.UUID(req.recommendation_id) if req.recommendation_id else None,
        metadata=req.metadata,
    )
    return {"event_id": str(event_id)}


@router.get("/profile")
async def behavior_profile(
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    return await BehaviorService(session).get_behavior_profile(user_id)
