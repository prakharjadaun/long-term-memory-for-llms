import tiktoken
import os
from dotenv import load_dotenv
load_dotenv(override=True)

TOKEN_LIMIT = int(os.getenv('TOKEN_LIMIT'))

async def check_token_count_tool(chat_history):
    global TOKEN_LIMIT
    enc = tiktoken.encoding_for_model("gpt-4o")
    
    def count_tokens(msg):
        if msg["role"] == "system":
            return 0
        elif msg["role"] == "tool":
            return len(enc.encode(msg.get("content", "")))
        elif msg["role"] == "assistant" and "tool_calls" in msg:
            return sum(
                len(enc.encode(str(tc.get("function", {}).get("arguments", ""))))
                for tc in msg["tool_calls"]
            )
        else:
            return len(enc.encode(msg.get("content", "")))

    total_tokens = sum(count_tokens(m) for m in chat_history)

    if total_tokens > TOKEN_LIMIT:
        return {"status": "exceeds-limit", "tokens": total_tokens}
    else:
        return {"status": "within-limit", "tokens": total_tokens}


check_token_count_definition = {
    "name": "check_token_count",
    "description": "Checks total token count in the chat history and returns the status whether the chat history is within the limit or exceeds the limit.",
    "parameters": {
        "type": "object",
        "properties": {
        },
        "required": []
    }
}

if __name__=='__main__':
    import json
    import asyncio

    with open("../content.json","r") as f:
        chat_history = json.load(f)
    
    response = asyncio.run(check_token_count_tool(chat_history=chat_history))
    
    print(response)