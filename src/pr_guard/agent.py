from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain.agents.middleware import ToolCallLimitMiddleware
from langgraph.checkpoint.memory import InMemorySaver

from pr_guard.prompt import review_prompt, cli_prompt
from pr_guard.model import llm
from pr_guard.tools import TOOLS
from pr_guard.schema.response import GitHubPRReview


async def init_review_agent():
    agent = create_agent(
        tools=TOOLS,
        model=llm,
        system_prompt=review_prompt,
        # middleware=[ToolCallLimitMiddleware(run_limit=5)],
        name="PR_Guard_Agent",
        response_format=ToolStrategy(GitHubPRReview),
    )
    return agent


async def chat_agent():
    agent = create_agent(
        tools=TOOLS,
        model=llm,
        system_prompt=cli_prompt,
        # middleware=[ToolCallLimitMiddleware(run_limit=5)],
        name="PR_Guard_Agent",
        checkpointer=InMemorySaver(),
    )
    return agent


async def one_click_pr_agent():
    agent = create_agent(
        tools=TOOLS,
        model=llm,
        system_prompt="You are an automated GitHub Pull Request generator. You dont ask questions, just do what is told to you.",
        # middleware=[ToolCallLimitMiddleware(run_limit=5)],
        name="PR_Guard_Agent",
        checkpointer=InMemorySaver(),
    )
    return agent
