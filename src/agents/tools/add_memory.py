from typing import List, Annotated
from memory_handler.azure_search_memory_handler import AzureSearchMemoryHandler
from llm_handler.openai_handler import OpenAIHandler
from utilities.llm_config_handler import find_llm_config
from providers.vector_db_provider import MemoryDocument
from loguru import logger
from uuid import uuid1
import datetime
import asyncio

openai_handler_obj = OpenAIHandler(config_path=find_llm_config())

openai_handler_obj.init_client()

async def add_memory_tool(
    memory: Annotated[str, "memory segment from the conversation"],
    category: Annotated[str, "category to which the memory segment belongs to"],
) -> str:
    try:
        memory_handler_obj =  await AzureSearchMemoryHandler.create()
        logger.info("adding memory to the memory store")
        status = await memory_handler_obj.add_documents(
            docs=[MemoryDocument(id=str(uuid1()).split("-")[0],
                memory=memory,
                category=category,
                embeddings=(await openai_handler_obj.embed_inputs(inputs=[memory]))[
                    "data"
                ][0]["embedding"],
                time=datetime.datetime.now(),
            )]
        )
        if status:
            logger.info("successfully added to the memory store")
            return "successfully added to the memory store"
        else:
            logger.warning("failed to add the segment to memory store")
            return "failed to add the segment to memory store"
    except Exception as e:
        logger.exception(f"{e}")
        return f"Exception occured while adding memory: {e}"


add_memory_tool_definition = {
    "name": "add_memory",
    "description": "Add a memory item to the store",
    "parameters": {
        "type": "object",
        "properties": {
            "memory": {"type": "string", "description": "relevant memory segment"},
            "category": {
                "type": "string",
                "description": "category the memory segment belongs to",
            },
        },
        "required": ["memory", "category"],
    },
}

if __name__=='__main__':
    asyncio.run(add_memory_tool(memory="my name is prakhar",category="general_info"))