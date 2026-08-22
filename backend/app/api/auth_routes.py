from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_session
from app.modules.identity.api import AuthAPI, LoginRequest, RegisterRequest

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register(req: RegisterRequest, session: AsyncSession = Depends(get_session)):
    result = await AuthAPI(session).register(req)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/login")
async def login(req: LoginRequest, session: AsyncSession = Depends(get_session)):
    result = await AuthAPI(session).login(req)
    if "error" in result:
        raise HTTPException(status_code=401, detail=result["error"])
    return result


@router.post("/refresh")
async def refresh(refresh_token: str, session: AsyncSession = Depends(get_session)):
    result = await AuthAPI(session).refresh(refresh_token)
    if "error" in result:
        raise HTTPException(status_code=401, detail=result["error"])
    return result
