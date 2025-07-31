from typing import List, Annotated
from memory_handler.azure_search_memory_handler import AzureSearchMemoryHandler
from loguru import logger



async def delete_memory_tool(
    document_ids: Annotated[List[str], "List of document ids which has to be deleted"],
) -> Annotated[str, "Status message of the deletion operation"]:
    try:
        memory_handler_obj =  await AzureSearchMemoryHandler.create()
        logger.info("deleting memory from the memory store")
        status = await memory_handler_obj.delete_document(
            doc_ids=[{"id": doc_id} for doc_id in document_ids]
        )
        if status:
            logger.info("successfully deleted provided ids from the memory store")
            return "successfully deleted provided ids from the memory store"
        else:
            logger.warning("failed to delete the ids from memory store")
            return "failed to delete the ids from memory store"
    except Exception as e:
        logger.exception(f"{e}")
        return f"Exception occured while deleting memory: {e}"


delete_memory_tool_definition = {
    "name": "delete_memory",
    "description": "Delete memory items from the store",
    "parameters": {
        "type": "object",
        "properties": {
            "document_ids": {
                "type": "array",
                "description": "List of document ids which needs to be deleted from the memory",
                "items": {"type": "string"}
            }
        },
        "required": ["document_ids"],
    },
}
