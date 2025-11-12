#!/usr/bin/env python3
"""
Redis Memory Manager for RAG Pipeline
Provides monitoring, cleanup, and management tools for Redis-based conversation memory.
"""

import os
import sys
import time
import json
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import Config
from rag.rag_pipeline import RedisConversationMemory

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class RedisMemoryManager:
    """
    Redis memory management and monitoring tools
    """

    def __init__(self, redis_url: str = Config.REDIS_URL):
        self.redis_url = redis_url
        self.redis_memory = RedisConversationMemory(redis_url)

    def get_memory_overview(self) -> Dict[str, Any]:
        """Get comprehensive memory overview"""
        try:
            stats = self.redis_memory.get_memory_stats()
            health = self.redis_memory.get_redis_health()

            return {
                "timestamp": datetime.now().isoformat(),
                "redis_health": health,
                "memory_stats": stats,
                "config": {
                    "redis_url": self.redis_url,
                    "ttl_hours": Config.REDIS_TTL_HOURS,
                    "max_entries": Config.REDIS_MAX_ENTRIES,
                    "memory_enabled": Config.MEMORY_ENABLED,
                },
            }
        except Exception as e:
            logger.error(f"Error getting memory overview: {e}")
            return {"error": str(e)}

    def list_active_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List active sessions with their interaction counts"""
        try:
            if not self.redis_memory.redis_available:
                return []

            sessions = []
            session_pattern = self.redis_memory._get_session_key("*")
            session_keys = self.redis_memory.redis.keys(session_pattern)

            for session_key in session_keys[:limit]:
                session_id = session_key.replace("conversation:", "")
                interaction_count = self.redis_memory.redis.llen(session_key)

                # Get last interaction time
                if interaction_count > 0:
                    last_interaction_id = self.redis_memory.redis.lindex(session_key, 0)
                    last_interaction_key = self.redis_memory._get_interaction_key(
                        session_id, last_interaction_id
                    )
                    last_interaction_data = self.redis_memory.redis.get(
                        last_interaction_key
                    )

                    if last_interaction_data:
                        last_interaction = json.loads(last_interaction_data)
                        last_activity = datetime.fromtimestamp(
                            last_interaction["timestamp"]
                        )
                    else:
                        last_activity = None
                else:
                    last_activity = None

                sessions.append(
                    {
                        "session_id": session_id,
                        "interaction_count": interaction_count,
                        "last_activity": (
                            last_activity.isoformat() if last_activity else None
                        ),
                        "ttl_remaining": self.redis_memory.redis.ttl(session_key),
                    }
                )

            # Sort by last activity (most recent first)
            sessions.sort(key=lambda x: x["last_activity"] or "", reverse=True)
            return sessions

        except Exception as e:
            logger.error(f"Error listing active sessions: {e}")
            return []

    def cleanup_expired_sessions(self, dry_run: bool = True) -> Dict[str, Any]:
        """Clean up expired sessions and interactions"""
        try:
            if not self.redis_memory.redis_available:
                return {"error": "Redis not available"}

            session_pattern = self.redis_memory._get_session_key("*")
            session_keys = self.redis_memory.redis.keys(session_pattern)

            cleaned_sessions = 0
            cleaned_interactions = 0

            for session_key in session_keys:
                session_id = session_key.replace("conversation:", "")
                ttl = self.redis_memory.redis.ttl(session_key)

                # If TTL is -1 (no expiry) or -2 (key doesn't exist), skip
                if ttl <= 0:
                    if not dry_run:
                        # Get all interaction IDs for this session
                        interaction_ids = self.redis_memory.redis.lrange(
                            session_key, 0, -1
                        )

                        # Delete all interactions
                        for interaction_id in interaction_ids:
                            interaction_key = self.redis_memory._get_interaction_key(
                                session_id, interaction_id
                            )
                            self.redis_memory.redis.delete(interaction_key)
                            cleaned_interactions += 1

                        # Delete session key
                        self.redis_memory.redis.delete(session_key)
                        cleaned_sessions += 1
                        logger.info(f"Cleaned expired session: {session_id}")
                    else:
                        cleaned_sessions += 1
                        logger.info(f"Would clean expired session: {session_id}")

            return {
                "dry_run": dry_run,
                "cleaned_sessions": cleaned_sessions,
                "cleaned_interactions": cleaned_interactions,
                "total_sessions_checked": len(session_keys),
            }

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return {"error": str(e)}

    def get_session_details(self, session_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific session"""
        try:
            if not self.redis_memory.redis_available:
                return {"error": "Redis not available"}

            session_key = self.redis_memory._get_session_key(session_id)
            interaction_ids = self.redis_memory.redis.lrange(session_key, 0, -1)

            interactions = []
            for interaction_id in interaction_ids:
                interaction_key = self.redis_memory._get_interaction_key(
                    session_id, interaction_id
                )
                interaction_data = self.redis_memory.redis.get(interaction_key)

                if interaction_data:
                    interaction = json.loads(interaction_data)
                    interactions.append(
                        {
                            "id": interaction_id,
                            "timestamp": interaction["timestamp"],
                            "question": (
                                interaction["question"][:100] + "..."
                                if len(interaction["question"]) > 100
                                else interaction["question"]
                            ),
                            "answer_length": len(interaction["answer"]),
                            "context_length": len(interaction["context"]),
                            "metadata": interaction["metadata"],
                        }
                    )

            return {
                "session_id": session_id,
                "total_interactions": len(interactions),
                "session_ttl": self.redis_memory.redis.ttl(session_key),
                "interactions": interactions,
            }

        except Exception as e:
            logger.error(f"Error getting session details: {e}")
            return {"error": str(e)}

    def export_session_data(self, session_id: str) -> Dict[str, Any]:
        """Export complete session data"""
        try:
            if not self.redis_memory.redis_available:
                return {"error": "Redis not available"}

            session_key = self.redis_memory._get_session_key(session_id)
            interaction_ids = self.redis_memory.redis.lrange(session_key, 0, -1)

            interactions = []
            for interaction_id in interaction_ids:
                interaction_key = self.redis_memory._get_interaction_key(
                    session_id, interaction_id
                )
                interaction_data = self.redis_memory.redis.get(interaction_key)

                if interaction_data:
                    interaction = json.loads(interaction_data)
                    interactions.append(interaction)

            return {
                "session_id": session_id,
                "export_timestamp": datetime.now().isoformat(),
                "total_interactions": len(interactions),
                "interactions": interactions,
            }

        except Exception as e:
            logger.error(f"Error exporting session data: {e}")
            return {"error": str(e)}


