from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Конфигурация аналитической системы.
    
    Пример архитектуры настроек.
    Реальные параметры зависят от инфраструктуры проекта.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database settings
    postgres_user: str = "analytics_user"
    postgres_password: str = "analytics_secret"
    postgres_db: str = "analytics_db"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # Redis settings
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    # API settings
    server_api_key: str = "change_me_api_key"

    # Queue settings
    redis_events_queue: str = "analytics:events:queue"
    redis_batch_size: int = 500

    @property
    def database_url(self) -> str:
        """PostgreSQL connection URL."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        """Redis connection URL."""
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


settings = Settings()
