"""
Advanced Agent with Chain-of-Thought Reasoning for Intelligent Retrieval Decision Making
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import asyncio
import json
import re
from datetime import datetime
from rag.rag_utils import llm_client

logger = logging.getLogger(__name__)


class QuestionAnalysisTool:
    """Tool to perform deep analysis of user questions using chain-of-thought reasoning"""

    def __init__(self, llm_client=None):
        self.llm_client = llm_client or llm_client

    async def analyze_question(self, question: str, conversation_history: str) -> str:
        """Analyze the question using chain-of-thought reasoning"""

        analysis_prompt = f"""You are an expert at analyzing user questions to understand their information needs. 
        Use chain-of-thought reasoning to deeply analyze the user's question and determine what they're really asking for.

        Analyze the question step by step:
        1. **Intent Analysis**: What is the user trying to accomplish?
        2. **Context Analysis**: How does this relate to previous conversation?
        3. **Information Gap Analysis**: What information is needed to answer this question?
        4. **Reference Analysis**: Is the user referring to previously mentioned items/concepts?
        5. **Scope Analysis**: Is this a new request or elaboration on existing information?

        Return your analysis as a JSON object with the following structure:
        {{
            "reasoning_steps": [
                "Step 1: Intent analysis...",
                "Step 2: Context analysis...",
                "Step 3: Information gap analysis...",
                "Step 4: Reference analysis...",
                "Step 5: Scope analysis..."
            ],
            "intent": "primary intent of the question",
            "context_dependency": "high|medium|low - how much this depends on conversation history",
            "information_sufficiency": "sufficient|insufficient|partial - whether conversation history has enough info",
            "reference_type": "explicit|implicit|none - type of reference to previous conversation",
            "question_type": "new_request|clarification|comparison|elaboration|follow_up",
            "confidence": "high|medium|low - confidence in analysis"
        }}

        Question: "{question}"

        Conversation History:
        {conversation_history}

        Please analyze this question using chain-of-thought reasoning."""

        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert question analyzer. Provide detailed analysis in JSON format.",
                },
                {"role": "user", "content": analysis_prompt},
            ]

            response = await self.llm_client.generate_response_async(messages)

            # Extract JSON from response
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                return json_match.group(0)
            else:
                return response

        except Exception as e:
            logger.error(f"Error in question analysis: {e}")
            return json.dumps(
                {
                    "reasoning_steps": [f"Error in analysis: {str(e)}"],
                    "intent": "unknown",
                    "context_dependency": "low",
                    "information_sufficiency": "insufficient",
                    "reference_type": "none",
                    "question_type": "new_request",
                    "confidence": "low",
                }
            )


class ConversationContextTool:
    """Tool to extract and analyze relevant context from conversation history"""

    def __init__(self, llm_client=None):
        self.llm_client = llm_client or llm_client

    async def analyze_context(self, question: str, conversation_history: str) -> str:
        """Analyze conversation context asynchronously"""

        if not conversation_history:
            return json.dumps(
                {
                    "relevant_context": [],
                    "sufficiency": "insufficient",
                    "missing_information": ["No conversation history available"],
                    "confidence": "high",
                }
            )

        context_prompt = f"""You are an expert at analyzing conversation context to determine information availability.

        Analyze the conversation history to determine:
        1. What relevant information is already available
        2. Whether this information is sufficient to answer the current question
        3. What specific information might be missing
        4. How confident you are in this assessment

        Return your analysis as JSON:
        {{
            "relevant_context": ["list of relevant information from conversation"],
            "sufficiency": "sufficient|partial|insufficient",
            "missing_information": ["list of information that would be needed"],
            "confidence": "high|medium|low"
        }}

        Current Question: "{question}"

        Conversation History:
        {conversation_history}

        Analyze the conversation context for this question."""

        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert context analyzer. Provide detailed analysis in JSON format.",
                },
                {"role": "user", "content": context_prompt},
            ]

            response = await self.llm_client.generate_response_async(messages)

            content = response
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                return json_match.group(0)
            else:
                return content

        except Exception as e:
            logger.error(f"Error in context analysis: {e}")
            return json.dumps(
                {
                    "relevant_context": [],
                    "sufficiency": "insufficient",
                    "missing_information": [f"Error in analysis: {str(e)}"],
                    "confidence": "low",
                }
            )


class RetrievalDecisionTool:
    """Advanced tool to make intelligent retrieval decisions using chain-of-thought reasoning"""

    def __init__(self, llm_client=None):
        self.llm_client = llm_client or llm_client

    async def make_decision(self, question_analysis: str, context_analysis: str) -> str:
        """Make retrieval decision using chain-of-thought reasoning"""

        decision_prompt = f"""You are an expert decision maker for information retrieval systems.

        Based on the question analysis and context analysis provided, make an intelligent decision about whether to:
        1. RETRIEVE - Get new information from external sources
        2. CONVERSATION - Use existing conversation history
        3. HYBRID - Use conversation context but supplement with new retrieval

        Use chain-of-thought reasoning to make your decision:

        Decision Criteria:
        - If question_type is "new_request" and context sufficiency is "insufficient" → RETRIEVE
        - If question_type is "follow_up" or "clarification" and context sufficiency is "sufficient" → CONVERSATION  
        - If context sufficiency is "partial" → HYBRID
        - If reference_type is "explicit" and sufficiency is "sufficient" → CONVERSATION
        - If information_sufficiency is "insufficient" regardless of context → RETRIEVE

        Return your decision as JSON:
        {{
            "reasoning_steps": [
                "Step 1: Analyzing question type and intent...",
                "Step 2: Evaluating context sufficiency...",
                "Step 3: Considering reference patterns...",
                "Step 4: Making final decision..."
            ],
            "decision": "RETRIEVE|CONVERSATION|HYBRID",
            "confidence": "high|medium|low",
            "rationale": "detailed explanation of the decision"
        }}

        Question Analysis:
        {question_analysis}

        Context Analysis:
        {context_analysis}

        Please make a retrieval decision using chain-of-thought reasoning."""

        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert decision maker. Provide detailed analysis in JSON format.",
                },
                {"role": "user", "content": decision_prompt},
            ]

            response = await self.llm_client.generate_response_async(messages)

            content = response
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                return json_match.group(0)
            else:
                return content

        except Exception as e:
            logger.error(f"Error in retrieval decision: {e}")
            return json.dumps(
                {
                    "reasoning_steps": [f"Error in decision making: {str(e)}"],
                    "decision": "RETRIEVE",
                    "confidence": "low",
                    "rationale": "Defaulting to retrieval due to analysis error",
                }
            )


class AdvancedRetrievalAgent:
    """Advanced Agent with Chain-of-Thought Reasoning for Intelligent Retrieval Decisions"""

    def __init__(self, memory_manager=None, llm_client=None):
        self.memory_manager = memory_manager
        self.llm_client = llm_client or llm_client

        # Initialize tools
        self.question_tool = QuestionAnalysisTool(self.llm_client)
        self.context_tool = ConversationContextTool(self.llm_client)
        self.decision_tool = RetrievalDecisionTool(self.llm_client)

    async def should_retrieve_new_data(
        self, question: str, session_id: str = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Use advanced chain-of-thought reasoning to determine if new data retrieval is needed.

        Args:
            question: The user's question
            session_id: The session ID for conversation history

        Returns:
            Tuple of (should_retrieve: bool, analysis_details: Dict)
        """
        try:
            # Get conversation history if available
            conversation_history = ""
            if session_id and self.memory_manager:
                try:
                    conversation_history = (
                        await self.memory_manager.get_conversation_summary_async(
                            session_id
                        )
                    )
                except Exception as e:
                    logger.warning(f"Error getting conversation history: {e}")

            # Step 1: Analyze the question
            logger.info("Step 1: Analyzing question with chain-of-thought reasoning")
            question_analysis = await self.question_tool.analyze_question(
                question, conversation_history
            )

            # Step 2: Analyze conversation context
            logger.info("Step 2: Analyzing conversation context")
            context_analysis = await self.context_tool.analyze_context(
                question, conversation_history
            )

            # Step 3: Make retrieval decision
            logger.info("Step 3: Making intelligent retrieval decision")
            decision_analysis = await self.decision_tool.make_decision(
                question_analysis, context_analysis
            )

            # Parse the decision
            try:
                decision_data = json.loads(decision_analysis)
                decision = decision_data.get("decision", "RETRIEVE")

                logger.info(f"Agent decision for question '{question}': {decision}")
                logger.info(
                    f"Decision rationale: {decision_data.get('rationale', 'No rationale provided')}"
                )

                # Prepare detailed analysis for return
                analysis_details = {
                    "question_analysis": (
                        json.loads(question_analysis)
                        if question_analysis.startswith("{")
                        else {"error": "Failed to parse question analysis"}
                    ),
                    "context_analysis": (
                        json.loads(context_analysis)
                        if context_analysis.startswith("{")
                        else {"error": "Failed to parse context analysis"}
                    ),
                    "decision_analysis": decision_data,
                    "timestamp": datetime.now().isoformat(),
                }

                # Return decision
                if decision == "RETRIEVE":
                    return True, analysis_details
                elif decision == "CONVERSATION":
                    return False, analysis_details
                elif decision == "HYBRID":
                    # For hybrid approach, we'll return True but include context information
                    analysis_details["hybrid_mode"] = True
                    return True, analysis_details
                else:
                    logger.warning(
                        f"Unknown decision type: {decision}, defaulting to RETRIEVE"
                    )
                    return True, analysis_details

            except json.JSONDecodeError as e:
                logger.error(f"Error parsing decision analysis JSON: {e}")
                return True, {
                    "error": "Failed to parse decision analysis",
                    "raw_response": decision_analysis,
                }

        except Exception as e:
            logger.error(f"Error in advanced retrieval decision: {e}")
            # Fallback to simple keyword-based approach
            return self._fallback_decision(question, conversation_history), {
                "error": str(e),
                "fallback": True,
            }

    def _fallback_decision(self, question: str, conversation_history: str) -> bool:
        """Enhanced fallback decision with basic reasoning"""

        if not conversation_history:
            return True

        # Enhanced keyword analysis with context
        new_request_patterns = [
            r"\b(find|search|look for|show me|get|retrieve)\b",
            r"\b(what are|which|recommend|suggest)\b",
            r"\b(new|different|other|more|additional)\b",
            r"\b(latest|best|top|popular)\b",
        ]

        conversation_reference_patterns = [
            r"\b(you (mentioned|said|told)|what did you)\b",
            r"\b(from (before|earlier)|previously)\b",
            r"\b(that|those|the ones|them|it|this)\b",
            r"\b(compare|between these|which of)\b",
        ]

        question_lower = question.lower()

        new_request_score = sum(
            1 for pattern in new_request_patterns if re.search(pattern, question_lower)
        )
        conversation_score = sum(
            1
            for pattern in conversation_reference_patterns
            if re.search(pattern, question_lower)
        )

        logger.info(
            f"Fallback analysis - New request score: {new_request_score}, Conversation score: {conversation_score}"
        )

        if new_request_score > conversation_score:
            return True
        elif conversation_score > new_request_score:
            return False
        else:
            # Default to conversation if we have history, otherwise retrieve
            return len(conversation_history.strip()) < 100

    async def get_detailed_analysis(
        self, question: str, session_id: str = None
    ) -> Dict[str, Any]:
        """
        Get detailed analysis of the question and decision-making process.

        Args:
            question: The user's question
            session_id: The session ID for conversation history

        Returns:
            Detailed analysis dictionary
        """
        should_retrieve, analysis = await self.should_retrieve_new_data(
            question, session_id
        )
        analysis["final_decision"] = "RETRIEVE" if should_retrieve else "CONVERSATION"
        return analysis


# Alias for backward compatibility
RetrievalAgent = AdvancedRetrievalAgent
