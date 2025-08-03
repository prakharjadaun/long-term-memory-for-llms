import json
import ast
from typing import Annotated
from loguru import logger

async def is_valid_ast_literal(
    response: Annotated[str, "LLM JSON Response in string"]
) -> Annotated[bool,"Whether LLM response is valid ast literal or not"]:
    try:
        ast.literal_eval(response)
        return True
    except Exception as e:
        return False
    

async def jsonize_response(
    response: Annotated[str, ""]
) -> Annotated[dict, "JSON Response"]:
    try:
        if await is_valid_ast_literal(response):
            return ast.literal_eval(response)
        else:
            return json.loads(response)
    except Exception as e:
        logger.exception(f"Exception occured while jsonizing the llm response: {e}")