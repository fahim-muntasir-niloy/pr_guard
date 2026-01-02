from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain.agents.middleware import ToolCallLimitMiddleware

from src.prompt import system_prompt
from src.model import llm
from src.tools import TOOLS
from src.schema.response import pr_agent_response


async def init_agent():
    agent = create_agent(
        tools=TOOLS,
        model=llm,
        system_prompt=system_prompt,
        # middleware=[ToolCallLimitMiddleware(run_limit=10)],
        name="PR_Guard_Agent",
        response_format=ToolStrategy(pr_agent_response),
    )
    return agent
