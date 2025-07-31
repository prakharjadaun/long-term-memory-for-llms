from typing import List, Annotated, Union
from memory_handler.azure_search_memory_handler import AzureSearchMemoryHandler
from llm_handler.openai_handler import OpenAIHandler
from utilities.llm_config_handler import find_llm_config
from providers.vector_db_provider import MemoryDocument
from loguru import logger


openai_handler_obj = OpenAIHandler(config_path=find_llm_config())

openai_handler_obj.init_client()

async def search_memory_tool(
    search_text: Annotated[str, "memory segment from the conversation"],
    category: Annotated[str, "category to which the search text belongs to"],
) -> Union[List[MemoryDocument],str]:
    try:
        logger.info("Searching in the memory...!")
        memory_handler_obj = await AzureSearchMemoryHandler.create()
        documents = await memory_handler_obj.vector_search(
            query_emb=(await openai_handler_obj.embed_inputs(inputs=[search_text]))[
                    "data"
                ][0]["embedding"],
            category=category
        )
        return documents
    except Exception as e:
        logger.exception(f"{e}")
        return f"Exception occured while searching in the memory: {e}"


search_memory_tool_definition = {
    "name": "search_memory",
    "description": "Search for memory item in the memory store",
    "parameters": {
        "type": "object",
        "properties": {
            "search_text": {"type": "string", "description": "relevant text that you want to search about"},
            "category": {
                "type": "string",
                "description": "category the search text belongs to",
            },
        },
        "required": ["search_text", "category"],
    },
}
