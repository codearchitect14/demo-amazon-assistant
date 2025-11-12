#!/usr/bin/env python3
"""
Script to create a test table in Supabase for testing the integration.

This script will help you create a simple test table that you can use
to verify the Supabase integration is working correctly.
"""

import pandas as pd
from supabase_client import SupabaseManager


def create_test_table():
    """Create a test table in Supabase."""

    print("🚀 Creating test table in Supabase...")

    try:
        # Initialize Supabase manager
        manager = SupabaseManager()

        # Test connection first
        if not manager.test_connection():
            print("❌ Connection failed. Please check your credentials.")
            return False

        print("✅ Connection successful!")

        # Create a sample DataFrame
        test_df = pd.DataFrame(
            {
                "id": [1, 2, 3, 4, 5],
                "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
                "age": [25, 30, 35, 28, 32],
                "city": ["NYC", "LA", "Chicago", "Boston", "Seattle"],
                "is_active": [True, True, False, True, True],
                "created_at": pd.date_range("2024-01-01", periods=5, freq="D"),
            }
        )

        print(
            f"📊 Created test DataFrame with {len(test_df)} rows and {len(test_df.columns)} columns"
        )
        print(f"   Columns: {list(test_df.columns)}")

        # Try to create the table and insert data
        print("\n📝 Creating table 'test_users' and inserting data...")

        result = manager.insert_dataframe(
            test_df,
            "test_users",
            if_exists="replace",  # This will create the table if it doesn't exist
            chunk_size=1000,
        )

        if result["success"]:
            print(f"✅ Table 'test_users' created successfully!")
            print(f"   Inserted {result['total_inserted']} records")
            print(f"   Total records processed: {result['total_records']}")

            # Verify the data was inserted
            print("\n🔍 Verifying data insertion...")
            try:
                retrieved_data = manager.get_all_data("test_users")
                print(
                    f"✅ Retrieved {len(retrieved_data)} records from 'test_users' table"
                )
                print(f"   Columns: {list(retrieved_data.columns)}")
                print("\n📋 Sample data:")
                print(retrieved_data.head())

                return True

            except Exception as e:
                print(f"⚠️  Could not retrieve data: {e}")
                print("   The table was created but there might be permission issues")
                return False

        else:
            print(f"❌ Table creation failed: {result['errors']}")
            print("\n💡 This might be due to:")
            print("   1. Insufficient permissions to create tables")
            print("   2. Row Level Security (RLS) policies blocking access")
            print("   3. Database connection issues")
            print("\n🔧 To fix this:")
            print("   1. Go to your Supabase dashboard")
            print("   2. Navigate to Table Editor")
            print("   3. Create a table manually with the following columns:")
            print("      - id (integer)")
            print("      - name (text)")
            print("      - age (integer)")
            print("      - city (text)")
            print("      - is_active (boolean)")
            print("      - created_at (timestamp)")
            print("   4. Set up appropriate RLS policies")

            return False

    except Exception as e:
        print(f"❌ Error creating test table: {e}")
        return False


def main():
    """Main function."""
    print("🧪 Supabase Test Table Creator")
    print("=" * 40)

    success = create_test_table()

    if success:
        print("\n🎉 Test table created successfully!")
        print("\n✅ You can now:")
        print("   1. Run the full example: python example_supabase_usage.py")
        print("   2. Use the Supabase integration in your code")
        print("   3. View the table in your Supabase dashboard")
    else:
        print("\n❌ Test table creation failed.")
        print("   Please check the error messages above and try again.")


if __name__ == "__main__":
    main()
