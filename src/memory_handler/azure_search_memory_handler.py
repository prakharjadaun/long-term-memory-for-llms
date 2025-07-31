import os
from typing import List
from datetime import datetime
from loguru import logger
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes.aio import SearchIndexClient
from azure.search.documents.aio import SearchClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
    SearchFieldDataType,
    SearchField,
    VectorSearchProfile,
    VectorSearchAlgorithmKind,
    HnswParameters,
    VectorSearchAlgorithmMetric,
    ExhaustiveKnnParameters,
    ExhaustiveKnnAlgorithmConfiguration,
    SemanticConfiguration,
    SemanticField,
    SemanticSearch,
    SemanticPrioritizedFields,
)
from azure.search.documents.models import VectorizedQuery
from providers.vector_db_provider import VectorDBProvider, MemoryDocument
from dotenv import load_dotenv
from utilities.llm_config_handler import find_llm_config

load_dotenv(override=True)


class AzureSearchMemoryHandler(VectorDBProvider):
    """
    Azure-based memory handler implementing index creation,
    document ingestion, vector search, and deletion.
    """

    # def __init__(self):
    #     logger.info("Initializing AzureSearchMemoryHandler")
    #     self.endpoint = os.getenv("AZURE_AI_SEARCH_ENDPOINT")
    #     key = os.getenv("AZURE_AI_SEARCH_KEY")
    #     self.cred = AzureKeyCredential(key)
    #     self.idx_client = SearchIndexClient(
    #         endpoint=self.endpoint, credential=self.cred
    #     )
    #     self.index_name = os.getenv("INDEX_NAME")
    #     self.search_client: SearchClient | None = None

    def __init__(self):
        # synchronous setup only
        pass
    
    @classmethod
    async def create(cls):
        self = cls()
        self.endpoint = os.getenv("AZURE_AI_SEARCH_ENDPOINT")
        self.key = os.getenv("AZURE_AI_SEARCH_KEY")
        self.index_name = os.getenv("INDEX_NAME")
        self.cred = AzureKeyCredential(self.key)
        self.idx_client = SearchIndexClient(
            endpoint=self.endpoint, credential=self.cred
        )
        self.search_client = None
        success = await self.create_index(dims=1536)
        if not success:
            raise RuntimeError("Index setup failed")
        return self

    async def index_exists(self) -> bool:
        try:
            idxs = self.idx_client.list_indexes()
            names = [idx.name async for idx in idxs]
            exists = self.index_name in names
            logger.info("Index '{}' exists? {}", self.index_name, exists)
            return exists
        except Exception:
            logger.exception("Error checking index existence: {}", self.index_name)
            return False

    async def create_index(self, dims: int = 1536) -> bool:
        try:
            fields = [
                SimpleField(
                    name="id",
                    type=SearchFieldDataType.String,
                    key=True,
                    sortable=True,
                    filterable=True,
                    facetable=True,
                ),
                SearchField(
                    name="media_url",
                    type=SearchFieldDataType.String,
                    sortable=True,
                    filterable=True,
                    facetable=True,
                ),
                SearchField(name="memory", type=SearchFieldDataType.String),
                SearchField(
                    name="category", type=SearchFieldDataType.String, filterable=True
                ),
                SearchField(
                    name="time",
                    type=SearchFieldDataType.DateTimeOffset,
                    filterable=True,
                ),
                SearchField(
                    name="embeddings",
                    type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                    searchable=True,
                    vector_search_dimensions=dims,
                    vector_search_profile_name="embedding_profile",
                ),
            ]

            vector_search = VectorSearch(
                algorithms=[
                    HnswAlgorithmConfiguration(
                        name="hnsw_config",
                        kind=VectorSearchAlgorithmKind.HNSW,
                        parameters=HnswParameters(
                            m=4,
                            ef_construction=400,
                            ef_search=500,
                            metric=VectorSearchAlgorithmMetric.COSINE,
                        ),
                    ),
                    ExhaustiveKnnAlgorithmConfiguration(
                        name="myExhaustiveKnn",
                        parameters=ExhaustiveKnnParameters(
                            metric=VectorSearchAlgorithmMetric.COSINE
                        ),
                    ),
                ],
                profiles=[
                    VectorSearchProfile(
                        name="embedding_profile",
                        algorithm_configuration_name="hnsw_config",
                    ),
                    VectorSearchProfile(
                        name="myExhaustiveKnnProfile",
                        algorithm_configuration_name="myExhaustiveKnn",
                    ),
                ],
            )

            semantic_config = SemanticConfiguration(
                name="my-semantic-config",
                prioritized_fields=SemanticPrioritizedFields(
                    content_fields=[SemanticField(field_name="memory")],
                    keywords_fields=[SemanticField(field_name="category")],
                ),
            )

            semantic_search = SemanticSearch(configurations=[semantic_config])

            idx = SearchIndex(
                name=self.index_name,
                fields=fields,
                vector_search=vector_search,
                semantic_search=semantic_search,
            )
            await self.idx_client.create_or_update_index(idx)
            self.search_client = SearchClient(self.endpoint, self.index_name, self.cred)
            logger.info("Index '{}' created", self.index_name)
            return True
        except Exception:
            logger.exception("Failed to create index '{}'", self.index_name)
            return False

    async def add_documents(self, docs: List[MemoryDocument]) -> bool:
        assert self.search_client
        try:
            payload = []
            for doc in docs:
                doc = doc.dict()
                if 'time' not in doc:
                    doc['time'] = datetime.now()
                payload.append(doc)

            res = await self.search_client.upload_documents(documents=payload)
            succeeded = all(r.succeeded for r in res)
            logger.info(
                "Uploaded {} docs to '{}', success={}",
                len(payload),
                self.index_name,
                succeeded,
            )
            return succeeded
        except Exception:
            logger.exception("Failed to upload documents to '{}'", self.index_name)
            return False

    async def vector_search(
        self,
        query_emb: List[float],
        top_k: int = 5,
        exhaustive: bool = False,
        category: str | None = None,
    ) -> List[MemoryDocument]:
        assert self.search_client
        try:

            vector_query = VectorizedQuery(
                vector=query_emb, k_nearest_neighbors=top_k, fields="embeddings"
            )

            filter_expr = f"category eq '{category}'" if category else None

            results = await self.search_client.search(
                search_text=None,
                vector_queries=[vector_query],
                top=top_k,
                query_type="semantic",
                filter=filter_expr,
                semantic_configuration_name="my-semantic-config",
            )

            docs = []
            async for r in results:
                docs.append(
                    MemoryDocument(
                        id=r["id"],
                        memory=r["memory"],
                        embeddings=None,
                        category=r['category'],
                        time=r['time']
                    )
                )
            logger.info("Vector search returned {} results", len(docs))

            return docs
        except Exception:
            logger.exception("Vector search failed on '{}'", self.index_name)
            return []

    async def delete_document(self, doc_ids: List[str]) -> bool:
        assert self.search_client
        try:
            res = await self.search_client.delete_documents(documents=doc_ids)
            succeeded = all(r.succeeded for r in res)
            logger.info(
                "Deleted document '{}' from '{}', success={}",
                doc_ids,
                self.index_name,
                succeeded,
            )
            return True
        except Exception:
            logger.exception(
                "Deletion failed for doc '{}' in '{}'", doc_ids, self.index_name
            )
            return False


if __name__ == "__main__":
    import asyncio
    from pydantic import BaseModel
    from llm_handler.openai_handler import OpenAIHandler

    async def main():
        logger.info(find_llm_config())
        openai_handler = OpenAIHandler(config_path=find_llm_config())
        try:
            openai_handler.init_client()
        except Exception:
            logger.error("Initialization failed, exiting.")
            return
        handler = AzureSearchMemoryHandler()

        await handler.create_index()

        memory = "My name is prakhar"
        embedding = await openai_handler.embed_inputs(inputs=[memory])
        doc = MemoryDocument(
            id="1",
            memory=memory,
            embeddings=embedding["data"][0]["embedding"],
            category="general_info",
            time=datetime.now(),
        )

        await handler.add_documents(docs=[doc])
        results = await handler.vector_search(
            query_emb=embedding["data"][0]["embedding"], top_k=3, category="general_info"
        )
        for res in results:
            print(res)

        await handler.delete_document(doc_ids=[{"id":"1"}])

    asyncio.run(main())
