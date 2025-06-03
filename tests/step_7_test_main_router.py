# tests/test_main_router.py - STEP 7: Test the complete router system
import sys
import os
import time

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from main_router import CustomerSupportRouter
from main import CustomerSupportSystem

def test_session_management():
    """Test session creation and management"""
    print("📱 Testing Session Management...\n")
    
    router = CustomerSupportRouter()
    
    # Test session creation
    user_data = {"name": "Test User", "email": "test@example.com"}
    session_id = "test_session_mgmt"
    
    result = router.start_session(session_id, user_data)
    assert result["success"] == True
    assert "welcome_message" in result
    print("✅ Session creation successful")
    
    # Test session stats
    stats = router._get_session_stats(session_id)
    assert stats["message_count"] >= 1  # Welcome message
    assert stats["agent_switches"] == 0
    print("✅ Session stats working")
    
    # Test session ending
    end_result = router.end_session(session_id)
    assert end_result["success"] == True
    assert "summary" in end_result
    print("✅ Session ending successful")

def test_command_handling():
    """Test special command handling"""
    print("\n🔧 Testing Command Handling...\n")
    
    router = CustomerSupportRouter()
    session_id = "test_commands"
    
    # Start session
    router.start_session(session_id)
    
    # Test help command
    help_result = router.process_message(session_id, "/help")
    assert help_result["success"] == True
    assert "Available Commands" in help_result["response"]
    print("✅ Help command working")
    
    # Test status command
    status_result = router.process_message(session_id, "/status")
    assert status_result["success"] == True
    assert "Session Status" in status_result["response"]
    print("✅ Status command working")
    
    # Test stats command
    stats_result = router.process_message(session_id, "/stats")
    assert stats_result["success"] == True
    assert "System Performance" in stats_result["response"]
    print("✅ Stats command working")
    
    # Test clear command
    clear_result = router.process_message(session_id, "/clear")
    assert clear_result["success"] == True
    print("✅ Clear command working")

def test_agent_routing_integration():
    """Test agent routing with the main router"""
    print("\n🔀 Testing Agent Routing Integration...\n")
    
    router = CustomerSupportRouter()
    session_id = "test_routing_integration"
    
    # Start session
    router.start_session(session_id)
    
    # Test order lookup routing
    order_message = "What's the status of order ORD1001?"
    order_result = router.process_message(session_id, order_message)
    
    assert order_result["success"] == True
    assert order_result["agent_used"] == "order_lookup"
    assert order_result["confidence"] > 0.5
    print(f"✅ Order routing: agent={order_result['agent_used']}, confidence={order_result['confidence']:.2f}")
    
    # Test FAQ routing
    faq_message = "What's your return policy?"
    faq_result = router.process_message(session_id, faq_message)
    
    assert faq_result["success"] == True
    assert faq_result["agent_used"] == "faq"
    assert faq_result["confidence"] > 0.5
    print(f"✅ FAQ routing: agent={faq_result['agent_used']}, confidence={faq_result['confidence']:.2f}")
    
    # Test agent switching tracking
    stats = router._get_session_stats(session_id)
    assert stats["agent_switches"] >= 1  # Should have switched between agents
    print(f"✅ Agent switching tracked: {stats['agent_switches']} switches")

def test_conversation_flow():
    """Test complete conversation flow with context"""
    print("\n💬 Testing Complete Conversation Flow...\n")
    
    router = CustomerSupportRouter()
    session_id = "test_conversation_flow"
    
    # Start session
    router.start_session(session_id)
    
    # Multi-turn conversation
    conversation = [
        ("Hi, I need help with my order", "Should route to FAQ first"),
        ("Order ORD1001 specifically", "Should switch to order lookup"),
        ("What about returns?", "Should switch to FAQ"),
        ("Thanks for the help!", "Should stay with FAQ")
    ]
    
    previous_agent = None
    
    for i, (message, expectation) in enumerate(conversation, 1):
        print(f"Turn {i}: '{message}' ({expectation})")
        
        result = router.process_message(session_id, message)
        
        assert result["success"] == True
        current_agent = result["agent_used"]
        processing_time = result["processing_time"]
        
        print(f"   → Agent: {current_agent}, Time: {processing_time:.2f}s")
        
        # Verify context is maintained
        if i > 1:
            conversation_history = router.redis.get_conversation_history(session_id)
            assert len(conversation_history) >= i * 2  # User + assistant messages
        
        previous_agent = current_agent
        time.sleep(0.5)  # Brief pause
    
    # Check final session stats
    final_stats = router._get_session_stats(session_id)
    print(f"\n📊 Final Stats:")
    print(f"   Messages: {final_stats['message_count']}")
    print(f"   Agent switches: {final_stats['agent_switches']}")
    print(f"   Duration: {final_stats['session_duration_minutes']} minutes")
    
    assert final_stats["message_count"] >= len(conversation) * 2

