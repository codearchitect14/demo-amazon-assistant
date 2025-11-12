#!/usr/bin/env python3
"""
Test script to demonstrate intent indicators and intelligent retrieval behavior.
"""

import asyncio
import aiohttp
import json
import time

async def test_intent_indicators():
    """Test different query types to show intent recognition."""
    
    base_url = "http://localhost:3001"
    session_id = "test_intent_demo"
    
    test_cases = [
        {
            "name": "NEW_SEARCH - Fresh Product Search",
            "query": "show me gaming laptops",
            "expected_intent": "NEW_SEARCH",
            "expected_behavior": "Fresh retrieval with product data"
        },
        {
            "name": "FOLLOW_UP - Using Previous Context",
            "query": "tell me more about that laptop",
            "expected_intent": "FOLLOW_UP", 
            "expected_behavior": "Fast response using conversation context"
        },
        {
            "name": "COMPARISON - Product Comparison",
            "query": "compare these laptops",
            "expected_intent": "COMPARISON",
            "expected_behavior": "Fresh retrieval for comparison"
        },
        {
            "name": "CLARIFICATION - Asking for Details",
            "query": "which one do you recommend?",
            "expected_intent": "CLARIFICATION",
            "expected_behavior": "Using conversation context"
        }
    ]
    
    print("🧪 Testing Intent Recognition System")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   Query: '{test_case['query']}'")
        print(f"   Expected Intent: {test_case['expected_intent']}")
        print(f"   Expected Behavior: {test_case['expected_behavior']}")
        
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{base_url}/chat/stream",
                    json={
                        "query": test_case['query'],
                        "session_id": session_id,
                        "top_k": 5,
                        "retrieval_method": "title_first"
                    },
                    headers={"Accept": "text/event-stream"}
                ) as response:
                    
                    if response.status == 200:
                        context_data = ""
                        intent_data = {}
                        
                        async for line in response.content:
                            line = line.decode("utf-8").strip()
                            if line.startswith("data: "):
                                try:
                                    data = json.loads(line[6:])
                                    if data["type"] == "complete":
                                        context_data = data.get("context", "")
                                        intent_data = data.get("metadata", {}).get("intent", {})
                                        break
                                except json.JSONDecodeError:
                                    continue
                        
                        end_time = time.time()
                        response_time = end_time - start_time
                        
                        # Analyze results
                        actual_intent = intent_data.get("intent_type", "UNKNOWN")
                        needs_retrieval = intent_data.get("needs_retrieval", True)
                        has_context = bool(context_data.strip())
                        
                        print(f"   ⏱️  Response Time: {response_time:.2f}s")
                        print(f"   🎯 Actual Intent: {actual_intent}")
                        print(f"   🔍 Needs Retrieval: {needs_retrieval}")
                        print(f"   📦 Has Context: {has_context}")
                        
                        # Determine behavior
                        if needs_retrieval and has_context:
                            behavior = "🔍 Fresh Search (Retrieved new data)"
                        elif not needs_retrieval and not has_context:
                            behavior = "💬 Conversation (Used previous context)"
                        else:
                            behavior = "❓ Mixed behavior"
                        
                        print(f"   🤖 Behavior: {behavior}")
                        
                        # Success indicator
                        if actual_intent == test_case['expected_intent']:
                            print(f"   ✅ Intent Match: YES")
                        else:
                            print(f"   ❌ Intent Match: NO (Expected: {test_case['expected_intent']})")
                            
                    else:
                        print(f"   ❌ API Error: {response.status}")
                        
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print("-" * 50)
    
    print("\n🎉 Intent Recognition Test Complete!")
    print("\n📋 Summary:")
    print("• NEW_SEARCH queries should retrieve fresh data (slower)")
    print("• FOLLOW_UP queries should use conversation context (faster)")
    print("• Frontend should show appropriate indicators")
    print("• Sidebar should display system status")

if __name__ == "__main__":
    asyncio.run(test_intent_indicators()) 