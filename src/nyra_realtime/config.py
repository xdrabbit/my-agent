import os
from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "nyra-realtime"
    ENV: str = "development"
    TWILIO_ACCOUNT_SID: Optional[str]
    TWILIO_AUTH_TOKEN: Optional[str]
    OPENAI_API_KEY: Optional[str]
    CHRONICLE_ENDPOINT: Optional[str]
    ADMIN_TOKEN: str = "replace-me"

    class Config:
        env_file = ".env"

settings = Settings()
