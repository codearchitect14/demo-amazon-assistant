"""
Advanced Prompt Engineering for RAG with Chain-of-Thought Reasoning
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class ReasoningType(Enum):
    CHAIN_OF_THOUGHT = "chain_of_thought"
    TREE_OF_THOUGHTS = "tree_of_thoughts"
    STEP_BY_STEP = "step_by_step"
    STRUCTURED_REASONING = "structured_reasoning"


@dataclass
class AdvancedPromptConfig:
    """Advanced prompt configuration"""

    reasoning_type: ReasoningType = ReasoningType.CHAIN_OF_THOUGHT
    enable_structured_output: bool = True
    enable_confidence_scoring: bool = True
    enable_source_citation: bool = True
    enable_uncertainty_handling: bool = True
    enable_multi_step_reasoning: bool = True
    max_reasoning_steps: int = 5


class AdvancedPromptEngineer:
    """Advanced prompt engineering with structured reasoning"""

    def __init__(self, config: Optional[AdvancedPromptConfig] = None):
        self.config = config or AdvancedPromptConfig()
        logger.info(
            f"Advanced prompt engineer initialized with reasoning type: {self.config.reasoning_type}"
        )

    def build_chain_of_thought_prompt(
        self, context: str, question: str, conversation_history: str = ""
    ) -> str:
        """Build chain-of-thought reasoning prompt"""

        prompt = f"""You are an intelligent assistant that helps users find and understand product information. Use chain-of-thought reasoning to provide accurate, helpful responses.

CONTEXT INFORMATION:
{context}

CONVERSATION HISTORY:
{conversation_history if conversation_history else "No previous conversation."}

USER QUESTION: {question}

INSTRUCTIONS:
1. First, analyze the context information carefully
2. Consider the conversation history for context
3. Think step-by-step about how to answer the question
4. Provide a clear, helpful response
5. If you're unsure about something, acknowledge the uncertainty
6. Cite specific information from the context when possible

REASONING PROCESS:
Let me think through this step by step:

1. What is the user asking for?
2. What relevant information is available in the context?
3. How does this relate to any previous conversation?
4. What is the best way to answer this question?
5. Are there any uncertainties or limitations?

ANSWER:
"""
        return prompt

    def build_tree_of_thoughts_prompt(self, context: str, question: str) -> str:
        """Build tree-of-thoughts reasoning prompt"""

        prompt = f"""You are an intelligent assistant that helps users find and understand product information. Use tree-of-thoughts reasoning to explore multiple perspectives.

CONTEXT INFORMATION:
{context}

USER QUESTION: {question}

INSTRUCTIONS:
Consider multiple approaches to answering this question:

APPROACH 1: Direct answer based on context
APPROACH 2: Comparative analysis if multiple options exist
APPROACH 3: Consider user preferences and needs
APPROACH 4: Address potential concerns or questions

EVALUATE EACH APPROACH:
- Which approach provides the most helpful answer?
- What are the pros and cons of each approach?
- How can we combine insights from multiple approaches?

FINAL ANSWER:
"""
        return prompt

    def build_structured_reasoning_prompt(self, context: str, question: str) -> str:
        """Build structured reasoning prompt with JSON output"""

        prompt = f"""You are an intelligent assistant that helps users find and understand product information. Provide a structured response.

CONTEXT INFORMATION:
{context}

USER QUESTION: {question}

INSTRUCTIONS:
Analyze the question and context, then provide a structured response in the following JSON format:

{{
    "reasoning": {{
        "question_analysis": "What the user is asking for",
        "context_relevance": "How the context relates to the question",
        "key_findings": ["List of important information found"],
        "uncertainties": ["Any areas of uncertainty"]
    }},
    "answer": {{
        "main_response": "Your primary answer",
        "supporting_details": ["Supporting information"],
        "recommendations": ["Any recommendations"],
        "caveats": ["Any limitations or warnings"]
    }},
    "confidence": {{
        "score": 0.95,
        "reasoning": "Why you're confident or uncertain"
    }},
    "sources": {{
        "cited_information": ["Specific information from context"],
        "source_quality": "Assessment of information quality"
    }}
}}

