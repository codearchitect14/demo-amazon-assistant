#!/usr/bin/env python3
"""
Demonstration script for production logging system with Rich integration.

This script showcases the comprehensive logging capabilities including:
- Structured JSON logging for production monitoring
- Rich console output for development/debugging
- Performance metrics and monitoring
- Error tracking and alerting
- Token usage analytics
- System health monitoring
"""

import asyncio
import time
import random
from typing import Dict, Any

# Import production logging
from production_logging import (
    setup_production_logging, get_production_logger,
    log_pipeline_start, log_pipeline_end, log_retrieval, log_generation,
    log_token_usage, log_memory_operation, log_error, log_performance,
    log_health_check, pipeline_context, count_tokens
)

# Import RAG logging integration
from rag.logging_integration import (
    setup_rag_logging, get_rag_logging_integration,
    log_retrieval_operation, log_generation_operation,
    log_token_breakdown, log_memory_operation as log_memory_op,
    log_error_with_context, log_performance_metrics, log_health_status
)


def demo_basic_logging():
    """Demonstrate basic logging functionality."""
    print("\n" + "="*60)
    print("🚀 DEMO: Basic Production Logging")
    print("="*60)
    
    # Setup production logging
    logger = setup_production_logging(
        log_level="INFO",
        enable_rich=True,
        enable_file_logging=True,
        enable_json_logging=True,
        log_directory="logs"
    )
    
    # Simulate pipeline operations
    session_id = "demo_session_001"
    
    # Log pipeline start
    log_pipeline_start(session_id, {
        "question_length": 45,
        "memory_enabled": True,
        "retrieval_method": "hybrid",
        "model": "llama-3.3-70b-versatile"
    })
    
    # Simulate retrieval
    await asyncio.sleep(0.5)
    log_retrieval(session_id, {
        "query": "What are the best wireless headphones?",
        "documents_retrieved": 5,
        "context_length": 2500,
        "method": "hybrid_search"
    }, 450.5)
    
    # Simulate generation
    await asyncio.sleep(0.3)
    log_generation(session_id, {
        "input_tokens": 1200,
        "output_tokens": 200,
        "model": "llama-3.3-70b-versatile",
        "prompt_preview": "You are a helpful AI assistant...",
        "response_preview": "Based on the product information..."
    }, 1200.8)
    
    # Log token usage
    token_data = {
        "system_prompt": 150,
        "conversation_history": 300,
        "retrieved_context": 800,
        "user_question": 50
    }
    log_token_usage(session_id, token_data)
    
    # Log memory operation
    log_memory_operation(session_id, "add_interaction", {
        "interaction_size_bytes": 1024,
        "session_size_bytes": 5120,
        "total_interactions": 5,
        "context_saved_bytes": 5000
    })
    
    # Log pipeline end
    log_pipeline_end(session_id, {
        "total_tokens": 1300,
        "retrieval_performed": True,
        "response_length": 450,
        "response_preview": "The best wireless headphones are..."
    }, 2150.3)
    
    print("✅ Basic logging demo completed!")


def demo_error_logging():
    """Demonstrate error logging with Rich tracebacks."""
    print("\n" + "="*60)
    print("❌ DEMO: Error Logging with Rich Tracebacks")
    print("="*60)
    
    session_id = "error_demo_session"
    
    # Simulate different types of errors
    errors_to_demo = [
        (ValueError("Invalid input parameter"), "Input validation"),
        (ConnectionError("Failed to connect to database"), "Database connection"),
        (TimeoutError("Request timed out"), "API timeout"),
        (Exception("Unexpected error occurred"), "General error")
    ]
    
    for error, context in errors_to_demo:
        log_error(error, context, session_id)
        await asyncio.sleep(0.5)
    
    print("✅ Error logging demo completed!")


def demo_performance_monitoring():
    """Demonstrate performance monitoring."""
    print("\n" + "="*60)
    print("📊 DEMO: Performance Monitoring")
    print("="*60)
    
    session_id = "perf_demo_session"
    
    # Simulate performance metrics
    performance_metrics = {
        "response_time_ms": 1250.5,
        "memory_usage_mb": 512.3,
        "cpu_usage_percent": 45.2,
        "cache_hit_rate": 0.85,
        "throughput_requests_per_second": 2.3,
        "error_rate": 0.02,
        "average_tokens_per_request": 650
    }
    
    log_performance(session_id, performance_metrics)
    
    # Simulate health check
    health_data = {
        "status": "healthy",
        "database": {"status": "connected", "details": "PostgreSQL 14.5"},
        "vector_store": {"status": "healthy", "details": "Qdrant running"},
        "llm_service": {"status": "healthy", "details": "Groq API accessible"},
        "memory": {"status": "healthy", "details": "Redis connected"},
        "uptime_seconds": 3600,
        "last_error": None
    }
    
    log_health_check(health_data)
    
    print("✅ Performance monitoring demo completed!")


