#!/usr/bin/env python3
"""
Script to rebuild embeddings with correct index structure
"""

import os
import sys
import logging
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Add the parent directory to Python path to import app.config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.config import Config
from build_embeddings import MultiVectorEmbeddingBuilder

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def drop_collections():
    """Drop existing collections to rebuild with correct indexes"""
    logger.info("Dropping existing collections...")

    client = QdrantClient(url=Config.QDRANT_URL, api_key=Config.QDRANT_API_KEY)

    collection_names = [
        f"{Config.EMBEDDING_COLLECTION_PREFIX}_titles",
        f"{Config.EMBEDDING_COLLECTION_PREFIX}_reviews",
        f"{Config.EMBEDDING_COLLECTION_PREFIX}_qas",
    ]

    for collection_name in collection_names:
        try:
            # Check if collection exists
            collections = client.get_collections()
            existing_collections = [col.name for col in collections.collections]

            if collection_name in existing_collections:
                logger.info(f"Dropping collection: {collection_name}")
                client.delete_collection(collection_name)
                logger.info(f"Successfully dropped collection: {collection_name}")
            else:
                logger.info(f"Collection {collection_name} does not exist")

        except Exception as e:
            logger.error(f"Error dropping collection {collection_name}: {e}")


def rebuild_embeddings():
    """Rebuild embeddings with correct index structure"""
    logger.info("Starting embedding rebuild process...")

    # Drop existing collections
    drop_collections()

    # Initialize builder
    builder = MultiVectorEmbeddingBuilder(
        qdrant_url=Config.QDRANT_URL, qdrant_api_key=Config.QDRANT_API_KEY
    )

    try:
        # Build embeddings from raw dataset
        logger.info("Building embeddings from raw dataset...")
        builder.build_embeddings_from_file("../data/processed/final_10k_dataset.jsonl")

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

        logger.info("Embedding rebuild completed successfully!")

    except Exception as e:
        logger.error(f"Error in rebuild process: {e}")
        raise


if __name__ == "__main__":
    rebuild_embeddings()
