from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OPENAI_API_KEY: str
    GITHUB_TOKEN: Optional[str] = None
    HUGGINGFACE_API_KEY: Optional[str] = None
    LANGSMITH_API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
