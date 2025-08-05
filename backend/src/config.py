from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ollama_url: str = "http://ollama:11434/api/embeddings"
    pg_host: str = "localhost"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    rabbitmq_host: str = "localhost"

    class Config:
        env_file = ".env"

settings = Settings()
