from typing import Callable
from contextlib import AbstractAsyncContextManager

from sqlalchemy.ext.asyncio import AsyncSession

from .models import User
from .schemas import UserCreateSchema

from .helpers import hash_password


class UserRepository:
    def __init__(
        self, session_factory: Callable[..., AbstractAsyncContextManager[AsyncSession]]
    ) -> None:
        self.session_factory = session_factory

    async def create(self, data: UserCreateSchema) -> User:
        obj = User(
            password=hash_password(data.password),
            **data.dict(exclude={"password"}),
        )
        async with self.session_factory() as session:
            session.add(obj)
            await session.commit()
        return obj
