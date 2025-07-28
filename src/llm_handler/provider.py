# provider.py

import os
import yaml
from typing import Literal, Optional
from pydantic import BaseModel, Field, ValidationError
from loguru import logger
from openai import AsyncOpenAI, AsyncAzureOpenAI
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
load_dotenv(override=True)

class OpenAIConfig(BaseModel):
    api_key: str
    api_base: Optional[str] = None

class AzureConfig(BaseModel):
    api_key: str
    endpoint: str
    api_version: str
    chat_deployment: str
    embedding_deployment: str
    embedding_api_version: Optional[str] = None

class LLMProviderConfig(BaseSettings):
    provider: Literal["azure", "openai"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra fields from YAML

class LLMProvider:
    """
    Initializes and exposes an async LLM client based on provider configuration.
    Supports both Azure OpenAI and standard OpenAI via async clients.
    """

    def __init__(self, config_path: str = "llm_config.yaml"):
        logger.info("Loading configuration from {}", config_path)
        try:
            with open(config_path, "r") as f:
                raw = yaml.safe_load(f)
            self.cfg = LLMProviderConfig(**raw)
            
            # Load provider-specific config directly from environment
            if self.cfg.provider == "azure":
                self.azure_config = AzureConfig(
                    api_key=os.getenv("AZURE_OAI_KEY"),
                    endpoint=os.getenv("AZURE_OAI_ENDPOINT"),
                    api_version=os.getenv("AZURE_OAI_API_VERSION"),
                    chat_deployment=os.getenv("AZURE_OAI_DEPLOYMENT_NAME"),
                    embedding_deployment=os.getenv("AZURE_OAI_EMBEDDING_DEPLOYMENT_NAME"),
                    embedding_api_version=os.getenv("AZURE_OAI_EMBEDDING_API_VERSION")
                )
                self.openai_config = None
                logger.info("Azure config loaded from environment")
            elif self.cfg.provider == "openai":
                self.openai_config = OpenAIConfig(
                    api_key=os.getenv("OPENAI_API_KEY"),
                    api_base=os.getenv("OPENAI_API_BASE")
                )
                self.azure_config = None
                logger.info("OpenAI config loaded from environment")
            
            logger.info("Config loaded: provider={}", self.cfg.provider)
        except FileNotFoundError:
            logger.exception("Configuration file not found: {}", config_path)
            raise
        except ValidationError as e:
            logger.exception("Configuration validation error: {}", e.json())
            raise
        except Exception as e:
            logger.exception("Error loading configuration: {}", e)
            raise

        self.client = None

    async def init_client(self) -> None:
        """
        Validates and initializes async client for the selected provider.
        """
        try:
            if self.cfg.provider == "azure":
                assert self.azure_config is not None
                self.client = AsyncAzureOpenAI(
                    api_key=self.azure_config.api_key,
                    azure_endpoint=self.azure_config.endpoint,
                    api_version=self.azure_config.api_version,
                )
                logger.info("AsyncAzureOpenAI client initialized")
            elif self.cfg.provider == "openai":
                assert self.openai_config is not None
                kwargs = {"api_key": self.openai_config.api_key}
                if self.openai_config.api_base:
                    kwargs["api_base"] = self.openai_config.api_base
                self.client = AsyncOpenAI(**kwargs)
                logger.info("AsyncOpenAI client initialized")
            else:
                raise ValueError(f"Unsupported provider: {self.cfg.provider}")
        except Exception as e:
            logger.exception("Failed to initialize client")
            raise

    async def chat_completion(self, messages: list[dict], **kwargs) -> dict:
        """
        Send chat completion request via the selected client.
        """
        if self.client is None:
            raise RuntimeError("Client not initialized; call init_client() first")

        try:
            if self.cfg.provider == "azure":
                resp = await self.client.chat.completions.create(
                    model=self.azure_config.chat_deployment,
                    messages=messages,
                    **kwargs
                )
            else:
                resp = await self.client.chat.completions.create(
                    model=kwargs.pop("model", None),
                    messages=messages,
                    **kwargs
                )
            logger.info("LLM chat_completion response received")
            return resp.model_dump() if hasattr(resp, "model_dump") else resp
        except Exception as e:
            logger.exception("Error during chat_completion call")
            raise

    async def embed_inputs(self, inputs: list[str], **kwargs) -> dict:
        """
        Generate embeddings via selected provider client.
        """
        if self.client is None:
            raise RuntimeError("Client not initialized; call init_client() first")

        try:
            if self.cfg.provider == "azure":
                resp = await self.client.embeddings.create(
                    model=self.azure_config.embedding_deployment,
                    input=inputs,
                    # **{"api_version": self.azure_config.embedding_api_version or self.azure_config.api_version, **kwargs}
                )
            else:
                resp = await self.client.embeddings.create(
                    model=kwargs.pop("model", None),
                    input=inputs,
                    **kwargs
                )
            logger.info("LLM embed_inputs response received")
            return resp.model_dump() if hasattr(resp, "model_dump") else resp
        except Exception as e:
            logger.exception("Error during embed_inputs call")
            raise


if __name__ == "__main__":
    import asyncio
    async def main():
        provider = LLMProvider(config_path="../../llm_config.yaml")
        try:
            await provider.init_client()
        except Exception:
            logger.error("Initialization failed, exiting.")
            return

        # Test chat
        try:
            resp = await provider.chat_completion(
                messages=[{"role": "user", "content": "Say hello"}],
                temperature=0.0
            )
            logger.info("Chat response: {}", resp)
        except Exception:
            logger.error("Chat completion test failed.")

        # Test embeddings
        try:
            emb = await provider.embed_inputs(["Hello world", "Test"])
            logger.info("Embedding response: {}", emb)
        except Exception:
            logger.error("Embedding test failed.")

    asyncio.run(main())