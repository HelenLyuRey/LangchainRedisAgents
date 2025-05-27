# verify_structure.py
import os

expected_structure = [
    '.env',
    'requirements.txt', 
    'run.py',
    'src/__init__.py',
    'src/config.py',
    'src/agents.py',
    'src/redis_manager.py', 
    'src/main.py',
    'data/orders.py',
    'data/faq.py',
    'tests/test_redis.py'
]

print("📁 Verifying project structure...")
for file_path in expected_structure:
    if os.path.exists(file_path):
        print(f"✅ {file_path}")
    else:
        print(f"❌ {file_path} - MISSING")

print("\n🧪 Running basic tests...")
os.system("python tests/test_redis_2.py")