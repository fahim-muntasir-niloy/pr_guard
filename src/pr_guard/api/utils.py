import json
from typing import AsyncGenerator
from langchain.messages import AIMessageChunk
from pr_guard.cli.utils import token_processor


async def review_event_generator(agent) -> AsyncGenerator[str, None]:
    """
    Generator for PR review events (tools and final report).
    """
    try:
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
                            if "args" in tc and tc["args"]:
                                yield f"data: {json.dumps({'type': 'tool_call', 'name': tc['name'], 'args': tc['args']})}\n\n"

                # Stream the final structured response when available
                if "structured_response" in update:
                    res = update["structured_response"]
                    yield f"data: {json.dumps({'type': 'report', 'content': res.model_dump()})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'content': f'AI Review Error: {str(e)}'})}\n\n"


async def chat_event_generator(
    agent, message: str, thread_id: str
) -> AsyncGenerator[str, None]:
    try:
        async for chunk in agent.astream(
            {"messages": [{"role": "user", "content": message}]},
            stream_mode=["updates", "messages"],
            config={"configurable": {"thread_id": thread_id}},
        ):
            stream_mode, data = chunk

            # 1. Tool calls (intent + args)
            if stream_mode == "updates":
                for _, step_data in data.items():
                    if not step_data or "messages" not in step_data:
                        continue

                    last_msg = step_data["messages"][-1]

                    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                        for tc in last_msg.tool_calls:
                            if "args" in tc and tc.get("args"):
                                yield f"data: {
                                    json.dumps(
                                        {
                                            'type': 'tool_call',
                                            'name': tc.get('name'),
                                            'args': tc.get('args'),
                                        }
                                    )
                                }\n\n"

            # 2. AI token streaming
            elif stream_mode == "messages":
                msg, metadata = data

                # Stream tokens only
                if isinstance(msg, AIMessageChunk) and msg.content:
                    token = token_processor(msg.content)
                    if token:
                        yield f"data: {
                            json.dumps(
                                {
                                    'type': 'token',
                                    'content': token,
                                }
                            )
                        }\n\n"

                # Ignore ToolMessage and full AIMessage
                else:
                    continue
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'content': f'AI Chat Error: {str(e)}'})}\n\n"


async def pr_event_generator(agent, message: str) -> AsyncGenerator[str, None]:
    try:
        async for chunk in agent.astream(
            {"messages": [{"role": "user", "content": message}]},
            stream_mode=["updates", "messages"],
        ):
            stream_mode, data = chunk

            # 1. Tool calls (intent + args)
            if stream_mode == "updates":
                for _, step_data in data.items():
                    if not step_data or "messages" not in step_data:
                        continue

                    last_msg = step_data["messages"][-1]

                    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                        for tc in last_msg.tool_calls:
                            if "args" in tc and tc.get("args"):
                                yield f"data: {
                                    json.dumps(
                                        {
                                            'type': 'tool_call',
                                            'name': tc.get('name'),
                                            'args': tc.get('args'),
                                        }
                                    )
                                }\n\n"

            # 2. AI token streaming
            elif stream_mode == "messages":
                msg, metadata = data

                # Stream tokens only
                if isinstance(msg, AIMessageChunk) and msg.content:
                    token = token_processor(msg.content)
                    if token:
                        yield f"data: {
                            json.dumps(
                                {
                                    'type': 'token',
                                    'content': token,
                                }
                            )
                        }\n\n"

                # Ignore ToolMessage and full AIMessage
                else:
                    continue
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'content': f'PR Generation Error: {str(e)}'})}\n\n"
