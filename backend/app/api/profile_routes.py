import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.infrastructure.database import get_session
from app.modules.embedding.service import EmbeddingService
from app.modules.identity.service import IdentityService

router = APIRouter(prefix="/profile", tags=["profile"])


class ProfileUpdate(BaseModel):
    education_level: str | None = None
    major: str | None = None
    university: str | None = None
    graduation_year: int | None = None
    cgpa: float | None = None
    skills: list[str] | None = None
    experience: list[dict] | None = None
    interests: list[str] | None = None
    goals: list[str] | None = None
    location: str | None = None


@router.get("")
async def get_profile(
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    return await IdentityService(session).get_profile(user_id)


@router.put("")
async def update_profile(
    req: ProfileUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    data = {k: v for k, v in req.model_dump().items() if v is not None}
    result = await IdentityService(session).update_profile(user_id, **data)
    await session.commit()

    # #2 loop personalisasi: re-embed profil setelah update
    try:
        await EmbeddingService(session).embed_user_profile(user_id)
        await session.commit()
    except Exception:
        pass

    return result


@router.get("/saved")
async def saved_list(
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    return await _list_by_event(session, user_id, "save")


@router.get("/applied")
async def applied_list(
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    return await _list_by_event(session, user_id, "apply")


async def _list_by_event(session: AsyncSession, user_id: uuid.UUID, event_type: str):
    from sqlalchemy import text

    rows = await session.execute(
        text(
            "SELECT DISTINCT ON (o.id) o.id, o.title, o.slug, o.category, o.organizer, "
            "o.location, o.end_date, e.created_at "
            "FROM user_events e JOIN opportunities o ON o.id = e.opportunity_id "
            "WHERE e.user_id = :uid AND e.event_type = :etype "
            "ORDER BY o.id, e.created_at DESC"
        ),
        {"uid": user_id, "etype": event_type},
    )
    return [
        {
            "id": str(r[0]),
            "title": r[1],
            "slug": r[2],
            "category": r[3],
            "organizer": r[4],
            "location": r[5],
            "end_date": str(r[6]) if r[6] else None,
            "at": str(r[7]),
        }
        for r in rows.fetchall()
    ]
