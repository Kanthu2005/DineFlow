from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    MONGO_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "restaurant_management"

    APP_NAME: str = "Restaurant Management System"
    DEBUG: bool = True

    # JWT Authentication settings
    JWT_SECRET_KEY: str = "supersecretjwtkeyforrestaurantmanagementsystem2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()