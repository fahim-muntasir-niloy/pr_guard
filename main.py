import asyncio
from src.agent import init_agent
from rich import print
import os
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
            
        # Optional: Test a simple command if you want to see it in action
        response = await agent.ainvoke({"input": "Give a short review on this last git push"})
        print(response)

    except Exception as e:
        print(f"Failed to initialize agent: {e}")

if __name__ == "__main__":
    # import uvicorn
    asyncio.run(main())
    # uvicorn.run(app, host="0.0.0.0", port=8000)
