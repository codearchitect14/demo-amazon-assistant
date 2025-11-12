"""
Advanced RAG Retriever with Hybrid Search, Semantic Chunking, and Re-ranking
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import CrossEncoder
from rank_bm25 import BM25Okapi
import re

from qdrant_client import QdrantClient
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)


class RetrievalMethod(Enum):
    HYBRID = "hybrid"
    DENSE_ONLY = "dense"
    SPARSE_ONLY = "sparse"
    SEMANTIC_CHUNKING = "semantic_chunking"
    HIERARCHICAL = "hierarchical"


@dataclass
class RetrievalConfig:
    """Advanced retrieval configuration"""

    method: RetrievalMethod = RetrievalMethod.HYBRID
    dense_weight: float = 0.7
    sparse_weight: float = 0.3
    re_rank_top_k: int = 20
    final_top_k: int = 5
    semantic_chunk_size: int = 512
    semantic_chunk_overlap: int = 50
    enable_cross_encoder: bool = True
    cross_encoder_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    enable_reranking: bool = True
    enable_query_expansion: bool = True
    enable_contextual_reranking: bool = True


class AdvancedMultiVectorRetriever:
    """
    Advanced RAG retriever with hybrid search, semantic chunking, and sophisticated re-ranking
    """

    def __init__(
        self,
        qdrant_url: str,
        qdrant_api_key: Optional[str] = None,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        config: Optional[RetrievalConfig] = None,
    ):

        self.config = config or RetrievalConfig()
        self.qdrant_client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)

        # Initialize embedding models
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

        # Initialize cross-encoder for re-ranking
        if self.config.enable_cross_encoder:
            try:
                self.cross_encoder = CrossEncoder(self.config.cross_encoder_model)
                logger.info(
                    f"Cross-encoder initialized: {self.config.cross_encoder_model}"
                )
            except Exception as e:
                logger.warning(f"Failed to initialize cross-encoder: {e}")
                self.cross_encoder = None
        else:
            self.cross_encoder = None

        # Initialize text splitter for semantic chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.semantic_chunk_size,
            chunk_overlap=self.config.semantic_chunk_overlap,
            separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],
        )

        # BM25 for sparse retrieval
        self.bm25_indexes = {}

        logger.info(f"Advanced retriever initialized with method: {self.config.method}")

    def semantic_chunk_text(
        self, text: str, metadata: Dict[str, Any] = None
    ) -> List[Document]:
        """Create semantic chunks with metadata preservation"""
        chunks = self.text_splitter.split_text(text)
        documents = []

        for i, chunk in enumerate(chunks):
            doc_metadata = metadata.copy() if metadata else {}
            doc_metadata.update(
                {
                    "chunk_id": i,
                    "total_chunks": len(chunks),
                    "chunk_size": len(chunk),
                    "semantic_chunk": True,
                }
            )

            documents.append(Document(page_content=chunk, metadata=doc_metadata))

        return documents

    def query_expansion(self, query: str) -> List[str]:
        """Expand query using synonyms and related terms"""
        # Basic query expansion - can be enhanced with LLM-based expansion
        expanded_queries = [query]

        # Add common synonyms
        synonyms = {
            "headphones": ["earphones", "earbuds", "cans"],
            "wireless": ["bluetooth", "cordless"],
            "noise": ["sound", "audio"],
            "cancellation": ["reduction", "isolation"],
            "battery": ["power", "life", "duration"],
            "comfort": ["comfortable", "ergonomic", "fit"],
        }

        query_lower = query.lower()
        for term, syns in synonyms.items():
            if term in query_lower:
                for syn in syns:
                    expanded_query = query_lower.replace(term, syn)
                    if expanded_query != query_lower:
                        expanded_queries.append(expanded_query)

        return expanded_queries

    def hybrid_search(
        self, query: str, collection_name: str, top_k: int = 20
    ) -> List[Document]:
        """Perform hybrid dense + sparse search"""
        # Dense search
        dense_results = self._dense_search(query, collection_name, top_k)

        # Sparse search (BM25)
        sparse_results = self._sparse_search(query, collection_name, top_k)

        # Combine results using reciprocal rank fusion
        combined_results = self._reciprocal_rank_fusion(dense_results, sparse_results)

        return combined_results[:top_k]

    async def hybrid_search_async(
        self, query: str, collection_name: str, top_k: int = 20
    ) -> List[Document]:
        """Perform hybrid dense + sparse search (async)"""
        # For now, just call the sync version
        return self.hybrid_search(query, collection_name, top_k)

    def _dense_search(
        self, query: str, collection_name: str, top_k: int
    ) -> List[Document]:
        """Perform dense vector search"""
        try:
            query_embedding = self.embeddings.embed_query(query)

            search_result = self.qdrant_client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=top_k,
                with_payload=True,
                with_vectors=False,
            )

            documents = []
            for result in search_result:
                doc = Document(
                    page_content=result.payload.get("text", ""),
                    metadata=result.payload.get("metadata", {}),
                )
                doc.metadata["score"] = result.score
                doc.metadata["search_type"] = "dense"
                documents.append(doc)

            return documents
        except Exception as e:
            logger.error(f"Error in dense search: {e}")
            return []

    def _sparse_search(
        self, query: str, collection_name: str, top_k: int
    ) -> List[Document]:
        """Perform sparse BM25 search"""
        # This would require building BM25 index from documents
        # For now, return empty list - implement based on your data structure
        return []

    def _reciprocal_rank_fusion(
        self, dense_results: List[Document], sparse_results: List[Document]
    ) -> List[Document]:
        """Combine results using reciprocal rank fusion"""
        all_results = {}

        # Add dense results
        for i, doc in enumerate(dense_results):
            doc_id = doc.page_content[:100]  # Use content as ID
            if doc_id not in all_results:
                all_results[doc_id] = {"doc": doc, "scores": []}
            all_results[doc_id]["scores"].append(1.0 / (i + 1))

        # Add sparse results
        for i, doc in enumerate(sparse_results):
            doc_id = doc.page_content[:100]
            if doc_id not in all_results:
                all_results[doc_id] = {"doc": doc, "scores": []}
            all_results[doc_id]["scores"].append(1.0 / (i + 1))

        # Calculate final scores
        for doc_id, result in all_results.items():
            result["final_score"] = sum(result["scores"])

        # Sort by final score
        sorted_results = sorted(
            all_results.values(), key=lambda x: x["final_score"], reverse=True
        )

        return [result["doc"] for result in sorted_results]

    def re_rank_with_cross_encoder(
        self, query: str, documents: List[Document]
    ) -> List[Document]:
        """Re-rank documents using cross-encoder"""
        if not self.cross_encoder or not documents:
            return documents

        try:
            # Prepare pairs for cross-encoder
            pairs = [(query, doc.page_content) for doc in documents]

            # Get scores from cross-encoder
            scores = self.cross_encoder.predict(pairs)

            # Update document scores and sort
            for doc, score in zip(documents, scores):
                doc.metadata["cross_encoder_score"] = float(score)

            # Sort by cross-encoder score
            documents.sort(
                key=lambda x: x.metadata.get("cross_encoder_score", 0), reverse=True
            )

            return documents
        except Exception as e:
            logger.error(f"Error in cross-encoder re-ranking: {e}")
            return documents

    def contextual_reranking(
        self, query: str, documents: List[Document], conversation_history: str = ""
    ) -> List[Document]:
        """Re-rank based on conversation context"""
        if not conversation_history:
            return documents

        # Create context-aware query
        contextual_query = f"Context: {conversation_history}\nQuery: {query}"

        # Re-rank with context
        return self.re_rank_with_cross_encoder(contextual_query, documents)

    def hierarchical_search(
        self, query: str, collection_names: List[str]
    ) -> List[Document]:
        """Perform hierarchical search across multiple collections"""
        all_results = []

        for collection_name in collection_names:
            results = self.hybrid_search(query, collection_name, top_k=10)
            all_results.extend(results)

        # Re-rank all results together
        if self.config.enable_reranking:
            all_results = self.re_rank_with_cross_encoder(query, all_results)

        return all_results[: self.config.final_top_k]

    async def advanced_search(
        self, query: str, session_id: str = None, conversation_history: str = ""
    ) -> Dict[str, Any]:
        """Advanced search with all features enabled"""

        # Query expansion
        if self.config.enable_query_expansion:
            expanded_queries = self.query_expansion(query)
            logger.info(f"Expanded queries: {expanded_queries}")
        else:
            expanded_queries = [query]

        # Perform search based on method
        if self.config.method == RetrievalMethod.HYBRID:
            results = await self.hybrid_search_async(
                query, "amazon_products_titles", self.config.re_rank_top_k
            )
        elif self.config.method == RetrievalMethod.SEMANTIC_CHUNKING:
            # Implement semantic chunking search
            results = self._semantic_chunking_search(query)
        elif self.config.method == RetrievalMethod.HIERARCHICAL:
            results = self.hierarchical_search(
                query,
                [
                    "amazon_products_titles",
                    "amazon_products_reviews",
                    "amazon_products_qas",
                ],
            )
        else:
            results = self._dense_search(
                query, "amazon_products_titles", self.config.re_rank_top_k
            )

        # Re-ranking
        if self.config.enable_reranking:
            results = self.re_rank_with_cross_encoder(query, results)

        # Contextual re-ranking
        if self.config.enable_contextual_reranking and conversation_history:
            results = self.contextual_reranking(query, results, conversation_history)

        # Final selection
        final_results = results[: self.config.final_top_k]

        return {
            "documents": final_results,
            "query": query,
            "expanded_queries": expanded_queries,
            "total_candidates": len(results),
            "final_count": len(final_results),
            "search_method": self.config.method,
        }

    def _semantic_chunking_search(self, query: str) -> List[Document]:
        """Search with semantic chunking"""
        # This would implement semantic chunking search
        # For now, return regular search
        return self._dense_search(
            query, "amazon_products_titles", self.config.re_rank_top_k
        )

    # Add compatibility methods for the existing retriever interface
    def search_titles(self, query: str, k: int = 10) -> List[Document]:
        """Search titles (compatibility method)"""
        return self._dense_search(query, "amazon_products_titles", k)

    async def search_titles_async(self, query: str, k: int = 10) -> List[Document]:
        """Search titles async (compatibility method)"""
        return self.search_titles(query, k)

    def search_reviews(self, query: str, k: int = 10) -> List[Document]:
        """Search reviews (compatibility method)"""
        return self._dense_search(query, "amazon_products_reviews", k)

    async def search_reviews_async(self, query: str, k: int = 10) -> List[Document]:
        """Search reviews async (compatibility method)"""
        return self.search_reviews(query, k)

    def search_qas(self, query: str, k: int = 10) -> List[Document]:
        """Search QAs (compatibility method)"""
        return self._dense_search(query, "amazon_products_qas", k)

    async def search_qas_async(self, query: str, k: int = 10) -> List[Document]:
        """Search QAs async (compatibility method)"""
        return self.search_qas(query, k)
