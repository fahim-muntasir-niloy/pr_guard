import os
import asyncio
from src.agent import init_agent
from rich import print
from src.config import settings
from src.api import app

os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGSMITH_API_KEY"] = settings.LANGSMITH_API_KEY
os.environ["LANGSMITH_PROJECT"] = "pr-agent"


async def main():
    print("Initializing PR Guard Agent...")
    try:
        agent = await init_agent()
        print("Agent initialized successfully with tools")

        result = await agent.ainvoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": """Execute a pre-merge code review for the latest git commit.

                                        You must:
                                        - Use git tools to identify changed files
                                        - Review only modified lines and their immediate context
                                        - Produce GitHub-style diff comments
                                        - Assign severity to each issue
                                        - Output only valid `pr_agent_response` JSON

                                        Do not explain your process.
                                        """,
                    }
                ]
            }
        )
        print(result["structured_response"])

    except Exception as e:
        print(f"Failed to initialize agent: {e}")


if __name__ == "__main__":
    # import uvicorn
    asyncio.run(main())
    # uvicorn.run(app, host="0.0.0.0", port=8000)