RESPONSE:
"""
        return prompt

    def build_multi_step_reasoning_prompt(
        self, context: str, question: str, steps: List[str]
    ) -> str:
        """Build multi-step reasoning prompt"""

        step_text = "\n".join([f"{i+1}. {step}" for i, step in enumerate(steps)])

        prompt = f"""You are an intelligent assistant that helps users find and understand product information. Follow these reasoning steps:

CONTEXT INFORMATION:
{context}

USER QUESTION: {question}

REASONING STEPS:
{step_text}

INSTRUCTIONS:
Follow each step carefully and provide your reasoning for each step before giving the final answer.

STEP-BY-STEP REASONING:
"""
        return prompt

    def build_uncertainty_aware_prompt(self, context: str, question: str) -> str:
        """Build uncertainty-aware prompt"""

        prompt = f"""You are an intelligent assistant that helps users find and understand product information. Be honest about what you know and don't know.

CONTEXT INFORMATION:
{context}

USER QUESTION: {question}

INSTRUCTIONS:
1. Answer the question based on the available context
2. Clearly indicate any uncertainties or limitations
3. Distinguish between facts and opinions
4. If information is missing, acknowledge it
5. Provide the best possible answer given the available information

UNCERTAINTY ASSESSMENT:
- What do we know for certain?
- What might be true but we're not sure?
- What information is missing?
- How confident should the user be in this answer?

ANSWER:
"""
        return prompt

    def build_source_citation_prompt(self, context: str, question: str) -> str:
        """Build prompt that requires source citation"""

        prompt = f"""You are an intelligent assistant that helps users find and understand product information. Always cite your sources.

CONTEXT INFORMATION:
{context}

USER QUESTION: {question}

INSTRUCTIONS:
1. Answer the question based on the provided context
2. Cite specific information from the context
3. Use phrases like "According to the context..." or "Based on the information..."
4. If you're making inferences, clearly state them
5. Provide a helpful, accurate response

CITATION FORMAT:
- When stating facts: "According to the context, [fact]"
- When making comparisons: "The context shows that [comparison]"
- When providing recommendations: "Based on the available information, [recommendation]"

ANSWER:
"""
        return prompt

    def build_advanced_prompt(
        self, context: str, question: str, conversation_history: str = ""
    ) -> str:
        """Build advanced prompt based on configuration"""

        if self.config.reasoning_type == ReasoningType.CHAIN_OF_THOUGHT:
            return self.build_chain_of_thought_prompt(
                context, question, conversation_history
            )
        elif self.config.reasoning_type == ReasoningType.TREE_OF_THOUGHTS:
            return self.build_tree_of_thoughts_prompt(context, question)
        elif self.config.reasoning_type == ReasoningType.STRUCTURED_REASONING:
            return self.build_structured_reasoning_prompt(context, question)
        else:
            # Default to chain of thought
            return self.build_chain_of_thought_prompt(
                context, question, conversation_history
            )

    def parse_structured_response(self, response: str) -> Dict[str, Any]:
        """Parse structured response from LLM"""
        try:
            # Try to extract JSON from response
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]

                parsed = json.loads(json_str)

                # Validate structure
                return self.validate_response_structure(parsed)
            else:
                # Fallback to simple parsing
                return {
                    "final_answer": response.strip(),
                    "reasoning": "No structured reasoning provided",
                    "confidence": {"score": 0.7, "reasoning": "Default confidence"},
                }
        except Exception as e:
            logger.warning(f"Failed to parse structured response: {e}")
            return {
                "final_answer": response.strip(),
                "reasoning": "Failed to parse structured response",
                "confidence": {"score": 0.5, "reasoning": "Parsing failed"},
            }

    def validate_response_structure(
        self, parsed_response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate and clean parsed response structure"""

        # Ensure required fields exist
        if "answer" not in parsed_response:
            parsed_response["answer"] = {"main_response": "No answer provided"}

        if "reasoning" not in parsed_response:
            parsed_response["reasoning"] = {
                "question_analysis": "No reasoning provided"
            }

        if "confidence" not in parsed_response:
            parsed_response["confidence"] = {
                "score": 0.7,
                "reasoning": "Default confidence",
            }

        # Extract final answer
        if isinstance(parsed_response["answer"], dict):
            final_answer = parsed_response["answer"].get(
                "main_response", "No answer provided"
            )
        else:
            final_answer = str(parsed_response["answer"])

        parsed_response["final_answer"] = final_answer

        return parsed_response
