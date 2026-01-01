import asyncio
from src.agent import init_agent
from rich import print
import os

os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGSMITH_API_KEY"] = "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"
os.environ["LANGSMITH_PROJECT"] = "pr-agent"


async def main():
    print("Initializing PR Guard Agent...")
    try:
        agent = await init_agent()
        print("Agent initialized successfully with tools")
            
        # Optional: Test a simple command if you want to see it in action
        response = await agent.ainvoke({"input": "What files are in this directory?"})
        print(response)

    except Exception as e:
        print(f"Failed to initialize agent: {e}")

if __name__ == "__main__":
    asyncio.run(main())
