#!/usr/bin/env python3
"""
Test script for comprehensive token tracking with rich tabular output.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from rich_logging import log_comprehensive_token_breakdown, get_token_statistics
from rich.console import Console

console = Console()

async def test_comprehensive_token_tracking():
    """Test the comprehensive token tracking functionality."""
    
    console.print("[bold blue]Testing Comprehensive Token Tracking[/bold blue]")
    console.print("=" * 60)
    
    # Test data for different scenarios
    test_cases = [
        {
            "name": "Simple Query with Context",
            "session_id": "test_session_001",
            "query_data": {
                "user_prompt": "What are the best features of this product?",
                "system_prompt": "You are a helpful assistant that provides accurate information about products. Always be concise and informative.",
                "conversation_history": "",
                "retrieved_context": "Product features include: 1. High performance with 99.9% uptime 2. Easy to use interface with intuitive design 3. Affordable pricing starting at $9.99/month 4. 24/7 customer support 5. Advanced security features with encryption",
                "llm_response": "Based on the information provided, this product offers excellent features including high performance with 99.9% uptime, an easy-to-use interface, affordable pricing starting at $9.99/month, 24/7 customer support, and advanced security features with encryption."
            }
        },
        {
            "name": "Conversation with History",
            "session_id": "test_session_002", 
            "query_data": {
                "user_prompt": "Can you tell me more about the pricing?",
                "system_prompt": "You are a helpful assistant that provides accurate information about products. Always be concise and informative.",
                "conversation_history": "User: What are the best features of this product? Assistant: Based on the information provided, this product offers excellent features including high performance with 99.9% uptime, an easy-to-use interface, affordable pricing starting at $9.99/month, 24/7 customer support, and advanced security features with encryption.",
                "retrieved_context": "Pricing details: Basic plan: $9.99/month, Pro plan: $19.99/month, Enterprise plan: $49.99/month. All plans include 24/7 support and security features.",
                "llm_response": "Based on our previous conversation and the pricing information, the product offers three tiers: Basic at $9.99/month, Pro at $19.99/month, and Enterprise at $49.99/month. All plans include the 24/7 support and security features we discussed earlier."
            }
        },
        {
            "name": "Complex Query with Large Context",
            "session_id": "test_session_003",
            "query_data": {
                "user_prompt": "How does this compare to competitors?",
                "system_prompt": "You are a helpful assistant that provides accurate information about products. Always be concise and informative. When comparing products, focus on objective differences and avoid making unsubstantiated claims.",
                "conversation_history": "User: What are the best features of this product? Assistant: Based on the information provided, this product offers excellent features including high performance with 99.9% uptime, an easy-to-use interface, affordable pricing starting at $9.99/month, 24/7 customer support, and advanced security features with encryption. User: Can you tell me more about the pricing? Assistant: Based on our previous conversation and the pricing information, the product offers three tiers: Basic at $9.99/month, Pro at $19.99/month, and Enterprise at $49.99/month. All plans include the 24/7 support and security features we discussed earlier.",
                "retrieved_context": "Competitive analysis: Our product vs competitors: 1. Performance: Our product achieves 99.9% uptime vs competitor average of 98.5% 2. Pricing: Our Basic plan at $9.99/month is 20% lower than competitor average of $12.49/month 3. Features: We offer 5 core features vs competitor average of 3 features 4. Support: 24/7 support included vs competitors offering 8-5 support only 5. Security: Advanced encryption vs basic security in most competitors 6. Ease of use: 4.8/5 user rating vs competitor average of 4.2/5",
                "llm_response": "Based on the competitive analysis, our product compares favorably to competitors in several key areas: 1. Performance: 99.9% uptime vs competitor average of 98.5% 2. Pricing: 20% lower than competitor average 3. Features: 5 core features vs competitor average of 3 4. Support: 24/7 support vs competitors' 8-5 support 5. Security: Advanced encryption vs basic security 6. User satisfaction: 4.8/5 rating vs competitor average of 4.2/5"
            }
        },
        {
            "name": "Conversation Only Mode",
            "session_id": "test_session_004",
            "query_data": {
                "user_prompt": "What did we discuss earlier?",
                "system_prompt": "You are a helpful assistant. Use the conversation history to provide relevant information from previous interactions.",
                "conversation_history": "User: What are the best features of this product? Assistant: Based on the information provided, this product offers excellent features including high performance with 99.9% uptime, an easy-to-use interface, affordable pricing starting at $9.99/month, 24/7 customer support, and advanced security features with encryption. User: Can you tell me more about the pricing? Assistant: Based on our previous conversation and the pricing information, the product offers three tiers: Basic at $9.99/month, Pro at $19.99/month, and Enterprise at $49.99/month. All plans include the 24/7 support and security features we discussed earlier. User: How does this compare to competitors? Assistant: Based on the competitive analysis, our product compares favorably to competitors in several key areas: 1. Performance: 99.9% uptime vs competitor average of 98.5% 2. Pricing: 20% lower than competitor average 3. Features: 5 core features vs competitor average of 3 4. Support: 24/7 support vs competitors' 8-5 support 5. Security: Advanced encryption vs basic security 6. User satisfaction: 4.8/5 rating vs competitor average of 4.2/5",
                "retrieved_context": "",
                "llm_response": "Based on our previous conversation, we discussed the product's key features including high performance (99.9% uptime), easy-to-use interface, affordable pricing (starting at $9.99/month), 24/7 customer support, and advanced security features. We also covered the three pricing tiers (Basic $9.99/month, Pro $19.99/month, Enterprise $49.99/month) and how the product compares favorably to competitors in performance, pricing, features, support, security, and user satisfaction."
            }
        }
    ]
    
    # Run test cases
    for i, test_case in enumerate(test_cases, 1):
        console.print(f"\n[bold cyan]Test Case {i}: {test_case['name']}[/bold cyan]")
        console.print("-" * 40)
        
        # Log comprehensive token breakdown
        log_comprehensive_token_breakdown(
            test_case["session_id"], 
            test_case["query_data"]
        )
        
        # Add some spacing between test cases
        console.print("\n" + "=" * 60)
    
    # Show final statistics
    console.print("\n[bold green]Final Token Statistics[/bold green]")
    console.print("-" * 30)
    
    stats = get_token_statistics()
    console.print(f"Total Queries: {stats['total_queries']}")
    console.print(f"Total Tokens Processed: {stats['total_tokens_processed']:,}")
    console.print(f"Average Tokens per Query: {stats['average_tokens_per_query']:.1f}")
    
    if stats['session_breakdown']:
        console.print("\n[bold]Session Breakdown:[/bold]")
        for session_id, session_stats in stats['session_breakdown'].items():
            console.print(f"  {session_id}: {session_stats['queries']} queries, {session_stats['total_tokens']:,} tokens")
    
    console.print("\n[bold green]✅ Comprehensive token tracking test completed![/bold green]")


if __name__ == "__main__":
    asyncio.run(test_comprehensive_token_tracking()) 