"""
Advanced RAG Evaluation System with Multiple Quality Metrics
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import json
import time


def convert_numpy_types(obj):
    """Convert numpy types to Python types for JSON serialization"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj


logger = logging.getLogger(__name__)


class MetricType(Enum):
    RELEVANCE = "relevance"
    ACCURACY = "accuracy"
    COMPLETENESS = "completeness"
    COHERENCE = "coherence"
    FLUENCY = "fluency"
    SOURCE_CITATION = "source_citation"
    HALLUCINATION = "hallucination"
    RESPONSE_TIME = "response_time"


@dataclass
class EvaluationConfig:
    """Evaluation configuration"""

    enable_relevance_scoring: bool = True
    enable_accuracy_checking: bool = True
    enable_hallucination_detection: bool = True
    enable_source_verification: bool = True
    enable_response_time_tracking: bool = True
    enable_confidence_calibration: bool = True
    relevance_threshold: float = 0.7
    accuracy_threshold: float = 0.8
    hallucination_threshold: float = 0.3


class RAGEvaluator:
    """Advanced RAG evaluation with multiple metrics"""

    def __init__(self, config: Optional[EvaluationConfig] = None):
        self.config = config or EvaluationConfig()

        # Initialize sentence transformer for similarity calculations
        try:
            self.similarity_model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Similarity model initialized for evaluation")
        except Exception as e:
            logger.warning(f"Failed to initialize similarity model: {e}")
            self.similarity_model = None

        logger.info(f"RAG evaluator initialized with config: {self.config}")

    def evaluate_rag_response(
        self,
        query: str,
        context: str,
        response: str,
        ground_truth: Optional[str] = None,
        response_time: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Evaluate RAG response quality"""

        evaluation_results = {
            "query": query,
            "response": response,
            "context_length": len(context),
            "response_length": len(response),
            "metrics": {},
        }

        # Relevance evaluation
        if self.config.enable_relevance_scoring:
            relevance_score = self._evaluate_relevance(query, response, context)
            evaluation_results["metrics"]["relevance"] = relevance_score

        # Accuracy evaluation
        if self.config.enable_accuracy_checking:
            accuracy_score = self._evaluate_accuracy(response, context)
            evaluation_results["metrics"]["accuracy"] = accuracy_score

        # Hallucination detection
        if self.config.enable_hallucination_detection:
            hallucination_score = self._detect_hallucinations(response, context)
            evaluation_results["metrics"]["hallucination"] = hallucination_score

        # Source citation evaluation
        if self.config.enable_source_verification:
            citation_score = self._evaluate_source_citations(response, context)
            evaluation_results["metrics"]["source_citation"] = citation_score

        # Response time evaluation
        if self.config.enable_response_time_tracking and response_time:
            time_score = self._evaluate_response_time(response_time)
            evaluation_results["metrics"]["response_time"] = time_score

        # Ground truth comparison
        if ground_truth:
            ground_truth_score = self._compare_with_ground_truth(response, ground_truth)
            evaluation_results["metrics"][
                "ground_truth_comparison"
            ] = ground_truth_score

        # Calculate overall score
        overall_score = self._calculate_overall_score(evaluation_results["metrics"])
        evaluation_results["overall_score"] = overall_score

        # Generate recommendations
        recommendations = self._generate_recommendations(evaluation_results["metrics"])
        evaluation_results["recommendations"] = recommendations

        # Convert any numpy types to Python types for JSON serialization
        return convert_numpy_types(evaluation_results)

    def _evaluate_relevance(
        self, query: str, response: str, context: str
    ) -> Dict[str, Any]:
        """Evaluate response relevance to query"""
        try:
            if not self.similarity_model:
                return {"score": 0.5, "reasoning": "Similarity model not available"}

            # Encode query, response, and context
            query_embedding = self.similarity_model.encode([query])[0]
            response_embedding = self.similarity_model.encode([response])[0]
            context_embedding = self.similarity_model.encode([context])[0]

            # Calculate similarities
            query_response_similarity = cosine_similarity(
                [query_embedding], [response_embedding]
            )[0][0]

            response_context_similarity = cosine_similarity(
                [response_embedding], [context_embedding]
            )[0][0]

            # Combined relevance score
            relevance_score = (
                query_response_similarity + response_context_similarity
            ) / 2

            result = {
                "score": float(relevance_score),
                "query_response_similarity": float(query_response_similarity),
                "response_context_similarity": float(response_context_similarity),
                "threshold": self.config.relevance_threshold,
                "is_above_threshold": bool(
                    relevance_score >= self.config.relevance_threshold
                ),
            }
            return convert_numpy_types(result)
        except Exception as e:
            logger.error(f"Error in relevance evaluation: {e}")
            return {"score": 0.5, "error": str(e)}

    def _evaluate_accuracy(self, response: str, context: str) -> Dict[str, Any]:
        """Evaluate response accuracy against context"""
        try:
            # Extract claims from response
            claims = self._extract_claims(response)

            if not claims:
                return {"score": 0.5, "reasoning": "No claims found in response"}

            verified_claims = 0
            total_claims = len(claims)

            for claim in claims:
                if self._verify_claim_in_context(claim, context):
                    verified_claims += 1

            accuracy_score = verified_claims / total_claims if total_claims > 0 else 0.5

            result = {
                "score": accuracy_score,
                "verified_claims": verified_claims,
                "total_claims": total_claims,
                "threshold": self.config.accuracy_threshold,
                "is_above_threshold": bool(
                    accuracy_score >= self.config.accuracy_threshold
                ),
            }
            return convert_numpy_types(result)
        except Exception as e:
            logger.error(f"Error in accuracy evaluation: {e}")
            return {"score": 0.5, "error": str(e)}

    def _detect_hallucinations(self, response: str, context: str) -> Dict[str, Any]:
        """Detect potential hallucinations in response"""
        try:
            # Extract claims from response
            claims = self._extract_claims(response)

            if not claims:
                return {"score": 0.5, "reasoning": "No claims found in response"}

            hallucinated_claims = 0
            total_claims = len(claims)

            for claim in claims:
                if not self._verify_claim_in_context(claim, context):
                    hallucinated_claims += 1

            hallucination_score = (
                hallucinated_claims / total_claims if total_claims > 0 else 0.0
            )

            result = {
                "score": hallucination_score,
                "hallucinated_claims": hallucinated_claims,
                "total_claims": total_claims,
                "threshold": self.config.hallucination_threshold,
                "is_below_threshold": bool(
                    hallucination_score <= self.config.hallucination_threshold
                ),
            }
            return convert_numpy_types(result)
        except Exception as e:
            logger.error(f"Error in hallucination detection: {e}")
            return {"score": 0.5, "error": str(e)}

    def _evaluate_source_citations(self, response: str, context: str) -> Dict[str, Any]:
        """Evaluate source citation quality"""
        try:
            # Check for citation indicators
            citation_indicators = [
                "according to",
                "based on",
                "the context shows",
                "as mentioned in",
                "from the information",
                "the data indicates",
                "research shows",
            ]

            citation_count = 0
            for indicator in citation_indicators:
                if indicator.lower() in response.lower():
                    citation_count += 1

            # Check for specific information from context
            context_words = set(context.lower().split())
            response_words = set(response.lower().split())
            context_overlap = len(context_words.intersection(response_words))

            citation_score = min(1.0, (citation_count + context_overlap / 100) / 2)

            result = {
                "score": citation_score,
                "citation_indicators": citation_count,
                "context_overlap": context_overlap,
                "reasoning": "Based on citation indicators and context overlap",
            }
            return convert_numpy_types(result)
        except Exception as e:
            logger.error(f"Error in source citation evaluation: {e}")
            return {"score": 0.5, "error": str(e)}

    def _evaluate_response_time(self, response_time: float) -> Dict[str, Any]:
        """Evaluate response time performance"""
        try:
            # Define time thresholds (in seconds)
            excellent_threshold = 2.0
            good_threshold = 5.0
            acceptable_threshold = 10.0

            if response_time <= excellent_threshold:
                score = 1.0
                rating = "excellent"
            elif response_time <= good_threshold:
                score = 0.8
                rating = "good"
            elif response_time <= acceptable_threshold:
                score = 0.6
                rating = "acceptable"
            else:
                score = 0.3
                rating = "slow"

            result = {
                "score": score,
                "response_time": response_time,
                "rating": rating,
                "excellent_threshold": excellent_threshold,
                "good_threshold": good_threshold,
                "acceptable_threshold": acceptable_threshold,
            }
            return convert_numpy_types(result)
        except Exception as e:
            logger.error(f"Error in response time evaluation: {e}")
            return {"score": 0.5, "error": str(e)}

    def _compare_with_ground_truth(
        self, response: str, ground_truth: str
    ) -> Dict[str, Any]:
        """Compare response with ground truth"""
        try:
            if not self.similarity_model:
                return {"score": 0.5, "reasoning": "Similarity model not available"}

            # Calculate similarity between response and ground truth
            response_embedding = self.similarity_model.encode([response])[0]
            ground_truth_embedding = self.similarity_model.encode([ground_truth])[0]

            similarity = cosine_similarity(
                [response_embedding], [ground_truth_embedding]
            )[0][0]

            result = {
                "score": float(similarity),
                "ground_truth_length": len(ground_truth),
                "response_length": len(response),
                "similarity": float(similarity),
            }
            return convert_numpy_types(result)
        except Exception as e:
            logger.error(f"Error in ground truth comparison: {e}")
            return {"score": 0.5, "error": str(e)}

    def _extract_claims(self, text: str) -> List[str]:
        """Extract factual claims from text"""
        # Simple claim extraction - can be enhanced with NLP
        sentences = text.split(".")
        claims = []

        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 10:  # Filter out very short sentences
                # Look for factual statements
                factual_indicators = [
                    "is",
                    "are",
                    "has",
                    "have",
                    "contains",
                    "includes",
                    "features",
                    "offers",
                    "provides",
                    "supports",
                    "works",
                    "functions",
                ]

                if any(
                    indicator in sentence.lower() for indicator in factual_indicators
                ):
                    claims.append(sentence)

        return claims

    def _verify_claim_in_context(self, claim: str, context: str) -> bool:
        """Verify if a claim is supported by the context"""
        try:
            if not self.similarity_model:
                return True  # Assume true if no similarity model

            # Calculate similarity between claim and context
            claim_embedding = self.similarity_model.encode([claim])[0]
            context_embedding = self.similarity_model.encode([context])[0]

            similarity = cosine_similarity([claim_embedding], [context_embedding])[0][0]

            # Consider claim verified if similarity is above threshold
            return bool(similarity > 0.3)
        except Exception as e:
            logger.error(f"Error in claim verification: {e}")
            return True  # Assume true on error

    def _calculate_overall_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate overall evaluation score"""
        try:
            scores = []
            weights = {
                "relevance": 0.3,
                "accuracy": 0.25,
                "hallucination": 0.2,
                "source_citation": 0.15,
                "response_time": 0.1,
            }

            for metric_name, weight in weights.items():
                if metric_name in metrics:
                    metric_data = metrics[metric_name]
                    if isinstance(metric_data, dict) and "score" in metric_data:
                        # For hallucination, invert the score (lower is better)
                        if metric_name == "hallucination":
                            score = 1.0 - metric_data["score"]
                        else:
                            score = metric_data["score"]
                        scores.append(score * weight)

            overall_score = sum(scores) if scores else 0.5
            return min(1.0, max(0.0, overall_score))
        except Exception as e:
            logger.error(f"Error calculating overall score: {e}")
            return 0.5

    def _generate_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """Generate improvement recommendations based on metrics"""
        recommendations = []

        # Relevance recommendations
        if "relevance" in metrics:
            relevance_data = metrics["relevance"]
            if isinstance(relevance_data, dict) and "score" in relevance_data:
                if relevance_data["score"] < 0.7:
                    recommendations.append("Improve response relevance to the query")

        # Accuracy recommendations
        if "accuracy" in metrics:
            accuracy_data = metrics["accuracy"]
            if isinstance(accuracy_data, dict) and "score" in accuracy_data:
                if accuracy_data["score"] < 0.8:
                    recommendations.append(
                        "Ensure all claims are supported by the context"
                    )

        # Hallucination recommendations
        if "hallucination" in metrics:
            hallucination_data = metrics["hallucination"]
            if isinstance(hallucination_data, dict) and "score" in hallucination_data:
                if hallucination_data["score"] > 0.3:
                    recommendations.append("Reduce unsupported claims in the response")

        # Source citation recommendations
        if "source_citation" in metrics:
            citation_data = metrics["source_citation"]
            if isinstance(citation_data, dict) and "score" in citation_data:
                if citation_data["score"] < 0.6:
                    recommendations.append("Add more source citations to the response")

        # Response time recommendations
        if "response_time" in metrics:
            time_data = metrics["response_time"]
            if isinstance(time_data, dict) and "score" in time_data:
                if time_data["score"] < 0.6:
                    recommendations.append("Optimize response generation time")

        if not recommendations:
            recommendations.append("Response quality is good overall")

        return recommendations

    def evaluate_retrieval_quality(
        self, query: str, retrieved_docs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Evaluate retrieval quality"""
        try:
            if not retrieved_docs:
                return {"score": 0.0, "reasoning": "No documents retrieved"}

            # Calculate diversity of retrieved documents
            unique_sources = set()
            total_score = 0

            for doc in retrieved_docs:
                if "metadata" in doc and "source" in doc["metadata"]:
                    unique_sources.add(doc["metadata"]["source"])

                if "score" in doc:
                    total_score += doc["score"]

            diversity_score = (
                len(unique_sources) / len(retrieved_docs) if retrieved_docs else 0
            )
            average_score = total_score / len(retrieved_docs) if retrieved_docs else 0

            result = {
                "score": (diversity_score + average_score) / 2,
                "diversity_score": diversity_score,
                "average_score": average_score,
                "unique_sources": len(unique_sources),
                "total_documents": len(retrieved_docs),
            }
            return convert_numpy_types(result)
        except Exception as e:
            logger.error(f"Error in retrieval quality evaluation: {e}")
            return {"score": 0.5, "error": str(e)}

    def generate_evaluation_report(self, evaluation_results: Dict[str, Any]) -> str:
        """Generate a human-readable evaluation report"""
        try:
            report = f"""
RAG Evaluation Report
====================

Query: {evaluation_results.get('query', 'N/A')}
Response Length: {evaluation_results.get('response_length', 0)} characters
Context Length: {evaluation_results.get('context_length', 0)} characters

Overall Score: {evaluation_results.get('overall_score', 0):.2f}

Detailed Metrics:
"""

            metrics = evaluation_results.get("metrics", {})
            for metric_name, metric_data in metrics.items():
                if isinstance(metric_data, dict) and "score" in metric_data:
                    report += f"- {metric_name.title()}: {metric_data['score']:.2f}\n"

            recommendations = evaluation_results.get("recommendations", [])
            if recommendations:
                report += "\nRecommendations:\n"
                for rec in recommendations:
                    report += f"- {rec}\n"

            return report
        except Exception as e:
            logger.error(f"Error generating evaluation report: {e}")
            return f"Error generating report: {e}"
