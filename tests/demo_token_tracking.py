#!/usr/bin/env python3
"""
Demo script showing comprehensive token tracking in the RAG pipeline.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from rag.rag_pipeline import RAGPipeline
from app.config import Config
from rich.console import Console

console = Console()

async def demo_token_tracking():
    """Demo the comprehensive token tracking functionality."""
    
    console.print("[bold blue]RAG Pipeline Token Tracking Demo[/bold blue]")
    console.print("=" * 60)
    
    try:
        # Initialize RAG pipeline
        console.print("[yellow]Initializing RAG pipeline...[/yellow]")
        pipeline = RAGPipeline(
            enable_memory=True,
            memory_type="in_memory"  # Use in-memory for demo
        )
        
        # Test queries
        test_queries = [
            {
                "question": "What are the best features of Amazon products?",
                "session_id": "demo_session_001",
                "description": "First query with context retrieval"
            },
            {
                "question": "Can you tell me more about the pricing?",
                "session_id": "demo_session_001", 
                "description": "Follow-up query using conversation history"
            },
            {
                "question": "What did we discuss earlier?",
                "session_id": "demo_session_001",
                "description": "Conversation-only query"
            }
        ]
        
        for i, query_info in enumerate(test_queries, 1):
            console.print(f"\n[bold cyan]Query {i}: {query_info['description']}[/bold cyan]")
            console.print(f"[dim]Question: {query_info['question']}[/dim]")
            console.print("-" * 50)
            
            # Run RAG pipeline
            result = await pipeline.run_rag_pipeline_async(
                question=query_info["question"],
                session_id=query_info["session_id"],
                top_k=3
            )
            
            console.print(f"[green]Answer:[/green] {result['answer'][:200]}...")
            console.print(f"[blue]Context Length:[/blue] {len(result['context'])} characters")
            console.print(f"[yellow]History Length:[/yellow] {len(result['conversation_history'])} characters")
            
            # Add spacing between queries
            console.print("\n" + "=" * 60)
        
        # Show final statistics
        console.print("\n[bold green]Final Token Statistics[/bold green]")
        console.print("-" * 30)
        
        from rich_logging import get_token_statistics
        stats = get_token_statistics()
        
        console.print(f"Total Queries: {stats['total_queries']}")
        console.print(f"Total Tokens Processed: {stats['total_tokens_processed']:,}")
        console.print(f"Average Tokens per Query: {stats['average_tokens_per_query']:.1f}")
        
        if stats['session_breakdown']:
            console.print("\n[bold]Session Breakdown:[/bold]")
            for session_id, session_stats in stats['session_breakdown'].items():
                console.print(f"  {session_id}: {session_stats['queries']} queries, {session_stats['total_tokens']:,} tokens")
        
        console.print("\n[bold green]✅ Token tracking demo completed successfully![/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]Error during demo: {e}[/bold red]")
        console.print("[yellow]Note: Make sure you have the required dependencies and configuration set up.[/yellow]")


if __name__ == "__main__":
    asyncio.run(demo_token_tracking()) 