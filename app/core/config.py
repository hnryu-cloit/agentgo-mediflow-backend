from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "agentgo-mediflow"
    app_env: str = "local"
    database_url: str = "sqlite:///./app.db"
    external_api_key: str = "stub-key"
    allowed_origins: list[str] = ["http://localhost:5173"]


settings = Settings()