from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AgentTutor"
    app_env: str = "development"
    database_url: str = "postgresql+asyncpg://agenttutor:agenttutor@localhost:5433/agenttutor"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "change-me"
    llm_provider: str = "stub"
    llm_api_key: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