def demo_context_manager():
    """Demonstrate context manager usage."""
    print("\n" + "="*60)
    print("🔄 DEMO: Context Manager Usage")
    print("="*60)
    
    session_id = "context_demo_session"
    
    # Use context manager for pipeline operations
    with pipeline_context(session_id, {
        "question_length": 30,
        "memory_enabled": True,
        "retrieval_method": "semantic"
    }):
        # Simulate pipeline work
        await asyncio.sleep(1.0)
        
        # Simulate some operations
        log_retrieval(session_id, {
            "query": "Find laptop recommendations",
            "documents_retrieved": 3,
            "context_length": 1800
        }, 350.0)
        
        log_generation(session_id, {
            "input_tokens": 800,
            "output_tokens": 150,
            "model": "llama-3.1-8b-instant"
        }, 800.0)
    
    print("✅ Context manager demo completed!")


def demo_rag_integration():
    """Demonstrate RAG pipeline integration."""
    print("\n" + "="*60)
    print("🤖 DEMO: RAG Pipeline Integration")
    print("="*60)
    
    # Setup RAG logging
    setup_rag_logging(
        log_level="INFO",
        enable_rich=True,
        enable_file_logging=True,
        enable_json_logging=True,
        log_directory="logs"
    )
    
    integration = get_rag_logging_integration()
    
    # Simulate RAG pipeline operations
    session_id = "rag_demo_session"
    
    # Log pipeline start
    integration.log_rag_pipeline_start(
        session_id,
        "What are the best gaming laptops under $1000?",
        memory_enabled=True,
        retrieval_method="hybrid"
    )
    
    # Simulate retrieval
    await asyncio.sleep(0.5)
    integration.log_retrieval_operation(
        session_id,
        "gaming laptops under $1000",
        ["Laptop A: RTX 3060, $899", "Laptop B: RTX 3050, $799"],
        450.0,
        method="hybrid_search"
    )
    
    # Simulate generation
    await asyncio.sleep(0.3)
    integration.log_generation_operation(
        session_id,
        "Based on the product information, here are the best gaming laptops...",
        "The best gaming laptops under $1000 include models with RTX 3060 and RTX 3050 graphics cards...",
        1200.0,
        model="llama-3.3-70b-versatile"
    )
    
    # Log token breakdown
    token_data = {
        "system_prompt": 120,
        "conversation_history": 250,
        "retrieved_context": 600,
        "user_question": 40
    }
    integration.log_token_breakdown(session_id, token_data)
    
    # Log memory operation
    integration.log_memory_operation(session_id, "add_interaction", {
        "interaction_size_bytes": 2048,
        "session_size_bytes": 8192,
        "total_interactions": 8,
        "context_saved_bytes": 8000
    })
    
    # Log pipeline end
    integration.log_rag_pipeline_end(session_id, {
        "answer": "The best gaming laptops under $1000 include models with RTX 3060 and RTX 3050 graphics cards...",
        "total_tokens": 1010,
        "retrieval_performed": True,
        "context_used": True
    })
    
    print("✅ RAG integration demo completed!")


