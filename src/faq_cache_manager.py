# src/faq_cache_manager.py - STEP 5: New file for FAQ caching
import sys
import os
from typing import Optional, Dict, List, Tuple
import time

# Add data directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'data'))

from redis_manager import RedisManager
from faq import search_faqs as db_search_faqs, get_best_faq_answer as db_get_best_faq_answer

class FAQCacheManager:
    """Manages FAQ data with Redis caching layer"""
    
    def __init__(self, redis_manager: RedisManager):
        self.redis = redis_manager
        
    def search_faqs(self, query: str, use_cache: bool = True) -> List[Tuple[str, Dict, float]]:
        """Search FAQs with Redis caching - STEP 5 FIX: Better type handling"""
        
        # Try cache first
        if use_cache:
            cached_results = self.redis.get_cached_faq_search(query)
            if cached_results:
                print(f"🚀 Cache HIT for FAQ search: '{query}'")
                # Ensure we return the correct type
                if cached_results and isinstance(cached_results[0], tuple):
                    return cached_results
                else:
                    print("⚠️  Cached results format issue, fetching fresh data")
        
        print(f"💾 Cache MISS for FAQ search: '{query}'")
        
        # Search in database
        start_time = time.time()
        results = db_search_faqs(query)
        search_time = time.time() - start_time
        
        print(f"📊 FAQ search took {search_time:.2f}s, found {len(results)} results")
        
        # Cache results - ensure we have tuples
        if use_cache and results:
            # Verify results are tuples before caching
            verified_results = []
            for result in results:
                if isinstance(result, tuple) and len(result) == 3:
                    verified_results.append(result)
                else:
                    print(f"⚠️  Skipping invalid result format: {type(result)}")
            
            if verified_results:
                self.redis.cache_faq_search(query, verified_results)
                print(f"💾 Cached {len(verified_results)} FAQ search results for: '{query}'")
            
            return verified_results
        
        return results
    
    def get_best_faq_answer(self, query: str, use_cache: bool = True) -> Optional[str]:
        """Get best FAQ answer with caching"""
        
        # Try to get from cached search first
        cached_results = self.search_faqs(query, use_cache)
        
        if cached_results:
            best_result = cached_results[0]
            answer = best_result[1]["answer"]
            
            print(f"📋 Returning best answer from {'cached' if use_cache else 'fresh'} search")
            
            return answer
        
        # Fallback to direct database call if no results
        return db_get_best_faq_answer(query)
    
    def get_faq_suggestions(self, query: str, max_suggestions: int = 3) -> List[str]:
        """Get FAQ suggestions based on search results"""
        
        results = self.search_faqs(query, use_cache=True)
        
        suggestions = []
        for faq_id, faq_data, score in results[:max_suggestions]:
            suggestions.append(faq_data["question"])
        
        return suggestions
    
    def preload_common_faqs(self, common_queries: List[str]) -> int:
        """Preload cache with common FAQ searches"""
        
        preloaded_count = 0
        
        print("🔄 Preloading common FAQ searches...")
        
        for query in common_queries:
            # Check if already cached
            if not self.redis.get_cached_faq_search(query):
                # Force a search to populate cache
                results = self.search_faqs(query, use_cache=True)
                if results:
                    preloaded_count += 1
                    print(f"   Preloaded: '{query}' ({len(results)} results)")
        
        print(f"✅ Preloaded {preloaded_count} FAQ searches")
        return preloaded_count
    
    def get_cache_performance_stats(self) -> Dict[str, any]:
        """Get FAQ cache performance statistics"""
        stats = self.redis.get_stats()
        return {
            "total_faq_cache_entries": stats.get("faq_cache", 0),
            "cache_hit_benefit": "~0.2s saved per FAQ search",
            "recommended_preload_queries": [
                "return policy",
                "shipping policy", 
                "track order",
                "payment methods",
                "contact support",
                "warranty",
                "cancel order"
            ]
        }