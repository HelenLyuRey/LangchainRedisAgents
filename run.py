# run.py
#!/usr/bin/env python3
"""
Entry point for the Redis-LangChain Agents Demo
"""
import sys
import os

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from main import CustomerSupportSystem
from config import Config

def main():
    try:
        # Validate configuration
        Config.validate()
        print("🚀 Starting Customer Support System...")
        
        # Initialize and run the system
        system = CustomerSupportSystem()
        system.run_interactive()
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()