import logging
import os
from typing import Dict, List, Optional

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from app.config import get_settings


logger = logging.getLogger(__name__)

COLLECTION_NAME = "marketmate_sales"


class VectorStoreError(Exception):
    """Raised when a ChromaDB operation fails."""


class VectorStore:
    def __init__(self) -> None:
        settings = get_settings()
        try:
            os.makedirs(settings.chroma_persist_dir, exist_ok=True)
            self._client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
            self._embedding_fn = SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
            self._collection = self._client.get_or_create_collection(
                name=COLLECTION_NAME,
                embedding_function=self._embedding_fn,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(
                "VectorStore initialised: persist_dir=%s collection=%s documents=%d",
                settings.chroma_persist_dir,
                COLLECTION_NAME,
                self._collection.count(),
            )
        except Exception as exc:
            logger.error("Failed to initialise VectorStore: %s", exc)
            raise VectorStoreError(f"VectorStore init failed: {exc}") from exc

    def add_documents(self, documents: List[Dict]) -> None:
        if not documents:
            logger.warning("add_documents called with empty list")
            return
        try:
            ids = [doc["id"] for doc in documents]
            texts = [doc["text"] for doc in documents]
            metadatas = [doc.get("metadata", {}) for doc in documents]
            self._collection.upsert(ids=ids, documents=texts, metadatas=metadatas)
            logger.info("Upserted %d documents into ChromaDB", len(documents))
        except Exception as exc:
            logger.error("ChromaDB add_documents error: %s", exc)
            raise VectorStoreError(f"add_documents failed: {exc}") from exc

    def query(self, query_text: str, n_results: int = 4) -> List[Dict]:
        try:
            results = self._collection.query(
                query_texts=[query_text],
                n_results=min(n_results, max(self._collection.count(), 1)),
                include=["documents", "metadatas", "distances"],
            )
            output: List[Dict] = []
            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            dists = results.get("distances", [[]])[0]
            for text, meta, dist in zip(docs, metas, dists):
                output.append({"text": text, "metadata": meta, "distance": dist})
            return output
        except Exception as exc:
            logger.error("ChromaDB query error: %s", exc)
            raise VectorStoreError(f"query failed: {exc}") from exc

    def collection_exists(self) -> bool:
        try:
            names = [c.name for c in self._client.list_collections()]
            return COLLECTION_NAME in names
        except Exception as exc:
            logger.error("ChromaDB list_collections error: %s", exc)
            return False

    def document_count(self) -> int:
        try:
            return self._collection.count()
        except Exception as exc:
            logger.error("ChromaDB count error: %s", exc)
            return 0


_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