def test_error_handling():
    """Test error handling and recovery"""
    print("\n🛡️  Testing Error Handling...\n")
    
    router = CustomerSupportRouter()
    session_id = "test_error_handling"
    
    # Start session
    router.start_session(session_id)
    
    # Test with invalid order ID
    invalid_order_result = router.process_message(session_id, "Check order ORD9999")
    assert invalid_order_result["success"] == True  # Should handle gracefully
    assert "not found" in invalid_order_result["response"].lower()
    print("✅ Invalid order handled gracefully")
    
    # Test with nonsensical input
    nonsense_result = router.process_message(session_id, "asdfghjkl qwerty")
    assert nonsense_result["success"] == True  # Should still work
    print("✅ Nonsensical input handled")
    
    # Test empty message
    try:
        empty_result = router.process_message(session_id, "")
        print("✅ Empty message handled")
    except:
        print("⚠️  Empty message caused error (expected)")

def test_performance_metrics():
    """Test performance tracking and metrics"""
    print("\n⚡ Testing Performance Metrics...\n")
    
    router = CustomerSupportRouter()
    session_id = "test_performance"
    
    # Start session
    router.start_session(session_id)
    
    # Test order lookup performance (should use cache on second call)
    order_id = "ORD1001"
    
    # First call (cache miss)
    start_time = time.time()
    result1 = router.process_message(session_id, f"Check order {order_id}")
    first_time = time.time() - start_time
    
    # Second call (cache hit)
    start_time = time.time()
    result2 = router.process_message(session_id, f"Check order {order_id} again")
    second_time = time.time() - start_time
    
    print(f"First lookup: {first_time:.2f}s")
    print(f"Second lookup: {second_time:.2f}s")
    print(f"Performance improvement: {((first_time - second_time) / first_time * 100):.1f}%")
    
    # Verify both succeeded
    assert result1["success"] == True
    assert result2["success"] == True
    
    # Second call should be faster (due to caching)
    assert second_time < first_time
    print("✅ Caching performance improvement verified")

def test_system_integration():
    """Test the complete system integration"""
    print("\n🔗 Testing System Integration...\n")
    
    system = CustomerSupportSystem()
    
    # Test session creation through main system
    user_data = {"name": "Integration Test", "email": "integration@test.com"}
    session_id = system.create_session(user_data)
    assert session_id is not None
    print(f"✅ System session created: {session_id}")
    
    # Test messaging through main system
    response = system.chat("What's the status of order ORD1001?", session_id)
    assert response["success"] == True
    assert "agent_used" in response
    print(f"✅ System messaging works: {response['agent_used']}")
    
    # Test session ending through main system
    end_result = system.end_session(session_id)
    assert end_result["success"] == True
    print("✅ System session ending works")
    
    # Test system info
    info = system.get_system_info()
    assert "config" in info
    assert "redis_stats" in info
    print("✅ System info retrieval works")

def run_router_tests():
    """Run all router tests"""
    print("🧪 Starting Main Router Tests...\n")
    
    try:
        test_session_management()
        test_command_handling()
        test_agent_routing_integration()
        test_conversation_flow()
        test_error_handling()
        test_performance_metrics()
        test_system_integration()
        
        print("\n🎉 All router tests passed!")
        print("\n💡 Key Achievements:")
        print("   ✅ Session management with Redis")
        print("   ✅ Intelligent agent routing")
        print("   ✅ Conversation context preservation")
        print("   ✅ Performance optimization with caching")
        print("   ✅ Comprehensive error handling")
        print("   ✅ Command system integration")
        print("   ✅ End-to-end system integration")
        
    except Exception as e:
        print(f"❌ Router test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_router_tests()