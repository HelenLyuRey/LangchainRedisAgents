# tests/test_redis_integration.py - STEP 5: New integration test file
import sys
import os
import time

# Add src and data to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'data'))

from redis_manager import RedisManager
from order_cache_manager import OrderCacheManager
from faq_cache_manager import FAQCacheManager
from orders import get_sample_order_ids

def test_order_caching_performance():
    """Test order caching performance improvements"""
    print("🛒 Testing Order Caching Performance...")
    
    redis_manager = RedisManager()
    order_cache = OrderCacheManager(redis_manager)
    
    # Get a sample order ID
    sample_ids = get_sample_order_ids(1)
    order_id = sample_ids[0]
    
    # Clear any existing cache for this order
    order_cache.invalidate_order(order_id)
    
    # Test 1: First fetch (cache miss)
    print(f"\n🔄 Test 1: First fetch of order {order_id} (should be cache miss)")
    start_time = time.time()
    order1 = order_cache.get_order(order_id)
    first_fetch_time = time.time() - start_time
    
    # Test 2: Second fetch (cache hit)
    print(f"\n🔄 Test 2: Second fetch of order {order_id} (should be cache hit)")
    start_time = time.time()
    order2 = order_cache.get_order(order_id)
    second_fetch_time = time.time() - start_time
    
    # Verify results
    assert order1 == order2
    assert first_fetch_time > second_fetch_time
    performance_improvement = (first_fetch_time - second_fetch_time) / first_fetch_time * 100
    
    print(f"\n📊 Performance Results:")
    print(f"   First fetch:  {first_fetch_time:.3f}s (cache miss)")
    print(f"   Second fetch: {second_fetch_time:.3f}s (cache hit)")
    print(f"   Improvement:  {performance_improvement:.1f}% faster!")
    
    return performance_improvement

def test_faq_caching_performance():
    """Test FAQ caching performance improvements - STEP 5 FIX: Better comparison logic"""
    print("\n❓ Testing FAQ Caching Performance...")
    
    redis_manager = RedisManager()
    faq_cache = FAQCacheManager(redis_manager)
    
    test_query = "return policy"
    
    # Clear any existing cache for this query
    normalized_query = test_query.lower().strip()
    cache_key = f"cache:faq_search:{hash(normalized_query)}"
    redis_manager.redis_client.delete(cache_key)
    
    # Test 1: First search (cache miss)
    print(f"\n🔄 Test 1: First search for '{test_query}' (should be cache miss)")
    start_time = time.time()
    results1 = faq_cache.search_faqs(test_query)
    first_search_time = time.time() - start_time
    
    # Test 2: Second search (cache hit)
    print(f"\n🔄 Test 2: Second search for '{test_query}' (should be cache hit)")
    start_time = time.time()
    results2 = faq_cache.search_faqs(test_query)
    second_search_time = time.time() - start_time
    
    # STEP 5 FIX: Better comparison - compare content rather than exact equality
    print(f"\nDEBUG - Results comparison:")
    print(f"Results1 type: {type(results1)}, length: {len(results1) if results1 else 0}")
    print(f"Results2 type: {type(results2)}, length: {len(results2) if results2 else 0}")
    
    if results1 and results2:
        print(f"First result1: {type(results1[0])}, content: {results1[0] if results1 else 'None'}")
        print(f"First result2: {type(results2[0])}, content: {results2[0] if results2 else 'None'}")
    
    # Verify results have same content (more flexible comparison)
    assert len(results1) == len(results2), f"Result lengths differ: {len(results1)} vs {len(results2)}"
    
    # Compare each result tuple/list content
    for i, (r1, r2) in enumerate(zip(results1, results2)):
        # Convert both to tuples for comparison
        r1_tuple = tuple(r1) if isinstance(r1, list) else r1
        r2_tuple = tuple(r2) if isinstance(r2, list) else r2
        
        assert r1_tuple == r2_tuple, f"Result {i} differs: {r1_tuple} vs {r2_tuple}"
    
    assert first_search_time > second_search_time
    performance_improvement = (first_search_time - second_search_time) / first_search_time * 100
    
    print(f"\n📊 Performance Results:")
    print(f"   First search:  {first_search_time:.3f}s (cache miss)")
    print(f"   Second search: {second_search_time:.3f}s (cache hit)")
    print(f"   Improvement:   {performance_improvement:.1f}% faster!")
    
    return performance_improvement

