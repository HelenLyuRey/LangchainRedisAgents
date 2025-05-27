# Test py for STEP 4

import sys
import os

# Add src and data to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'data'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from orders import get_order, get_sample_order_ids, get_order_status_summary, search_orders_by_email
from faq import search_faqs, get_best_faq_answer, get_random_faq

def test_order_operations():
    """Test order database operations"""
    print("🛒 Testing Order Operations...")
    
    # Test getting sample orders
    sample_ids = get_sample_order_ids(3)
    print(f"Sample Order IDs: {sample_ids}")
    
    # Test order lookup
    order_id = sample_ids[0]
    order = get_order(order_id)
    assert order is not None
    print(f"✅ Order lookup successful for {order_id}")
    print(f"   Product: {order['product']}")
    print(f"   Status: {order['status']}")
    
    # Test status summary
    summary = get_order_status_summary(order_id)
    assert summary is not None
    print(f"   Summary: {summary}")
    
    # Test email search
    email = order['customer_email']
    orders = search_orders_by_email(email)
    assert len(orders) >= 1
    print(f"✅ Found {len(orders)} orders for {email}")

def test_faq_operations():
    """Test FAQ database operations"""
    print("\n❓ Testing FAQ Operations...")
    
    # Test FAQ search
    test_queries = [
        "return policy",
        "shipping",
        "track order",
        "payment methods"
    ]
    
    for query in test_queries:
        results = search_faqs(query)
        assert len(results) > 0
        print(f"✅ Search '{query}': {len(results)} results")
        
        # Test best answer
        best_answer = get_best_faq_answer(query)
        assert best_answer is not None
        print(f"   Best answer: {best_answer[:80]}...")

def test_performance_simulation():
    """Test that our mock data simulates realistic delays"""
    import time
    
    print("\n⏱️  Testing Performance Simulation...")
    
    # Test order lookup delay
    start_time = time.time()
    sample_ids = get_sample_order_ids(1)
    get_order(sample_ids[0])
    order_time = time.time() - start_time
    
    print(f"✅ Order lookup took {order_time:.2f}s (simulated DB delay)")
    assert order_time >= 0.5  # Should have simulated delay
    
    # Test FAQ search delay
    start_time = time.time()
    search_faqs("return policy")
    faq_time = time.time() - start_time
    
    print(f"✅ FAQ search took {faq_time:.2f}s (simulated search delay)")
    assert faq_time >= 0.2  # Should have simulated delay

def run_mock_data_tests():
    """Run all mock data tests"""
    print("🧪 Starting Mock Data Tests...\n")
    
    test_order_operations()
    test_faq_operations() 
    test_performance_simulation()
    
    print("\n🎉 All mock data tests passed!")
    print("\n💡 Key Points:")
    print("   - Order lookups have 0.5s delay (perfect for Redis caching)")
    print("   - FAQ searches have 0.2s delay (also good for caching)")
    print("   - Both databases return realistic, structured data")
    print("   - Ready for Redis integration!")

if __name__ == "__main__":
    run_mock_data_tests()