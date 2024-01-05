from .models import User
from .schemas import UserCreateSchema
from .repositories import UserRepository


class UserService:
    def __init__(self, repo: UserRepository) -> None:
        self.repo: UserRepository = repo

    async def create(self, data: UserCreateSchema) -> User:
        return await self.repo.create(data=data)
