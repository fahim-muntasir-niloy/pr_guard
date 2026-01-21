import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    OPENAI_API_KEY: Optional[str] = None
    XAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    LANGSMITH_API_KEY: Optional[str] = None
    LLM_MODEL: str = "grok-4-1-fast-reasoning"
    LLM_PROVIDER: str = "xai"

    model_config = SettingsConfigDict(
        env_file=(
            os.path.join(os.path.expanduser("~"), ".pr_guard", ".env"),
            ".env",
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
