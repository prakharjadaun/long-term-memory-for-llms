# services/vector_db_provider.py
from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class MemoryDocument(BaseModel):
    id: str
    memory: str
    embeddings: List[float]
    category: Optional[str]
    time: datetime


class VectorDBProvider(ABC):
    """Abstract interface for vector‑db memory providers."""

    @abstractmethod
    async def create_index(self, dims: int) -> bool:
        """Return True if index created (or already exists)."""

    @abstractmethod
    async def index_exists(self) -> bool:
        """Return True if an index with that name exists."""

    @abstractmethod
    async def add_documents(self, docs: List[MemoryDocument]) -> bool:
        """Upload or upsert memory documents."""

    @abstractmethod
    async def vector_search(
        self,
        query_emb: List[float],
        top_k: int = 5,
        exhaustive: bool = False,
        category: str = None,
    ) -> List[MemoryDocument]:
        """Return top-k similar documents."""

    @abstractmethod
    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document by its unique id."""
