import streamlit as st
import json
import gzip
import base64
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
from session_manager import SessionManager, SessionData, init_session_manager

logger = logging.getLogger(__name__)


class SessionPersistence:
    """Handles session data persistence to browser storage"""

    @staticmethod
    def save_session_to_browser(
        session_data: Dict[str, Any], key: str = "session_data"
    ):
        """Save session data to browser storage"""
        try:
            # Compress and encode session data
            json_data = json.dumps(session_data, default=str)
            compressed_data = gzip.compress(json_data.encode("utf-8"))
            encoded_data = base64.b64encode(compressed_data).decode("utf-8")

            # Save to Streamlit session state
            st.session_state[key] = encoded_data
            logger.info(f"Saved session data to browser storage with key: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to save session to browser: {e}")
            return False

    @staticmethod
    def load_session_from_browser(
        key: str = "session_data",
    ) -> Optional[Dict[str, Any]]:
        """Load session data from browser storage"""
        try:
            if key not in st.session_state:
                return None

            encoded_data = st.session_state[key]
            compressed_data = base64.b64decode(encoded_data.encode("utf-8"))
            json_data = gzip.decompress(compressed_data).decode("utf-8")
            session_data = json.loads(json_data)

            logger.info(f"Loaded session data from browser storage with key: {key}")
            return session_data
        except Exception as e:
            logger.error(f"Failed to load session from browser: {e}")
            return None

    @staticmethod
    def clear_browser_session(key: str = "session_data"):
        """Clear session data from browser storage"""
        if key in st.session_state:
            del st.session_state[key]
            logger.info(f"Cleared session data from browser storage with key: {key}")


class SessionAnalytics:
    """Provides analytics and insights about session usage"""

    @staticmethod
    def get_conversation_summary(session_manager: SessionManager) -> Dict[str, Any]:
        """Get summary of current conversation"""
        try:
            session = session_manager.get_current_session()
            messages = session.messages

            if not messages:
                return {
                    "total_messages": 0,
                    "user_messages": 0,
                    "assistant_messages": 0,
                    "avg_message_length": 0,
                    "conversation_duration_seconds": 0,
                    "first_message_time": None,
                    "last_message_time": None,
                    "summary": "No messages yet",
                }

            # Count message types
            user_messages = [m for m in messages if m.role == "user"]
            assistant_messages = [m for m in messages if m.role == "assistant"]

            # Calculate average message length
            total_length = sum(len(m.content) for m in messages)
            avg_length = total_length / len(messages) if messages else 0

            # Get conversation duration
            if len(messages) >= 2:
                duration = (
                    messages[-1].timestamp - messages[0].timestamp
                ).total_seconds()
            else:
                duration = 0

            return {
                "total_messages": len(messages),
                "user_messages": len(user_messages),
                "assistant_messages": len(assistant_messages),
                "avg_message_length": round(avg_length, 1),
                "conversation_duration_seconds": round(duration, 1),
                "first_message_time": (
                    messages[0].timestamp.isoformat() if messages else None
                ),
                "last_message_time": (
                    messages[-1].timestamp.isoformat() if messages else None
                ),
            }
        except Exception as e:
            logger.error(f"Error getting conversation summary: {e}")
            return {
                "total_messages": 0,
                "user_messages": 0,
                "assistant_messages": 0,
                "avg_message_length": 0,
                "conversation_duration_seconds": 0,
                "first_message_time": None,
                "last_message_time": None,
                "summary": "Error loading conversation",
            }

    @staticmethod
    def get_session_health(session_manager: SessionManager) -> Dict[str, Any]:
        """Get health metrics for current session"""
        session = session_manager.get_current_session()
        now = datetime.now()

        # Calculate session age and inactivity
        session_age = (now - session.created_at).total_seconds() / 3600  # hours
        inactivity_hours = (now - session.last_activity).total_seconds() / 3600

        # Check for potential issues
        issues = []
        if len(session.messages) > 40:  # Close to limit
            issues.append("High message count")
        if session_age > 12:  # Old session
            issues.append("Old session")
        if inactivity_hours > 2:  # Inactive
            issues.append("Inactive session")

        return {
            "session_age_hours": round(session_age, 1),
            "inactivity_hours": round(inactivity_hours, 1),
            "message_count": len(session.messages),
            "message_limit": session_manager.max_messages,
            "issues": issues,
            "is_healthy": len(issues) == 0,
        }


