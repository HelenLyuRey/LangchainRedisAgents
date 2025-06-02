# src/order_cache_manager.py - STEP 5: New file for order caching
import sys
import os
from typing import Optional, Dict, List
import time

# Add data directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'data'))

from redis_manager import RedisManager
from orders import get_order as db_get_order, get_order_status_summary as db_get_order_summary, search_orders_by_email as db_search_orders_by_email

class OrderCacheManager:
    """Manages order data with Redis caching layer"""
    
    def __init__(self, redis_manager: RedisManager):
        self.redis = redis_manager
        
    def get_order(self, order_id: str, use_cache: bool = True) -> Optional[Dict]:
        """Get order with Redis caching"""
        
        # Try cache first if enabled
        if use_cache:
            cached_order = self.redis.get_cached_order(order_id)
            if cached_order:
                print(f"🚀 Cache HIT for order {order_id}")
                return cached_order
        
        print(f"💾 Cache MISS for order {order_id} - fetching from database...")
        
        # Fetch from "database" (our mock data)
        start_time = time.time()
        order_data = db_get_order(order_id)
        fetch_time = time.time() - start_time
        
        print(f"📊 Database fetch took {fetch_time:.2f}s")
        
        # Cache the result if found
        if order_data and use_cache:
            self.redis.cache_order(order_id, order_data)
            print(f"💾 Cached order {order_id}")
        
        return order_data
    
    def get_order_status_summary(self, order_id: str, use_cache: bool = True) -> Optional[str]:
        """Get order status summary with caching"""
        
        # Try cache first
        if use_cache:
            cached_summary = self.redis.get_cached_order_summary(order_id)
            if cached_summary:
                print(f"🚀 Cache HIT for order summary {order_id}")
                return cached_summary
        
        print(f"💾 Cache MISS for order summary {order_id}")
        
        # Generate summary (this involves getting the order first)
        order_data = self.get_order(order_id, use_cache)
        if not order_data:
            return None
        
        # Get summary from database function (includes its own delay)
        start_time = time.time()
        summary = db_get_order_summary(order_id)
        fetch_time = time.time() - start_time
        
        print(f"📊 Summary generation took {fetch_time:.2f}s")
        
        # Cache the summary
        if summary and use_cache:
            self.redis.cache_order_summary(order_id, summary)
            print(f"💾 Cached order summary {order_id}")
        
        return summary
    
    def search_orders_by_email(self, email: str, use_cache: bool = True) -> List[Dict]:
        """Search orders by email with caching"""
        
        # Create cache key for email searches
        cache_key = f"email_search:{email.lower()}"
        
        if use_cache:
            cached_results = self.redis.cache_get(cache_key)
            if cached_results:
                print(f"🚀 Cache HIT for email search: {email}")
                return cached_results
        
        print(f"💾 Cache MISS for email search: {email}")
        
        # Search in database
        start_time = time.time()
        results = db_search_orders_by_email(email)
        search_time = time.time() - start_time
        
        print(f"📊 Email search took {search_time:.2f}s, found {len(results)} orders")
        
        # Cache results (shorter TTL for searches)
        if use_cache:
            self.redis.cache_set(cache_key, results, ttl=600)  # 10 minutes
            print(f"💾 Cached email search results for {email}")
        
        return results
    
    def invalidate_order(self, order_id: str) -> int:
        """Invalidate all cached data for an order"""
        deleted_count = self.redis.invalidate_order_cache(order_id)
        if deleted_count > 0:
            print(f"🗑️  Invalidated {deleted_count} cache entries for order {order_id}")
        return deleted_count
    
    def get_cache_performance_stats(self) -> Dict[str, any]:
        """Get performance statistics"""
        stats = self.redis.get_stats()
        return {
            "total_order_cache_entries": stats.get("order_cache", 0),
            "redis_memory_usage": stats.get("used_memory_human", "Unknown"),
            "cache_hit_benefit": "~0.5s saved per order lookup",
            "summary_cache_benefit": "~0.5s saved per summary generation"
        }