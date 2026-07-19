from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AgentTutor"
    app_env: str = "development"
    database_url: str = "postgresql+asyncpg://agenttutor:agenttutor@localhost:5433/agenttutor"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "change-me"
    access_token_expire_minutes: int = 60
    frontend_url: str = "http://localhost:3000"
    llm_provider: str = "stub"
    llm_api_key: str | None = None
    llm_base_url: str = "http://localhost:11434"
    llm_model: str = "qwen3:4b"
    embedding_dimensions: int = 384

    @model_validator(mode="after")
    def production_secrets_must_be_configured(self):
        if self.app_env == "production" and self.jwt_secret == "change-me":
            raise ValueError("JWT_SECRET must be set to a strong secret in production")
        return self

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
