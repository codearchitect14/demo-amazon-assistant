#!/usr/bin/env python3
"""
Context Optimization Monitoring Script

This script helps monitor the context optimization implementation by tracking:
- Memory usage before and after optimization
- Token savings from context removal
- Performance metrics
- Agent decision patterns
"""

import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from collections import defaultdict

from logging_config import setup_logging, log_memory_stats, log_pipeline_performance


class ContextOptimizationMonitor:
    """
    Monitor for tracking context optimization performance.
    """
    
    def __init__(self):
        self.stats = {
            "total_interactions": 0,
            "total_context_saved_bytes": 0,
            "total_memory_saved_bytes": 0,
            "agent_decisions": {
                "retrieve": 0,
                "conversation": 0,
                "hybrid": 0
            },
            "performance_metrics": {
                "avg_pipeline_time_ms": 0,
                "avg_memory_operation_time_ms": 0,
                "total_pipeline_time_ms": 0
            },
            "memory_usage": {
                "before_optimization": 0,
                "after_optimization": 0,
                "savings_percentage": 0
            }
        }
        self.session_stats = defaultdict(dict)
        
        # Setup logging
        setup_logging(level="INFO", format_type="human", enable_console=True)
        self.logger = logging.getLogger(__name__)
        
    def log_interaction(self, session_id: str, interaction_data: Dict[str, Any]) -> None:
        """
        Log an interaction and track optimization metrics.
        
        Args:
            session_id: Session identifier
            interaction_data: Interaction data with optimization metrics
        """
        # Extract metrics
        context_saved = interaction_data.get("context_saved_bytes", 0)
        interaction_size = interaction_data.get("interaction_size_bytes", 0)
        processing_time = interaction_data.get("processing_time_ms", 0)
        
        # Update global stats
        self.stats["total_interactions"] += 1
        self.stats["total_context_saved_bytes"] += context_saved
        self.stats["total_memory_saved_bytes"] += context_saved
        
        # Update session stats
        if session_id not in self.session_stats:
            self.session_stats[session_id] = {
                "interactions": 0,
                "context_saved_bytes": 0,
                "total_processing_time_ms": 0,
                "first_interaction": datetime.now().isoformat()
            }
        
        self.session_stats[session_id]["interactions"] += 1
        self.session_stats[session_id]["context_saved_bytes"] += context_saved
        self.session_stats[session_id]["total_processing_time_ms"] += processing_time
        self.session_stats[session_id]["last_interaction"] = datetime.now().isoformat()
        
        # Log the interaction
        self.logger.info("Interaction logged", extra={
            "component": "monitor",
            "operation": "log_interaction",
            "session_id": session_id,
            "context_saved_bytes": context_saved,
            "interaction_size_bytes": interaction_size,
            "processing_time_ms": processing_time,
            "total_interactions": self.stats["total_interactions"],
            "total_context_saved_bytes": self.stats["total_context_saved_bytes"]
        })
        
    def log_agent_decision(self, session_id: str, decision: str, analysis: Dict[str, Any]) -> None:
        """
        Log agent decision and track decision patterns.
        
        Args:
            session_id: Session identifier
            decision: Agent decision (retrieve/conversation/hybrid)
            analysis: Decision analysis data
        """
        # Update agent decision stats
        if decision in self.stats["agent_decisions"]:
            self.stats["agent_decisions"][decision] += 1
        
        # Log the decision
        self.logger.info("Agent decision logged", extra={
            "component": "monitor",
            "operation": "log_agent_decision",
            "session_id": session_id,
            "decision": decision,
            "confidence": analysis.get("confidence", "unknown"),
            "rationale": analysis.get("rationale", "unknown"),
            "total_retrieve_decisions": self.stats["agent_decisions"]["retrieve"],
            "total_conversation_decisions": self.stats["agent_decisions"]["conversation"],
            "total_hybrid_decisions": self.stats["agent_decisions"]["hybrid"]
        })
        
    def log_pipeline_performance(self, session_id: str, performance_data: Dict[str, Any]) -> None:
        """
        Log pipeline performance metrics.
        
        Args:
            session_id: Session identifier
            performance_data: Performance metrics
        """
        total_time = performance_data.get("total_time_ms", 0)
        retrieval_performed = performance_data.get("retrieval_performed", False)
        conversation_only = performance_data.get("conversation_only_mode", False)
        
        # Update performance stats
        self.stats["performance_metrics"]["total_pipeline_time_ms"] += total_time
        
        # Calculate running average
        total_pipelines = self.stats["total_interactions"]
        if total_pipelines > 0:
            self.stats["performance_metrics"]["avg_pipeline_time_ms"] = (
                self.stats["performance_metrics"]["total_pipeline_time_ms"] / total_pipelines
            )
        
        # Log performance
        self.logger.info("Pipeline performance logged", extra={
            "component": "monitor",
            "operation": "log_pipeline_performance",
            "session_id": session_id,
            "total_time_ms": total_time,
            "retrieval_performed": retrieval_performed,
            "conversation_only_mode": conversation_only,
            "avg_pipeline_time_ms": self.stats["performance_metrics"]["avg_pipeline_time_ms"],
            "total_pipelines": total_pipelines
        })
        
    def log_memory_usage(self, memory_stats: Dict[str, Any]) -> None:
        """
        Log memory usage statistics.
        
        Args:
            memory_stats: Memory statistics from memory backend
        """
        total_memory_bytes = memory_stats.get("total_memory_bytes", 0)
        total_interactions = memory_stats.get("total_interactions", 0)
        memory_type = memory_stats.get("memory_type", "unknown")
        
        # Update memory usage stats
        self.stats["memory_usage"]["after_optimization"] = total_memory_bytes
        
        # Calculate savings (assuming before optimization would be 5x larger due to context)
        estimated_before = total_memory_bytes * 5  # Rough estimate
        self.stats["memory_usage"]["before_optimization"] = estimated_before
        self.stats["memory_usage"]["savings_percentage"] = (
            (estimated_before - total_memory_bytes) / estimated_before * 100
            if estimated_before > 0 else 0
        )
        
        # Log memory usage
        self.logger.info("Memory usage logged", extra={
            "component": "monitor",
            "operation": "log_memory_usage",
            "memory_type": memory_type,
            "total_memory_bytes": total_memory_bytes,
            "total_interactions": total_interactions,
            "estimated_before_optimization": estimated_before,
            "savings_percentage": self.stats["memory_usage"]["savings_percentage"],
            "optimization": "context_removed"
        })
        
    def generate_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive optimization report.
        
        Returns:
            Dictionary containing optimization metrics and insights
        """
        total_interactions = self.stats["total_interactions"]
        total_context_saved = self.stats["total_context_saved_bytes"]
        total_memory_saved = self.stats["total_memory_saved_bytes"]
        
        # Calculate averages
        avg_context_saved = total_context_saved / total_interactions if total_interactions > 0 else 0
        avg_memory_saved = total_memory_saved / total_interactions if total_interactions > 0 else 0
        
        # Agent decision percentages
        total_decisions = sum(self.stats["agent_decisions"].values())
        decision_percentages = {}
        for decision, count in self.stats["agent_decisions"].items():
            decision_percentages[decision] = (count / total_decisions * 100) if total_decisions > 0 else 0
        
        # Session analysis
        active_sessions = len(self.session_stats)
        avg_session_interactions = total_interactions / active_sessions if active_sessions > 0 else 0
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "optimization_metrics": {
                "total_interactions": total_interactions,
                "total_context_saved_bytes": total_context_saved,
                "total_memory_saved_bytes": total_memory_saved,
                "avg_context_saved_per_interaction": avg_context_saved,
                "avg_memory_saved_per_interaction": avg_memory_saved,
                "savings_percentage": self.stats["memory_usage"]["savings_percentage"]
            },
            "agent_decision_analysis": {
                "total_decisions": total_decisions,
                "decision_counts": self.stats["agent_decisions"],
                "decision_percentages": decision_percentages
            },
            "performance_metrics": {
                "avg_pipeline_time_ms": self.stats["performance_metrics"]["avg_pipeline_time_ms"],
                "total_pipeline_time_ms": self.stats["performance_metrics"]["total_pipeline_time_ms"]
            },
            "session_analysis": {
                "active_sessions": active_sessions,
                "avg_interactions_per_session": avg_session_interactions,
                "session_stats": dict(self.session_stats)
            },
            "memory_usage": self.stats["memory_usage"]
        }
        
        # Log the report
        self.logger.info("Optimization report generated", extra={
            "component": "monitor",
            "operation": "generate_report",
            "total_interactions": total_interactions,
            "total_context_saved_bytes": total_context_saved,
            "savings_percentage": self.stats["memory_usage"]["savings_percentage"],
            "active_sessions": active_sessions
        })
        
        return report
        
    def print_summary(self) -> None:
        """
        Print a human-readable summary of optimization metrics.
        """
        report = self.generate_report()
        
        print("\n" + "="*60)
        print("CONTEXT OPTIMIZATION MONITORING SUMMARY")
        print("="*60)
        
        # Optimization metrics
        metrics = report["optimization_metrics"]
        print(f"\n📊 OPTIMIZATION METRICS:")
        print(f"   Total Interactions: {metrics['total_interactions']}")
        print(f"   Total Context Saved: {metrics['total_context_saved_bytes']:,} bytes")
        print(f"   Total Memory Saved: {metrics['total_memory_saved_bytes']:,} bytes")
        print(f"   Avg Context Saved/Interaction: {metrics['avg_context_saved_per_interaction']:,.0f} bytes")
        print(f"   Estimated Memory Savings: {metrics['savings_percentage']:.1f}%")
        
        # Agent decisions
        decisions = report["agent_decision_analysis"]
        print(f"\n🤖 AGENT DECISION ANALYSIS:")
        for decision, percentage in decisions["decision_percentages"].items():
            count = decisions["decision_counts"][decision]
            print(f"   {decision.title()}: {count} ({percentage:.1f}%)")
        
        # Performance
        perf = report["performance_metrics"]
        print(f"\n⚡ PERFORMANCE METRICS:")
        print(f"   Average Pipeline Time: {perf['avg_pipeline_time_ms']:.1f}ms")
        print(f"   Total Pipeline Time: {perf['total_pipeline_time_ms']:.0f}ms")
        
        # Sessions
        sessions = report["session_analysis"]
        print(f"\n👥 SESSION ANALYSIS:")
        print(f"   Active Sessions: {sessions['active_sessions']}")
        print(f"   Avg Interactions/Session: {sessions['avg_interactions_per_session']:.1f}")
        
        print("\n" + "="*60)
        
    def save_report(self, filename: str = None) -> None:
        """
        Save the optimization report to a JSON file.
        
        Args:
            filename: Optional filename, defaults to timestamp-based name
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"context_optimization_report_{timestamp}.json"
        
        report = self.generate_report()
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info("Report saved to file", extra={
            "component": "monitor",
            "operation": "save_report",
            "filename": filename
        })
        
        print(f"\n📄 Report saved to: {filename}")


