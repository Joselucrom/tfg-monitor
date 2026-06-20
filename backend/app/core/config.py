from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # apunta a backend/


class Settings(BaseSettings):
    app_name: str = "TFG Monitor"
    debug: bool = True

    database_url: str

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    gemini_api_key: str = ""

    class Config:
        env_file = str(BASE_DIR / ".env")


settings = Settings()