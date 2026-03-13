import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    supabase_url: str = "mock-url"
    supabase_key: str = "mock-key"
    whatsapp_token: str = "mock-token"
    whatsapp_verify_token: str = "my_secure_token_123"
    whatsapp_app_secret: str = "mock-app-secret" # For X-Hub-Signature-256
    groq_api_key: str = "mock-groq-key"
    redis_url: str = "redis://localhost:6379/0"
    sentry_dsn: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