def demo_token_analysis():
    """Demonstrate detailed token analysis."""
    print("\n" + "="*60)
    print("🔢 DEMO: Token Usage Analysis")
    print("="*60)
    
    session_id = "token_demo_session"
    
    # Simulate different token usage scenarios
    scenarios = [
        {
            "name": "Short Query",
            "tokens": {
                "system_prompt": 120,
                "conversation_history": 100,
                "retrieved_context": 300,
                "user_question": 25
            }
        },
        {
            "name": "Long Conversation",
            "tokens": {
                "system_prompt": 120,
                "conversation_history": 800,
                "retrieved_context": 500,
                "user_question": 30
            }
        },
        {
            "name": "Heavy Context",
            "tokens": {
                "system_prompt": 120,
                "conversation_history": 200,
                "retrieved_context": 1200,
                "user_question": 40
            }
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📊 {scenario['name']}:")
        log_token_usage(session_id, scenario['tokens'])
        # Note: This is in a sync context, so time.sleep is appropriate
        time.sleep(0.5)
    
    print("✅ Token analysis demo completed!")


def demo_system_health():
    """Demonstrate system health monitoring."""
    print("\n" + "="*60)
    print("🏥 DEMO: System Health Monitoring")
    print("="*60)
    
    # Simulate different health states
    health_scenarios = [
        {
            "name": "Healthy System",
            "data": {
                "status": "healthy",
                "database": {"status": "connected", "details": "PostgreSQL 14.5"},
                "vector_store": {"status": "healthy", "details": "Qdrant running"},
                "llm_service": {"status": "healthy", "details": "Groq API accessible"},
                "memory": {"status": "healthy", "details": "Redis connected"},
                "uptime_seconds": 7200,
                "last_error": None
            }
        },
        {
            "name": "Degraded System",
            "data": {
                "status": "degraded",
                "database": {"status": "connected", "details": "PostgreSQL 14.5"},
                "vector_store": {"status": "slow", "details": "High latency"},
                "llm_service": {"status": "healthy", "details": "Groq API accessible"},
                "memory": {"status": "warning", "details": "High memory usage"},
                "uptime_seconds": 7200,
                "last_error": "Vector store slow response"
            }
        },
        {
            "name": "Unhealthy System",
            "data": {
                "status": "unhealthy",
                "database": {"status": "connected", "details": "PostgreSQL 14.5"},
                "vector_store": {"status": "error", "details": "Connection failed"},
                "llm_service": {"status": "error", "details": "API key invalid"},
                "memory": {"status": "error", "details": "Redis connection failed"},
                "uptime_seconds": 7200,
                "last_error": "Multiple service failures"
            }
        }
    ]
    
    for scenario in health_scenarios:
        print(f"\n🏥 {scenario['name']}:")
        log_health_check(scenario['data'])
        # Note: This is in a sync context, so time.sleep is appropriate
        time.sleep(0.5)
    
    print("✅ System health demo completed!")


async def demo_async_operations():
    """Demonstrate async logging operations."""
    print("\n" + "="*60)
    print("⚡ DEMO: Async Operations")
    print("="*60)
    
    session_id = "async_demo_session"
    
    async def simulate_async_retrieval():
        await asyncio.sleep(0.5)
        log_retrieval(session_id, {
            "query": "Async search query",
            "documents_retrieved": 3,
            "context_length": 1500
        }, 500.0)
    
    async def simulate_async_generation():
        await asyncio.sleep(0.3)
        log_generation(session_id, {
            "input_tokens": 900,
            "output_tokens": 180,
            "model": "llama-3.3-70b-versatile"
        }, 900.0)
    
    # Run async operations
    await asyncio.gather(
        simulate_async_retrieval(),
        simulate_async_generation()
    )
    
    print("✅ Async operations demo completed!")


def demo_statistics():
    """Demonstrate logging statistics."""
    print("\n" + "="*60)
    print("📈 DEMO: Logging Statistics")
    print("="*60)
    
    from production_logging import get_logging_statistics
    
    # Get logging statistics
    stats = get_logging_statistics()
    
    print("📊 Logging Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("✅ Statistics demo completed!")


def main():
    """Run all demos."""
    print("🎯 Production Logging System Demo")
    print("="*60)
    print("This demo showcases the comprehensive logging system with Rich integration.")
    print("Features demonstrated:")
    print("  ✅ Structured JSON logging for production monitoring")
    print("  ✅ Rich console output for development/debugging")
    print("  ✅ Performance metrics and monitoring")
    print("  ✅ Error tracking and alerting")
    print("  ✅ Token usage analytics")
    print("  ✅ System health monitoring")
    print("  ✅ RAG pipeline integration")
    print("  ✅ Async operation support")
    print("="*60)
    
    try:
        # Run all demos
        demo_basic_logging()
        demo_error_logging()
        demo_performance_monitoring()
        demo_context_manager()
        demo_rag_integration()
        demo_token_analysis()
        demo_system_health()
        
        # Run async demo
        asyncio.run(demo_async_operations())
        
        demo_statistics()
        
        print("\n" + "="*60)
        print("🎉 All demos completed successfully!")
        print("📁 Check the 'logs' directory for generated log files:")
        print("  - rag_pipeline.json (structured JSON logs)")
        print("  - rag_pipeline.log (human-readable logs)")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 