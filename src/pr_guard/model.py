import os
from langchain.chat_models import init_chat_model
from pr_guard.config import settings

if settings.OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY

if settings.XAI_API_KEY:
    os.environ["XAI_API_KEY"] = settings.XAI_API_KEY

if settings.ANTHROPIC_API_KEY:
    os.environ["ANTHROPIC_API_KEY"] = settings.ANTHROPIC_API_KEY

if settings.GOOGLE_API_KEY:
    os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY

llm = init_chat_model(
    model=settings.LLM_MODEL,
    model_provider=settings.LLM_PROVIDER,
    temperature=0.5,
)