def test_cache_invalidation():
    """Test cache invalidation functionality"""
    print("\n🗑️  Testing Cache Invalidation...")
    
    redis_manager = RedisManager()
    order_cache = OrderCacheManager(redis_manager)
    
    # Get a sample order and cache it
    sample_ids = get_sample_order_ids(1)
    order_id = sample_ids[0]
    
    # Cache the order
    order_cache.get_order(order_id)
    order_cache.get_order_status_summary(order_id)
    
    # Verify it's cached
    cached_order = redis_manager.get_cached_order(order_id)
    cached_summary = redis_manager.get_cached_order_summary(order_id)
    
    assert cached_order is not None
    assert cached_summary is not None
    print(f"✅ Order {order_id} is cached")
    
    # Invalidate cache
    deleted_count = order_cache.invalidate_order(order_id)
    assert deleted_count > 0
    
    # Verify cache is cleared
    cached_order_after = redis_manager.get_cached_order(order_id)
    cached_summary_after = redis_manager.get_cached_order_summary(order_id)
    
    assert cached_order_after is None
    assert cached_summary_after is None
    print(f"✅ Order {order_id} cache invalidated")

def test_faq_preloading():
    """Test FAQ preloading functionality"""
    print("\n🔄 Testing FAQ Preloading...")
    
    redis_manager = RedisManager()
    faq_cache = FAQCacheManager(redis_manager)
    
    # Clear existing FAQ cache
    faq_keys = redis_manager.redis_client.keys("cache:faq_search:*")
    if faq_keys:
        redis_manager.redis_client.delete(*faq_keys)
    
    # Define common queries to preload
    common_queries = [
        "return policy",
        "shipping policy", 
        "track order",
        "payment methods",
        "contact support"
    ]
    
    # Preload FAQs
    preloaded_count = faq_cache.preload_common_faqs(common_queries)
    assert preloaded_count == len(common_queries)
    
    # Test that preloaded queries are now cached
    for query in common_queries:
        cached_results = redis_manager.get_cached_faq_search(query)
        assert cached_results is not None
        print(f"✅ '{query}' is preloaded in cache")

def test_faq_tuple_handling():
    """STEP 5 FIX: Specific test for FAQ tuple/list handling"""
    print("\n🔧 Testing FAQ Tuple/List Handling...")
    
    redis_manager = RedisManager()
    faq_cache = FAQCacheManager(redis_manager)
    
    test_query = "warranty information"
    
    # Clear cache
    normalized_query = test_query.lower().strip()
    cache_key = f"cache:faq_search:{hash(normalized_query)}"
    redis_manager.redis_client.delete(cache_key)
    
    # First search - should return tuples
    results1 = faq_cache.search_faqs(test_query)
    print(f"Direct search results type: {type(results1[0]) if results1 else 'None'}")
    
    # Second search - should return tuples from cache
    results2 = faq_cache.search_faqs(test_query)
    print(f"Cached search results type: {type(results2[0]) if results2 else 'None'}")
    
    # Both should be tuples
    if results1:
        assert isinstance(results1[0], tuple), f"First result should be tuple, got {type(results1[0])}"
    if results2:
        assert isinstance(results2[0], tuple), f"Second result should be tuple, got {type(results2[0])}"
    
    print("✅ FAQ tuple handling works correctly")

def test_redis_stats():
    """Test Redis statistics after all operations"""
    print("\n📊 Testing Redis Statistics...")
    
    redis_manager = RedisManager()
    order_cache = OrderCacheManager(redis_manager)
    faq_cache = FAQCacheManager(redis_manager)
    
    # Get comprehensive stats
    redis_stats = redis_manager.get_stats()
    order_stats = order_cache.get_cache_performance_stats()
    faq_stats = faq_cache.get_cache_performance_stats()
    
    print(f"\n📈 Redis Statistics:")
    print(f"   Total Keys: {redis_stats['total_keys']}")
    print(f"   Conversations: {redis_stats['conversations']}")
    print(f"   Sessions: {redis_stats['sessions']}")
    print(f"   Order Cache Entries: {redis_stats['order_cache']}")
    print(f"   FAQ Cache Entries: {redis_stats['faq_cache']}")
    print(f"   Memory Usage: {redis_stats['used_memory_human']}")
    
    print(f"\n⚡ Performance Benefits:")
    print(f"   Order Cache: {order_stats['cache_hit_benefit']}")
    print(f"   FAQ Cache: {faq_stats['cache_hit_benefit']}")

def run_integration_tests():
    """Run all integration tests"""
    print("🧪 Starting Fixed Redis Integration Tests...\n")
    
    try:
        order_perf = test_order_caching_performance()
        test_faq_tuple_handling()  # STEP 5 FIX: Test tuple handling first
        faq_perf = test_faq_caching_performance()
        test_cache_invalidation()
        test_faq_preloading()
        test_redis_stats()
        
        print(f"\n🎉 All integration tests passed!")
        print(f"\n💡 Key Results:")
        print(f"   Order lookups: {order_perf:.1f}% faster with Redis")
        print(f"   FAQ searches: {faq_perf:.1f}% faster with Redis")
        print(f"   Cache invalidation: ✅ Working")
        print(f"   FAQ preloading: ✅ Working")
        print(f"   Tuple/List handling: ✅ Fixed")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    run_integration_tests()