# src/main.py - STEP 7: Updated main application with new router
import sys
import os
from typing import Dict, Any, Optional
import uuid
from datetime import datetime

# Add src to path
sys.path.append(os.path.dirname(__file__))

from main_router import CustomerSupportRouter
from config import Config

class CustomerSupportSystem:
    """Main application class that manages the customer support system"""
    
    def __init__(self):
        self.config = Config()
        self.router = CustomerSupportRouter()
        self.current_session = None
        
    def create_session(self, user_data: Dict = None) -> str:
        """Create a new customer support session"""
        session_id = f"session_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}"
        
        result = self.router.start_session(session_id, user_data)
        
        if result["success"]:
            self.current_session = session_id
            return session_id
        else:
            raise Exception(f"Failed to create session: {result.get('error')}")
    
    def chat(self, message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Send a message and get response"""
        if not session_id:
            session_id = self.current_session
            
        if not session_id:
            raise Exception("No active session. Create a session first.")
        
        return self.router.process_message(session_id, message)
    
    def end_session(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """End the current session"""
        if not session_id:
            session_id = self.current_session
            
        if not session_id:
            raise Exception("No active session to end.")
        
        result = self.router.end_session(session_id)
        
        if session_id == self.current_session:
            self.current_session = None
            
        return result
    
    def run_interactive(self):
        """Run interactive chat session"""
        print("🤖 Customer Support System Starting...")
        print("="*60)
        
        try:
            # Validate configuration
            self.config.validate()
            
            # Get user information
            print("👋 Welcome! Let's get started.")
            name = input("Your name (optional): ").strip() or None
            email = input("Your email (optional): ").strip() or None
            
            user_data = {}
            if name:
                user_data["name"] = name
            if email:
                user_data["email"] = email
            
            # Create session
            session_id = self.create_session(user_data)
            session_result = self.router.start_session(session_id, user_data)
            
            print("\n" + "="*60)
            print(session_result["welcome_message"])
            print("\n💡 Type '/help' for commands, or just ask your question!")
            print("💡 Type 'quit' or 'exit' to end the session")
            print("="*60)
            
            # Main chat loop
            while True:
                try:
                    user_input = input("\n👤 You: ").strip()
                    
                    if not user_input:
                        continue
                    
                    if user_input.lower() in ['quit', 'exit', 'bye', 'goodbye']:
                        print("\n🤖 Ending session...")
                        end_result = self.end_session(session_id)
                        print(end_result["summary"])
                        break
                    
                    # Process message
                    response = self.chat(user_input, session_id)
                    
                    if response["success"]:
                        print(f"\n🤖 Assistant: {response['response']}")
                        
                        # Show additional info in verbose mode
                        if response.get("suggestions"):
                            print(f"\n💡 Suggestions:")
                            for suggestion in response["suggestions"]:
                                print(f"   • {suggestion}")
                        
                        # Show performance info
                        agent_used = response.get("agent_used", "unknown")
                        processing_time = response.get("processing_time", 0)
                        print(f"\n📊 [Agent: {agent_used}, Time: {processing_time:.2f}s]")
                        
                    else:
                        print(f"\n❌ Error: {response['response']}")
                
                except KeyboardInterrupt:
                    print("\n\n👋 Session interrupted. Goodbye!")
                    break
                except Exception as e:
                    print(f"\n❌ Unexpected error: {e}")
                    break
        
        except Exception as e:
            print(f"❌ Failed to start system: {e}")
    
    def run_demo_conversation(self):
        """Run a pre-scripted demo conversation"""
        print("🎬 Running Demo Conversation...")
        print("="*60)
        
        # Create demo session
        demo_user = {
            "name": "Demo User",
            "email": "demo@example.com"
        }
        
        session_id = self.create_session(demo_user)
        session_result = self.router.start_session(session_id, demo_user)
        
        print(session_result["welcome_message"])
        
        # Demo conversation script
        demo_script = [
            ("Hi there! I have a question about my recent order", 2),
            ("What's the status of order ORD1001?", 3),
            ("Great! When will it be delivered?", 1),
            ("What's your return policy?", 2), 
            ("How long do I have to return an item?", 1),
            ("Can you also check order ORD1002?", 3),
            ("Perfect! How can I contact support if I need help?", 2),
            ("Thanks for all the help!", 1)
        ]
        
        import time
        
        for message, delay in demo_script:
            print(f"\n👤 Demo User: {message}")
            
            # Process message
            response = self.chat(message, session_id)
            
            time.sleep(1)  # Brief pause for readability
            
            if response["success"]:
                print(f"\n🤖 Assistant: {response['response']}")
                
                # Show system info
                agent_used = response.get("agent_used", "unknown")
                confidence = response.get("confidence", 0)
                processing_time = response.get("processing_time", 0)
                
                print(f"\n📊 [Agent: {agent_used}, Confidence: {confidence:.2f}, Time: {processing_time:.2f}s]")
            else:
                print(f"\n❌ Error: {response['response']}")
            
            print("-" * 40)
            time.sleep(delay)
        
        # End demo
        print(f"\n🎬 Demo completed!")
        end_result = self.end_session(session_id)
        print(end_result["summary"])
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        return {
            "config": {
                "redis_host": self.config.REDIS_HOST,
                "redis_port": self.config.REDIS_PORT,
                "session_ttl": self.config.DEFAULT_SESSION_TTL
            },
            "active_sessions": self.router.get_active_sessions(),
            "redis_stats": self.router.redis.get_stats()
        }

# Entry point functions for different modes
def run_interactive():
    """Run interactive mode"""
    system = CustomerSupportSystem()
    system.run_interactive()

def run_demo():
    """Run demo mode"""
    system = CustomerSupportSystem()
    system.run_demo_conversation()

def show_system_info():
    """Show system information"""
    system = CustomerSupportSystem()
    info = system.get_system_info()
    
    print("🔧 System Information:")
    print(f"Redis: {info['config']['redis_host']}:{info['config']['redis_port']}")
    print(f"Active Sessions: {len(info['active_sessions'])}")
    print(f"Total Redis Keys: {info['redis_stats'].get('total_keys', 0)}")
    print(f"Memory Usage: {info['redis_stats'].get('used_memory_human', 'Unknown')}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode == "demo":
            run_demo()
        elif mode == "info":
            show_system_info()
        else:
            print("Usage: python main.py [demo|info]")
            print("Default: interactive mode")
            run_interactive()
    else:
        run_interactive()