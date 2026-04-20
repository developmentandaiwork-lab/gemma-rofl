from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://ollama_user:ollama_password@db:5432/ollama_chat"
    jwt_secret: str = "change_me"
    jwt_expire_minutes: int = 10080
    ollama_base_url: str = "http://host.docker.internal:11434"
    ollama_model: str = "gemma4:latest"
    ollama_timeout: int = 300
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/1"
    backend_cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
