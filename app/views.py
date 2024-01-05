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
