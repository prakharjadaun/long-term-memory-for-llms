# llm_provider.py
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    """
    Initializes and exposes an async LLM client based on provider configuration.
    """
    
    @abstractmethod
    async def init_client(self) -> None:
        """
        Validates and initializes async client for the selected provider.
        """
        

    @abstractmethod
    async def chat_completion(self, messages: list[dict], **kwargs) -> dict:
        """
        Send chat completion request via the selected client.
        """
        
    async def embed_inputs(self, inputs: list[str], **kwargs) -> dict:
        """
        Generate embeddings via selected provider client.
        """
        