import os
from langchain.chat_models import init_chat_model
from pr_guard.config import settings

if settings.OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY

if settings.XAI_API_KEY:
    os.environ["XAI_API_KEY"] = settings.XAI_API_KEY

# llm = init_chat_model(model="gpt-5")

llm = init_chat_model(
    model="grok-4-1-fast-reasoning", model_provider="xai", temperature=0.5
)
