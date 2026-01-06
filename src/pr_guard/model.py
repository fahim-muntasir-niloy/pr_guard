import os
from langchain.chat_models import init_chat_model
from pr_guard.config import settings
from rich import print

os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY

# llm = init_chat_model(model="gpt-5-mini")

llm = init_chat_model(model="gpt-5")

# print(llm.invoke("Hello, how are you?"))
