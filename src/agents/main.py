import asyncio
from loguru import logger
from llm_handler.openai_handler import OpenAIHandler
from prompts.system_prompt import system_message
from agents.tools.add_memory import add_memory_tool, add_memory_tool_definition
from agents.tools.search_memory import search_memory_tool, search_memory_tool_definition
from agents.tools.delete_memory import delete_memory_tool, delete_memory_tool_definition
from utilities.llm_config_handler import find_llm_config
import json

tools = [
    {"type": "function", "function": add_memory_tool_definition},
    {"type": "function", "function": search_memory_tool_definition},
    {"type": "function", "function": delete_memory_tool_definition},
]

tool_mapping = {
    add_memory_tool_definition["name"]: add_memory_tool,
    search_memory_tool_definition["name"]: search_memory_tool,
    delete_memory_tool_definition["name"]: delete_memory_tool,
}

client = OpenAIHandler(config_path=find_llm_config())
client.init_client()


async def run_agent_loop(user_input: str) -> str:
    """
    Runs the agent loop: model call -> function call -> tool invocation -> final response.
    """
   
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_input}
    ]

    while True:
        resp = await client.chat_completion(
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.3,
            top_p=0.4
        )
        logger.info("Model response: {}", resp)

        choice = resp["choices"][0]
        msg = choice["message"]

        # Check if the model wants to call a tool
        if msg.get("tool_calls"):
            for tc in msg["tool_calls"]:
                fname = tc["function"]["name"]
                args = json.loads(tc["function"]["arguments"])
                
                messages.append({
                    "role":"assistant","tool_calls": [tc]
                    })
                result = await tool_mapping[fname](**args)

                messages.append({
                    "role": "tool",
                    "name": fname,
                    "tool_call_id": tc["id"],
                    "content": json.dumps(result)
                })
            continue  # Loop again with updated messages
        else:
            return msg.get("content", "")

if __name__ == "__main__":
    logger.info("Starting interactive memory agent. Type 'exit' to quit.")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            print("Exiting.")
            break
        try:
            response = asyncio.run(run_agent_loop(user_input))
            print("Assistant:", response)
        except Exception as e:
            logger.exception("Error in conversation loop")
            print("An error occurred. See logs.")
