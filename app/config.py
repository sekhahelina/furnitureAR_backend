from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    MAX_FILE_SIZE_MB: int = 10

    # App
    APP_ENV: str = "development"

    # Cloudinary (додаємо сюди ваші нові ключі)
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str

    # CORS
    # Вказуємо тип list, Pydantic сам розпарсить рядок з .env
    ALLOWED_ORIGINS: List[str] = ["*"]

    # Новий формат налаштувань для Pydantic V2
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # ігнорувати змінні в .env, яких немає в цьому класі
    )


settings = Settings()