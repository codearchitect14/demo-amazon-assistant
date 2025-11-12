import streamlit as st
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
from dataclasses import dataclass, asdict
from collections import deque
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class SessionMessage:
    """Represents a single message in the conversation"""

    role: str
    content: str
    timestamp: datetime
    message_id: str
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "message_id": self.message_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionMessage":
        """Create from dictionary"""
        return cls(**data)


@dataclass
class SessionData:
    """Represents session data with metadata"""

    session_id: str
    user_id: str
    created_at: datetime
    last_activity: datetime
    messages: List[SessionMessage]
    debug_data: Dict[str, Any]
    filters: Dict[str, Any]
    metadata: Dict[str, Any]

    def __post_init__(self):
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)
        if isinstance(self.last_activity, str):
            self.last_activity = datetime.fromisoformat(self.last_activity)
        if not self.metadata:
            self.metadata = {}
        if not self.filters:
            self.filters = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "messages": [msg.to_dict() for msg in self.messages],
            "debug_data": self.debug_data,
            "filters": self.filters,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionData":
        """Create from dictionary"""
        messages = [SessionMessage.from_dict(msg) for msg in data.get("messages", [])]
        return cls(
            session_id=data["session_id"],
            user_id=data["user_id"],
            created_at=data["created_at"],
            last_activity=data["last_activity"],
            messages=messages,
            debug_data=data.get("debug_data", {}),
            filters=data.get("filters", {}),
            metadata=data.get("metadata", {}),
        )


