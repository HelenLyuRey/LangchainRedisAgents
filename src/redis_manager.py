# src/redis_manager.py
import redis
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from config import Config

class RedisManager:
    """Redis connection and operations manager for LangChain agents"""
    
    def __init__(self):
        self.config = Config()
        self.redis_client = None
        self._connect()
        
    def _connect(self):
        """Establish Redis connection with error handling"""
        try:
            self.redis_client = redis.Redis(
                host=self.config.REDIS_HOST,
                port=self.config.REDIS_PORT,
                db=self.config.REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # Test connection
            self.redis_client.ping()
            print(f"✅ Connected to Redis at {self.config.REDIS_HOST}:{self.config.REDIS_PORT}")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Redis: {e}")
    
    def ping(self) -> bool:
        """Test Redis connection"""
        try:
            return self.redis_client.ping()
        except Exception:
            return False
    
    # ========== Conversation History Methods ==========
    
    def get_conversation_key(self, session_id: str) -> str:
        """Generate Redis key for conversation history"""
        return f"conversation:{session_id}"
    
    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Add a message to conversation history"""
        key = self.get_conversation_key(session_id)
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add message to list
        self.redis_client.lpush(key, json.dumps(message))
        
        # Limit conversation length
        self.redis_client.ltrim(key, 0, self.config.MAX_CONVERSATION_LENGTH - 1)
        
        # Set TTL for session
        self.redis_client.expire(key, self.config.DEFAULT_SESSION_TTL)
    
    def get_conversation_history(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get conversation history for a session"""
        key = self.get_conversation_key(session_id)
        
        if limit:
            messages = self.redis_client.lrange(key, 0, limit - 1)
        else:
            messages = self.redis_client.lrange(key, 0, -1)
        
        # Parse and reverse (lpush stores in reverse order)
        parsed_messages = []
        for msg in reversed(messages):
            try:
                parsed_messages.append(json.loads(msg))
            except json.JSONDecodeError:
                continue
                
        return parsed_messages
    
    def clear_conversation(self, session_id: str) -> bool:
        """Clear conversation history for a session"""
        key = self.get_conversation_key(session_id)
        return bool(self.redis_client.delete(key))
    
    # ========== Caching Methods ==========
    
    def cache_set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Cache a value with TTL"""
        try:
            serialized_value = json.dumps(value) if not isinstance(value, str) else value
            return self.redis_client.setex(f"cache:{key}", ttl, serialized_value)
        except Exception as e:
            logging.error(f"Cache set error: {e}")
            return False
    
    def cache_get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        try:
            value = self.redis_client.get(f"cache:{key}")
            if value is None:
                return None
            
            # Try to parse as JSON, return as string if fails
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            logging.error(f"Cache get error: {e}")
            return None
    
    def cache_delete(self, key: str) -> bool:
        """Delete cached value"""
        return bool(self.redis_client.delete(f"cache:{key}"))
    
    # ========== STEP 5 : Domain-Specific Caching Methods ==========
    
    def cache_order(self, order_id: str, order_data: Dict, ttl: int = 1800) -> bool:
        """Cache order data with 30-minute TTL (orders don't change often)"""
        cache_key = f"order:{order_id}"
        cached_data = {
            "data": order_data,
            "cached_at": datetime.now().isoformat(),
            "cache_type": "order"
        }
        return self.cache_set(cache_key, cached_data, ttl)
    
    def get_cached_order(self, order_id: str) -> Optional[Dict]:
        """Get cached order data"""
        cache_key = f"order:{order_id}"
        cached_data = self.cache_get(cache_key)
        
        if cached_data and isinstance(cached_data, dict):
            return cached_data.get("data")
        return None
    
    def cache_faq_search(self, query: str, results: List[Tuple], ttl: int = 3600) -> bool:
        """Cache FAQ search results with 1-hour TTL - STEP 5 FIX: Handle tuple conversion"""
        # Normalize query for consistent caching
        normalized_query = query.lower().strip()
        cache_key = f"faq_search:{hash(normalized_query)}"
        
        # Convert tuples to lists for JSON serialization
        serializable_results = []
        for result in results:
            if isinstance(result, tuple):
                serializable_results.append(list(result))
            else:
                serializable_results.append(result)
        
        cached_data = {
            "query": query,
            "results": serializable_results,
            "cached_at": datetime.now().isoformat(),
            "cache_type": "faq_search"
        }
        return self.cache_set(cache_key, cached_data, ttl)
    
    def get_cached_faq_search(self, query: str) -> Optional[List[Tuple]]:
        """Get cached FAQ search results - STEP 5 FIX: Convert lists back to tuples"""
        normalized_query = query.lower().strip()
        cache_key = f"faq_search:{hash(normalized_query)}"
        cached_data = self.cache_get(cache_key)
        
        if cached_data and isinstance(cached_data, dict):
            results = cached_data.get("results")
            if results:
                # Convert lists back to tuples
                tuple_results = []
                for result in results:
                    if isinstance(result, list):
                        tuple_results.append(tuple(result))
                    else:
                        tuple_results.append(result)
                return tuple_results
        return None
    
    def cache_order_summary(self, order_id: str, summary: str, ttl: int = 1800) -> bool:
        """Cache order status summary"""
        cache_key = f"order_summary:{order_id}"
        cached_data = {
            "summary": summary,
            "cached_at": datetime.now().isoformat(),
            "cache_type": "order_summary"
        }
        return self.cache_set(cache_key, cached_data, ttl)
    
    def get_cached_order_summary(self, order_id: str) -> Optional[str]:
        """Get cached order status summary"""
        cache_key = f"order_summary:{order_id}"
        cached_data = self.cache_get(cache_key)
        
        if cached_data and isinstance(cached_data, dict):
            return cached_data.get("summary")
        return None
    
    def invalidate_order_cache(self, order_id: str) -> int:
        """Invalidate all cached data for an order (when order status changes)"""
        patterns = [
            f"cache:order:{order_id}",
            f"cache:order_summary:{order_id}"
        ]
        
        deleted_count = 0
        for pattern in patterns:
            if self.redis_client.delete(pattern):
                deleted_count += 1
                
        return deleted_count
    
    # ========== Session Management ==========
    
    def create_session(self, session_id: str, user_data: Dict[str, Any] = None) -> bool:
        """Create a new session"""
        session_key = f"session:{session_id}"
        session_data = {
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "user_data": user_data or {}
        }
        
        result = self.redis_client.setex(
            session_key, 
            self.config.DEFAULT_SESSION_TTL, 
            json.dumps(session_data)
        )
        
        if result:
            print(f"📱 Created session: {session_id}")
        return result
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        session_key = f"session:{session_id}"
        data = self.redis_client.get(session_key)
        
        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return None
        return None
    
    def update_session_activity(self, session_id: str) -> bool:
        """Update last activity timestamp"""
        session_data = self.get_session(session_id)
        if session_data:
            session_data["last_activity"] = datetime.now().isoformat()
            session_key = f"session:{session_id}"
            return self.redis_client.setex(
                session_key,
                self.config.DEFAULT_SESSION_TTL,
                json.dumps(session_data)
            )
        return False
    
    def list_active_sessions(self) -> List[str]:
        """List all active sessions"""
        session_keys = self.redis_client.keys("session:*")
        return [key.replace("session:", "") for key in session_keys]
    
    # ========== STEP 5: Agent State Management ==========
    
    def set_agent_state(self, session_id: str, agent_name: str, state_data: Dict, ttl: int = 3600) -> bool:
        """Store agent-specific state for a session"""
        state_key = f"agent_state:{session_id}:{agent_name}"
        state_with_metadata = {
            "agent": agent_name,
            "session_id": session_id,
            "state": state_data,
            "updated_at": datetime.now().isoformat()
        }
        return self.cache_set(state_key, state_with_metadata, ttl)
    
    def get_agent_state(self, session_id: str, agent_name: str) -> Optional[Dict]:
        """Get agent-specific state for a session"""
        state_key = f"agent_state:{session_id}:{agent_name}"
        cached_data = self.cache_get(state_key)
        
        if cached_data and isinstance(cached_data, dict):
            return cached_data.get("state")
        return None
    
    def clear_agent_state(self, session_id: str, agent_name: str = None) -> int:
        """Clear agent state(s) for a session"""
        if agent_name:
            # Clear specific agent state
            state_key = f"cache:agent_state:{session_id}:{agent_name}"
            return self.redis_client.delete(state_key)
        else:
            # Clear all agent states for session
            pattern = f"cache:agent_state:{session_id}:*"
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
    
    # ========== Utility Methods ==========
    
    def get_stats(self) -> Dict[str, Any]:
        """Get Redis usage statistics"""
        info = self.redis_client.info()
        
        # Count our specific key types
        conversation_count = len(self.redis_client.keys("conversation:*"))
        session_count = len(self.redis_client.keys("session:*"))
        cache_count = len(self.redis_client.keys("cache:*"))
        
        # STEP 5: Count domain-specific cache types
        order_cache_count = len(self.redis_client.keys("cache:order:*"))
        faq_cache_count = len(self.redis_client.keys("cache:faq_search:*"))
        agent_state_count = len(self.redis_client.keys("cache:agent_state:*"))
        
        return {
            "redis_version": info.get("redis_version"),
            "connected_clients": info.get("connected_clients"),
            "used_memory_human": info.get("used_memory_human"),
            "total_keys": info.get("db0", {}).get("keys", 0),
            "conversations": conversation_count,
            "sessions": session_count,
            "cached_items": cache_count,
            "order_cache": order_cache_count,
            "faq_cache": faq_cache_count,
            "agent_states": agent_state_count
        }
    
    def cleanup_expired(self) -> Dict[str, int]:
        """Clean up expired keys (manual cleanup)"""
        cleaned = {
            "conversations": 0,
            "sessions": 0,
            "cache": 0
        }
        
        # This is handled automatically by Redis TTL, but useful for monitoring
        for key_type in ["conversation", "session", "cache"]:
            keys = self.redis_client.keys(f"{key_type}:*")
            for key in keys:
                ttl = self.redis_client.ttl(key)
                if ttl == -1:  # No expiration set
                    self.redis_client.expire(key, self.config.DEFAULT_SESSION_TTL)
                    cleaned[key_type if key_type != "conversation" else "conversations"] += 1
        
        return cleaned