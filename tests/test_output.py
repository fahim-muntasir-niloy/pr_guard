import asyncio
from src.agent import init_agent
from rich import print

async def test_structured_output():
    print("Testing Structured Output...")
    agent = await init_agent()
    result = await agent.ainvoke({"messages": [{"role": "user", "content": "Just say 'Hello' and give a verdict 'Approve' with no changes."}]})
    print(result["structured_response"])

if __name__ == "__main__":
    asyncio.run(test_structured_output())
