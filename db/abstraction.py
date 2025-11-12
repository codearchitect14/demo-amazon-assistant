"""
Database abstraction layer to decouple from specific database implementations.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from abc import ABC, abstractmethod
from shared.utils.error_handling import DatabaseError
from shared.utils.validation import DataSanitizer

logger = logging.getLogger(__name__)


class DatabaseInterface(ABC):
    """Abstract database interface."""
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to database."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from database."""
        pass
    
    @abstractmethod
    async def is_connected(self) -> bool:
        """Check if connected to database."""
        pass
    
    @abstractmethod
    async def query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute database query."""
        pass
    
    @abstractmethod
    async def insert(self, table: str, data: Dict[str, Any]) -> bool:
        """Insert data into table."""
        pass
    
    @abstractmethod
    async def update(self, table: str, data: Dict[str, Any], condition: Dict[str, Any]) -> bool:
        """Update data in table."""
        pass
    
    @abstractmethod
    async def delete(self, table: str, condition: Dict[str, Any]) -> bool:
        """Delete data from table."""
        pass
    
    @abstractmethod
    async def get_health_status(self) -> Dict[str, Any]:
        """Get database health status."""
        pass


class QdrantDatabase(DatabaseInterface):
    """Qdrant-specific database implementation."""
    
    def __init__(self, url: str, api_key: Optional[str] = None):
        self.url = url
        self.api_key = api_key
        self.client = None
        self.sanitizer = DataSanitizer()
    
    async def connect(self) -> bool:
        """Connect to Qdrant database."""
        try:
            from qdrant_client import QdrantClient
            
            self.client = QdrantClient(
                url=self.url,
                api_key=self.api_key
            )
            
            # Test connection
            collections = self.client.get_collections()
            logger.info(f"Connected to Qdrant at {self.url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise DatabaseError(f"Connection failed: {str(e)}", operation="connect")
    
    async def disconnect(self) -> bool:
        """Disconnect from Qdrant database."""
        try:
            if self.client:
                self.client.close()
                self.client = None
            logger.info("Disconnected from Qdrant")
            return True
        except Exception as e:
            logger.error(f"Error disconnecting from Qdrant: {e}")
            return False
    
    async def is_connected(self) -> bool:
        """Check if connected to Qdrant."""
        try:
            if not self.client:
                return False
            # Test connection by getting collections
            self.client.get_collections()
            return True
        except Exception:
            return False
    
    async def query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute query on Qdrant (simplified for vector search)."""
        try:
            if not self.client:
                raise DatabaseError("Not connected to database", operation="query")
            
            # For Qdrant, we'll implement vector search queries
            # This is a simplified implementation
            logger.info(f"Executing query: {query[:50]}...")
            
            # Placeholder for actual vector search
            return []
            
        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise DatabaseError(f"Query failed: {str(e)}", operation="query")
    
    async def insert(self, table: str, data: Dict[str, Any]) -> bool:
        """Insert data into Qdrant collection."""
        try:
            if not self.client:
                raise DatabaseError("Not connected to database", operation="insert")
            
            # Sanitize data
            sanitized_data = {}
            for key, value in data.items():
                if isinstance(value, str):
                    sanitized_data[key] = self.sanitizer.sanitize_string(value)
                else:
                    sanitized_data[key] = value
            
            # For Qdrant, this would insert vectors into a collection
            logger.info(f"Inserting data into collection: {table}")
            
            # Placeholder for actual insertion
            return True
            
        except Exception as e:
            logger.error(f"Insert failed: {e}")
            raise DatabaseError(f"Insert failed: {str(e)}", operation="insert")
    
    async def update(self, table: str, data: Dict[str, Any], condition: Dict[str, Any]) -> bool:
        """Update data in Qdrant collection."""
        try:
            if not self.client:
                raise DatabaseError("Not connected to database", operation="update")
            
            logger.info(f"Updating data in collection: {table}")
            
            # Placeholder for actual update
            return True
            
        except Exception as e:
            logger.error(f"Update failed: {e}")
            raise DatabaseError(f"Update failed: {str(e)}", operation="update")
    
    async def delete(self, table: str, condition: Dict[str, Any]) -> bool:
        """Delete data from Qdrant collection."""
        try:
            if not self.client:
                raise DatabaseError("Not connected to database", operation="delete")
            
            logger.info(f"Deleting data from collection: {table}")
            
            # Placeholder for actual deletion
            return True
            
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            raise DatabaseError(f"Delete failed: {str(e)}", operation="delete")
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get Qdrant health status."""
        try:
            if not self.client:
                return {
                    "status": "disconnected",
                    "database": "qdrant",
                    "url": self.url
                }
            
            # Get collections info
            collections = self.client.get_collections()
            
            return {
                "status": "connected",
                "database": "qdrant",
                "url": self.url,
                "collections_count": len(collections.collections),
                "collections": [col.name for col in collections.collections]
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "error",
                "database": "qdrant",
                "url": self.url,
                "error": str(e)
            }


class DatabaseManager:
    """Database manager for handling different database types."""
    
    def __init__(self, database: DatabaseInterface):
        self.database = database
        self.connected = False
    
    async def initialize(self) -> bool:
        """Initialize database connection."""
        try:
            self.connected = await self.database.connect()
            return self.connected
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            return False
    
    async def cleanup(self) -> bool:
        """Cleanup database connection."""
        try:
            if self.connected:
                await self.database.disconnect()
                self.connected = False
            return True
        except Exception as e:
            logger.error(f"Database cleanup failed: {e}")
            return False
    
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute database query with error handling."""
        try:
            if not self.connected:
                await self.initialize()
            
            return await self.database.query(query, params)
            
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise DatabaseError(f"Query execution failed: {str(e)}", operation="execute_query")
    
    async def insert_data(self, table: str, data: Dict[str, Any]) -> bool:
        """Insert data with error handling."""
        try:
            if not self.connected:
                await self.initialize()
            
            return await self.database.insert(table, data)
            
        except Exception as e:
            logger.error(f"Data insertion failed: {e}")
            raise DatabaseError(f"Data insertion failed: {str(e)}", operation="insert_data")
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get database health status."""
        try:
            return await self.database.get_health_status()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }


def create_database_manager(url: str, api_key: Optional[str] = None) -> DatabaseManager:
    """
    Create database manager instance.
    
    Args:
        url: Database URL
        api_key: Database API key (optional)
        
    Returns:
        DatabaseManager instance
    """
    database = QdrantDatabase(url, api_key)
    return DatabaseManager(database) 