def main():
    """Main function for Redis memory management"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Redis Memory Manager for RAG Pipeline"
    )
    parser.add_argument(
        "--action",
        choices=["overview", "sessions", "cleanup", "details", "export"],
        default="overview",
        help="Action to perform",
    )
    parser.add_argument("--session-id", help="Session ID for details/export actions")
    parser.add_argument("--limit", type=int, default=50, help="Limit for sessions list")
    parser.add_argument("--dry-run", action="store_true", help="Dry run for cleanup")
    parser.add_argument("--output", help="Output file for export")

    args = parser.parse_args()

    manager = RedisMemoryManager()

    if args.action == "overview":
        overview = manager.get_memory_overview()
        print(json.dumps(overview, indent=2))

    elif args.action == "sessions":
        sessions = manager.list_active_sessions(args.limit)
        print(json.dumps(sessions, indent=2))

    elif args.action == "cleanup":
        result = manager.cleanup_expired_sessions(dry_run=args.dry_run)
        print(json.dumps(result, indent=2))

    elif args.action == "details":
        if not args.session_id:
            print("Error: --session-id is required for details action")
            sys.exit(1)
        details = manager.get_session_details(args.session_id)
        print(json.dumps(details, indent=2))

    elif args.action == "export":
        if not args.session_id:
            print("Error: --session-id is required for export action")
            sys.exit(1)
        data = manager.export_session_data(args.session_id)
        if args.output:
            with open(args.output, "w") as f:
                json.dump(data, f, indent=2)
            print(f"Exported session data to {args.output}")
        else:
            print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
