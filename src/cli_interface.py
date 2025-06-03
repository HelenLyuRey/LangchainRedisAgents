# src/cli_interface.py - STEP 8: Enhanced CLI interface
import sys
import os
from typing import Dict, Any, Optional
import json
from datetime import datetime

# Add src to path
sys.path.append(os.path.dirname(__file__))

from app import CustomerSupportApp, UserProfile, SessionStatus

class CLIInterface:
    """Enhanced CLI interface for the customer support system"""
    
    def __init__(self):
        self.app = CustomerSupportApp()
        self.current_session = None
        self.user_profile = None
        
        # CLI styling
        self.colors = {
            "GREEN": "\033[92m",
            "BLUE": "\033[94m", 
            "YELLOW": "\033[93m",
            "RED": "\033[91m",
            "PURPLE": "\033[95m",
            "CYAN": "\033[96m",
            "WHITE": "\033[97m",
            "BOLD": "\033[1m",
            "END": "\033[0m"
        }
    
    def colored(self, text: str, color: str) -> str:
        """Apply color to text"""
        return f"{self.colors.get(color, '')}{text}{self.colors['END']}"
    
    def print_header(self, title: str):
        """Print styled header"""
        border = "=" * 60
        print(f"\n{self.colored(border, 'BLUE')}")
        print(f"{self.colored(title.center(60), 'BOLD')}")
        print(f"{self.colored(border, 'BLUE')}\n")
    
    def print_section(self, title: str):
        """Print section divider"""
        print(f"\n{self.colored(f'--- {title} ---', 'CYAN')}")
    
    def get_user_input(self, prompt: str, required: bool = False) -> str:
        """Get user input with styling"""
        while True:
            user_input = input(f"{self.colored(prompt, 'YELLOW')} ").strip()
            if not required or user_input:
                return user_input
            print(f"{self.colored('This field is required. Please try again.', 'RED')}")
    
    def setup_user_profile(self) -> UserProfile:
        """Interactive user profile setup"""
        self.print_section("User Profile Setup")
        
        print("Let's set up your profile for a personalized experience.")
        print("(All fields are optional - press Enter to skip)")
        
        name = self.get_user_input("👤 Your name:")
        email = self.get_user_input("📧 Your email:")
        phone = self.get_user_input("📱 Your phone:")
        customer_id = self.get_user_input("🆔 Customer ID (if you have one):")
        
        profile = UserProfile(
            name=name or None,
            email=email or None,
            phone=phone or None,
            customer_id=customer_id or None
        )
        
        # Display profile summary
        print(f"\n{self.colored('✅ Profile created:', 'GREEN')}")
        if profile.name:
            print(f"   Name: {profile.name}")
        if profile.email:
            print(f"   Email: {profile.email}")
        if profile.customer_id:
            print(f"   Customer ID: {profile.customer_id}")
        
        return profile
    
    def start_session(self):
        """Start a new support session"""
        if not self.user_profile:
            self.user_profile = self.setup_user_profile()
        
        self.print_section("Starting Support Session")
        
        # Create session
        result = self.app.create_enhanced_session(
            self.user_profile,
            metadata={"interface": "cli", "version": "1.0.0"}
        )
        
        if result["success"]:
            self.current_session = result["session_id"]
            
            print(f"{self.colored('✅ Session started successfully!', 'GREEN')}")
            print(f"Session ID: {self.colored(self.current_session, 'BOLD')}")
            
            # Display welcome message
            print(f"\n{self.colored('🤖 Assistant:', 'BLUE')}")
            print(result["welcome_message"])
            
            return True
        else:
            print(f"{self.colored('❌ Failed to start session:', 'RED')} {result['error']}")
            return False
    
    def chat_loop(self):
        """Main chat interaction loop"""
        if not self.current_session:
            print(f"{self.colored('❌ No active session. Please start a session first.', 'RED')}")
            return
        
        print(f"\n{self.colored('💬 Chat started! Type your message or use these commands:', 'GREEN')}")
        print(f"   {self.colored('/help', 'CYAN')} - Show help")
        print(f"   {self.colored('/status', 'CYAN')} - Show session status")
        print(f"   {self.colored('/stats', 'CYAN')} - Show system stats")
        print(f"   {self.colored('/end', 'CYAN')} - End session")
        print(f"   {self.colored('quit/exit', 'CYAN')} - Exit application")
        
        while True:
            try:
                # Get user input
                message = self.get_user_input(f"\n{self.colored('👤 You:', 'PURPLE')}")
                
                if not message:
                    continue
                
                # Handle exit commands
                if message.lower() in ['quit', 'exit', 'bye', 'goodbye']:
                    self.end_session_interactive()
                    break
                
                # Handle custom CLI commands
                if message == '/end':
                    self.end_session_interactive()
                    break
                elif message == '/profile':
                    self.show_profile()
                    continue
                elif message == '/dashboard':
                    self.show_dashboard()
                    continue
                
                # Process message through app
                start_time = datetime.now()
                response = self.app.send_message(self.current_session, message)
                response_time = (datetime.now() - start_time).total_seconds()
                
                if response["success"]:
                    # Display assistant response
                    print(f"\n{self.colored('🤖 Assistant:', 'BLUE')}")
                    print(response["response"])
                    
                    # Show recommendations if available
                    recommendations = response.get("recommendations", [])
                    if recommendations:
                        print(f"\n{self.colored('💡 Suggestions:', 'CYAN')}")
                        for i, rec in enumerate(recommendations, 1):
                            print(f"   {i}. {rec}")
                    
                    # Show performance info
                    agent = response.get("agent_used", "unknown")
                    confidence = response.get("confidence", 0)
                    
                    print(f"\n{self.colored(f'📊 [Agent: {agent}, Confidence: {confidence:.2f}, Time: {response_time:.2f}s]', 'WHITE')}")
                    
                else:
                    print(f"\n{self.colored('❌ Error:', 'RED')} {response.get('error', 'Unknown error')}")
                
            except KeyboardInterrupt:
                print(f"\n{self.colored('Session interrupted. Type /end to properly end session.', 'YELLOW')}")
            except Exception as e:
                print(f"\n{self.colored(f'❌ Unexpected error: {e}', 'RED')}")
    
    def end_session_interactive(self):
        """Interactive session ending with feedback"""
        if not self.current_session:
            print(f"{self.colored('❌ No active session to end.', 'RED')}")
            return
        
        self.print_section("Session Feedback")
        
        # Get satisfaction rating
        print("How would you rate your support experience?")
        rating = None
        while not rating:
            try:
                rating_input = self.get_user_input("Rating (1-5 stars, or press Enter to skip):")
                if not rating_input:
                    break
                rating = int(rating_input)
                if 1 <= rating <= 5:
                    break
                else:
                    print(f"{self.colored('Please enter a number between 1 and 5.', 'RED')}")
                    rating = None
            except ValueError:
                print(f"{self.colored('Please enter a valid number.', 'RED')}")
                rating = None
        
        # Get feedback
        feedback = self.get_user_input("Any additional feedback? (optional):")
        
        # End session
        result = self.app.end_session(self.current_session, rating, feedback)
        
        if result["success"]:
            print(f"\n{self.colored('✅ Session ended successfully!', 'GREEN')}")
            print(result["summary"])
            
            # Show final stats
            stats = result.get("final_stats", {})
            print(f"\n{self.colored('📊 Final Statistics:', 'CYAN')}")
            print(f"   Duration: {stats.get('duration_minutes', 0)} minutes")
            print(f"   Messages: {stats.get('message_count', 0)}")
            if rating:
                print(f"   Your rating: {rating}/5 ⭐")
            
        else:
            print(f"{self.colored('❌ Error ending session:', 'RED')} {result.get('error')}")
        
        self.current_session = None
    
    def show_profile(self):
        """Show current user profile"""
        if self.user_profile:
            print(f"\n{self.colored('👤 Your Profile:', 'PURPLE')}")
            print(f"   Name: {self.user_profile.name or 'Not set'}")
            print(f"   Email: {self.user_profile.email or 'Not set'}")
            print(f"   Phone: {self.user_profile.phone or 'Not set'}")
            print(f"   Customer ID: {self.user_profile.customer_id or 'Not set'}")
        else:
            print(f"{self.colored('❌ No profile set up yet.', 'RED')}")
    
    def show_dashboard(self):
        """Show system dashboard"""
        print(f"\n{self.colored('📊 System Dashboard', 'PURPLE')}")
        
        try:
            dashboard = self.app.get_system_dashboard()
            
            # System health
            health = dashboard.get("system_health", {})
            status = health.get("overall_status", "unknown")
            status_color = "GREEN" if status == "healthy" else "YELLOW" if status == "degraded" else "RED"
            print(f"   System Status: {self.colored(status.upper(), status_color)}")
            
            # Performance metrics
            perf = dashboard.get("performance_metrics", {})
            print(f"   Active Sessions: {dashboard.get('active_sessions', 0)}")
            print(f"   Cache Hit Ratio: {perf.get('cache_hit_ratio', 0):.1%}")
            print(f"   Avg Response Time: {perf.get('average_response_time', 0):.0f}ms")
            
            # Redis stats
            redis_stats = dashboard.get("redis_stats", {})
            print(f"   Redis Memory: {redis_stats.get('used_memory_human', 'Unknown')}")
            print(f"   Total Keys: {redis_stats.get('total_keys', 0)}")
            
        except Exception as e:
            print(f"{self.colored(f'❌ Error loading dashboard: {e}', 'RED')}")
    
    def run_interactive(self):
        """Run the full interactive CLI experience"""
        self.print_header("🤖 Customer Support System")
        
        print(f"{self.colored('Welcome to our enhanced customer support system!', 'GREEN')}")
        print(f"This system uses Redis-powered AI agents to help you quickly and efficiently.")
        
        # Main menu
        while True:
            self.print_section("Main Menu")
            print("1. Start new support session")
            print("2. View system dashboard")
            print("3. Setup/update profile")
            print("4. Exit")
            
            choice = self.get_user_input("\nSelect option (1-4):")
            
            if choice == "1":
                if self.start_session():
                    self.chat_loop()
            elif choice == "2":
                self.show_dashboard()
            elif choice == "3":
                self.user_profile = self.setup_user_profile()
            elif choice == "4":
                print(f"\n{self.colored('👋 Thank you for using our support system!', 'GREEN')}")
                break
            else:
                print(f"{self.colored('❌ Invalid option. Please try again.', 'RED')}")

def run_cli():
    """Entry point for CLI interface"""
    cli = CLIInterface()
    cli.run_interactive()

if __name__ == "__main__":
    run_cli()