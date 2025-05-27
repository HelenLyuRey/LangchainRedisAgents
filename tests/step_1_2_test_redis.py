## FOR STEP 1 & 2 TEST

import redis
import os
from dotenv import load_dotenv

load_dotenv()

def test_redis_connection():
    try:
        # Connect to Redis
        r = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=int(os.getenv('REDIS_DB', 0)),
            decode_responses=True
        )
        
        # Test connection
        r.ping()
        print("✅ Redis connection successful!")
        
        # Test basic operations
        r.set('test_key', 'Hello Redis!')
        value = r.get('test_key')
        print(f"✅ Redis read/write test: {value}")
        
        # Cleanup
        r.delete('test_key')
        print("✅ Setup complete!")
        
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")

if __name__ == "__main__":
    test_redis_connection()