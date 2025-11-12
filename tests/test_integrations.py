#!/usr/bin/env python3
"""
Comprehensive Integration Test for Advanced RAG Application
Tests all API endpoints and frontend-backend communication
"""

import asyncio
import aiohttp
import requests
import json
import time
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000"
STREAMLIT_URL = "http://localhost:8501"


class IntegrationTester:
    """Comprehensive integration tester for the RAG application"""

    def __init__(self):
        self.session_id = f"test-session-{int(time.time())}"
        self.test_results = []

    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        self.test_results.append(
            {"test": test_name, "success": success, "details": details}
        )

    def test_health_endpoint(self) -> bool:
        """Test health endpoint"""
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get("status") == "ok"
            return False
        except Exception as e:
            self.log_test("Health Endpoint", False, str(e))
            return False

    def test_memory_stats(self) -> bool:
        """Test memory stats endpoint"""
        try:
            response = requests.get(f"{API_BASE_URL}/memory/stats", timeout=5)
            if response.status_code == 200:
                data = response.json()
                required_fields = [
                    "enabled",
                    "type",
                    "total_sessions",
                    "total_interactions",
                ]
                return all(field in data for field in required_fields)
            return False
        except Exception as e:
            self.log_test("Memory Stats", False, str(e))
            return False

    def test_retrieval_methods(self) -> bool:
        """Test retrieval methods endpoint"""
        try:
            response = requests.get(f"{API_BASE_URL}/retrieval-methods", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return "methods" in data and "default_method" in data
            return False
        except Exception as e:
            self.log_test("Retrieval Methods", False, str(e))
            return False

    def test_embedding_cache_status(self) -> bool:
        """Test embedding cache status endpoint"""
        try:
            response = requests.get(f"{API_BASE_URL}/embedding/cache/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return "embedding_cache" in data
            return False
        except Exception as e:
            self.log_test("Embedding Cache Status", False, str(e))
            return False

    def test_performance_stats(self) -> bool:
        """Test performance stats endpoint"""
        try:
            response = requests.get(f"{API_BASE_URL}/performance/stats", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return "performance_stats" in data
            return False
        except Exception as e:
            self.log_test("Performance Stats", False, str(e))
            return False

    def test_evaluation_endpoint(self) -> bool:
        """Test evaluation endpoint"""
        try:
            payload = {
                "query": "What are good wireless headphones?",
                "response": "Based on the context, Sony WH-1000XM4 and Bose QuietComfort 45 are excellent wireless headphones.",
                "context": "Sony WH-1000XM4 wireless headphones with noise cancellation. Bose QuietComfort 45 wireless headphones.",
            }
            response = requests.post(
                f"{API_BASE_URL}/evaluate", json=payload, timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return "evaluation" in data
            return False
        except Exception as e:
            self.log_test("Evaluation Endpoint", False, str(e))
            return False

    def test_chat_endpoint(self) -> bool:
        """Test chat endpoint"""
        try:
            payload = {
                "query": "Hi, what are some good products?",
                "session_id": self.session_id,
                "use_advanced_features": True,
                "top_k": 3,
                "retrieval_method": "hybrid",
            }
            response = requests.post(f"{API_BASE_URL}/chat", json=payload, timeout=30)
            if response.status_code == 200:
                data = response.json()
                required_fields = ["answer", "context", "metadata"]
                return all(field in data for field in required_fields)
            return False
        except Exception as e:
            self.log_test("Chat Endpoint", False, str(e))
            return False

    async def test_streaming_chat(self) -> bool:
        """Test streaming chat endpoint"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "query": "Tell me about wireless headphones",
                    "session_id": self.session_id,
                    "use_advanced_features": True,
                    "top_k": 3,
                    "retrieval_method": "hybrid",
                }

                async with session.post(
                    f"{API_BASE_URL}/chat/stream",
                    json=payload,
                    headers={"Accept": "text/event-stream"},
                ) as response:
                    if response.status == 200:
                        events_received = 0
                        async for line in response.content:
                            line = line.decode("utf-8").strip()
                            if line.startswith("data: "):
                                try:
                                    data = json.loads(line[6:])
                                    events_received += 1
                                    if data.get("type") == "complete":
                                        return True
                                except json.JSONDecodeError:
                                    continue
                        return events_received > 0
                    return False
        except Exception as e:
            self.log_test("Streaming Chat", False, str(e))
            return False

    def test_memory_operations(self) -> bool:
        """Test memory operations"""
        try:
            # Test session history
            response = requests.get(
                f"{API_BASE_URL}/memory/session/{self.session_id}/history", timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                return "session_id" in data and "history" in data
            return False
        except Exception as e:
            self.log_test("Memory Operations", False, str(e))
            return False

    def test_memory_clear(self) -> bool:
        """Test memory clear operation"""
        try:
            response = requests.delete(
                f"{API_BASE_URL}/memory/session/{self.session_id}", timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            self.log_test("Memory Clear", False, str(e))
            return False

    def test_streamlit_connectivity(self) -> bool:
        """Test if Streamlit is accessible"""
        try:
            response = requests.get(STREAMLIT_URL, timeout=5)
            return response.status_code == 200
        except Exception as e:
            self.log_test("Streamlit Connectivity", False, str(e))
            return False

    def run_all_tests(self):
        """Run all integration tests"""
        print("🚀 Starting Comprehensive Integration Tests")
        print("=" * 50)

        # Basic API tests
        self.log_test("Health Endpoint", self.test_health_endpoint())
        self.log_test("Memory Stats", self.test_memory_stats())
        self.log_test("Retrieval Methods", self.test_retrieval_methods())
        self.log_test("Embedding Cache Status", self.test_embedding_cache_status())
        self.log_test("Performance Stats", self.test_performance_stats())
        self.log_test("Evaluation Endpoint", self.test_evaluation_endpoint())

        # Chat functionality tests
        self.log_test("Chat Endpoint", self.test_chat_endpoint())

        # Memory tests
        self.log_test("Memory Operations", self.test_memory_operations())
        self.log_test("Memory Clear", self.test_memory_clear())

        # Frontend tests
        self.log_test("Streamlit Connectivity", self.test_streamlit_connectivity())

        # Async tests
        print("\n🔄 Testing Async Endpoints...")

        async def run_async_tests():
            self.log_test("Streaming Chat", await self.test_streaming_chat())

        asyncio.run(run_async_tests())

        # Summary
        print("\n" + "=" * 50)
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        print(f"📊 Test Results: {passed}/{total} tests passed")

        if passed == total:
            print("🎉 All integrations are working perfectly!")
        else:
            print("⚠️ Some tests failed. Check the details above.")

        return passed == total


def main():
    """Main test runner"""
    tester = IntegrationTester()
    success = tester.run_all_tests()

    if success:
        print("\n✅ Integration test completed successfully!")
        print("🌐 Your Advanced RAG Application is fully operational!")
        print(f"📱 Frontend: {STREAMLIT_URL}")
        print(f"🔧 API: {API_BASE_URL}")
    else:
        print("\n❌ Some integration tests failed.")
        print("Please check the API server and Streamlit app are running.")


if __name__ == "__main__":
    main()
