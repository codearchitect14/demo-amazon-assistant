import os
import asyncio
import json
import sys
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging
from datetime import datetime

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import (
    Distance,
    VectorParams,
    CreateCollection,
    PointStruct,
)
from langchain.schema import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_qdrant import Qdrant
from tqdm import tqdm
import uuid

# Add the parent directory to Python path to import app.config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.config import Config

from create_multivector_docs import MultiVectorDocumentProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class EmbeddingConfig:
    """Configuration for embedding models and vector stores"""

    model_name: str = Config.EMBEDDING_MODEL
    vector_size: int = Config.EMBEDDING_VECTOR_SIZE
    distance_metric: Distance = Distance.COSINE
    collection_prefix: str = Config.EMBEDDING_COLLECTION_PREFIX
    batch_size: int = Config.EMBEDDING_BATCH_SIZE


class MultiVectorEmbeddingBuilder:
    """
    Builds embeddings and stores them in Qdrant for multi-vector RAG
    """

    def __init__(
        self,
        qdrant_url: str = Config.QDRANT_URL,
        qdrant_api_key: Optional[str] = Config.QDRANT_API_KEY,
        config: Optional[EmbeddingConfig] = None,
    ):

        self.config = config or EmbeddingConfig()

        # Initialize Qdrant client
        self.qdrant_client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)

        # Initialize embedding model
        logger.info(f"Loading embedding model: {self.config.model_name}")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.config.model_name,
            model_kwargs={"device": "cpu"},  # Change to 'cuda' if GPU available
            encode_kwargs={"normalize_embeddings": True},
        )

        # Collection names
        self.collection_names = {
            "titles": f"{self.config.collection_prefix}_titles",
            "reviews": f"{self.config.collection_prefix}_reviews",
            "qas": f"{self.config.collection_prefix}_qas",
        }

        # Vector stores (will be initialized after collections are created)
        self.vector_stores = {}

    def create_collections(self) -> None:
        """Create Qdrant collections for each content type"""
        logger.info("Creating Qdrant collections...")

        for content_type, collection_name in self.collection_names.items():
            try:
                # Check if collection exists
                collections = self.qdrant_client.get_collections()
                existing_collections = [col.name for col in collections.collections]

                if collection_name in existing_collections:
                    logger.info(f"Collection '{collection_name}' already exists")
                    continue

                # Create collection with optimized configuration
                collection_config = self._get_collection_config(content_type)

                self.qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=self.config.vector_size,
                        distance=self.config.distance_metric,
                    ),
                    optimizers_config=collection_config["optimizers"],
                    hnsw_config=collection_config["hnsw"],
                )

                logger.info(f"Created collection: {collection_name}")

                # Create payload indexes for efficient filtering
                self._create_payload_indexes(collection_name)

            except Exception as e:
                logger.error(f"Error creating collection {collection_name}: {e}")
                raise

    def _get_collection_config(self, content_type: str) -> Dict[str, Any]:
        """Get optimized configuration for each collection type"""
        configs = {
            "titles": {
                "optimizers": models.OptimizersConfigDiff(default_segment_number=2),
                "hnsw": models.HnswConfigDiff(m=16, ef_construct=200),
            },
            "reviews": {
                "optimizers": models.OptimizersConfigDiff(default_segment_number=4),
                "hnsw": models.HnswConfigDiff(m=16, ef_construct=200),
            },
            "qas": {
                "optimizers": models.OptimizersConfigDiff(default_segment_number=2),
                "hnsw": models.HnswConfigDiff(m=16, ef_construct=200),
            },
        }
        return configs.get(content_type, configs["reviews"])

    def _create_payload_indexes(self, collection_name: str) -> None:
        """Create indexes on payload fields for efficient filtering"""
        try:
            # Create index on metadata.asin for fast filtering (LangChain stores metadata nested)
            self.qdrant_client.create_payload_index(
                collection_name=collection_name,
                field_name="metadata.asin",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )

            # Create index on metadata.content_type
            self.qdrant_client.create_payload_index(
                collection_name=collection_name,
                field_name="metadata.content_type",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )

            logger.info(f"Created payload indexes for {collection_name}")

        except Exception as e:
            logger.warning(f"Error creating payload indexes for {collection_name}: {e}")

    def initialize_vector_stores(self) -> None:
        """Initialize LangChain vector stores for each collection"""
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

    def embed_documents_batch(
        self, documents: List[Document], content_type: str
    ) -> None:
        """Embed and store documents in batches"""
        if not documents:
            logger.info(f"No {content_type} documents to process")
            return

        logger.info(f"Processing {len(documents)} {content_type} documents...")
        vector_store = self.vector_stores[content_type]

        # Process in batches
        for i in tqdm(
            range(0, len(documents), self.config.batch_size),
            desc=f"Embedding {content_type}",
        ):
            batch = documents[i : i + self.config.batch_size]

            try:
                # Extract texts and metadatas
                texts = [doc.page_content for doc in batch]
                metadatas = [doc.metadata for doc in batch]

                # Use existing document IDs if available, otherwise generate new ones
                ids = []
                for doc in batch:
                    if hasattr(doc, "id") and doc.id:
                        ids.append(doc.id)
                    else:
                        ids.append(str(uuid.uuid4()))

                # Add to vector store
                vector_store.add_texts(
                    texts=texts,
                    metadatas=metadatas,
                    ids=ids,
                    batch_size=self.config.batch_size,
                )

            except Exception as e:
                logger.error(
                    f"Error processing batch {i//self.config.batch_size + 1} for {content_type}: {e}"
                )
                continue

        logger.info(f"Completed embedding {content_type} documents")

    def build_embeddings_from_processor(
        self, processor: MultiVectorDocumentProcessor
    ) -> None:
        """Build embeddings from a document processor"""
        logger.info("Starting embedding build process...")

        # Create collections
        self.create_collections()

        # Initialize vector stores
        self.initialize_vector_stores()

        # Get all documents
        all_documents = processor.get_all_documents()

        # Embed each document type
        for content_type, documents in all_documents.items():
            if content_type == "titles":
                self.embed_documents_batch(documents, "titles")
            elif content_type == "reviews":
                self.embed_documents_batch(documents, "reviews")
            elif content_type == "qas":
                self.embed_documents_batch(documents, "qas")

        logger.info("Embedding build process completed!")

    def build_embeddings_from_file(self, jsonl_file_path: str) -> None:
        """Build embeddings directly from JSONL file"""
        logger.info(f"Building embeddings from file: {jsonl_file_path}")

        # Process documents
        processor = MultiVectorDocumentProcessor()
        processor.process_all_products(jsonl_file_path)

        # Build embeddings
        self.build_embeddings_from_processor(processor)

    def build_embeddings_from_processed_file(self, jsonl_file_path: str) -> None:
        """Build embeddings from already processed JSONL file (like all_documents.jsonl)"""
        logger.info(f"Building embeddings from processed file: {jsonl_file_path}")

        # Load documents directly from processed JSONL
        documents = []
        with open(jsonl_file_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    doc_data = json.loads(line.strip())
                    # Create Document object from processed data
                    doc = Document(
                        page_content=doc_data.get("page_content", ""),
                        metadata=doc_data.get("metadata", {}),
                        id=doc_data.get("id"),
                    )
                    documents.append(doc)
                except json.JSONDecodeError as e:
                    logger.warning(f"Error parsing line: {e}")
                    continue

        # Group documents by type
        documents_by_type = {"titles": [], "reviews": [], "qas": []}
        for doc in documents:
            content_type = doc.metadata.get("content_type", "unknown")
            if content_type == "title":
                documents_by_type["titles"].append(doc)
            elif content_type == "review":
                documents_by_type["reviews"].append(doc)
            elif content_type == "qa":
                documents_by_type["qas"].append(doc)

        # Create collections and initialize vector stores
        self.create_collections()
        self.initialize_vector_stores()

        # Embed each document type
        for content_type, docs in documents_by_type.items():
            if docs:
                self.embed_documents_batch(docs, content_type)

        logger.info("Embedding build process completed!")

    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about created collections"""
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

    def test_search(
        self, query: str, content_type: str = "titles", k: int = 5
    ) -> List[Document]:
        """Test search functionality"""
        if content_type not in self.vector_stores:
            raise ValueError(f"Content type {content_type} not available")

        logger.info(f"Testing search for '{query}' in {content_type}")
        vector_store = self.vector_stores[content_type]

        try:
            results = vector_store.similarity_search(query, k=k)
            logger.info(f"Found {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Error during search: {e}")
            return []


def main():
    """Main function to build embeddings"""
    # Configuration
    config = EmbeddingConfig(
        model_name=Config.EMBEDDING_MODEL,
        vector_size=Config.EMBEDDING_VECTOR_SIZE,
        batch_size=Config.EMBEDDING_BATCH_SIZE,
    )

    # Initialize builder
    builder = MultiVectorEmbeddingBuilder(qdrant_url=Config.QDRANT_URL, config=config)

    try:
        # Option 1: Build embeddings from raw dataset (recommended)
        logger.info("Building embeddings from raw dataset...")
        builder.build_embeddings_from_file("../data/processed/final_10k_dataset.jsonl")

        # Option 2: Build embeddings from processed documents (if you have all_documents.jsonl)
        # logger.info("Building embeddings from processed documents...")
        # builder.build_embeddings_from_processed_file('../data/processed/all_documents.jsonl')

        # Print collection info
        logger.info("Collection Information:")
        collection_info = builder.get_collection_info()
        for content_type, info in collection_info.items():
            logger.info(f"  {content_type}: {info}")

        # Test basic search functionality
        logger.info("\nTesting basic search functionality...")
        test_query = "wireless bluetooth headphones"
        title_results = builder.test_search(test_query, content_type="titles", k=3)
        logger.info(f"Found {len(title_results)} title results for '{test_query}'")

        if title_results:
            logger.info("Sample title result:")
            logger.info(f"  Content: {title_results[0].page_content[:100]}...")
            logger.info(f"  ASIN: {title_results[0].metadata.get('asin', 'N/A')}")

    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise


if __name__ == "__main__":
    main()
