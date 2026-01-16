import json
from typing import AsyncGenerator
from langchain.messages import AIMessageChunk
import uuid
from pr_guard.cli.utils import token_processor


async def review_event_generator(agent) -> AsyncGenerator[str, None]:
    """
    Generator for PR review events (tools and final report).
    """
    async for chunk in agent.astream(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "Execute a full code review for the latest git commits. Call the tools needed to understand the scope and diff.",
                }
            ]
        },
        stream_mode="updates",
    ):
        for node_name, update in chunk.items():
            # Stream tool calls or progress
            if "messages" in update:
                last_msg = update["messages"][-1]
                if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                    for tc in last_msg.tool_calls:
                        yield f"data: {json.dumps({'type': 'tool_call', 'name': tc['name'], 'args': tc['args']})}\n\n"

            # Stream the final structured response when available
            if "structured_response" in update:
                res = update["structured_response"]
                yield f"data: {json.dumps({'type': 'report', 'content': res.model_dump()})}\n\n"


async def chat_event_generator(
    agent, message: str, thread_id: str
) -> AsyncGenerator[str, None]:
    """
    Generator for chat events (tools and tokens).
    """
    async for chunk in agent.astream(
        {"messages": [{"role": "user", "content": message}]},
        stream_mode=["updates", "messages"],
        config={"configurable": {"thread_id": thread_id}},
    ):
        stream_mode_name, data = chunk
        if stream_mode_name == "updates":
            for step_name, step_data in data.items():
                if step_data and "messages" in step_data:
                    latest_msg = step_data["messages"][-1]
                    if hasattr(latest_msg, "tool_calls") and latest_msg.tool_calls:
                        for tc in latest_msg.tool_calls:
                            yield f"data: {json.dumps({'type': 'tool_call', 'name': tc.get('name')})}\n\n"
        elif stream_mode_name == "messages":
            msg, metadata = data
            if isinstance(msg, AIMessageChunk) and msg.content:
                token = token_processor(msg.content)
                if token:
                    yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
