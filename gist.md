In this gist I show the example how to setup pytest for web application with test database.

Let's create simple webapp with user model and view to create it.

*models.py*
```python
import datetime

from sqlalchemy import Column, String, Boolean, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    password = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_active = Column(Boolean, default=True)
```

*repositories.py*
```python
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
```


*services.py*
```python
from .models import User
from .schemas import UserCreateSchema
from .repositories import UserRepository


class UserService:
    def __init__(self, repo: UserRepository) -> None:
        self.repo: UserRepository = repo

    async def create(self, data: UserCreateSchema) -> User:
        return await self.repo.create(data=data)
```

*views.py*
```python
from fastapi import APIRouter, Depends
from dependency_injector.wiring import Provide, inject

from .schemas import UserCreateSchema, UserSchema
from .services import UserService

from .containers import Container

router = APIRouter(prefix="/users")


@router.post(
    "/",
    status_code=201,
    response_model=UserSchema,
)
@inject
async def create_user(
    data: UserCreateSchema,
    user_service: UserService = Depends(Provide[Container.user_service]),
):
    return await user_service.create(data=data)
```

And dependency injector container which have SQLAlchemy engine and async context manager which wire into repositories.

```python
from dependency_injector import containers, providers
from sqlalchemy import orm
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from .repositories import UserRepository
from .services import UserService

from .settings import settings


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
```

Full source code of app is [here](https://github.com/Maksim-Burtsev/test_webapp).

Now let's setup *conftest.py* file that will up Postgres and create all tables every time when the tests will run.
This is also were all necessary fixtures will be placed.

*conftest.py*
```python
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


# test database can be up simply by using the Docker 
# without testcontainers library
@pytest.fixture(scope="session", autouse=True)
def test_postgres_url(event_loop) -> Generator[str, None, None]:
    with PostgresContainer() as postgres:
        yield postgres.get_connection_url().replace(
            "postgresql+psycopg2://",
            "postgresql+asyncpg://",
        )

# create all used tables
@pytest_asyncio.fixture(scope="session", autouse=True)
async def db(test_postgres_url: str, event_loop):
    engine = create_async_engine(test_postgres_url, pool_size=10)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# sync session for usage inside tests
# (because @pytest_asyncio.fixture with async session
# runs in the different event loop and this raises exception)
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

# replace database url inside DI container
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
```

Now we can test the application. 

Let's test view which creates user.

*tests.py*
```python
from typing import Generator

import pytest

from sqlalchemy import exists
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from httpx import AsyncClient

from .models import User
from .helpers import hash_password


@pytest.mark.asyncio
async def test_create_user(client: AsyncClient, session: Session):
    assert not session.query(exists().where(User.email == "test@gmail.com")).scalar()

    data = {
        "email": "test@gmail.com",
        "password": "test_password12456",
    }
    response = await client.post("/users/", json=data)
    print(response.json())
    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "email": "test@gmail.com",
    }

    user: User = session.get(User, response.json()["id"])
    assert user.email == "test@gmail.com"
    assert user.is_active

    # clean
    session.delete(user)
    session.commit()
```

and run it:

```shell
pytest tests.py

====== 1 passed ======
```

Here is [repository](https://github.com/Maksim-Burtsev/test_webapp) with all source code.