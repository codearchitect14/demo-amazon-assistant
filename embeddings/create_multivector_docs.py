import json
import uuid
import sys
import os
from typing import List, Dict, Any
from dataclasses import dataclass
from langchain.schema import Document
import logging

# Add the parent directory to Python path to import app.config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ProcessedProduct:
    """Data class to hold processed product information"""

    asin: str
    title_doc: Document
    review_docs: List[Document]
    qa_docs: List[Document]


class MultiVectorDocumentProcessor:
    """
    Processes Amazon product data into separate document collections for multi-vector RAG
    """

    def __init__(self):
        self.processed_products = []

    def extract_dynamic_metadata(
        self,
        product_data: Dict[str, Any],
        content_type: str,
        doc_id: str,
        exclude_fields: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Dynamically extract metadata from product data, excluding specified fields

        Args:
            product_data: The original product data dictionary
            content_type: Type of content (title, review, qa)
            doc_id: Unique document identifier
            exclude_fields: List of fields to exclude from metadata (defaults to content fields)

        Returns:
            Dictionary containing all metadata
        """
        if exclude_fields is None:
            exclude_fields = [
                "title",
                "reviews",
                "review_combined",
                "qa_chunks",
                "qa_sample",
                "qa",
            ]

        # Start with base metadata
        metadata = {
            "asin": product_data.get("asin", ""),
            "content_type": content_type,
            "doc_id": doc_id,
            "source": "amazon_products",
        }

        # For title documents only, include all fields except content fields
        if content_type == "title":
            for key, value in product_data.items():
                if key not in exclude_fields and value is not None:
                    # Handle different data types appropriately
                    if isinstance(value, (str, int, float, bool)):
                        metadata[key] = value
                    elif isinstance(value, list):
                        # For lists, store the length and first few items if they're strings
                        metadata[f"{key}_count"] = len(value)
                        if value and isinstance(value[0], str):
                            metadata[f"{key}_sample"] = value[:3]  # First 3 items
                    elif isinstance(value, dict):
                        # For dictionaries, flatten key-value pairs
                        for sub_key, sub_value in value.items():
                            if isinstance(sub_value, (str, int, float, bool)):
                                metadata[f"{key}_{sub_key}"] = sub_value
        # For review and qa documents, keep only the basic metadata (no additional fields)

        return metadata

    def load_jsonl_data(self, file_path: str) -> List[Dict[str, Any]]:
        """Load data from JSONL file"""
        data = []
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                for line_num, line in enumerate(file, 1):
                    try:
                        data.append(json.loads(line.strip()))
                    except json.JSONDecodeError as e:
                        logger.error(f"Error parsing line {line_num}: {e}")
                        continue
            logger.info(f"Successfully loaded {len(data)} products from {file_path}")
        except FileNotFoundError:
            logger.error(f"File {file_path} not found")
            raise
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise
        return data

    def create_title_document(self, product_data: Dict[str, Any]) -> Document:
        """Create a LangChain document for product title"""
        asin = product_data.get("asin", "")
        title = product_data.get("title", "")

        # Handle None case for title
        if title is None:
            title = ""

        # Generate unique UUID for this document
        doc_uuid = str(uuid.uuid4())

        # Extract dynamic metadata
        metadata = self.extract_dynamic_metadata(product_data, "title", f"title_{asin}")

        return Document(page_content=title, metadata=metadata, id=doc_uuid)

    def create_review_documents(self, product_data: Dict[str, Any]) -> List[Document]:
        """Create LangChain documents for product reviews"""
        asin = product_data.get("asin", "")
        review_docs = []

        # Check for different possible review fields
        reviews = product_data.get("reviews", [])
        review_combined = product_data.get("review_combined")

        # If review_combined is a string, treat it as a single review
        if isinstance(review_combined, str) and review_combined.strip():
            # Generate unique UUID for this document
            doc_uuid = str(uuid.uuid4())

            # Extract dynamic metadata
            metadata = self.extract_dynamic_metadata(
                product_data, "review", f"review_{asin}_combined"
            )
            metadata["review_index"] = 0

            review_docs.append(
                Document(page_content=review_combined, metadata=metadata, id=doc_uuid)
            )

        # Handle None case for reviews list
        if reviews is None:
            reviews = []

        for idx, review in enumerate(reviews):
            if not review or not review.strip():  # Skip empty reviews
                continue

            # Generate unique UUID for this document
            doc_uuid = str(uuid.uuid4())

            # Extract dynamic metadata
            metadata = self.extract_dynamic_metadata(
                product_data, "review", f"review_{asin}_{idx}"
            )
            metadata["review_index"] = idx

            # If review is a dict with additional fields (rating, date, etc.)
            if isinstance(review, dict):
                review_text = review.get("text", review.get("content", ""))
                # Add review-specific metadata
                for key, value in review.items():
                    if key not in ["text", "content"] and value is not None:
                        metadata[f"review_{key}"] = value
            else:
                review_text = str(review)

            if review_text.strip():  # Only add non-empty reviews
                review_docs.append(
                    Document(page_content=review_text, metadata=metadata, id=doc_uuid)
                )

        return review_docs

    def create_qa_documents(self, product_data: Dict[str, Any]) -> List[Document]:
        """Create LangChain documents for product Q&As"""
        asin = product_data.get("asin", "")
        qa_chunks = product_data.get("qa_chunks", [])
        qa_docs = []

        # Handle None case
        if qa_chunks is None:
            qa_chunks = []

        # Handle nested structure: list of lists of JSON objects
        chunk_idx = 0
        for chunk_group in qa_chunks:
            if not isinstance(chunk_group, list):
                continue

            for qa_item in chunk_group:
                if not isinstance(qa_item, dict):
                    continue

                question = qa_item.get("question", "").strip()
                answer = qa_item.get("answer", "").strip()

                if not question or not answer:  # Skip incomplete Q&As
                    continue

                # Combine question and answer for better semantic search
                qa_content = f"Q: {question}\nA: {answer}"

                # Generate unique UUID for this document
                doc_uuid = str(uuid.uuid4())

                # Extract dynamic metadata
                metadata = self.extract_dynamic_metadata(
                    product_data, "qa", f"qa_{asin}_{chunk_idx}"
                )
                metadata["qa_index"] = chunk_idx
                metadata["question"] = question
                metadata["answer"] = answer

                # Add QA-specific metadata from qa_item
                for key, value in qa_item.items():
                    if key not in ["question", "answer"] and value is not None:
                        metadata[f"qa_{key}"] = value

                qa_docs.append(
                    Document(page_content=qa_content, metadata=metadata, id=doc_uuid)
                )

                chunk_idx += 1

        return qa_docs

    def process_single_product(self, product_data: Dict[str, Any]) -> ProcessedProduct:
        """Process a single product into multi-vector documents"""
        asin = product_data.get("asin", "")

        if not asin:
            logger.warning("Product missing ASIN, skipping")
            return None

        try:
            # Log the structure for debugging
            logger.debug(f"Processing product {asin}")
            logger.debug(f"  - Title: {type(product_data.get('title'))}")
            logger.debug(f"  - Reviews: {type(product_data.get('reviews'))}")
            logger.debug(
                f"  - Review Combined: {type(product_data.get('review_combined'))}"
            )
            logger.debug(f"  - QA Chunks: {type(product_data.get('qa_chunks'))}")

            # Create documents for each content type
            title_doc = self.create_title_document(product_data)
            review_docs = self.create_review_documents(product_data)
            qa_docs = self.create_qa_documents(product_data)

            logger.debug(
                f"  Created: 1 title, {len(review_docs)} reviews, {len(qa_docs)} QAs"
            )

            return ProcessedProduct(
                asin=asin, title_doc=title_doc, review_docs=review_docs, qa_docs=qa_docs
            )
        except Exception as e:
            logger.error(f"Error processing product {asin}: {e}")
            logger.error(f"  Product data keys: {list(product_data.keys())}")
            logger.error(f"  Reviews type: {type(product_data.get('reviews'))}")
            logger.error(
                f"  Review Combined type: {type(product_data.get('review_combined'))}"
            )
            logger.error(f"  QA Chunks type: {type(product_data.get('qa_chunks'))}")
            return None

    def process_all_products(self, file_path: str) -> None:
        """Process all products from JSONL file"""
        logger.info("Starting product processing...")

        # Load data
        raw_data = self.load_jsonl_data(file_path)

        # Process each product
        self.processed_products = []
        skipped_count = 0

        for product_data in raw_data:
            processed = self.process_single_product(product_data)
            if processed:
                self.processed_products.append(processed)
            else:
                skipped_count += 1

        logger.info(f"Processing complete:")
        logger.info(
            f"  - Successfully processed: {len(self.processed_products)} products"
        )
        logger.info(f"  - Skipped: {skipped_count} products")

        # Print statistics
        self.print_processing_stats()

    def print_processing_stats(self) -> None:
        """Print statistics about processed data"""
        if not self.processed_products:
            logger.info("No products processed")
            return

        total_titles = len(self.processed_products)
        total_reviews = sum(len(p.review_docs) for p in self.processed_products)
        total_qas = sum(len(p.qa_docs) for p in self.processed_products)

        avg_reviews = total_reviews / total_titles if total_titles > 0 else 0
        avg_qas = total_qas / total_titles if total_titles > 0 else 0

        logger.info("Dataset Statistics:")
        logger.info(f"  - Total Products: {total_titles}")
        logger.info(f"  - Total Title Documents: {total_titles}")
        logger.info(f"  - Total Review Documents: {total_reviews}")
        logger.info(f"  - Total QA Documents: {total_qas}")
        logger.info(f"  - Average Reviews per Product: {avg_reviews:.2f}")
        logger.info(f"  - Average QAs per Product: {avg_qas:.2f}")
        logger.info(f"  - Total Documents: {total_titles + total_reviews + total_qas}")

    def get_documents_by_type(self, content_type: str) -> List[Document]:
        """Get all documents of a specific type"""
        if content_type == "title":
            return [p.title_doc for p in self.processed_products]
        elif content_type == "review":
            docs = []
            for p in self.processed_products:
                docs.extend(p.review_docs)
            return docs
        elif content_type == "qa":
            docs = []
            for p in self.processed_products:
                docs.extend(p.qa_docs)
            return docs
        else:
            raise ValueError(f"Unknown content type: {content_type}")

    def get_all_documents(self) -> Dict[str, List[Document]]:
        """Get all documents organized by type"""
        return {
            "titles": self.get_documents_by_type("title"),
            "reviews": self.get_documents_by_type("review"),
            "qas": self.get_documents_by_type("qa"),
        }

    def save_processed_data(self, output_file: str) -> None:
        """Save processed documents to JSON file for inspection"""
        output_data = {
            "processing_stats": {
                "total_products": len(self.processed_products),
                "total_titles": len(self.get_documents_by_type("title")),
                "total_reviews": len(self.get_documents_by_type("review")),
                "total_qas": len(self.get_documents_by_type("qa")),
            },
            "all_documents": {
                "titles": [doc.dict() for doc in self.get_documents_by_type("title")],
                "reviews": [doc.dict() for doc in self.get_documents_by_type("review")],
                "qas": [doc.dict() for doc in self.get_documents_by_type("qa")],
            },
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        logger.info(f"All processed documents saved to {output_file}")

    def save_documents_by_type(self, base_output_dir: str) -> None:
        """Save all documents organized by type to separate files"""
        import os

        # Create output directory if it doesn't exist
        os.makedirs(base_output_dir, exist_ok=True)

        # Save each document type separately
        for doc_type in ["titles", "reviews", "qas"]:
            docs = self.get_documents_by_type(doc_type[:-1])  # Remove 's' from plural
            output_file = os.path.join(base_output_dir, f"{doc_type}.jsonl")

            with open(output_file, "w", encoding="utf-8") as f:
                for doc in docs:
                    f.write(json.dumps(doc.dict(), ensure_ascii=False) + "\n")

            logger.info(f"Saved {len(docs)} {doc_type} to {output_file}")

    def save_all_documents_jsonl(self, output_file: str) -> None:
        """Save all documents to a single JSONL file"""
        all_docs = []

        # Add all document types with type identifier
        for doc in self.get_documents_by_type("title"):
            doc_dict = doc.dict()
            doc_dict["doc_type"] = "title"
            all_docs.append(doc_dict)

        for doc in self.get_documents_by_type("review"):
            doc_dict = doc.dict()
            doc_dict["doc_type"] = "review"
            all_docs.append(doc_dict)

        for doc in self.get_documents_by_type("qa"):
            doc_dict = doc.dict()
            doc_dict["doc_type"] = "qa"
            all_docs.append(doc_dict)

        with open(output_file, "w", encoding="utf-8") as f:
            for doc in all_docs:
                f.write(json.dumps(doc, ensure_ascii=False) + "\n")

        logger.info(f"Saved {len(all_docs)} total documents to {output_file}")


def main():
    """Example usage"""
    processor = MultiVectorDocumentProcessor()

    # Process the dataset
    processor.process_all_products("../data/processed/final_10k_dataset.jsonl")

    # Get documents by type
    all_docs = processor.get_all_documents()

    # Save all documents in different formats
    processor.save_processed_data("../data/processed/processed_data_summary.json")
    processor.save_documents_by_type("../data/processed/documents_by_type")
    processor.save_all_documents_jsonl("../data/processed/all_documents.jsonl")

    # Example: Access specific document types
    print(f"Title documents: {len(all_docs['titles'])}")
    print(f"Review documents: {len(all_docs['reviews'])}")
    print(f"QA documents: {len(all_docs['qas'])}")

    # Example: Look at a sample document
    if all_docs["titles"]:
        sample_title = all_docs["titles"][0]
        print(f"\nSample title document:")
        print(f"Content: {sample_title.page_content}")
        print(f"Metadata: {sample_title.metadata}")


if __name__ == "__main__":
    main()
