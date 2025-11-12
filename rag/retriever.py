import os
import logging
import asyncio
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
from langchain.schema import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_qdrant import Qdrant
from rag.embedding_cache import get_embedding_cache

# Configuration constants
DEFAULT_QDRANT_URL = "http://localhost:6333"
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_TOP_PRODUCTS = 20
DEFAULT_ITEMS_PER_PRODUCT = 5
DEFAULT_QA_PER_PRODUCT = 3  # Number of QAs to include per product
DEFAULT_REVIEW_PER_PRODUCT = 3  # Number of reviews to include per product

# Collection names
COLLECTION_NAMES = {
    "titles": "amazon_products_titles",
    "reviews": "amazon_products_reviews",
    "qas": "amazon_products_qas",
}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CachedHuggingFaceEmbeddings:
    """
    HuggingFace embeddings with caching support.
    """

    def __init__(self, model_name: str, **kwargs):
        self.model_name = model_name
        self.kwargs = kwargs
        self.cache = get_embedding_cache()
        # Create a regular HuggingFaceEmbeddings instance for compatibility
        self._embeddings = HuggingFaceEmbeddings(model_name=model_name, **kwargs)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed documents using cached model"""
        return self.cache.encode(texts)

    def embed_query(self, text: str) -> List[float]:
        """Embed query using cached model"""
        return self.cache.encode_single(text)

    def __call__(self, texts: List[str]) -> List[List[float]]:
        """Make the object callable for compatibility with vector stores"""
        if isinstance(texts, str):
            # Single text - return as a list with one item
            return [self.embed_query(texts)]
        else:
            # List of texts
            return self.embed_documents(texts)

    def __getattr__(self, name):
        """Delegate other attributes to the underlying HuggingFaceEmbeddings instance"""
        return getattr(self._embeddings, name)

    def embed_documents_async(self, texts: List[str]) -> List[List[float]]:
        """Async version of embed_documents for compatibility"""
        return self.embed_documents(texts)

    def embed_query_async(self, text: str) -> List[float]:
        """Async version of embed_query for compatibility"""
        return self.embed_query(text)


class MultiVectorRetriever:
    """
    Retrieves documents from Qdrant vector store for multi-vector RAG
    """

    def __init__(
        self,
        qdrant_url: str = DEFAULT_QDRANT_URL,
        qdrant_api_key: Optional[str] = None,
        embedding_model: str = DEFAULT_EMBEDDING_MODEL,
    ):

        # Initialize Qdrant client
        self.qdrant_client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)

        # Initialize embedding model with caching
        logger.info(f"Initializing cached embedding model: {embedding_model}")
        self.embeddings = CachedHuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

        # Collection names
        self.collection_names = COLLECTION_NAMES

        # Vector stores (will be initialized on demand)
        self.vector_stores = {}

    def initialize_vector_stores(self) -> None:
        """Initialize vector stores for each collection"""
        logger.info("Initializing vector stores...")

        for content_type, collection_name in self.collection_names.items():
            try:
                self.vector_stores[content_type] = Qdrant(
                    client=self.qdrant_client,
                    collection_name=collection_name,
                    embeddings=self.embeddings,
                )
                logger.info(f"Initialized vector store for {content_type}")
            except Exception as e:
                logger.error(f"Error initializing vector store for {content_type}: {e}")
                raise

    async def initialize_vector_stores_async(self) -> None:
        """Initialize vector stores for each collection (async)"""
        logger.info("Initializing vector stores...")

        for content_type, collection_name in self.collection_names.items():
            try:
                # Run the synchronous initialization in a thread pool
                await asyncio.to_thread(
                    self._initialize_single_vector_store, content_type, collection_name
                )
                logger.info(f"Initialized vector store for {content_type}")
            except Exception as e:
                logger.error(f"Error initializing vector store for {content_type}: {e}")
                raise

    def _initialize_single_vector_store(
        self, content_type: str, collection_name: str
    ) -> None:
        """Initialize a single vector store (synchronous helper)"""
        self.vector_stores[content_type] = Qdrant(
            client=self.qdrant_client,
            collection_name=collection_name,
            embeddings=self.embeddings,
        )

    def search_titles(self, query: str, k: int = 10) -> List[Document]:
        """Search in title documents"""
        try:
            # Use direct Qdrant API instead of LangChain wrapper
            query_vector = self.embeddings.embed_query(query)

            search_result = self.qdrant_client.search(
                collection_name=self.collection_names["titles"],
                query_vector=query_vector,
                limit=k,
            )

            # Convert to Documents
            documents = []
            for point in search_result:
                try:
                    metadata = point.payload.copy() if point.payload else {}
                    doc = Document(
                        page_content=(
                            point.payload.get("page_content", "")
                            if point.payload
                            else ""
                        ),
                        metadata=metadata,
                    )
                    documents.append(doc)
                except Exception as e:
                    logger.warning(f"Error processing search result point: {e}")
                    continue

            logger.info(f"Found {len(documents)} title results")
            return documents
        except Exception as e:
            logger.error(f"Error searching titles: {e}")
            return []

    async def search_titles_async(self, query: str, k: int = 10) -> List[Document]:
        """Search in title documents (async)"""
        try:
            # Use direct Qdrant API instead of LangChain wrapper
            query_vector = await asyncio.to_thread(self.embeddings.embed_query, query)

            search_result = await asyncio.to_thread(
                self.qdrant_client.search,
                collection_name=self.collection_names["titles"],
                query_vector=query_vector,
                limit=k,
            )

            # Convert to Documents
            documents = []
            for point in search_result:
                try:
                    metadata = point.payload.copy() if point.payload else {}
                    doc = Document(
                        page_content=(
                            point.payload.get("page_content", "")
                            if point.payload
                            else ""
                        ),
                        metadata=metadata,
                    )
                    documents.append(doc)
                except Exception as e:
                    logger.warning(f"Error processing search result point: {e}")
                    continue

            logger.info(f"Found {len(documents)} title results")
            return documents
        except Exception as e:
            logger.error(f"Error searching titles: {e}")
            return []

    def search_reviews(self, query: str, k: int = 10) -> List[Document]:
        """Search in review documents"""
        try:
            # Use direct Qdrant API instead of LangChain wrapper
            query_vector = self.embeddings.embed_query(query)

            search_result = self.qdrant_client.search(
                collection_name=self.collection_names["reviews"],
                query_vector=query_vector,
                limit=k,
            )

            # Convert to Documents
            documents = []
            for point in search_result:
                try:
                    metadata = point.payload.copy() if point.payload else {}
                    doc = Document(
                        page_content=(
                            point.payload.get("page_content", "")
                            if point.payload
                            else ""
                        ),
                        metadata=metadata,
                    )
                    documents.append(doc)
                except Exception as e:
                    logger.warning(f"Error processing search result point: {e}")
                    continue

            logger.info(f"Found {len(documents)} review results")
            return documents
        except Exception as e:
            logger.error(f"Error searching reviews: {e}")
            return []

    async def search_reviews_async(self, query: str, k: int = 10) -> List[Document]:
        """Search in review documents (async)"""
        try:
            # Use direct Qdrant API instead of LangChain wrapper
            query_vector = await asyncio.to_thread(self.embeddings.embed_query, query)

            search_result = await asyncio.to_thread(
                self.qdrant_client.search,
                collection_name=self.collection_names["reviews"],
                query_vector=query_vector,
                limit=k,
            )

            # Convert to Documents
            documents = []
            for point in search_result:
                try:
                    metadata = point.payload.copy() if point.payload else {}
                    doc = Document(
                        page_content=(
                            point.payload.get("page_content", "")
                            if point.payload
                            else ""
                        ),
                        metadata=metadata,
                    )
                    documents.append(doc)
                except Exception as e:
                    logger.warning(f"Error processing search result point: {e}")
                    continue

            logger.info(f"Found {len(documents)} review results")
            return documents
        except Exception as e:
            logger.error(f"Error searching reviews: {e}")
            return []

    def search_qas(self, query: str, k: int = 10) -> List[Document]:
        """Search in QA documents"""
        try:
            # Use direct Qdrant API instead of LangChain wrapper
            query_vector = self.embeddings.embed_query(query)

            search_result = self.qdrant_client.search(
                collection_name=self.collection_names["qas"],
                query_vector=query_vector,
                limit=k,
            )

            # Convert to Documents
            documents = []
            for point in search_result:
                try:
                    metadata = point.payload.copy() if point.payload else {}
                    doc = Document(
                        page_content=(
                            point.payload.get("page_content", "")
                            if point.payload
                            else ""
                        ),
                        metadata=metadata,
                    )
                    documents.append(doc)
                except Exception as e:
                    logger.warning(f"Error processing search result point: {e}")
                    continue

            logger.info(f"Found {len(documents)} QA results")
            return documents
        except Exception as e:
            logger.error(f"Error searching QAs: {e}")
            return []

    async def search_qas_async(self, query: str, k: int = 10) -> List[Document]:
        """Search in QA documents (async)"""
        try:
            # Use direct Qdrant API instead of LangChain wrapper
            query_vector = await asyncio.to_thread(self.embeddings.embed_query, query)

            search_result = await asyncio.to_thread(
                self.qdrant_client.search,
                collection_name=self.collection_names["qas"],
                query_vector=query_vector,
                limit=k,
            )

            # Convert to Documents
            documents = []
            for point in search_result:
                try:
                    metadata = point.payload.copy() if point.payload else {}
                    doc = Document(
                        page_content=(
                            point.payload.get("page_content", "")
                            if point.payload
                            else ""
                        ),
                        metadata=metadata,
                    )
                    documents.append(doc)
                except Exception as e:
                    logger.warning(f"Error processing search result point: {e}")
                    continue

            logger.info(f"Found {len(documents)} QA results")
            return documents
        except Exception as e:
            logger.error(f"Error searching QAs: {e}")
            return []

    def search_with_asin_filter(
        self, query: str, asins: List[str], content_type: str, k: int = 10
    ) -> List[Document]:
        """Search within specific ASINs (for two-stage retrieval)"""
        if content_type not in self.collection_names:
            raise ValueError(f"Content type {content_type} not available")

        logger.info(
            f"Searching {content_type} for ASINs: {asins[:5]}{'...' if len(asins) > 5 else ''}"
        )

        # First try with the direct API approach
        try:
            # Create ASIN filter - Fixed: Use correct filter structure for LangChain's nested metadata
            if len(asins) == 1:
                # Single ASIN filter
                filter_condition = models.Filter(
                    must=[
                        models.FieldCondition(
                            key="metadata.asin",  # LangChain stores metadata nested
                            match=models.MatchValue(value=asins[0]),
                        )
                    ]
                )
            else:
                # Multiple ASINs filter
                filter_condition = models.Filter(
                    must=[
                        models.FieldCondition(
                            key="metadata.asin",  # LangChain stores metadata nested
                            match=models.MatchAny(any=asins),
                        )
                    ]
                )

            # Get query vector
            query_vector = self.embeddings.embed_query(query)

            # Perform filtered search
            search_result = self.qdrant_client.search(
                collection_name=self.collection_names[content_type],
                query_vector=query_vector,
                query_filter=filter_condition,
                limit=k,
            )

            logger.info(
                f"Direct API search result for {content_type}: {len(search_result)} documents"
            )

            # Convert to Documents
            documents = []
            for point in search_result:
                try:
                    # The payload structure should match your data
                    metadata = point.payload.copy() if point.payload else {}

                    doc = Document(
                        page_content=(
                            point.payload.get("page_content", "")
                            if point.payload
                            else ""
                        ),
                        metadata=metadata,
                    )
                    documents.append(doc)
                except Exception as e:
                    logger.warning(f"Error processing search result point: {e}")
                    continue

            logger.info(
                f"Successfully converted {len(documents)} documents for {content_type}"
            )
            return documents

        except Exception as e:
            logger.error(f"Direct API search failed for {content_type}: {e}")
            logger.info(f"Falling back to scroll-based approach for {content_type}")

            # Fallback: Use scroll to get documents by ASIN, then rank by similarity
            try:
                all_docs_for_asins = []

                # Get documents for each ASIN using scroll
                for asin in asins:
                    try:
                        asin_filter = models.Filter(
                            must=[
                                models.FieldCondition(
                                    key="metadata.asin",  # LangChain stores metadata nested
                                    match=models.MatchValue(value=asin),
                                )
                            ]
                        )

                        # Get documents for this ASIN
                        scroll_result = self.qdrant_client.scroll(
                            collection_name=self.collection_names[content_type],
                            scroll_filter=asin_filter,
                            limit=100,  # Get up to 100 docs per ASIN
                        )

                        # Convert to Documents
                        points, _ = (
                            scroll_result  # scroll returns (points, next_page_offset)
                        )
                        for point in points:
                            try:
                                metadata = point.payload.copy() if point.payload else {}
                                doc = Document(
                                    page_content=(
                                        point.payload.get("page_content", "")
                                        if point.payload
                                        else ""
                                    ),
                                    metadata=metadata,
                                )
                                all_docs_for_asins.append(doc)
                            except Exception as e:
                                logger.warning(
                                    f"Error processing scroll result point: {e}"
                                )
                                continue

                    except Exception as asin_error:
                        logger.warning(
                            f"Error getting documents for ASIN {asin}: {asin_error}"
                        )
                        continue

                logger.info(
                    f"Scroll approach found {len(all_docs_for_asins)} documents for target ASINs"
                )

                if not all_docs_for_asins:
                    logger.warning(f"No documents found for target ASINs: {asins}")
                    return []

                # Rank documents by semantic similarity
                query_vector = self.embeddings.embed_query(query)

                # Calculate similarity scores
                scored_docs = []
                for doc in all_docs_for_asins:
                    try:
                        doc_vector = self.embeddings.embed_query(doc.page_content)
                        # Calculate cosine similarity manually
                        import numpy as np

                        similarity = np.dot(query_vector, doc_vector) / (
                            np.linalg.norm(query_vector) * np.linalg.norm(doc_vector)
                        )
                        scored_docs.append((similarity, doc))
                    except Exception as e:
                        logger.warning(f"Error scoring document: {e}")
                        # Fallback to simple text matching
                        query_terms = query.lower().split()
                        doc_content = doc.page_content.lower()
                        score = sum(1 for term in query_terms if term in doc_content)
                        scored_docs.append((score, doc))

                # Sort by similarity score and return top k
                scored_docs.sort(key=lambda x: x[0], reverse=True)
                top_docs = [doc for _, doc in scored_docs[:k]]

                logger.info(
                    f"Fallback similarity-based search found {len(top_docs)} documents for {content_type}"
                )
                return top_docs

            except Exception as fallback_error:
                logger.error(
                    f"Fallback search also failed for {content_type}: {fallback_error}"
                )
                return []

    async def search_with_asin_filter_async(
        self, query: str, asins: List[str], content_type: str, k: int = 10
    ) -> List[Document]:
        """Search within specific ASINs (for two-stage retrieval) - async version"""
        try:
            result = await asyncio.to_thread(
                self.search_with_asin_filter, query, asins, content_type, k
            )
            # Ensure we always return a list
            if result is None:
                logger.warning(
                    f"search_with_asin_filter returned None for {content_type}"
                )
                return []
            return result
        except Exception as e:
            logger.error(
                f"Error in search_with_asin_filter_async for {content_type}: {e}"
            )
            return []

    def title_first_search(
        self,
        query: str,
        top_products: int = DEFAULT_TOP_PRODUCTS,
        items_per_product: int = DEFAULT_ITEMS_PER_PRODUCT,
    ) -> Dict[str, Any]:
        """
        Execute title-first search pipeline with caching
        """
        # Try to get cached result first
        from rag.performance_optimizer import PerformanceOptimizer, PerformanceConfig
        
        # Initialize performance optimizer with caching
        optimizer = PerformanceOptimizer(PerformanceConfig(enable_caching=True))
        
        # Create cache key
        cache_key = optimizer.cache_key("title_first_search", query, top_products, items_per_product)
        
        # Try to get from cache
        cached_result = optimizer.get_cached_result(cache_key)
        if cached_result is not None:
            logger.info(f"Cache HIT for query: '{query}'")
            return cached_result
        
        logger.info(f"Cache MISS for query: '{query}' - performing fresh search")
        
        # Perform fresh search
        result = self._perform_title_first_search(query, top_products, items_per_product)
        
        # Cache the result
        optimizer.set_cached_result(cache_key, result)
        
        return result
    
    def _perform_title_first_search(
        self,
        query: str,
        top_products: int = DEFAULT_TOP_PRODUCTS,
        items_per_product: int = DEFAULT_ITEMS_PER_PRODUCT,
    ) -> Dict[str, Any]:
        """
        Execute title-first search pipeline (internal method without caching)
        """
        logger.info(f"Starting title_first_search for query: '{query}'")

        # Stage 1: Search titles to get relevant products
        title_results = self.search_titles(query, k=top_products)
        logger.info(f"Found {len(title_results)} title results")

        if not title_results:
            return {"message": "No relevant products found", "results": []}

        # Extract ASINs from title results
        selected_asins = []
        for doc in title_results[:top_products]:
            # Check different possible ASIN locations in metadata
            asin = None
            if "asin" in doc.metadata:
                asin = doc.metadata["asin"]
            elif "metadata" in doc.metadata and "asin" in doc.metadata["metadata"]:
                asin = doc.metadata["metadata"]["asin"]

            if asin:
                selected_asins.append(asin)
        logger.info(f"Selected ASINs: {selected_asins}")

        # Stage 2: Search reviews and QAs within selected products
        logger.info("Searching for reviews within selected ASINs...")
        review_results = self.search_with_asin_filter(
            query=query,
            asins=selected_asins,
            content_type="reviews",
            k=items_per_product * top_products,
        )
        logger.info(f"Found {len(review_results)} review results")

        logger.info("Searching for QAs within selected ASINs...")
        qa_results = self.search_with_asin_filter(
            query=query,
            asins=selected_asins,
            content_type="qas",
            k=items_per_product * top_products,
        )
        logger.info(f"Found {len(qa_results)} QA results")

        # Stage 3: Aggregate results by ASIN
        aggregated_results = self._aggregate_by_asin(
            title_results[:top_products], review_results, qa_results, items_per_product
        )

        logger.info(f"Aggregated {len(aggregated_results)} products with data")

        return {
            "query": query,
            "total_products": len(aggregated_results),
            "results": aggregated_results,
        }

    async def title_first_search_async(
        self,
        query: str,
        top_products: int = DEFAULT_TOP_PRODUCTS,
        items_per_product: int = DEFAULT_ITEMS_PER_PRODUCT,
    ) -> Dict[str, Any]:
        """
        Execute title-first search pipeline (async)
        """
        logger.info(f"Starting title_first_search for query: '{query}'")

        # Stage 1: Search titles to get relevant products
        title_results = await self.search_titles_async(query, k=top_products)
        logger.info(f"Found {len(title_results)} title results")

        if not title_results:
            return {"message": "No relevant products found", "results": []}

        # Extract ASINs from title results
        selected_asins = []
        for doc in title_results[:top_products]:
            # Check different possible ASIN locations in metadata
            asin = None
            if "asin" in doc.metadata:
                asin = doc.metadata["asin"]
            elif "metadata" in doc.metadata and "asin" in doc.metadata["metadata"]:
                asin = doc.metadata["metadata"]["asin"]

            if asin:
                selected_asins.append(asin)
        logger.info(f"Selected ASINs: {selected_asins}")

        # Stage 2: Search reviews and QAs within selected products
        logger.info("Searching for reviews within selected ASINs...")
        review_results = await self.search_with_asin_filter_async(
            query=query,
            asins=selected_asins,
            content_type="reviews",
            k=items_per_product * top_products,
        )
        logger.info(f"Found {len(review_results)} review results")

        logger.info("Searching for QAs within selected ASINs...")
        qa_results = await self.search_with_asin_filter_async(
            query=query,
            asins=selected_asins,
            content_type="qas",
            k=items_per_product * top_products,
        )
        logger.info(f"Found {len(qa_results)} QA results")

        # Stage 3: Aggregate results by ASIN
        aggregated_results = await asyncio.to_thread(
            self._aggregate_by_asin,
            title_results[:top_products],
            review_results,
            qa_results,
            items_per_product,
        )

        logger.info(f"Aggregated {len(aggregated_results)} products with data")

        return {
            "query": query,
            "total_products": len(aggregated_results),
            "results": aggregated_results,
        }

    def _aggregate_by_asin(
        self,
        title_results: List[Document],
        review_results: List[Document],
        qa_results: List[Document],
        items_per_product: int,
    ) -> List[Dict[str, Any]]:
        """Aggregate search results by ASIN"""
        logger.info(
            f"Aggregating data: {len(title_results)} titles, {len(review_results)} reviews, {len(qa_results)} QAs"
        )

        product_data = {}

        # Initialize with titles
        for title_doc in title_results:
            # Defensive check for metadata
            if not hasattr(title_doc, "metadata") or title_doc.metadata is None:
                logger.warning(f"Title document missing metadata: {title_doc}")
                continue

            # Check different possible ASIN locations in metadata
            asin = None
            if "asin" in title_doc.metadata:
                asin = title_doc.metadata["asin"]
            elif (
                "metadata" in title_doc.metadata
                and "asin" in title_doc.metadata["metadata"]
            ):
                asin = title_doc.metadata["metadata"]["asin"]

            if not asin:
                logger.warning(f"Title document missing ASIN: {title_doc.metadata}")
                continue

            product_data[asin] = {
                "asin": asin,
                "title": title_doc.page_content,
                "title_metadata": title_doc.metadata,
                "reviews": [],
                "qas": [],
            }

        logger.info(f"Initialized {len(product_data)} products with title data")

        # Add reviews
        review_count = 0
        logger.info(f"Processing {len(review_results)} review documents")

        for i, review_doc in enumerate(review_results):
            # Defensive check for metadata
            if not hasattr(review_doc, "metadata") or review_doc.metadata is None:
                logger.warning(f"Review document {i+1} missing metadata: {review_doc}")
                continue

            # Check different possible ASIN locations in metadata
            asin = None
            if "asin" in review_doc.metadata:
                asin = review_doc.metadata["asin"]
            elif (
                "metadata" in review_doc.metadata
                and "asin" in review_doc.metadata["metadata"]
            ):
                asin = review_doc.metadata["metadata"]["asin"]

            if asin and asin in product_data:
                product_data[asin]["reviews"].append(
                    {
                        "content": review_doc.page_content,
                        "metadata": review_doc.metadata,
                    }
                )
                review_count += 1
                logger.debug(f"Added review document {i+1} with ASIN: {asin}")
            elif asin:
                logger.debug(
                    f"Review document {i+1} has ASIN {asin} but not in product_data"
                )
            else:
                logger.debug(
                    f"Review document {i+1} has no ASIN found in metadata: {list(review_doc.metadata.keys())}"
                )

        logger.info(f"Added {review_count} reviews to products")

        # Add QAs
        qa_count = 0
        logger.info(f"Processing {len(qa_results)} QA documents")

        for i, qa_doc in enumerate(qa_results):
            # Defensive check for metadata
            if not hasattr(qa_doc, "metadata") or qa_doc.metadata is None:
                logger.warning(f"QA document {i+1} missing metadata: {qa_doc}")
                continue

            # Check different possible ASIN locations in metadata
            asin = None
            if "asin" in qa_doc.metadata:
                asin = qa_doc.metadata["asin"]
            elif (
                "metadata" in qa_doc.metadata and "asin" in qa_doc.metadata["metadata"]
            ):
                asin = qa_doc.metadata["metadata"]["asin"]

            if asin and asin in product_data:
                product_data[asin]["qas"].append(
                    {"content": qa_doc.page_content, "metadata": qa_doc.metadata}
                )
                qa_count += 1
                logger.debug(f"Added QA document {i+1} with ASIN: {asin}")
            elif asin:
                logger.debug(
                    f"QA document {i+1} has ASIN {asin} but not in product_data"
                )
            else:
                logger.debug(
                    f"QA document {i+1} has no ASIN found in metadata: {list(qa_doc.metadata.keys())}"
                )

        logger.info(f"Added {qa_count} QAs to products")

        # Limit items per product and return
        results = []
        for asin, data in product_data.items():
            data["reviews"] = data["reviews"][:DEFAULT_REVIEW_PER_PRODUCT]
            data["qas"] = data["qas"][
                :DEFAULT_QA_PER_PRODUCT
            ]  # Exactly 3 QAs per product
            results.append(data)

        # Log summary of final results
        products_with_reviews = sum(1 for p in results if p["reviews"])
        products_with_qas = sum(1 for p in results if p["qas"])
        logger.info(
            f"Final results: {len(results)} products, {products_with_reviews} with reviews, {products_with_qas} with QAs"
        )

        return results

    def format_product_data_for_llm(self, product_data: List[Dict[str, Any]]) -> str:
        """
        Format product data into a structured string for LLM consumption.
        Each product is clearly separated with its metadata, reviews, and QAs.
        """
        if not product_data:
            return "No product information available."

        formatted_products = []

        for i, product in enumerate(product_data, 1):
            # product_lines = [f"PRODUCT {i}:"]
            product_lines = [""]
            product_lines.append("=" * 50)

            # Product metadata (from title document)
            asin = product.get("asin", "Unknown")
            title = product.get("title", "No title available")
            title_metadata = product.get("title_metadata", {})

            product_lines.append(f"ASIN: {asin}")
            product_lines.append(f"Title: {title}")

            # Add all metadata fields from title document (excluding technical fields)
            metadata_lines = []
            # Fields to exclude from display
            exclude_fields = ["asin", "content_type", "doc_id", "source"]

            # Handle nested metadata structure
            actual_metadata = title_metadata.get("metadata", title_metadata)

            for key, value in actual_metadata.items():
                if key not in exclude_fields:
                    if value is not None and str(value).strip():
                        formatted_value = self._format_metadata_value(key, value)
                        if formatted_value:
                            metadata_lines.append(
                                f"  {key.replace('_', ' ').title()}: {formatted_value}"
                            )

            if metadata_lines:
                product_lines.append("Product Details:")
                product_lines.extend(metadata_lines)

            # Reviews section
            reviews = product.get("reviews", [])
            if reviews:
                product_lines.append("")
                product_lines.append("Reviews:")
                for j, review in enumerate(reviews, 1):
                    review_content = review.get("content", "")
                    review_metadata = review.get("metadata", {})

                    product_lines.append(f"  Review {j}: {review_content}")

                    # Add review-specific metadata if available (excluding technical fields)
                    review_meta_lines = []
                    exclude_fields = [
                        "asin",
                        "page_content",
                        "content_type",
                        "doc_id",
                        "source",
                        "metadata",
                    ]

                    # Handle nested metadata structure for reviews
                    actual_review_metadata = review_metadata.get(
                        "metadata", review_metadata
                    )

                    for key, value in actual_review_metadata.items():
                        if key not in exclude_fields:
                            if value is not None and str(value).strip():
                                formatted_value = self._format_metadata_value(
                                    key, value
                                )
                                if formatted_value:
                                    review_meta_lines.append(
                                        f"    {key.replace('_', ' ').title()}: {formatted_value}"
                                    )

                    if review_meta_lines:
                        product_lines.extend(review_meta_lines)

            # QAs section - show content and non-technical metadata
            qas = product.get("qas", [])
            if qas:
                product_lines.append("")
                product_lines.append("Q&A:")
                for j, qa in enumerate(qas, 1):
                    qa_content = qa.get("content", "")
                    qa_metadata = qa.get("metadata", {})
                    product_lines.append(f"  Q&A {j}: {qa_content}")

                    # Add QA-specific metadata if available (excluding technical fields)
                    qa_meta_lines = []
                    exclude_fields = [
                        "asin",
                        "page_content",
                        "content_type",
                        "doc_id",
                        "source",
                        "metadata",
                    ]

                    # Handle nested metadata structure for QAs
                    actual_qa_metadata = qa_metadata.get("metadata", qa_metadata)

                    for key, value in actual_qa_metadata.items():
                        if key not in exclude_fields:
                            if value is not None and str(value).strip():
                                formatted_value = self._format_metadata_value(
                                    key, value
                                )
                                if formatted_value:
                                    qa_meta_lines.append(
                                        f"    {key.replace('_', ' ').title()}: {formatted_value}"
                                    )

                    if qa_meta_lines:
                        product_lines.extend(qa_meta_lines)

            product_lines.append("")  # Empty line between products
            formatted_products.append("\n".join(product_lines))

        return "\n".join(formatted_products)

    async def format_product_data_for_llm_async(
        self, product_data: List[Dict[str, Any]]
    ) -> str:
        """
        Format product data into a structured string for LLM consumption (async).
        Each product is clearly separated with its metadata, reviews, and QAs.
        """
        return await asyncio.to_thread(self.format_product_data_for_llm, product_data)

    def _format_metadata_value(self, key: str, value: Any) -> str:
        """Format metadata values for display"""
        try:
            if value is None:
                return ""

            # Handle different data types
            if isinstance(value, (list, tuple)):
                if len(value) == 0:
                    return ""
                else:
                    return "; ".join(str(item) for item in value if item)

            elif isinstance(value, dict):
                return "; ".join(f"{k}: {v}" for k, v in value.items() if v is not None)

            elif isinstance(value, str):
                return value  # No truncation - return complete string

            elif isinstance(value, (int, float)):
                if key.lower() in ["price", "cost", "amount"] and isinstance(
                    value, (int, float)
                ):
                    return f"${value:.2f}" if value > 0 else str(value)
                elif key.lower() in ["rating", "score"] and isinstance(
                    value, (int, float)
                ):
                    return f"{value:.1f}" if 0 <= value <= 5 else str(value)
                else:
                    return str(value)

            else:
                str_value = str(value)
                return str_value  # No truncation - return complete string

        except Exception as e:
            logger.warning(f"Error formatting metadata value for {key}: {e}")
            return str(value) if value else ""

    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about collections"""
        info = {}
        for content_type, collection_name in self.collection_names.items():
            try:
                collection_info = self.qdrant_client.get_collection(collection_name)
                info[content_type] = {
                    "collection_name": collection_name,
                    "points_count": collection_info.points_count,
                    "vectors_count": collection_info.vectors_count,
                    "status": collection_info.status,
                }
            except Exception as e:
                info[content_type] = {"error": str(e)}
        return info


# Convenience functions for backward compatibility
def search_titles(query: str, k: int = 10) -> List[Document]:
    """Search in title documents"""
    retriever = MultiVectorRetriever()
    return retriever.search_titles(query, k)


def search_reviews(query: str, k: int = 10) -> List[Document]:
    """Search in review documents"""
    retriever = MultiVectorRetriever()
    return retriever.search_reviews(query, k)


def search_qas(query: str, k: int = 10) -> List[Document]:
    """Search in QA documents"""
    retriever = MultiVectorRetriever()
    return retriever.search_qas(query, k)


def title_first_search(
    query: str,
    top_products: int = DEFAULT_TOP_PRODUCTS,
    items_per_product: int = DEFAULT_ITEMS_PER_PRODUCT,
) -> Dict[str, Any]:
    """Execute title-first search pipeline"""
    retriever = MultiVectorRetriever()
    return retriever.title_first_search(query, top_products, items_per_product)
