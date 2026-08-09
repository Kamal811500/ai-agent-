"""
ChromaDB Vector Retriever integration for RAG technical knowledge indexing.
Supports vector embedding search and keyword fallback.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False
    logger.info("ChromaDB not available — TF-IDF vector retriever active.")


class ChromaVectorRetriever:
    """
    ChromaDB Vector Store Retriever for RAG.
    Maintains embeddings of technical curriculum documents for semantic search.
    """

    def __init__(self, collection_name: str = "interview_curriculum_knowledge") -> None:
        self.collection_name = collection_name
        self.enabled = HAS_CHROMADB
        self._client = None
        self._collection = None

        if HAS_CHROMADB:
            try:
                self._client = chromadb.Client(ChromaSettings(anonymized_telemetry=False))
                self._collection = self._client.get_or_create_collection(name=self.collection_name)
                self._seed_documents()
                logger.info(f"ChromaDB Vector Store initialized with collection '{self.collection_name}'")
            except Exception as e:
                logger.warning(f"ChromaDB initialization fallback: {e}")
                self.enabled = False

    def _seed_documents(self) -> None:
        """Seed technical knowledge base into ChromaDB vector store."""
        if not self._collection:
            return
        from rag.knowledge_data import KNOWLEDGE_BASE
        
        ids = []
        documents = []
        metadatas = []

        for idx, item in enumerate(KNOWLEDGE_BASE):
            doc_id = f"doc_{idx}_{item['topic'].replace(' ', '_').lower()}"
            content = f"Topic: {item['topic']} (Day {item['day']}, {item['difficulty']})\nConcepts: {', '.join(item['concepts'])}\n{item['content']}"
            
            ids.append(doc_id)
            documents.append(content)
            metadatas.append({
                "day": item["day"],
                "topic": item["topic"],
                "difficulty": item["difficulty"],
            })

        if ids:
            self._collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Semantic vector search against ChromaDB."""
        if not self.enabled or not self._collection:
            return []
        try:
            results = self._collection.query(query_texts=[query], n_results=top_k)
            ret = []
            if results and "documents" in results and results["documents"]:
                docs = results["documents"][0]
                metas = results["metadatas"][0] if "metadatas" in results else [{}] * len(docs)
                for doc, meta in zip(docs, metas):
                    ret.append({"content": doc, "metadata": meta})
            return ret
        except Exception as e:
            logger.warning(f"ChromaDB query error: {e}")
            return []
