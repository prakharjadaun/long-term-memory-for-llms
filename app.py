import asyncio
import json
import os
import chainlit as cl
from loguru import logger
from agents.tools.check_token_count import check_token_count_tool, check_token_count_definition
from agents.tools.add_memory import add_memory_tool, add_memory_tool_definition
from agents.tools.search_memory import search_memory_tool, search_memory_tool_definition
from agents.tools.delete_memory import delete_memory_tool, delete_memory_tool_definition
from llm_handler.openai_handler import OpenAIHandler
from prompts.system_prompt import system_message
from utilities.llm_config_handler import find_llm_config

# Tool schema registrations
TOOLS = [
    {"type": "function", "function": add_memory_tool_definition},
    {"type": "function", "function": check_token_count_definition},
    {"type": "function", "function": search_memory_tool_definition},
    {"type": "function", "function": delete_memory_tool_definition},
]
TOOL_MAP = {
    add_memory_tool_definition["name"]: add_memory_tool,
    check_token_count_definition["name"]: check_token_count_tool,
    search_memory_tool_definition["name"]: search_memory_tool,
    delete_memory_tool_definition["name"]: delete_memory_tool,
}

@cl.on_chat_start
def start_chat():
    """Initialize session."""
    cl.user_session.set("chat_history", [{"role": "system", "content": system_message}])
    cl.user_session.set("openai_client", OpenAIHandler(config_path=find_llm_config()))

@cl.on_message
async def main(message: cl.Message):
    """Handle incoming user message, invoke agent loop."""
    history = cl.user_session.get("chat_history")
    history.append({"role": "user", "content": message.content})

    client: OpenAIHandler = cl.user_session.get("openai_client")
    await asyncio.to_thread(client.init_client)

    assistant_msg = cl.Message(content="")
    await assistant_msg.send()

    while True:
        resp = await client.chat_completion(
            messages=history,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.3,
            top_p=0.4,
            stream=True
        )

        # Initialize variables to collect response data
        assistant_content = ""
        tool_calls = None

        async for part in resp:
            if hasattr(part, 'choices') and part.choices:
                delta = part.choices[0].delta
                
                # Handling the content streaming
                if hasattr(delta, 'content') and delta.content:
                    assistant_content += delta.content
                    await assistant_msg.stream_token(delta.content)
                
                # Handling the tool calls
                if hasattr(delta, 'tool_calls') and delta.tool_calls:
                    if tool_calls is None:
                        tool_calls = []
                    
                    # Processing tool call deltas
                    for tc_delta in delta.tool_calls:
                        # Extend tool_calls list if needed
                        while len(tool_calls) <= tc_delta.index:
                            tool_calls.append({
                                "id": "",
                                "type": "function",
                                "function": {"name": "", "arguments": ""}
                            })
                        
                        # Updating tool call data
                        if tc_delta.id:
                            tool_calls[tc_delta.index]["id"] = tc_delta.id
                        if tc_delta.function:
                            if tc_delta.function.name:
                                tool_calls[tc_delta.index]["function"]["name"] = tc_delta.function.name
                            if tc_delta.function.arguments:
                                tool_calls[tc_delta.index]["function"]["arguments"] += tc_delta.function.arguments

        logger.info("Model streamed response.")

        if tool_calls:
            history.append({
                "role": "assistant", 
                "content": assistant_content if assistant_content else None,
                "tool_calls": tool_calls
            })

            for tc in tool_calls:
                tool_fn = TOOL_MAP.get(tc["function"]["name"])
                if not tool_fn:
                    logger.error(f"Unknown tool: {tc['function']['name']}")
                    continue
                
                try:
                    args = json.loads(tc["function"]["arguments"])
                    if tc["function"]["name"] == check_token_count_definition["name"]:
                        args["chat_history"] = history
                    if tc['function']['name'] == add_memory_tool_definition['name']:
                        args['chat_history'] = history

                    @cl.step(type="tool", name=tc["function"]["name"])
                    async def tool_step():
                        return await tool_fn(**args) if asyncio.iscoroutinefunction(tool_fn) else tool_fn(**args)

                    result = await tool_step()
                    logger.info("Tool result: %s", result)

                    # Add tool result to history
                    history.append({
                        "role": "tool",
                        "name": tc["function"]["name"],
                        "tool_call_id": tc["id"],
                        "content": json.dumps(result)
                    })
                except Exception as e:
                    logger.error(f"Error executing tool {tc['function']['name']}: {e}")
                    
                    # Adding error result to history
                    history.append({
                        "role": "tool",
                        "name": tc["function"]["name"],
                        "tool_call_id": tc["id"],
                        "content": json.dumps({"error": str(e)})
                    })
            
            continue
        else:
            if assistant_content:
                history.append({"role": "assistant", "content": assistant_content})
            return assistant_content