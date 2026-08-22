import uuid
from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class BaseRepository(Generic[T]):
    model: type[T]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, id: uuid.UUID) -> T | None:
        return await self.session.get(self.model, id)

    async def create(self, **kwargs: Any) -> T:
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def update(self, instance: T, **kwargs: Any) -> T:
        for key, value in kwargs.items():
            setattr(instance, key, value)
        await self.session.flush()
        return instance

    async def delete(self, instance: T) -> None:
        await self.session.delete(instance)
        await self.session.flush()

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[T]:
        stmt = select(self.model).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def commit(self) -> None:
        await self.session.commit()
