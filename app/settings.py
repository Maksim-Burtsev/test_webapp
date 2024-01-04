import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    PG_USER: str = os.environ.get("PG_USER", "postgres")
    PG_PASSWORD: str = os.environ.get("PG_PASSWORD", "postgres")
    PG_HOST: str = os.environ.get("PG_HOST", "localhost")
    PG_PORT: int = os.environ.get("PG_PORT", 5432)
    PG_DATABASE: str = os.environ.get("PG_DATABASE", "postgres")

    def get_postgres_url(self) -> str:
        return (
            "postgresql+asyncpg://"
            f"{self.PG_USER}:{self.PG_PASSWORD}"
            f"@{self.PG_HOST}:{self.PG_PORT}/{self.PG_DATABASE}"
        )


settings = Settings()
