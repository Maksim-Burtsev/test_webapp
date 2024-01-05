from typing import Generator

import pytest

from sqlalchemy import exists
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from httpx import AsyncClient

from .models import User
from .helpers import hash_password


@pytest.fixture(scope="function")
def test_user(session: Session) -> Generator[User, None, None]:
    obj = User(
        email="test123@gmail.com",
        password=hash_password("test12345"),
    )
    session.add(obj)
    session.commit()

    yield obj

    session.delete(obj)
    session.commit()


@pytest.mark.asyncio
async def test_create_user_201(client: AsyncClient, session: Session):
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
    assert user.created_at

    # clean
    session.delete(user)
    session.commit()


# @pytest.mark.asyncio
# async def test_create_user_with_existend_email(
#     client: AsyncClient, session: Session, test_user: User
# ):
#     data = {"email": "test123@gmail.com", "password": "test_password12456"}
#     with pytest.raises(IntegrityError):
#         await client.post("/users/", json=data)
