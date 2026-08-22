from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_session
from app.modules.opportunities.search import SearchService

router = APIRouter(prefix="/opportunities", tags=["opportunities"])


@router.get("")
async def search_opportunities(
    q: str | None = Query(None),
    category: str | None = Query(None),
    location: str | None = Query(None),
    date_after: str | None = Query(None),
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    return await SearchService(session).search(
        q=q, category=category, location=location,
        date_after=date_after, limit=limit, offset=offset,
    )
