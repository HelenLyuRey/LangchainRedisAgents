# tests/test_agents.py - STEP 6: Test our agents
import sys
import os
import time

# Add src and data to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'data'))

from redis_manager import RedisManager
from agents import OrderLookupAgent, FAQAgent
from agent_router import AgentRouter
from orders import get_sample_order_ids

def test_order_agent():
    """Test the Order Lookup Agent"""
    print("🛒 Testing Order Lookup Agent...\n")
    
    redis_manager = RedisManager()
    order_agent = OrderLookupAgent(redis_manager)
    
    session_id = "test_order_session"
    
    # Test 1: Order lookup
    sample_ids = get_sample_order_ids(1)
    test_order_id = sample_ids[0]
    
    print(f"Test 1: Looking up order {test_order_id}")
    message1 = f"What's the status of my order {test_order_id}?"
    
    start_time = time.time()
    response1 = order_agent.process_message(message1, session_id)
    process_time = time.time() - start_time
    
    print(f"Response (took {process_time:.2f}s):")
    print(response1)
    print("\n" + "="*50 + "\n")
    
    # Test 2: Email search
    print("Test 2: Searching orders by email")
    message2 = "Can you show me all orders for customer1@example.com?"
    
    start_time = time.time()
    response2 = order_agent.process_message(message2, session_id)
    process_time = time.time() - start_time
    
    print(f"Response (took {process_time:.2f}s):")
    print(response2)
    print("\n" + "="*50 + "\n")
    
    # Test 3: Invalid order
    print("Test 3: Invalid order lookup")
    message3 = "What's the status of order ORD9999?"
    
    response3 = order_agent.process_message(message3, session_id)
    print("Response:")
    print(response3)

def test_faq_agent():
    """Test the FAQ Agent"""
    print("\n❓ Testing FAQ Agent...\n")
    
    redis_manager = RedisManager()
    faq_agent = FAQAgent(redis_manager)
    
    session_id = "test_faq_session"
    
    # Test 1: Return policy
    print("Test 1: Asking about return policy")
    message1 = "What is your return policy?"
    
    start_time = time.time()
    response1 = faq_agent.process_message(message1, session_id)
    process_time = time.time() - start_time
    
    print(f"Response (took {process_time:.2f}s):")
    print(response1)
    print("\n" + "="*50 + "\n")
    
    # Test 2: Shipping question
    print("Test 2: Asking about shipping")
    message2 = "How long does shipping take?"
    
    start_time = time.time()
    response2 = faq_agent.process_message(message2, session_id)
    process_time = time.time() - start_time
    
    print(f"Response (took {process_time:.2f}s):")
    print(response2)
    print("\n" + "="*50 + "\n")
    
    # Test 3: Contact information
    print("Test 3: Asking for contact info")
    message3 = "How can I contact customer support?"
    
    response3 = faq_agent.process_message(message3, session_id)
    print("Response:")
    print(response3)

def test_agent_router():
    """Test the Agent Router"""
    print("\n🔀 Testing Agent Router...\n")
    
    redis_manager = RedisManager()
    router = AgentRouter(redis_manager)
    
    test_messages = [
        "What's the status of order ORD1001?",
        "What is your return policy?",
        "Can you track my package?",
        "How do I contact support?",
        "Where is my order ORD1002?",
        "What payment methods do you accept?",
        "Show me orders for test@example.com",
        "How long is the warranty?"
    ]
    
    session_id = "test_routing_session"
    
    for i, message in enumerate(test_messages, 1):
        agent, confidence = router.route_message(message, session_id)
        print(f"Test {i}: \"{message}\"")
        print(f"   → Routed to: {agent} (confidence: {confidence:.2f})")
        print()

def test_conversation_flow():
    """Test a complete conversation flow with both agents"""
    print("\n💬 Testing Complete Conversation Flow...\n")
    
    redis_manager = RedisManager()
    order_agent = OrderLookupAgent(redis_manager)
    faq_agent = FAQAgent(redis_manager)
    router = AgentRouter(redis_manager)
    
    session_id = "test_conversation_flow"
    
    # Simulate a customer conversation
    conversation = [
        "Hi, I have a question about my recent order",
        "What's the status of order ORD1001?",  
        "Great! What's your return policy?",
        "How long do I have to return an item?",
        "Can you also check order ORD1002 for me?"
    ]
    
    for i, message in enumerate(conversation, 1):
        print(f"👤 Customer: {message}")
        
        # Route the message
        agent_type, confidence = router.route_message(message, session_id)
        print(f"🤖 Routing to {agent_type} (confidence: {confidence:.2f})")
        
        # Process with appropriate agent
        if agent_type == "order_lookup":
            response = order_agent.process_message(message, session_id)
        else:
            response = faq_agent.process_message(message, session_id)
        
        print(f"🤖 Assistant: {response}")
        
        # Add to conversation history
        redis_manager.add_message(session_id, "user", message)
        redis_manager.add_message(session_id, "assistant", response)
        
        print("\n" + "-"*50 + "\n")
        
        time.sleep(1)  # Brief pause between messages

def run_agent_tests():
    """Run all agent tests"""
    print("🧪 Starting Agent Tests...\n")
    
    try:
        test_order_agent()
        test_faq_agent()
        test_agent_router()
        test_conversation_flow()
        
        print("\n🎉 All agent tests completed!")
        print("\n💡 Key Observations:")
        print("   - Order agent uses Redis caching for fast lookups")
        print("   - FAQ agent preloads common searches")
        print("   - Router intelligently routes based on message content")
        print("   - Conversation history is maintained across agent switches")
        print("   - Both agents save state for analytics and context")
        
    except Exception as e:
        print(f"❌ Agent test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_agent_tests()