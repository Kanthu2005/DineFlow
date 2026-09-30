from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):

    MONGO_URL: str = "mongodb://localhost:27017"
    ATLAS_URL: Optional[str] = None
    DATABASE_NAME: str = "restaurant_management"

    APP_NAME: str = "Restaurant Management System"
    DEBUG: bool = True

    # JWT Authentication settings
    JWT_SECRET_KEY: str = "supersecretjwtkeyforrestaurantmanagementsystem2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()