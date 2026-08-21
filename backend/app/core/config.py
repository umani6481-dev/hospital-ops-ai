import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Hospital Operations AI"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./hospital_ops.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-change-me")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-jwt-secret-change-me")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    MODEL_PATH: str = os.getenv("MODEL_PATH", "./ml/models/artifacts")
    CORS_ORIGINS: list[str] = ["*"]
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    class Config:
        env_file = ".env"


settings = Settings()
