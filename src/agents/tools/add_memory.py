from typing import List, Annotated
from memory_handler.azure_search_memory_handler import AzureSearchMemoryHandler
from llm_handler.openai_handler import OpenAIHandler
from utilities.llm_config_handler import find_llm_config
from providers.vector_db_provider import MemoryDocument
from loguru import logger
from uuid import uuid1
import datetime
import asyncio
from prompts.chat_history_summary_prompt import chat_history_summary_prompt
from utilities.llm_helper import jsonize_response
openai_handler_obj = OpenAIHandler(config_path=find_llm_config())

openai_handler_obj.init_client()

async def add_memory_tool(
    chat_history: Annotated[List[dict], "Chat history"]
) -> bool:
    try:
        memory_handler_obj =  await AzureSearchMemoryHandler.create()
        logger.info("adding memory to the memory store")
        messages = [{"role": "system", "content": chat_history_summary_prompt},{"role": "user","content":f"chat history: >>>{chat_history}<<<"}]  
        memory_summary = await openai_handler_obj.chat_completion(
            messages=messages,
            response_format={"type":"json_object"},
            temperature=0.2,
            top_p=0.4,
            seed=42
        ) 
        memory_summary =  await jsonize_response(memory_summary['choices'][0]['message']['content'])
        memory_documents = [MemoryDocument(id=str(uuid1()).split("-")[0],
                memory=obj['memory'],
                category=obj['category'],
                embeddings=(await openai_handler_obj.embed_inputs(inputs=[obj['memory']]))[
                    "data"
                ][0]["embedding"],
                time=datetime.datetime.now(),
            ) 
            for obj in memory_summary['segments']
        ]
        status = await memory_handler_obj.add_documents(
            docs=memory_documents
        )
        if status:
            logger.info("successfully added to the memory store")
            return {"status": "successfully added to the memory store", "chat_history": chat_history[:1]}
        else:
            logger.warning("failed to add the segment to memory store")
            return {"status": "failed to add the segment to memory store", "chat_history": chat_history}
    except Exception as e:
        logger.exception(f"{e}")
        return {"status": f"Exception occured while adding memory: {e}", "chat_history": chat_history}



add_memory_tool_definition = {
    "name": "add_memory",
    "description": "Adds the chat history to the memory vector store and returns the status of addition of the memory",
    "parameters": {
        "type": "object",
        "properties": {
        },
        "required": []
    }
}

if __name__=='__main__':
    import json
    with open("../content.json","r") as f:
        chat_history = json.load(f)

    response = asyncio.run(add_memory_tool(chat_histoy=chat_history))
    print(response)