from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str
    telegram_bot_token: str
    jwt_secret: str
    jwt_expire_minutes: int = 10080
    webapp_url: str = ""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
