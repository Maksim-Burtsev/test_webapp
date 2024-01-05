import asyncio
from typing import Generator, AsyncGenerator

import pytest
import pytest_asyncio

from httpx import AsyncClient

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import create_async_engine

from testcontainers.postgres import PostgresContainer

from .application import create_app
from .models import Base
from .containers import Container


@pytest.fixture(scope="session")
def event_loop(request):
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def test_postgres_url(event_loop) -> Generator[str, None, None]:
    with PostgresContainer() as postgres:
        yield postgres.get_connection_url().replace(
            "postgresql+psycopg2://",
            "postgresql+asyncpg://",
        )


@pytest_asyncio.fixture(scope="session", autouse=True)
async def db(test_postgres_url: str, event_loop):
    engine = create_async_engine(test_postgres_url, pool_size=10)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="session")
def session(test_postgres_url: str) -> Generator[Session, None, None]:
    engine = create_engine(
        test_postgres_url.replace(
            "postgresql+asyncpg://",
            "postgresql+psycopg2://",
        )
    )
    session = Session(engine)

    yield session

    session.close()


@pytest.fixture(scope="session", autouse=True)
def test_container(test_postgres_url: str) -> Generator[Container, None, None]:
    Container.engine.clear_args()
    Container.engine.set_args(test_postgres_url)

    yield Container()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def client(test_container, db, event_loop) -> AsyncGenerator[AsyncClient, None]:
    app = create_app(container=test_container)
    async with AsyncClient(app=app, base_url="http://localhost:12345") as client:
        yield client
