from langchain.agents import create_agent
from src.prompt import system_prompt
from src.model import llm
from src.tools import TOOLS

async def init_agent():
    agent = create_agent(
        tools=TOOLS,
        model=llm,
        system_prompt=system_prompt,
    )
    return agent