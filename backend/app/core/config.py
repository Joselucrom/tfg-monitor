from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "TFG Monitor"
    debug: bool = True

    database_url: str

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    class Config:
        env_file = ".env"

    gemini_api_key: str = ""
    
settings = Settings()
