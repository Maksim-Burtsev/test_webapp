from fastapi import FastAPI

from .views import router as users_router

from .containers import Container


def create_app(container: Container = Container()) -> FastAPI:
    app = FastAPI()
    app.container: Container = container
    app.container.wire([".views"])
    app.include_router(users_router)

    return app
