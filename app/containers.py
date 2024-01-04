from dependency_injector import containers, providers
from sqlalchemy import orm
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from repositories import UserRepository
from services import UserService

from settings import settings


class Container(containers.DeclarativeContainer):
    engine = providers.Singleton(
        create_async_engine,
        settings.get_postgres_url(),
        pool_size=10,
    )
    session_factory = providers.Factory(
        orm.sessionmaker,
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    user_repo = providers.Singleton(
        UserRepository,
        session_factory=session_factory,
    )
    user_service = providers.Singleton(
        UserService,
        repo=user_repo,
    )