class SessionHelpers:
    """Helper functions for common session operations"""

    @staticmethod
    def create_user_message(
        content: str, metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create a user message with proper formatting"""
        return {
            "role": "user",
            "content": content,
            "avatar": "🧑",
            "metadata": metadata or {},
        }

    @staticmethod
    def create_assistant_message(
        content: str, metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create an assistant message with proper formatting"""
        return {
            "role": "assistant",
            "content": content,
            "avatar": "🤖",
            "metadata": metadata or {},
        }

    @staticmethod
    def format_debug_data(
        query: str,
        context: str,
        metadata: Dict[str, Any],
        answer: str,
        error: str = None,
    ) -> Dict[str, Any]:
        """Format debug data for storage"""
        return {
            "query": query,
            "context": context,
            "metadata": metadata,
            "answer": answer,
            "error": error,
            "timestamp": datetime.now().isoformat(),
            "context_length": len(context),
            "answer_length": len(answer),
        }

    @staticmethod
    def validate_session_data(session_data: Dict[str, Any]) -> bool:
        """Validate session data structure"""
        required_keys = [
            "session_id",
            "user_id",
            "created_at",
            "last_activity",
            "messages",
        ]
        return all(key in session_data for key in required_keys)

    @staticmethod
    def sanitize_session_data(session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize session data for storage"""
        # Remove sensitive or unnecessary data
        sanitized = session_data.copy()

        # Limit context size to prevent memory issues
        if "debug_data" in sanitized and "context" in sanitized["debug_data"]:
            context = sanitized["debug_data"]["context"]
            if len(context) > 10000:  # 10KB limit
                sanitized["debug_data"]["context"] = context[:10000] + "... [truncated]"

        return sanitized


def setup_session_management(
    max_messages: int = 50,
    max_session_age_hours: int = 24,
    enable_persistence: bool = True,
    auto_cleanup: bool = True,
) -> SessionManager:
    """
    Setup session management with recommended production settings

    Args:
        max_messages: Maximum messages per session
        max_session_age_hours: Maximum session age before cleanup
        enable_persistence: Enable browser storage persistence
        auto_cleanup: Enable automatic cleanup of old sessions
    """
    # Initialize session manager
    session_manager = init_session_manager(
        max_messages=max_messages,
        max_session_age_hours=max_session_age_hours,
        enable_persistence=enable_persistence,
        enable_compression=True,
        cleanup_interval_minutes=30 if auto_cleanup else None,
    )

    # Load persisted session if available
    if enable_persistence:
        persisted_data = SessionPersistence.load_session_from_browser()
        if persisted_data and SessionHelpers.validate_session_data(persisted_data):
            try:
                session_manager.import_session(persisted_data)
                logger.info("Loaded persisted session data")
            except Exception as e:
                logger.warning(f"Failed to load persisted session: {e}")

    return session_manager


def cleanup_session_data(session_manager: SessionManager):
    """Clean up session data and save to browser if enabled"""
    try:
        # Get current session data
        session = session_manager.get_current_session()
        session_data = session.to_dict()

        # Sanitize data
        sanitized_data = SessionHelpers.sanitize_session_data(session_data)

        # Save to browser storage
        SessionPersistence.save_session_to_browser(sanitized_data)

        logger.info("Session data cleaned up and saved")
    except Exception as e:
        logger.error(f"Failed to cleanup session data: {e}")


def display_session_info(session_manager: SessionManager):
    """Display session information in Streamlit sidebar"""
    try:
        with st.sidebar:
            st.subheader("📊 Session Info")

            # Session health
            try:
                health = SessionAnalytics.get_session_health(session_manager)
                if health.get("is_healthy", False):
                    st.success("✅ Session Healthy")
                else:
                    st.warning("⚠️ Session Issues Detected")
                    for issue in health.get("issues", []):
                        st.caption(f"• {issue}")
            except Exception as e:
                st.warning("⚠️ Unable to check session health")
                logger.error(f"Error checking session health: {e}")

            # Conversation summary
            try:
                summary = SessionAnalytics.get_conversation_summary(session_manager)
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Messages", summary.get("total_messages", 0))
                with col2:
                    duration = summary.get("conversation_duration_seconds", 0)
                    st.metric("Duration", f"{duration:.0f}s")
            except Exception as e:
                st.warning("⚠️ Unable to load conversation summary")
                logger.error(f"Error loading conversation summary: {e}")

            # Session actions
            st.subheader("🔧 Session Actions")
            col1, col2 = st.columns(2)

            with col1:
                if st.button("Clear Session", type="secondary"):
                    try:
                        session_manager.clear_session()
                        st.rerun()
                    except Exception as e:
                        st.error("Failed to clear session")
                        logger.error(f"Error clearing session: {e}")

            with col2:
                if st.button("Export Session", type="secondary"):
                    try:
                        session_data = session_manager.export_session()
                        st.download_button(
                            label="Download Session",
                            data=json.dumps(session_data, indent=2, default=str),
                            file_name=f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json",
                        )
                    except Exception as e:
                        st.error("Failed to export session")
                        logger.error(f"Error exporting session: {e}")

            # Session stats
            try:
                stats = session_manager.get_session_stats()
                st.caption(f"Active Sessions: {stats.get('active_sessions', 0)}")
                st.caption(f"Total Messages: {stats.get('total_messages', 0)}")
            except Exception as e:
                st.caption("Unable to load session stats")
                logger.error(f"Error loading session stats: {e}")
    except Exception as e:
        st.error("Session info display error")
        logger.error(f"Error displaying session info: {e}")


def handle_session_errors(session_manager: SessionManager):
    """Handle common session errors gracefully"""
    try:
        # Check if session is valid
        if not session_manager.is_session_valid():
            st.error("Session state corrupted. Resetting...")
            session_manager.handle_session_error()
            return False

        # Check session health
        health = SessionAnalytics.get_session_health(session_manager)
        if not health["is_healthy"]:
            st.warning("Session health issues detected. Consider clearing session.")

        return True
    except Exception as e:
        logger.error(f"Session error: {e}")
        st.error("Session error occurred. Please refresh the page.")
        return False
