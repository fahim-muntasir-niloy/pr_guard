import os
from langchain.chat_models import init_chat_model
from pr_guard.config import settings

if settings.OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY

llm = init_chat_model(model="gpt-5")
