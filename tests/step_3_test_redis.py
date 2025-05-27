# FOR STEP 3 TEST
# tests/test_redis.py
import pytest
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import Config
from redis_manager import RedisManager

def test_config_loading():
    """Test configuration loading"""
    assert Config.REDIS_HOST is not None
    assert Config.REDIS_PORT is not None
    print("✅ Configuration loaded successfully")

def test_redis_connection():
    """Test Redis connection"""
    try:
        redis_manager = RedisManager()
        result = redis_manager.ping()
        assert result is True
        print("✅ Redis connection test passed")
        return redis_manager
    except Exception as e:
        pytest.fail(f"Redis connection failed: {e}")

def test_conversation_operations():
    """Test conversation history operations"""
    redis_manager = RedisManager()
    session_id = "test_session_123"
    
    # Clear any existing conversation
    redis_manager.clear_conversation(session_id)
    
    # Add some messages
    redis_manager.add_message(session_id, "user", "Hello!")
    redis_manager.add_message(session_id, "assistant", "Hi there! How can I help?")
    redis_manager.add_message(session_id, "user", "What's my order status?")
    
    # Get conversation history
    history = redis_manager.get_conversation_history(session_id)
    
    assert len(history) == 3
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Hello!"
    assert history[-1]["content"] == "What's my order status?"
    
    print("✅ Conversation operations test passed")

def test_caching_operations():
    """Test caching functionality"""
    redis_manager = RedisManager()
    
    # Test string caching
    redis_manager.cache_set("test_key", "test_value", 60)
    cached_value = redis_manager.cache_get("test_key")
    assert cached_value == "test_value"
    
    # Test object caching
    test_data = {"order_id": "123", "status": "shipped"}
    redis_manager.cache_set("test_object", test_data, 60)
    cached_object = redis_manager.cache_get("test_object")
    assert cached_object == test_data
    
    print("✅ Caching operations test passed")

def test_session_management():
    """Test session management"""
    redis_manager = RedisManager()
    session_id = "test_session_456"
    
    # Create session
    user_data = {"user_id": "user123", "name": "John Doe"}
    redis_manager.create_session(session_id, user_data)
    
    # Get session
    session = redis_manager.get_session(session_id)
    assert session is not None
    assert session["user_data"]["name"] == "John Doe"
    
    # Update activity
    redis_manager.update_session_activity(session_id)
    
    print("✅ Session management test passed")

def test_redis_stats():
    """Test Redis statistics"""
    redis_manager = RedisManager()
    stats = redis_manager.get_stats()
    
    assert "redis_version" in stats
    assert "total_keys" in stats
    assert "conversations" in stats
    
    print("✅ Redis stats test passed")
    print(f"📊 Redis Stats: {stats}")

def run_all_tests():
    """Run all tests in sequence"""
    print("🧪 Starting Redis Manager Tests...\n")
    
    test_config_loading()
    test_redis_connection() 
    test_conversation_operations()
    test_caching_operations()
    test_session_management()
    test_redis_stats()
    
    print("\n🎉 All tests passed!")

if __name__ == "__main__":
    run_all_tests()