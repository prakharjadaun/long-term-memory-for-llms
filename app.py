import chainlit as cl
import os
from dotenv import load_dotenv
from loguru import logger
load_dotenv(override=True)


@cl.on_message
async def main(message: cl.Message):

    # Send a response back to the user
    await cl.Message(
        content=f"Received: {message.content}",
    ).send()


