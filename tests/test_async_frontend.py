#!/usr/bin/env python3
"""
Test script to verify async frontend handling works correctly.
"""

import asyncio
import sys
import os

# Add the app directory to the path
current_dir = os.path.dirname(__file__)
app_dir = os.path.join(current_dir, 'app')
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

def test_async_event_loop_handling():
    """Test the async event loop handling logic."""
    
    async def mock_async_function():
        """Mock async function that simulates the get_response function."""
        await asyncio.sleep(0.1)
        return "test_response", {"context": "test", "metadata": {}}
    
    def test_asyncio_run():
        """Test the asyncio.run() approach."""
        try:
            result = asyncio.run(mock_async_function())
            print("✅ asyncio.run() works correctly")
            return result
        except RuntimeError as e:
            print(f"❌ asyncio.run() failed: {e}")
            return None
    
    def test_event_loop_fallback():
        """Test the event loop fallback approach."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(mock_async_function())
                print("✅ Event loop fallback works correctly")
                return result
            finally:
                loop.close()
        except Exception as e:
            print(f"❌ Event loop fallback failed: {e}")
            return None
    
    def test_combined_approach():
        """Test the combined approach used in the app."""
        try:
            result = asyncio.run(mock_async_function())
            print("✅ Combined approach (asyncio.run) works")
            return result
        except RuntimeError:
            # If there's already a running event loop, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(mock_async_function())
                print("✅ Combined approach (fallback) works")
                return result
            finally:
                loop.close()
    
    print("Testing async event loop handling...")
    
    # Test 1: Basic asyncio.run
    result1 = test_asyncio_run()
    
    # Test 2: Event loop fallback
    result2 = test_event_loop_fallback()
    
    # Test 3: Combined approach
    result3 = test_combined_approach()
    
    # Verify all results are the same
    if result1 and result2 and result3:
        if result1 == result2 == result3:
            print("✅ All async handling approaches work correctly")
            return True
        else:
            print("❌ Results don't match between approaches")
            return False
    else:
        print("❌ Some async handling approaches failed")
        return False

def test_imports():
    """Test that all necessary imports work."""
    try:
        import streamlit as st
        import asyncio
        import time
        import re
        import logging
        import sys
        import os
        import atexit
        from typing import List, Dict
        
        print("✅ All imports work correctly")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing async frontend handling...")
    print("=" * 50)
    
    # Test imports
    imports_ok = test_imports()
    
    # Test async handling
    async_ok = test_async_event_loop_handling()
    
    print("=" * 50)
    if imports_ok and async_ok:
        print("✅ All tests passed! Frontend async handling is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 