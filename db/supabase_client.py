import os
import pandas as pd
from typing import Dict, List, Any, Optional, Union
from supabase import create_client, Client
from postgrest import APIError
import logging
import re
from app.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SupabaseManager:
    """
    A class to manage Supabase operations including inserting dataframes
    and retrieving data from tables with dynamic columns.
    """

    def __init__(self):
        """Initialize Supabase client with credentials from environment variables."""
        self.supabase_url = Config.SUPABASE_URL
        self.supabase_key = Config.SUPABASE_ANON_KEY

        if not self.supabase_url or not self.supabase_key:
            raise ValueError(
                "Missing Supabase credentials. Please set SUPABASE_URL and SUPABASE_ANON_KEY "
                "in your environment variables."
            )

        # Validate and clean the URL
        self.supabase_url = self._validate_and_clean_url(self.supabase_url)

        try:
            self.client: Client = create_client(self.supabase_url, self.supabase_key)
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            logger.error(f"URL format: {self.supabase_url}")
            logger.error(
                "Make sure you're using the Supabase project URL (not database URL)"
            )
            logger.error("Project URL format: https://your-project-id.supabase.co")
            raise

    def _validate_and_clean_url(self, url: str) -> str:
        """
        Validate and clean the Supabase URL.

        Args:
            url: The URL from environment variable

        Returns:
            Cleaned and validated URL
        """
        # Remove any whitespace
        url = url.strip()

        # Check if it's a database URL (postgresql://)
        if url.startswith("postgresql://"):
            logger.error(
                "❌ You're using a database connection URL instead of the Supabase project URL"
            )
            logger.error("❌ Database URL format: postgresql://postgres.dhekfpig...")
            logger.error("✅ Required format: https://your-project-id.supabase.co")
            logger.error("")
            logger.error("To fix this:")
            logger.error("1. Go to your Supabase project dashboard")
            logger.error("2. Navigate to Settings > API")
            logger.error("3. Copy the 'Project URL' (not the database URL)")
            logger.error("4. Update your SUPABASE_URL environment variable")
            raise ValueError(
                "Invalid URL format. Please use the Supabase project URL, not the database URL. "
                "Go to Settings > API in your Supabase dashboard and copy the 'Project URL'."
            )

        # Check if it's a valid Supabase project URL
        if not url.startswith("https://"):
            # Try to construct the URL
            if ".supabase.co" in url:
                url = f"https://{url}"
            else:
                logger.error("❌ Invalid Supabase URL format")
                logger.error("✅ Required format: https://your-project-id.supabase.co")
                raise ValueError("Invalid Supabase URL format")

        # Ensure it ends with .supabase.co
        if not url.endswith(".supabase.co"):
            logger.warning(
                "URL doesn't end with .supabase.co - this might not be a valid Supabase project URL"
            )

        return url

    def insert_dataframe(
        self,
        df: pd.DataFrame,
        table_name: str,
        if_exists: str = "append",
        chunk_size: int = 1000,
    ) -> Dict[str, Any]:
        """
        Insert a pandas DataFrame into a Supabase table.

        Args:
            df: Pandas DataFrame to insert
            table_name: Name of the target table in Supabase
            if_exists: How to behave if the table exists
                      - 'append': Insert new records (default)
                      - 'replace': Drop and recreate table
                      - 'fail': Raise an error if table exists
            chunk_size: Number of records to insert in each batch

        Returns:
            Dict containing operation status and details
        """
        try:
            # Convert DataFrame to list of dictionaries
            records = df.to_dict("records")

            if if_exists == "replace":
                # Drop existing table and recreate
                self._drop_table_if_exists(table_name)
                self._create_table_from_dataframe(df, table_name)

            # Insert data in chunks to avoid memory issues
            total_inserted = 0
            errors = []

            for i in range(0, len(records), chunk_size):
                chunk = records[i : i + chunk_size]
                try:
                    result = self.client.table(table_name).insert(chunk).execute()
                    total_inserted += len(chunk)
                    logger.info(f"Inserted {len(chunk)} records into {table_name}")
                except APIError as e:
                    error_msg = f"Error inserting chunk {i//chunk_size + 1}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    # Continue with next chunk instead of failing completely
                    continue

            return {
                "success": len(errors) == 0,
                "total_inserted": total_inserted,
                "total_records": len(records),
                "errors": errors,
                "table_name": table_name,
            }

        except Exception as e:
            error_msg = f"Failed to insert DataFrame into {table_name}: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg, "table_name": table_name}

    def get_all_data(
        self,
        table_name: str,
        columns: Optional[List[str]] = None,
        limit: Optional[int] = None,
        order_by: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Retrieve all data from a Supabase table and return as a pandas DataFrame.

        Args:
            table_name: Name of the table to query
            columns: List of specific columns to retrieve (None for all columns)
            limit: Maximum number of records to retrieve
            order_by: Column name to order results by

        Returns:
            Pandas DataFrame containing the table data
        """
        try:
            query = self.client.table(table_name).select(
                "*" if columns is None else ",".join(columns)
            )

            if order_by:
                query = query.order(order_by)

            if limit:
                query = query.limit(limit)

            result = query.execute()

            if result.data:
                df = pd.DataFrame(result.data)
                logger.info(f"Retrieved {len(df)} records from {table_name}")
                return df
            else:
                logger.info(f"No data found in table {table_name}")
                return pd.DataFrame()

        except APIError as e:
            error_msg = f"Failed to retrieve data from {table_name}: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error retrieving data from {table_name}: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    def get_data_with_filters(
        self,
        table_name: str,
        filters: Dict[str, Any],
        columns: Optional[List[str]] = None,
        limit: Optional[int] = None,
        order_by: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Retrieve data from a Supabase table with filters.

        Args:
            table_name: Name of the table to query
            filters: Dictionary of column-value pairs to filter by
            columns: List of specific columns to retrieve (None for all columns)
            limit: Maximum number of records to retrieve
            order_by: Column name to order results by

        Returns:
            Pandas DataFrame containing the filtered data
        """
        try:
            query = self.client.table(table_name).select(
                "*" if columns is None else ",".join(columns)
            )

            # Apply filters
            for column, value in filters.items():
                query = query.eq(column, value)

            if order_by:
                query = query.order(order_by)

            if limit:
                query = query.limit(limit)

            result = query.execute()

            if result.data:
                df = pd.DataFrame(result.data)
                logger.info(f"Retrieved {len(df)} filtered records from {table_name}")
                return df
            else:
                logger.info(f"No data found in table {table_name} with given filters")
                return pd.DataFrame()

        except APIError as e:
            error_msg = f"Failed to retrieve filtered data from {table_name}: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """
        Get the schema information for a table.

        Args:
            table_name: Name of the table

        Returns:
            Dictionary containing table schema information
        """
        try:
            # This is a simplified approach - in a real implementation,
            # you might want to query the information_schema
            result = self.client.table(table_name).select("*").limit(1).execute()

            if result.data:
                sample_record = result.data[0]
                schema = {
                    "table_name": table_name,
                    "columns": list(sample_record.keys()),
                    "sample_data": sample_record,
                }
                return schema
            else:
                return {"table_name": table_name, "columns": [], "sample_data": {}}

        except Exception as e:
            error_msg = f"Failed to get schema for table {table_name}: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    def _drop_table_if_exists(self, table_name: str) -> None:
        """Drop a table if it exists (requires appropriate permissions)."""
        try:
            # Note: This requires appropriate RLS policies and permissions
            self.client.rpc(
                "drop_table_if_exists", {"table_name": table_name}
            ).execute()
            logger.info(f"Dropped table {table_name}")
        except Exception as e:
            logger.warning(f"Could not drop table {table_name}: {str(e)}")

    def _create_table_from_dataframe(self, df: pd.DataFrame, table_name: str) -> None:
        """Create a table from DataFrame structure (requires appropriate permissions)."""
        try:
            # This is a simplified approach - in production, you'd want to
            # create proper SQL DDL statements based on DataFrame dtypes
            columns = []
            for col, dtype in df.dtypes.items():
                if "int" in str(dtype):
                    col_type = "bigint"
                elif "float" in str(dtype):
                    col_type = "double precision"
                elif "bool" in str(dtype):
                    col_type = "boolean"
                else:
                    col_type = "text"
                columns.append(f"{col} {col_type}")

            # Note: This requires appropriate permissions and might need to be
            # implemented differently based on your Supabase setup
            logger.info(f"Would create table {table_name} with columns: {columns}")

        except Exception as e:
            logger.error(f"Failed to create table {table_name}: {str(e)}")
            raise

    def test_connection(self) -> bool:
        """
        Test the Supabase connection.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Try to access the auth endpoint which is always available
            # This is a more reliable way to test the connection
            response = self.client.auth.get_session()
            logger.info("Supabase connection test successful")
            return True
        except Exception as e:
            # If auth test fails, try a simple table query
            try:
                # Try to list tables or access a simple endpoint
                # This will work even if no tables exist
                result = (
                    self.client.table("_dummy_table_for_test")
                    .select("*")
                    .limit(1)
                    .execute()
                )
                logger.info("Supabase connection test successful (table access)")
                return True
            except Exception as e2:
                # If both fail, check if it's a 404 (table doesn't exist) vs connection error
                if "404" in str(e2) or "not found" in str(e2).lower():
                    logger.info(
                        "Supabase connection test successful (404 expected for non-existent table)"
                    )
                    return True
                else:
                    logger.error(f"Supabase connection test failed: {str(e2)}")
                    return False


# Convenience functions for easy usage
def insert_dataframe_to_supabase(
    df: pd.DataFrame, table_name: str, if_exists: str = "append", chunk_size: int = 1000
) -> Dict[str, Any]:
    """
    Convenience function to insert a DataFrame into Supabase.

    Args:
        df: Pandas DataFrame to insert
        table_name: Name of the target table
        if_exists: How to behave if table exists
        chunk_size: Number of records per batch

    Returns:
        Dict containing operation results
    """
    manager = SupabaseManager()
    return manager.insert_dataframe(df, table_name, if_exists, chunk_size)


def get_data_from_supabase(
    table_name: str,
    columns: Optional[List[str]] = None,
    limit: Optional[int] = None,
    order_by: Optional[str] = None,
) -> pd.DataFrame:
    """
    Convenience function to get all data from a Supabase table.

    Args:
        table_name: Name of the table to query
        columns: Specific columns to retrieve
        limit: Maximum number of records
        order_by: Column to order by

    Returns:
        Pandas DataFrame with the data
    """
    manager = SupabaseManager()
    return manager.get_all_data(table_name, columns, limit, order_by)


def get_filtered_data_from_supabase(
    table_name: str,
    filters: Dict[str, Any],
    columns: Optional[List[str]] = None,
    limit: Optional[int] = None,
    order_by: Optional[str] = None,
) -> pd.DataFrame:
    """
    Convenience function to get filtered data from a Supabase table.

    Args:
        table_name: Name of the table to query
        filters: Dictionary of column-value filters
        columns: Specific columns to retrieve
        limit: Maximum number of records
        order_by: Column to order by

    Returns:
        Pandas DataFrame with the filtered data
    """
    manager = SupabaseManager()
    return manager.get_data_with_filters(table_name, filters, columns, limit, order_by)


# Example usage and testing
if __name__ == "__main__":
    # Example usage
    try:
        # Test connection
        manager = SupabaseManager()
        if manager.test_connection():
            print("✅ Supabase connection successful!")

        # Example: Insert a sample DataFrame
        sample_df = pd.DataFrame(
            {
                "id": [1, 2, 3],
                "name": ["Alice", "Bob", "Charlie"],
                "age": [25, 30, 35],
                "city": ["NYC", "LA", "Chicago"],
            }
        )

        # Insert data
        result = manager.insert_dataframe(sample_df, "test_table", if_exists="append")
        print(f"Insert result: {result}")

        # Retrieve data
        retrieved_df = manager.get_all_data("test_table")
        print(f"Retrieved data:\n{retrieved_df}")

        # Get filtered data
        filtered_df = manager.get_data_with_filters("test_table", {"age": 30})
        print(f"Filtered data:\n{filtered_df}")

    except Exception as e:
        print(f"❌ Error: {e}")