class SessionManager:
    """Production-ready session management for Streamlit apps"""

    def __init__(
        self,
        max_messages: int = 50,
        max_session_age_hours: int = 24,
        cleanup_interval_minutes: int = 30,
        enable_persistence: bool = True,
        enable_compression: bool = True,
    ):
        """
        Initialize session manager

        Args:
            max_messages: Maximum number of messages per session
            max_session_age_hours: Maximum age of sessions before cleanup
            cleanup_interval_minutes: How often to run cleanup
            enable_persistence: Whether to persist sessions to browser storage
            enable_compression: Whether to compress session data
        """
        self.max_messages = max_messages
        self.max_session_age_hours = max_session_age_hours
        self.cleanup_interval_minutes = cleanup_interval_minutes
        self.enable_persistence = enable_persistence
        self.enable_compression = enable_compression

        # Initialize session state keys
        self._init_session_state()

        # Run cleanup if needed
        self._run_cleanup_if_needed()

    def _init_session_state(self):
        """Initialize session state with proper structure"""
        if "session_manager_initialized" not in st.session_state:
            st.session_state.session_manager_initialized = True
            st.session_state.sessions = {}
            st.session_state.current_session_id = None
            st.session_state.last_cleanup = time.time()
            st.session_state.session_stats = {
                "total_sessions": 0,
                "active_sessions": 0,
                "total_messages": 0,
                "last_cleanup": None,
            }

    def _generate_session_id(self, user_id: str = None) -> str:
        """Generate a unique session ID"""
        if user_id is None:
            user_id = "anonymous"

        # Create a hash based on user ID and timestamp
        timestamp = str(time.time())
        session_hash = hashlib.md5(f"{user_id}_{timestamp}".encode()).hexdigest()[:12]
        return f"{user_id}_{session_hash}"

    def _get_user_id(self) -> str:
        """Get or generate user ID"""
        if "user_id" not in st.session_state:
            # Generate a pseudo-anonymous user ID
            user_id = hashlib.md5(f"{time.time()}_{id(st)}".encode()).hexdigest()[:8]
            st.session_state.user_id = user_id
        return st.session_state.user_id

    def get_current_session(self) -> SessionData:
        """Get or create current session"""
        try:
            user_id = self._get_user_id()

            if st.session_state.current_session_id is None:
                # Create new session
                session_id = self._generate_session_id(user_id)
                st.session_state.current_session_id = session_id

                session_data = SessionData(
                    session_id=session_id,
                    user_id=user_id,
                    created_at=datetime.now(),
                    last_activity=datetime.now(),
                    messages=[],
                    debug_data={},
                    filters={},
                    metadata={"created_by": "session_manager"},
                )

                st.session_state.sessions[session_id] = session_data
                st.session_state.session_stats["total_sessions"] += 1
                st.session_state.session_stats["active_sessions"] += 1

                logger.info(f"Created new session: {session_id}")

            # Update last activity
            session = st.session_state.sessions[st.session_state.current_session_id]
            session.last_activity = datetime.now()

            return session
        except Exception as e:
            logger.error(f"Error getting current session: {e}")
            # Create a fallback session
            fallback_session = SessionData(
                session_id="fallback_session",
                user_id="fallback_user",
                created_at=datetime.now(),
                last_activity=datetime.now(),
                messages=[],
                debug_data={},
                filters={},
                metadata={"created_by": "fallback"},
            )
            return fallback_session

    def add_message(
        self, role: str, content: str, metadata: Dict[str, Any] = None
    ) -> str:
        """Add a message to the current session"""
        session = self.get_current_session()

        # Create message
        message = SessionMessage(
            role=role,
            content=content,
            timestamp=datetime.now(),
            message_id=str(uuid.uuid4()),
            metadata=metadata or {},
        )

        # Add to session
        session.messages.append(message)
        session.last_activity = datetime.now()

        # Enforce message limit
        if len(session.messages) > self.max_messages:
            # Remove oldest messages, keeping the most recent
            session.messages = session.messages[-self.max_messages :]
            logger.info(f"Trimmed messages for session {session.session_id}")

        st.session_state.session_stats["total_messages"] += 1

        return message.message_id

    def get_messages(self) -> List[Dict[str, Any]]:
        """Get messages in Streamlit-compatible format"""
        session = self.get_current_session()
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "avatar": self._get_avatar(msg.role),
                "timestamp": msg.timestamp,
                "message_id": msg.message_id,
            }
            for msg in session.messages
        ]

    def _get_avatar(self, role: str) -> str:
        """Get avatar for message role"""
        avatars = {"user": "🧑", "assistant": "🤖", "system": "⚙️"}
        return avatars.get(role, "💬")

    def update_debug_data(self, debug_data: Dict[str, Any]):
        """Update debug data for current session"""
        session = self.get_current_session()
        session.debug_data.update(debug_data)
        session.last_activity = datetime.now()

    def get_debug_data(self) -> Dict[str, Any]:
        """Get debug data for current session"""
        session = self.get_current_session()
        return session.debug_data

    def update_filters(self, filters: Dict[str, Any]):
        """Update filters for current session"""
        session = self.get_current_session()
        session.filters.update(filters)
        session.last_activity = datetime.now()

    def get_filters(self) -> Dict[str, Any]:
        """Get filters for current session"""
        session = self.get_current_session()
        return session.filters

    def clear_session(self):
        """Clear current session"""
        if st.session_state.current_session_id:
            session_id = st.session_state.current_session_id
            if session_id in st.session_state.sessions:
                del st.session_state.sessions[session_id]
                st.session_state.session_stats["active_sessions"] -= 1
                logger.info(f"Cleared session: {session_id}")

            st.session_state.current_session_id = None

    def clear_all_sessions(self):
        """Clear all sessions"""
        st.session_state.sessions = {}
        st.session_state.current_session_id = None
        st.session_state.session_stats["active_sessions"] = 0
        logger.info("Cleared all sessions")

    def _run_cleanup_if_needed(self):
        """Run cleanup if enough time has passed"""
        current_time = time.time()
        last_cleanup = st.session_state.last_cleanup

        if current_time - last_cleanup > (self.cleanup_interval_minutes * 60):
            self._cleanup_old_sessions()
            st.session_state.last_cleanup = current_time

    def _cleanup_old_sessions(self):
        """Remove sessions older than max_session_age_hours"""
        cutoff_time = datetime.now() - timedelta(hours=self.max_session_age_hours)
        sessions_to_remove = []

        for session_id, session in st.session_state.sessions.items():
            if session.last_activity < cutoff_time:
                sessions_to_remove.append(session_id)

        for session_id in sessions_to_remove:
            del st.session_state.sessions[session_id]
            st.session_state.session_stats["active_sessions"] -= 1

        if sessions_to_remove:
            logger.info(f"Cleaned up {len(sessions_to_remove)} old sessions")
            st.session_state.session_stats["last_cleanup"] = datetime.now().isoformat()

    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        try:
            stats = st.session_state.session_stats.copy()
            stats["current_session_id"] = st.session_state.current_session_id
            stats["total_sessions_in_memory"] = len(st.session_state.sessions)
            return stats
        except Exception as e:
            logger.error(f"Error getting session stats: {e}")
            return {
                "total_sessions": 0,
                "active_sessions": 0,
                "total_messages": 0,
                "last_cleanup": None,
                "current_session_id": None,
                "total_sessions_in_memory": 0,
            }

    def export_session(self, session_id: str = None) -> Dict[str, Any]:
        """Export session data"""
        if session_id is None:
            session_id = st.session_state.current_session_id

        if session_id and session_id in st.session_state.sessions:
            session = st.session_state.sessions[session_id]
            return session.to_dict()
        return {}

    def import_session(self, session_data: Dict[str, Any]) -> str:
        """Import session data"""
        try:
            session = SessionData.from_dict(session_data)
            st.session_state.sessions[session.session_id] = session
            st.session_state.current_session_id = session.session_id
            st.session_state.session_stats["total_sessions"] += 1
            st.session_state.session_stats["active_sessions"] += 1
            logger.info(f"Imported session: {session.session_id}")
            return session.session_id
        except Exception as e:
            logger.error(f"Failed to import session: {e}")
            raise

    def get_session_info(self) -> Dict[str, Any]:
        """Get information about current session"""
        session = self.get_current_session()
        return {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "message_count": len(session.messages),
            "age_hours": (datetime.now() - session.created_at).total_seconds() / 3600,
            "inactive_hours": (datetime.now() - session.last_activity).total_seconds()
            / 3600,
        }

    def is_session_valid(self) -> bool:
        """Check if current session is valid"""
        try:
            session = self.get_current_session()
            return session.session_id is not None
        except Exception:
            return False

    def handle_session_error(self):
        """Handle session state corruption"""
        logger.warning("Session state corruption detected, resetting...")
        self.clear_all_sessions()
        self._init_session_state()
        st.rerun()


# Global session manager instance
_session_manager = None


def get_session_manager() -> SessionManager:
    """Get the global session manager instance"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


def init_session_manager(**kwargs) -> SessionManager:
    """Initialize session manager with custom parameters"""
    global _session_manager
    _session_manager = SessionManager(**kwargs)
    return _session_manager
