#!/usr/bin/env python3
"""
Test script to verify embedding cache functionality
"""

import time
import requests
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_embedding_cache_status():
    """Test embedding cache status endpoint"""
    print("Testing embedding cache status...")

    try:
        response = requests.get("http://localhost:3001/embedding/cache/status")
        if response.status_code == 200:
            data = response.json()
            cache_info = data.get("embedding_cache", {})

            print("✓ Embedding cache status retrieved")
            print(f"Model name: {cache_info.get('model_name')}")
            print(f"Model loaded: {cache_info.get('model_loaded')}")
            print(
                f"Time since last use: {cache_info.get('time_since_last_use_seconds')} seconds"
            )
            print(
                f"Time until expiry: {cache_info.get('time_until_expiry_seconds')} seconds"
            )

            return True
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error testing embedding cache status: {e}")
        return False


def test_embedding_cache_reload():
    """Test embedding cache reload endpoint"""
    print("\nTesting embedding cache reload...")

    try:
        response = requests.post("http://localhost:3001/embedding/cache/reload")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ {data.get('message')}")
            return True
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error testing embedding cache reload: {e}")
        return False


def test_embedding_cache_clear():
    """Test embedding cache clear endpoint"""
    print("\nTesting embedding cache clear...")

    try:
        response = requests.post("http://localhost:3001/embedding/cache/clear")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ {data.get('message')}")
            return True
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error testing embedding cache clear: {e}")
        return False


def test_chat_with_cache():
    """Test chat endpoint to trigger embedding model loading"""
    print("\nTesting chat to trigger embedding model loading...")

    try:
        response = requests.post(
            "http://localhost:3001/chat",
            json={
                "query": "What are some good wireless headphones?",
                "top_k": 5,
                "retrieval_method": "title_first",
                "session_id": "test_cache_session",
            },
            timeout=30,
        )

        if response.status_code == 200:
            data = response.json()
            print("✓ Chat request successful")
            print(f"Answer length: {len(data.get('answer', ''))}")
            print(f"Context length: {len(data.get('context', ''))}")
            return True
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error testing chat: {e}")
        return False


def test_cache_lifecycle():
    """Test the complete cache lifecycle"""
    print("\nTesting embedding cache lifecycle...")

    # Step 1: Check initial status
    print("1. Checking initial cache status...")
    if not test_embedding_cache_status():
        return False

    # Step 2: Clear cache
    print("\n2. Clearing cache...")
    if not test_embedding_cache_clear():
        return False

    # Step 3: Check status after clear
    print("\n3. Checking status after clear...")
    if not test_embedding_cache_status():
        return False

    # Step 4: Trigger model loading with chat
    print("\n4. Triggering model loading with chat...")
    if not test_chat_with_cache():
        return False

    # Step 5: Check status after loading
    print("\n5. Checking status after loading...")
    if not test_embedding_cache_status():
        return False

    # Step 6: Test reload
    print("\n6. Testing reload...")
    if not test_embedding_cache_reload():
        return False

    # Step 7: Final status check
    print("\n7. Final status check...")
    if not test_embedding_cache_status():
        return False

    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("EMBEDDING CACHE TEST")
    print("=" * 60)

    try:
        # Test individual endpoints
        test_embedding_cache_status()
        test_embedding_cache_reload()
        test_embedding_cache_clear()
        test_chat_with_cache()

        # Test complete lifecycle
        print("\n" + "=" * 60)
        print("TESTING COMPLETE LIFECYCLE")
        print("=" * 60)

        if test_cache_lifecycle():
            print("\n" + "=" * 60)
            print("ALL TESTS COMPLETED SUCCESSFULLY!")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("SOME TESTS FAILED!")
            print("=" * 60)

    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.error(f"Test error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
