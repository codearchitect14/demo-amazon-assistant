"""
Rich-based logging system for RAG pipeline with detailed token tracking.
"""

import logging
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live
from rich.layout import Layout
from rich.columns import Columns
from rich import box
import tiktoken

# Initialize rich console
console = Console()

# Initialize tokenizer for token counting
try:
    tokenizer = tiktoken.get_encoding("cl100k_base")  # GPT-4 tokenizer
except ImportError:
    # Fallback if tiktoken not available
    tokenizer = None
    console.print("[yellow]Warning: tiktoken not available, using character-based token estimation[/yellow]")


class TokenTracker:
    """
    Comprehensive token tracking for RAG pipeline components.
    """
    
    def __init__(self):
        self.session_tokens = {}
        self.total_tokens_processed = 0
        self.total_queries = 0
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        if not text:
            return 0
        
        if tokenizer:
            return len(tokenizer.encode(text))
        else:
            # Rough estimation: 1 token ≈ 4 characters
            return len(text) // 4
    
    def track_query_tokens(self, session_id: str, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """Track tokens for a complete query and return detailed breakdown."""
        
        # Count tokens for each component
        token_counts = {
            "user_prompt": self.count_tokens(query_data.get("user_prompt", "")),
            "system_prompt": self.count_tokens(query_data.get("system_prompt", "")),
            "conversation_history": self.count_tokens(query_data.get("conversation_history", "")),
            "retrieved_context": self.count_tokens(query_data.get("retrieved_context", "")),
            "total_input": 0,
            "llm_response": self.count_tokens(query_data.get("llm_response", ""))
        }
        
        # Calculate total input tokens
        token_counts["total_input"] = (
            token_counts["user_prompt"] + 
            token_counts["system_prompt"] + 
            token_counts["conversation_history"] + 
            token_counts["retrieved_context"]
        )
        
        # Store session data
        if session_id not in self.session_tokens:
            self.session_tokens[session_id] = []
        
        self.session_tokens[session_id].append({
            "timestamp": datetime.now().isoformat(),
            "token_counts": token_counts,
            "query_data": query_data
        })
        
        self.total_tokens_processed += token_counts["total_input"]
        self.total_queries += 1
        
        return token_counts


class RichLogger:
    """
    Rich-based logger for RAG pipeline with detailed token tracking.
    """
    
    def __init__(self, enable_rich: bool = True, log_to_file: bool = False, log_file: str = "rag_pipeline.log"):
        self.enable_rich = enable_rich
        self.log_to_file = log_to_file
        self.log_file = log_file
        self.console = Console()
        self.token_tracker = TokenTracker()
        
        # Setup file logging if enabled
        if log_to_file:
            self.file_handler = logging.FileHandler(log_file)
            self.file_handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            self.file_handler.setFormatter(formatter)
        
        # Token tracking
        self.token_stats = {
            "conversation_history": 0,
            "retrieved_context": 0,
            "system_prompt": 0,
            "user_prompt": 0,
            "total_input": 0,
            "output": 0,
            "savings_from_optimization": 0
        }
        
        self.pipeline_stats = {
            "session_id": None,
            "retrieval_performed": False,
            "conversation_only_mode": False,
            "processing_time_ms": 0,
            "context_length": 0,
            "history_length": 0
        }
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return self.token_tracker.count_tokens(text)
    
    def log_comprehensive_token_breakdown(self, session_id: str, query_data: Dict[str, Any]):
        """Log comprehensive token breakdown in tabular format."""
        if not self.enable_rich:
            return
        
        # Track tokens
        token_counts = self.token_tracker.track_query_tokens(session_id, query_data)
        
        # Create main table
        main_table = Table(title="🔍 Comprehensive Token Analysis", box=box.ROUNDED)
        main_table.add_column("Component", style="cyan", no_wrap=True)
        main_table.add_column("Content Length", style="green", justify="right")
        main_table.add_column("Tokens", style="yellow", justify="right")
        main_table.add_column("Percentage", style="magenta", justify="right")
        main_table.add_column("Content Preview", style="white")
        
        # Add rows for each component
        components = [
            ("User Prompt", "user_prompt", query_data.get("user_prompt", "")),
            ("System Prompt", "system_prompt", query_data.get("system_prompt", "")),
            ("Conversation History", "conversation_history", query_data.get("conversation_history", "")),
            ("Retrieved Context", "retrieved_context", query_data.get("retrieved_context", "")),
        ]
        
        total_input_tokens = token_counts["total_input"]
        
        for component_name, token_key, content in components:
            tokens = token_counts[token_key]
            if tokens > 0:
                percentage = (tokens / total_input_tokens * 100) if total_input_tokens > 0 else 0
                preview = content[:100] + "..." if len(content) > 100 else content
                
                main_table.add_row(
                    component_name,
                    f"{len(content):,}",
                    f"{tokens:,}",
                    f"{percentage:.1f}%",
                    preview
                )
        
        # Add total row
        main_table.add_row("", "", "", "", "")
        main_table.add_row(
            "[bold]TOTAL INPUT[/bold]",
            f"[bold]{sum(len(query_data.get(k, '')) for k in ['user_prompt', 'system_prompt', 'conversation_history', 'retrieved_context']):,}[/bold]",
            f"[bold]{total_input_tokens:,}[/bold]",
            "[bold]100%[/bold]",
            ""
        )
        
        # Add LLM response row
        if token_counts["llm_response"] > 0:
            main_table.add_row(
                "[bold green]LLM Response[/bold green]",
                f"[bold green]{len(query_data.get('llm_response', '')):,}[/bold green]",
                f"[bold green]{token_counts['llm_response']:,}[/bold green]",
                "",
                query_data.get("llm_response", "")[:100] + "..." if len(query_data.get("llm_response", "")) > 100 else query_data.get("llm_response", "")
            )
        
        # Create summary panel
        summary_panel = Panel(
            f"[bold blue]Session:[/bold blue] {session_id}\n"
            f"[bold green]Total Input Tokens:[/bold green] {total_input_tokens:,}\n"
            f"[bold yellow]LLM Response Tokens:[/bold yellow] {token_counts['llm_response']:,}\n"
            f"[bold magenta]Total Tokens:[/bold magenta] {total_input_tokens + token_counts['llm_response']:,}\n"
            f"[bold cyan]Timestamp:[/bold cyan] {datetime.now().strftime('%H:%M:%S')}",
            title="📊 Token Summary",
            border_style="blue"
        )
        
        # Display tables
        self.console.print(summary_panel)
        self.console.print(main_table)
        
        # Log to file if enabled
        if self.log_to_file:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id,
                "token_breakdown": token_counts,
                "query_data": {
                    "user_prompt_length": len(query_data.get("user_prompt", "")),
                    "system_prompt_length": len(query_data.get("system_prompt", "")),
                    "conversation_history_length": len(query_data.get("conversation_history", "")),
                    "retrieved_context_length": len(query_data.get("retrieved_context", "")),
                    "llm_response_length": len(query_data.get("llm_response", ""))
                }
            }
            with open(self.log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
    
    def log_token_breakdown(self, title: str, data: Dict[str, Any]):
        """Log detailed token breakdown."""
        if not self.enable_rich:
            return
        
        table = Table(title=f"🔍 {title}", box=box.ROUNDED)
        table.add_column("Component", style="cyan", no_wrap=True)
        table.add_column("Length", style="green")
        table.add_column("Tokens", style="yellow")
        table.add_column("Percentage", style="magenta")
        
        total_tokens = sum(data.values())
        
        for component, tokens in data.items():
            if tokens > 0:
                percentage = (tokens / total_tokens * 100) if total_tokens > 0 else 0
                table.add_row(
                    component.replace("_", " ").title(),
                    f"{len(component)} chars",
                    f"{tokens:,}",
                    f"{percentage:.1f}%"
                )
        
        table.add_row("", "", "", "")
        table.add_row("**TOTAL**", "", f"**{total_tokens:,}**", "**100%**")
        
        self.console.print(table)
    
    def log_prompt_analysis(self, session_id: str, prompt_data: Dict[str, Any]):
        """Log detailed analysis of what's being sent to LLM."""
        if not self.enable_rich:
            return
        
        # Create layout
        layout = Layout()
        layout.split_column(
            Layout(name="header"),
            Layout(name="body"),
            Layout(name="footer")
        )
        
        # Header with session info
        header = Panel(
            f"[bold blue]Session:[/bold blue] {session_id}\n"
            f"[bold green]Mode:[/bold green] {'Conversation Only' if prompt_data.get('conversation_only') else 'RAG with Context'}\n"
            f"[bold yellow]Timestamp:[/bold yellow] {datetime.now().strftime('%H:%M:%S')}",
            title="🤖 LLM Prompt Analysis",
            border_style="blue"
        )
        
        # Body with token breakdown
        token_data = {
            "System Prompt": prompt_data.get("system_tokens", 0),
            "Conversation History": prompt_data.get("history_tokens", 0),
            "Retrieved Context": prompt_data.get("context_tokens", 0),
            "User Question": prompt_data.get("question_tokens", 0)
        }
        
        body_table = Table(box=box.SIMPLE)
        body_table.add_column("Component", style="cyan")
        body_table.add_column("Tokens", style="yellow", justify="right")
        body_table.add_column("Content Preview", style="white")
        
        total_tokens = sum(token_data.values())
        
        for component, tokens in token_data.items():
            if tokens > 0:
                # Get content preview
                content_key = component.lower().replace(" ", "_")
                content = prompt_data.get(f"{content_key}_content", "")
                preview = content[:100] + "..." if len(content) > 100 else content
                
                body_table.add_row(
                    component,
                    f"{tokens:,}",
                    preview
                )
        
        body_table.add_row("", "", "")
        body_table.add_row("**TOTAL**", f"**{total_tokens:,}**", "")
        
        body = Panel(body_table, title="📊 Token Breakdown", border_style="green")
        
        # Footer with optimization info
        savings = prompt_data.get("savings_from_optimization", 0)
        footer_text = f"[bold green]Optimization Savings:[/bold green] {savings:,} tokens saved by not storing context in history"
        footer = Panel(footer_text, border_style="green")
        
        layout["header"].update(header)
        layout["body"].update(body)
        layout["footer"].update(footer)
        
        self.console.print(layout)
    
    def log_memory_operation(self, operation: str, session_id: str, data: Dict[str, Any]):
        """Log memory operations with token tracking."""
        if not self.enable_rich:
            return
        
        # Calculate token savings
        context_length = data.get("context_length", 0)
        context_tokens = self.count_tokens("x" * context_length)  # Estimate
        interaction_size = data.get("interaction_size_bytes", 0)
        
        panel = Panel(
            f"[bold blue]Operation:[/bold blue] {operation}\n"
            f"[bold green]Session:[/bold green] {session_id}\n"
            f"[bold yellow]Context Saved:[/bold yellow] {context_length:,} chars ({context_tokens:,} tokens)\n"
            f"[bold magenta]Interaction Size:[/bold magenta] {interaction_size:,} bytes\n"
            f"[bold cyan]Optimization:[/bold cyan] Context excluded from memory",
            title="💾 Memory Operation",
            border_style="cyan"
        )
        
        self.console.print(panel)
    
    def log_pipeline_step(self, step: str, session_id: str, data: Dict[str, Any]):
        """Log pipeline steps with progress tracking."""
        if not self.enable_rich:
            return
        
        # Create progress display
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task(f"[cyan]{step}[/cyan]", total=None)
            
            # Simulate progress
            for i in range(3):
                progress.update(task, description=f"[cyan]{step}[/cyan] - Step {i+1}/3")
                # Note: This is in a sync context, so time.sleep is appropriate
                time.sleep(0.1)
            
            progress.update(task, description=f"[green]{step}[/green] - Complete")
        
        # Show step details
        details = []
        for key, value in data.items():
            if isinstance(value, (int, float)):
                if key.endswith("_tokens"):
                    details.append(f"[yellow]{key.replace('_', ' ').title()}:[/yellow] {value:,}")
                elif key.endswith("_ms"):
                    details.append(f"[green]{key.replace('_', ' ').title()}:[/green] {value:.1f}ms")
                else:
                    details.append(f"[cyan]{key.replace('_', ' ').title()}:[/cyan] {value}")
            else:
                details.append(f"[cyan]{key.replace('_', ' ').title()}:[/cyan] {value}")
        
        if details:
            panel = Panel(
                "\n".join(details),
                title=f"📋 {step} Details",
                border_style="blue"
            )
            self.console.print(panel)
    
    def log_agent_decision(self, session_id: str, decision: str, analysis: Dict[str, Any]):
        """Log agent decisions with reasoning."""
        if not self.enable_rich:
            return
        
        # Color based on decision
        decision_color = {
            "retrieve": "green",
            "conversation": "yellow",
            "hybrid": "blue"
        }.get(decision, "white")
        
        panel = Panel(
            f"[bold {decision_color}]Decision:[/bold {decision_color}] {decision.upper()}\n"
            f"[bold cyan]Confidence:[/bold cyan] {analysis.get('confidence', 'unknown')}\n"
            f"[bold yellow]Rationale:[/bold yellow] {analysis.get('rationale', 'No reasoning provided')}\n"
            f"[bold magenta]Session:[/bold magenta] {session_id}",
            title="🤖 Agent Decision",
            border_style=decision_color
        )
        
        self.console.print(panel)
    
    def log_final_summary(self, session_id: str, summary_data: Dict[str, Any]):
        """Log final pipeline summary."""
        if not self.enable_rich:
            return
        
        # Create summary table
        table = Table(title="📊 Pipeline Summary", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="yellow")
        table.add_column("Details", style="white")
        
        # Add summary data
        for key, value in summary_data.items():
            if isinstance(value, (int, float)):
                if key.endswith("_tokens"):
                    table.add_row(key.replace("_", " ").title(), f"{value:,}", "tokens")
                elif key.endswith("_ms"):
                    table.add_row(key.replace("_", " ").title(), f"{value:.1f}", "milliseconds")
                else:
                    table.add_row(key.replace("_", " ").title(), str(value), "")
            else:
                table.add_row(key.replace("_", " ").title(), str(value), "")
        
        # Add optimization impact
        savings = summary_data.get("savings_from_optimization", 0)
        if savings > 0:
            table.add_row("", "", "")
            table.add_row("**Optimization Impact**", f"**{savings:,} tokens saved**", "context excluded from history")
        
        self.console.print(table)
    
    def log_error(self, error: Exception, context: str = ""):
        """Log errors with rich formatting."""
        if not self.enable_rich:
            return
        
        error_panel = Panel(
            f"[bold red]Error:[/bold red] {str(error)}\n"
            f"[bold yellow]Context:[/bold yellow] {context}\n"
            f"[bold cyan]Type:[/bold cyan] {type(error).__name__}",
            title="❌ Error",
            border_style="red"
        )
        
        self.console.print(error_panel)
    
    def log_what_sent_to_llm(self, session_id: str, prompt_components: Dict[str, Any]):
        """Log exactly what was sent to the LLM."""
        if not self.enable_rich:
            return
        
        # Create detailed breakdown
        layout = Layout()
        layout.split_column(
            Layout(name="overview"),
            Layout(name="details")
        )
        
        # Overview
        total_tokens = sum(prompt_components.get("tokens", {}).values())
        overview = Panel(
            f"[bold blue]Session:[/bold blue] {session_id}\n"
            f"[bold green]Total Tokens:[/bold green] {total_tokens:,}\n"
            f"[bold yellow]Components:[/bold yellow] {len(prompt_components.get('content', {}))}",
            title="📤 Sent to LLM",
            border_style="blue"
        )
        
        # Details
        details_table = Table(box=box.SIMPLE)
        details_table.add_column("Component", style="cyan")
        details_table.add_column("Tokens", style="yellow")
        details_table.add_column("Content", style="white")
        
        for component, content in prompt_components.get("content", {}).items():
            tokens = prompt_components.get("tokens", {}).get(component, 0)
            # Truncate content for display
            display_content = content[:200] + "..." if len(content) > 200 else content
            details_table.add_row(component, f"{tokens:,}", display_content)
        
        details = Panel(details_table, title="📋 Prompt Components", border_style="green")
        
        layout["overview"].update(overview)
        layout["details"].update(details)
        
        self.console.print(layout)
    
    def log_context_optimization_impact(self, before: Dict[str, Any], after: Dict[str, Any]):
        """Log the impact of context optimization."""
        if not self.enable_rich:
            return
        
        # Calculate savings
        before_tokens = before.get("total_tokens", 0)
        after_tokens = after.get("total_tokens", 0)
        savings = before_tokens - after_tokens
        savings_percentage = (savings / before_tokens * 100) if before_tokens > 0 else 0
        
        impact_panel = Panel(
            f"[bold red]Before Optimization:[/bold red] {before_tokens:,} tokens\n"
            f"[bold green]After Optimization:[/bold green] {after_tokens:,} tokens\n"
            f"[bold yellow]Savings:[/bold yellow] {savings:,} tokens ({savings_percentage:.1f}%)\n"
            f"[bold cyan]Impact:[/bold cyan] Context excluded from conversation history",
            title="🚀 Context Optimization Impact",
            border_style="yellow"
        )
        
        self.console.print(impact_panel)
    
    def get_token_statistics(self) -> Dict[str, Any]:
        """Get comprehensive token statistics."""
        return {
            "total_queries": self.token_tracker.total_queries,
            "total_tokens_processed": self.token_tracker.total_tokens_processed,
            "average_tokens_per_query": self.token_tracker.total_tokens_processed / max(self.token_tracker.total_queries, 1),
            "session_breakdown": {
                session_id: {
                    "queries": len(sessions),
                    "total_tokens": sum(session["token_counts"]["total_input"] for session in sessions)
                }
                for session_id, sessions in self.token_tracker.session_tokens.items()
            }
        }


# Global logger instance
rich_logger = RichLogger(enable_rich=True, log_to_file=True)


def log_pipeline_step(step: str, session_id: str, data: Dict[str, Any]):
    """Log a pipeline step."""
    rich_logger.log_pipeline_step(step, session_id, data)


def log_token_breakdown(title: str, data: Dict[str, Any]):
    """Log token breakdown."""
    rich_logger.log_token_breakdown(title, data)


def log_prompt_analysis(session_id: str, prompt_data: Dict[str, Any]):
    """Log prompt analysis."""
    rich_logger.log_prompt_analysis(session_id, prompt_data)


def log_memory_operation(operation: str, session_id: str, data: Dict[str, Any]):
    """Log memory operation."""
    rich_logger.log_memory_operation(operation, session_id, data)


def log_agent_decision(session_id: str, decision: str, analysis: Dict[str, Any]):
    """Log agent decision."""
    rich_logger.log_agent_decision(session_id, decision, analysis)


def log_final_summary(session_id: str, summary_data: Dict[str, Any]):
    """Log final summary."""
    rich_logger.log_final_summary(session_id, summary_data)


def log_error(error: Exception, context: str = ""):
    """Log error."""
    rich_logger.log_error(error, context)


def log_what_sent_to_llm(session_id: str, prompt_components: Dict[str, Any]):
    """Log what was sent to LLM."""
    rich_logger.log_what_sent_to_llm(session_id, prompt_components)


def log_context_optimization_impact(before: Dict[str, Any], after: Dict[str, Any]):
    """Log context optimization impact."""
    rich_logger.log_context_optimization_impact(before, after)


def log_comprehensive_token_breakdown(session_id: str, query_data: Dict[str, Any]):
    """Log comprehensive token breakdown in tabular format."""
    rich_logger.log_comprehensive_token_breakdown(session_id, query_data)


def count_tokens(text: str) -> int:
    """Count tokens in text."""
    return rich_logger.count_tokens(text)


def get_token_statistics() -> Dict[str, Any]:
    """Get comprehensive token statistics."""
    return rich_logger.get_token_statistics()


# Example usage
if __name__ == "__main__":
    # Test the logging system
    console.print("[bold blue]Testing Rich Logging System[/bold blue]")
    
    # Test token counting
    test_text = "This is a test message for token counting."
    tokens = count_tokens(test_text)
    console.print(f"Text: '{test_text}'")
    console.print(f"Tokens: {tokens}")
    
    # Test comprehensive token breakdown
    test_query_data = {
        "user_prompt": "What are the best features of this product?",
        "system_prompt": "You are a helpful assistant that provides accurate information about products.",
        "conversation_history": "User: Tell me about this product. Assistant: This product has many features including...",
        "retrieved_context": "Product features include: 1. High performance 2. Easy to use 3. Affordable price...",
        "llm_response": "Based on the information provided, this product offers excellent features including high performance, ease of use, and affordability."
    }
    
    log_comprehensive_token_breakdown("test_session_123", test_query_data)
    
    # Test token breakdown
    token_data = {
        "system_prompt": 150,
        "conversation_history": 300,
        "retrieved_context": 500,
        "user_question": 50
    }
    log_token_breakdown("Test Token Breakdown", token_data)
    
    # Test prompt analysis
    prompt_data = {
        "conversation_only": False,
        "system_tokens": 150,
        "history_tokens": 300,
        "context_tokens": 500,
        "question_tokens": 50,
        "savings_from_optimization": 200
    }
    log_prompt_analysis("test_session_123", prompt_data)
    
    console.print("[bold green]Rich logging system ready![/bold green]") 