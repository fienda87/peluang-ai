import uuid

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_session
from app.modules.identity.auth_service import AuthService
from app.shared.config import get_settings

bearer_scheme = HTTPBearer(auto_error=False)


async def _resolve_default_user(session: AsyncSession) -> uuid.UUID:
    """SINGLE_USER_MODE: fallback ke user pertama, atau auto-provision Owner."""
    row = await session.execute(
        text("SELECT id FROM users ORDER BY created_at ASC LIMIT 1")
    )
    uid = row.scalar()
    if uid:
        return uid

    new_id = uuid.uuid4()
    await session.execute(
        text(
            "INSERT INTO users (id, email, username, first_name, auth_provider) "
            "VALUES (:id, 'owner@local', 'owner', 'Owner', 'local') "
            "ON CONFLICT (email) DO NOTHING"
        ),
        {"id": new_id},
    )
    await session.commit()
    return new_id


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_session),
) -> uuid.UUID:
    if credentials is not None:
        user_id = AuthService.verify_token(credentials.credentials)
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        try:
            return uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid token payload")

    # Tanpa token: single-user mode (self-hosted) -> default user
    if get_settings().single_user_mode:
        return await _resolve_default_user(session)

    raise HTTPException(status_code=401, detail="Not authenticated")
