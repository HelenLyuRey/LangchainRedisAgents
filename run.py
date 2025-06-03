# run.py - STEP 7: Updated entry point with new router capabilities
#!/usr/bin/env python3
"""
Entry point for the Redis-LangChain Agents Demo
Enhanced with comprehensive routing and session management
"""
import sys
import os
import argparse

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from main import CustomerSupportSystem, run_interactive, run_demo, show_system_info
from config import Config

def main():
    parser = argparse.ArgumentParser(
        description="Redis-powered LangChain Customer Support System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py                    # Interactive mode
  python run.py --demo            # Run demo conversation
  python run.py --info            # Show system information
  python run.py --test            # Run system tests
        """
    )
    
    parser.add_argument('--demo', action='store_true',
                       help='Run a pre-scripted demo conversation')
    parser.add_argument('--info', action='store_true',
                       help='Show system information and statistics')
    parser.add_argument('--test', action='store_true',
                       help='Run comprehensive system tests')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    try:
        # Validate configuration
        Config.validate()
        
        if args.demo:
            print("🎬 Starting Demo Mode...")
            run_demo()
        elif args.info:
            print("📊 System Information:")
            show_system_info()
        elif args.test:
            print("🧪 Running System Tests...")
            run_system_tests()
        else:
            print("🚀 Starting Interactive Mode...")
            run_interactive()
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

def run_system_tests():
    """Run comprehensive system tests"""
    print("Running comprehensive system tests...\n")
    
    # Import and run all test modules
    test_modules = [
        "tests.test_redis",
        "tests.test_mock_data", 
        "tests.test_redis_integration",
        "tests.test_agents"
    ]
    
    for module_name in test_modules:
        try:
            print(f"🧪 Testing {module_name}...")
            module = __import__(module_name, fromlist=[''])
            
            # Look for main test function
            if hasattr(module, 'run_all_tests'):
                module.run_all_tests()
            elif hasattr(module, 'run_integration_tests'):
                module.run_integration_tests()
            elif hasattr(module, 'run_agent_tests'):
                module.run_agent_tests()
            elif hasattr(module, 'run_mock_data_tests'):
                module.run_mock_data_tests()
            else:
                print(f"   No test runner found in {module_name}")
            
            print(f"✅ {module_name} tests passed\n")
            
        except Exception as e:
            print(f"❌ {module_name} tests failed: {e}\n")
    
    print("🎉 All system tests completed!")

if __name__ == "__main__":
    main()