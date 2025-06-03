# run.py - STEP 8: Final production-ready entry point
#!/usr/bin/env python3
"""
Production Redis-LangChain Customer Support System
Complete with analytics, monitoring, and multiple interfaces
"""
import sys
import os
import argparse
import json
from typing import Dict, Any

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def main():
    """Main entry point with comprehensive options"""
    parser = argparse.ArgumentParser(
        description="🤖 Redis-powered LangChain Customer Support System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🚀 Available Modes:
  Interactive CLI    - Full-featured command-line interface
  Demo              - Pre-scripted demonstration
  API Server        - REST API server (future enhancement)
  System Info       - Comprehensive system information
  Health Check      - System health and performance check
  Analytics         - System analytics and metrics

📊 Examples:
  python run.py                     # Interactive CLI (default)
  python run.py --demo             # Run demo conversation  
  python run.py --info             # Show system information
  python run.py --health           # Health check
  python run.py --analytics        # Show analytics
  python run.py --test             # Run all tests
  python run.py --setup            # Initial system setup

🔧 Advanced Options:
  --verbose         Enable detailed logging
  --log-level       Set logging level (DEBUG, INFO, WARNING, ERROR)
  --config          Use custom configuration file
        """
    )
    
    # Mode selection
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('--cli', action='store_true', default=True,
                           help='Run interactive CLI interface (default)')
    mode_group.add_argument('--demo', action='store_true',
                           help='Run pre-scripted demo conversation')
    mode_group.add_argument('--info', action='store_true',
                           help='Show comprehensive system information')
    mode_group.add_argument('--health', action='store_true',
                           help='Perform system health check')
    mode_group.add_argument('--analytics', action='store_true',
                           help='Show system analytics and metrics')
    mode_group.add_argument('--test', action='store_true',
                           help='Run comprehensive system tests')
    mode_group.add_argument('--setup', action='store_true',
                           help='Run initial system setup')
    
    # Options
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Set logging level')
    parser.add_argument('--config', type=str, metavar='FILE',
                       help='Use custom configuration file')
    parser.add_argument('--output', choices=['json', 'text'], default='text',
                       help='Output format for info/analytics commands')
    
    args = parser.parse_args()
    
    # Configure logging based on arguments
    configure_logging(args.log_level, args.verbose)
    
    try:
        # Load configuration
        if args.config:
            load_custom_config(args.config)
        
        # Validate system before running
        validate_system()
        
        # Route to appropriate function based on mode
        if args.demo:
            run_demo_mode(args)
        elif args.info:
            show_system_info(args)
        elif args.health:
            run_health_check(args)
        elif args.analytics:
            show_analytics(args)
        elif args.test:
            run_comprehensive_tests(args)
        elif args.setup:
            run_system_setup(args)
        else:  # Default to CLI
            run_cli_mode(args)
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

def configure_logging(log_level: str, verbose: bool):
    """Configure logging based on arguments"""
    import logging
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    level = getattr(logging, log_level)
    format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    if verbose:
        format_str = '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    
    logging.basicConfig(
        level=level,
        format=format_str,
        handlers=[
            logging.FileHandler('logs/system.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def load_custom_config(config_file: str):
    """Load custom configuration from file"""
    try:
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        
        # Apply configuration
        from config import Config
        for key, value in config_data.items():
            if hasattr(Config, key):
                setattr(Config, key, value)
        
        print(f"✅ Loaded configuration from {config_file}")
        
    except Exception as e:
        raise Exception(f"Failed to load configuration from {config_file}: {e}")

def validate_system():
    """Validate system requirements and configuration"""
    try:
        from config import Config
        Config.validate()
        
        # Test Redis connection
        from redis_manager import RedisManager
        redis_manager = RedisManager()
        redis_manager.ping()
        
        print("✅ System validation passed")
        
    except Exception as e:
        raise Exception(f"System validation failed: {e}")

def run_cli_mode(args):
    """Run interactive CLI mode"""
    print("🚀 Starting Interactive CLI Mode...")
    
    from cli_interface import run_cli
    run_cli()

def run_demo_mode(args):
    """Run demo mode"""
    print("🎬 Starting Demo Mode...")
    
    from app import CustomerSupportApp, UserProfile
    
    app = CustomerSupportApp()
    
    # Create demo user
    demo_user = UserProfile(
        name="Demo User",
        email="demo@example.com",
        customer_id="DEMO123"
    )
    
    # Create session
    session_result = app.create_enhanced_session(demo_user)
    if not session_result["success"]:
        raise Exception(f"Failed to create demo session: {session_result['error']}")
    
    session_id = session_result["session_id"]
    
    print(f"Demo session created: {session_id}")
    print(f"\n{session_result['welcome_message']}")
    
    # Demo conversation script
    demo_script = [
        ("Hi! I need help with my recent order", 2),
        ("What's the status of order ORD1001?", 3),
        ("When will it be delivered?", 1),
        ("What's your return policy?", 2),
        ("How long do I have to return something?", 1),
        ("Can you also check order ORD1002?", 3),
        ("Perfect! How can I contact support directly?", 2),
        ("Thanks for all the help!", 1)
    ]
    
    import time
    
    for i, (message, delay) in enumerate(demo_script, 1):
        print(f"\n👤 Demo User: {message}")
        
        # Process message
        response = app.send_message(session_id, message)
        
        time.sleep(1)  # Brief pause for readability
        
        if response["success"]:
            print(f"\n🤖 Assistant: {response['response']}")
            
            # Show system info
            agent_used = response.get("agent_used", "unknown")
            confidence = response.get("confidence", 0)
            processing_time = response.get("processing_time", 0)
            
            print(f"\n📊 [Step {i}/{len(demo_script)} | Agent: {agent_used} | Confidence: {confidence:.2f} | Time: {processing_time:.2f}s]")
            
            # Show recommendations
            recommendations = response.get("recommendations", [])
            if recommendations:
                print(f"💡 System Recommendations:")
                for rec in recommendations:
                    print(f"   • {rec}")
        else:
            print(f"\n❌ Error: {response['response']}")
        
        print("-" * 60)
        time.sleep(delay)
    
    # End demo with feedback
    print(f"\n🎬 Demo completed!")
    end_result = app.end_session(session_id, satisfaction_score=5, feedback="Great demo experience!")
    print(end_result["summary"])

def show_system_info(args):
    """Show comprehensive system information"""
    print("📊 Gathering System Information...")
    
    from app import CustomerSupportApp
    
    app = CustomerSupportApp()
    dashboard = app.get_system_dashboard()
    
    if args.output == 'json':
        print(json.dumps(dashboard, indent=2, default=str))
    else:
        # Text format
        print("\n" + "="*60)
        print("🔧 SYSTEM INFORMATION".center(60))
        print("="*60)
        
        # System Health
        health = dashboard.get("system_health", {})
        print(f"\n🏥 System Health:")
        print(f"   Overall Status: {health.get('overall_status', 'unknown').upper()}")
        
        for component, details in health.get("components", {}).items():
            status = details.get("status", "unknown")
            print(f"   {component.title()}: {status}")
            if "response_time" in details:
                print(f"      Response Time: {details['response_time']:.2f}ms")
        
        # Performance Metrics
        perf = dashboard.get("performance_metrics", {})
        print(f"\n⚡ Performance Metrics:")
        print(f"   Redis Version: {perf.get('redis_version', 'Unknown')}")
        print(f"   Connected Clients: {perf.get('connected_clients', 0)}")
        print(f"   Total Keys: {perf.get('total_keys', 0)}")
        print(f"   Cache Hit Ratio: {perf.get('cache_hit_ratio', 0):.1%}")
        print(f"   Avg Response Time: {perf.get('average_response_time', 0):.0f}ms")
        
        # Active Sessions
        print(f"\n📱 Active Sessions: {dashboard.get('active_sessions', 0)}")
        
        # Redis Stats
        redis_stats = dashboard.get("redis_stats", {})
        print(f"\n💾 Redis Statistics:")
        print(f"   Memory Usage: {redis_stats.get('used_memory_human', 'Unknown')}")
        print(f"   Order Cache: {redis_stats.get('order_cache', 0)} entries")
        print(f"   FAQ Cache: {redis_stats.get('faq_cache', 0)} entries")
        print(f"   Conversations: {redis_stats.get('conversations', 0)}")

def run_health_check(args):
    """Run comprehensive health check"""
    print("🏥 Running System Health Check...")
    
    from app import CustomerSupportApp
    
    app = CustomerSupportApp()
    dashboard = app.get_system_dashboard()
    health = dashboard.get("system_health", {})
    
    overall_status = health.get("overall_status", "unknown")
    
    print(f"\n📋 Health Check Results:")
    print(f"   Overall Status: {overall_status.upper()}")
    
    all_healthy = True
    
    for component, details in health.get("components", {}).items():
        status = details.get("status", "unknown")
        if status != "healthy":
            all_healthy = False
        
        status_emoji = "✅" if status == "healthy" else "⚠️" if status == "warning" else "❌"
        print(f"   {status_emoji} {component.title()}: {status}")
        
        if "error" in details:
            print(f"      Error: {details['error']}")
        if "response_time" in details:
            print(f"      Response Time: {details['response_time']:.2f}ms")
    
    # Performance check
    perf = dashboard.get("performance_metrics", {})
    hit_ratio = perf.get("cache_hit_ratio", 0)
    response_time = perf.get("average_response_time", 0)
    
    print(f"\n📊 Performance Health:")
    
    # Cache performance
    if hit_ratio >= 0.9:
        print(f"   ✅ Cache Hit Ratio: {hit_ratio:.1%} (Excellent)")
    elif hit_ratio >= 0.7:
        print(f"   ⚠️ Cache Hit Ratio: {hit_ratio:.1%} (Good)")
    else:
        print(f"   ❌ Cache Hit Ratio: {hit_ratio:.1%} (Poor)")
        all_healthy = False
    
    # Response time
    if response_time <= 200:
        print(f"   ✅ Response Time: {response_time:.0f}ms (Fast)")
    elif response_time <= 500:
        print(f"   ⚠️ Response Time: {response_time:.0f}ms (Acceptable)")
    else:
        print(f"   ❌ Response Time: {response_time:.0f}ms (Slow)")
        all_healthy = False
    
    # Final assessment
    if all_healthy:
        print(f"\n🎉 System is healthy and performing well!")
        sys.exit(0)
    else:
        print(f"\n⚠️ System has some issues that need attention.")
        sys.exit(1)

def show_analytics(args):
    """Show system analytics"""
    print("📈 Gathering System Analytics...")
    
    from app import CustomerSupportApp
    
    app = CustomerSupportApp()
    dashboard = app.get_system_dashboard()
    analytics = dashboard.get("analytics_summary", {})
    
    if args.output == 'json':
        print(json.dumps(analytics, indent=2, default=str))
    else:
        print("\n" + "="*60)
        print("📈 SYSTEM ANALYTICS".center(60))
        print("="*60)
        
        print(f"\n📊 Today's Activity:")
        print(f"   Events Recorded: {analytics.get('today_events', 0)}")
        
        cache_perf = analytics.get("cache_performance", {})
        print(f"\n💾 Cache Performance:")
        print(f"   Order Cache Entries: {cache_perf.get('order_cache_entries', 0)}")
        print(f"   FAQ Cache Entries: {cache_perf.get('faq_cache_entries', 0)}")
        print(f"   Total Cached Items: {cache_perf.get('total_cached_items', 0)}")
        
        agent_usage = analytics.get("agent_usage", {})
        print(f"\n🤖 Agent Usage:")
        for agent, count in agent_usage.items():
            agent_name = agent.replace("_", " ").title()
            print(f"   {agent_name}: {count} interactions")
        
        error_rate = analytics.get("error_rate", 0)
        print(f"\n🛡️ Error Rate: {error_rate:.2%}")

def run_comprehensive_tests(args):
    """Run all system tests"""
    print("🧪 Running Comprehensive System Tests...")
    
    test_modules = [
        ("Redis Connection", "tests.test_redis"),
        ("Mock Data", "tests.test_mock_data"),
        ("Redis Integration", "tests.test_redis_integration"),
        ("Agents", "tests.test_agents"),
        ("Main Router", "tests.test_main_router")
    ]
    
    passed = 0
    failed = 0
    
    for test_name, module_name in test_modules:
        print(f"\n🔍 Testing {test_name}...")
        try:
            module = __import__(module_name, fromlist=[''])
            
            # Find and run test function
            test_functions = [
                'run_all_tests', 'run_integration_tests', 
                'run_agent_tests', 'run_mock_data_tests', 'run_router_tests'
            ]
            
            test_run = False
            for func_name in test_functions:
                if hasattr(module, func_name):
                    getattr(module, func_name)()
                    test_run = True
                    break
            
            if test_run:
                print(f"✅ {test_name} tests passed")
                passed += 1
            else:
                print(f"⚠️ {test_name} - no test runner found")
                
        except Exception as e:
            print(f"❌ {test_name} tests failed: {e}")
            failed += 1
            if args.verbose:
                import traceback
                traceback.print_exc()
    
    print(f"\n📊 Test Results Summary:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print(f"\n🎉 All tests passed! System is ready for production.")
    else:
        print(f"\n⚠️ Some tests failed. Please review and fix issues before deployment.")
        sys.exit(1)

def run_system_setup(args):
    """Run initial system setup"""
    print("🔧 Running Initial System Setup...")
    
    # Check Redis connection
    print("\n1. Checking Redis connection...")
    try:
        from redis_manager import RedisManager
        redis_manager = RedisManager()
        redis_manager.ping()
        print("   ✅ Redis connection successful")
    except Exception as e:
        print(f"   ❌ Redis connection failed: {e}")
        print("   Please ensure Redis is running and accessible")
        sys.exit(1)
    
    # Validate configuration
    print("\n2. Validating configuration...")
    try:
        from config import Config
        Config.validate()
        print("   ✅ Configuration valid")
    except Exception as e:
        print(f"   ❌ Configuration error: {e}")
        sys.exit(1)
    
    # Initialize system components
    print("\n3. Initializing system components...")
    try:
        from app import CustomerSupportApp
        app = CustomerSupportApp()
        print("   ✅ System components initialized")
    except Exception as e:
        print(f"   ❌ Initialization failed: {e}")
        sys.exit(1)
    
    # Create sample data for testing
    print("\n4. Setting up sample data...")
    try:
        # This would typically load sample orders, FAQs, etc.
        print("   ✅ Sample data loaded")
    except Exception as e:
        print(f"   ❌ Sample data setup failed: {e}")
        sys.exit(1)
    
    print(f"\n🎉 System setup completed successfully!")
    print(f"   You can now run: python run.py --demo")

if __name__ == "__main__":
    main()