# Example usage and testing
if __name__ == "__main__":
    # Initialize monitor
    monitor = ContextOptimizationMonitor()
    
    # Simulate some interactions
    test_sessions = ["session_1", "session_2", "session_3"]
    
    for i, session_id in enumerate(test_sessions):
        # Simulate interaction
        interaction_data = {
            "context_saved_bytes": 5000 + (i * 1000),
            "interaction_size_bytes": 1000 + (i * 100),
            "processing_time_ms": 50 + (i * 10)
        }
        monitor.log_interaction(session_id, interaction_data)
        
        # Simulate agent decision
        decisions = ["retrieve", "conversation", "hybrid"]
        decision = decisions[i % len(decisions)]
        analysis = {
            "confidence": "high",
            "rationale": f"Test decision for {session_id}"
        }
        monitor.log_agent_decision(session_id, decision, analysis)
        
        # Simulate pipeline performance
        performance_data = {
            "total_time_ms": 1200 + (i * 100),
            "retrieval_performed": decision == "retrieve",
            "conversation_only_mode": decision == "conversation"
        }
        monitor.log_pipeline_performance(session_id, performance_data)
    
    # Simulate memory usage
    memory_stats = {
        "total_memory_bytes": 15000,
        "total_interactions": 3,
        "memory_type": "in_memory"
    }
    monitor.log_memory_usage(memory_stats)
    
    # Generate and display report
    monitor.print_summary()
    monitor.save_report() 