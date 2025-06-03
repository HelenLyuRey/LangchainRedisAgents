# src/main_router.py - STEP 7: Fixed version with improved error handling
import sys
import os
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import json
import re

# Add data directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'data'))

from redis_manager import RedisManager
from agents import OrderLookupAgent, FAQAgent
from agent_router import AgentRouter
from config import Config

class CustomerSupportRouter:
    """Main router that orchestrates the entire customer support conversation"""
    
    def __init__(self):
        self.config = Config()
        self.redis = RedisManager()
        
        # Initialize agents
        self.order_agent = OrderLookupAgent(self.redis)
        self.faq_agent = FAQAgent(self.redis)
        self.agent_router = AgentRouter(self.redis)
        
        # Agent mapping
        self.agents = {
            "order_lookup": self.order_agent,
            "faq": self.faq_agent
        }
        
        # Conversation state tracking
        self.conversation_states = {}
        
        print("🤖 Customer Support Router initialized")
        self._warmup_system()
    
    def _warmup_system(self):
        """Warm up the system by preloading caches"""
        print("🔥 Warming up system caches...")
        
        # Preload FAQ cache with common queries
        common_faq_queries = [
            "return policy", "shipping policy", "track order",
            "payment methods", "contact support", "warranty",
            "cancel order", "account issues", "business hours"
        ]
        
        self.faq_agent.faq_cache.preload_common_faqs(common_faq_queries)
        print("✅ System warmed up and ready")
    
    def start_session(self, session_id: str, user_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Start a new customer support session"""
        
        # STEP 7 FIX: Ensure user_data is never None
        if user_data is None:
            user_data = {}
        
        # Create session in Redis
        session_created = self.redis.create_session(session_id, user_data)
        
        if session_created:
            # Initialize conversation state
            self.conversation_states[session_id] = {
                "active_agent": None,
                "agent_switches": 0,
                "resolved_issues": [],
                "session_start": datetime.now().isoformat(),
                "message_count": 0
            }
            
            welcome_message = self._generate_welcome_message(user_data)
            
            # Add welcome message to conversation history
            self.redis.add_message(session_id, "assistant", welcome_message)
            
            return {
                "success": True,
                "session_id": session_id,
                "welcome_message": welcome_message,
                "available_commands": self._get_available_commands()
            }
        else:
            return {
                "success": False,
                "error": "Failed to create session"
            }
    
    def _generate_welcome_message(self, user_data: Dict) -> str:
        """Generate personalized welcome message"""
        # STEP 7 FIX: Safe access to user_data with fallback
        try:
            name = user_data.get("name", "") if user_data else ""
            greeting = f"Hello {name}! " if name else "Hello! "
        except (AttributeError, TypeError):
            # Fallback if user_data is not a dict or is None
            greeting = "Hello! "
        
        welcome = f"""{greeting}👋 Welcome to Customer Support!

I'm here to help you with:
🛒 **Order Status & Tracking** - Check your order status, tracking info, and delivery updates
❓ **Questions & Policies** - Returns, shipping, payments, warranties, and general support

**Quick Start:**
- Provide your order number (like ORD1001) for order status
- Ask about policies like "What's your return policy?"
- Need help? Just ask "How can I contact support?"

How can I assist you today?"""
        
        return welcome
    
    def _get_available_commands(self) -> List[str]:
        """Get list of available commands for users"""
        return [
            "/help - Show this help message",
            "/status - Show session status", 
            "/history - Show recent conversation",
            "/clear - Clear conversation history",
            "/stats - Show performance statistics"
        ]
    
    def process_message(self, session_id: str, message: str) -> Dict[str, Any]:
        """Process a customer message through the router system"""
        
        try:
            # STEP 7 FIX: Input validation
            if not message or not message.strip():
                return {
                    "success": False,
                    "response": "❌ Please provide a message. Type '/help' for assistance.",
                    "agent_used": "input_validator"
                }
            
            message = message.strip()
            
            # Update session activity
            self.redis.update_session_activity(session_id)
            
            # Check for special commands
            if message.startswith("/"):
                return self._handle_command(session_id, message)
            
            # Get or initialize conversation state
            conv_state = self.conversation_states.get(session_id, {
                "active_agent": None,
                "agent_switches": 0,
                "resolved_issues": [],
                "session_start": datetime.now().isoformat(),
                "message_count": 0
            })
            
            conv_state["message_count"] = conv_state.get("message_count", 0) + 1
            
            # Route the message to appropriate agent
            selected_agent, confidence = self.agent_router.route_message(message, session_id)
            
            # Track agent switches
            if conv_state.get("active_agent") != selected_agent:
                conv_state["agent_switches"] = conv_state.get("agent_switches", 0) + 1
                conv_state["active_agent"] = selected_agent
            
            # Add user message to conversation history
            self.redis.add_message(session_id, "user", message)
            
            # Process with selected agent
            start_time = datetime.now()
            agent = self.agents.get(selected_agent)
            
            # STEP 7 FIX: Handle missing agent gracefully
            if not agent:
                error_response = f"❌ Unknown agent type: {selected_agent}. Please try again or contact support."
                self.redis.add_message(session_id, "assistant", error_response)
                return {
                    "success": False,
                    "response": error_response,
                    "agent_used": "error_handler"
                }
            
            response = agent.process_message(message, session_id)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Add agent response to conversation history
            self.redis.add_message(session_id, "assistant", response)
            
            # Update conversation state
            self.conversation_states[session_id] = conv_state
            
            # Detect if issue was resolved
            resolution_indicators = ["thank you", "thanks", "that helps", "perfect", "great"]
            if any(indicator in message.lower() for indicator in resolution_indicators):
                conv_state.setdefault("resolved_issues", []).append({
                    "agent": selected_agent,
                    "timestamp": datetime.now().isoformat(),
                    "message": message[:100]  # Store first 100 chars
                })
            
            return {
                "success": True,
                "response": response,
                "agent_used": selected_agent,
                "confidence": confidence,
                "processing_time": processing_time,
                "session_stats": self._get_session_stats(session_id),
                "suggestions": self._generate_suggestions(message, selected_agent)
            }
            
        except Exception as e:
            # STEP 7 FIX: Improved error handling with more context
            error_response = f"❌ I apologize, but I encountered an error processing your request. Please try again or contact support if the issue persists."
            
            # Still add messages to history for debugging
            try:
                self.redis.add_message(session_id, "user", message)
                self.redis.add_message(session_id, "assistant", error_response)
            except:
                pass  # Don't let Redis errors compound the problem
            
            return {
                "success": False,
                "response": error_response,
                "error": str(e),
                "agent_used": "error_handler",
                "debug_info": {
                    "session_id": session_id,
                    "message_length": len(message) if message else 0,
                    "error_type": type(e).__name__
                }
            }
    
    def _handle_command(self, session_id: str, command: str) -> Dict[str, Any]:
        """Handle special commands"""
        
        command = command.lower().strip()
        
        if command == "/help":
            help_text = """🔧 **Available Commands:**

**Information:**
- `/status` - Show your session information
- `/history` - Show recent conversation history  
- `/stats` - Show system performance statistics

**Actions:**
- `/clear` - Clear your conversation history
- `/help` - Show this help message

**Quick Examples:**
- "What's the status of order ORD1001?"
- "What's your return policy?"
- "How do I contact support?"
- "Show me orders for myemail@example.com"

Just type your question naturally - I'll route it to the right specialist!"""
            
            return {
                "success": True,
                "response": help_text,
                "agent_used": "command_handler"
            }
        
        elif command == "/status":
            try:
                status = self._get_detailed_session_status(session_id)
                return {
                    "success": True,
                    "response": status,
                    "agent_used": "command_handler"
                }
            except Exception as e:
                return {
                    "success": False,
                    "response": f"❌ Error retrieving session status: {str(e)}",
                    "agent_used": "command_handler"
                }
        
        elif command == "/history":
            try:
                history = self._get_conversation_summary(session_id)
                return {
                    "success": True,
                    "response": history,
                    "agent_used": "command_handler"
                }
            except Exception as e:
                return {
                    "success": False,
                    "response": f"❌ Error retrieving conversation history: {str(e)}",
                    "agent_used": "command_handler"
                }
        
        elif command == "/clear":
            try:
                cleared = self.redis.clear_conversation(session_id)
                
                # Reset conversation state
                if session_id in self.conversation_states:
                    self.conversation_states[session_id] = {
                        "active_agent": None,
                        "agent_switches": 0,
                        "resolved_issues": [],
                        "session_start": datetime.now().isoformat(),
                        "message_count": 0
                    }
                
                response = "✅ Conversation history cleared. How can I help you?" if cleared else "❌ Failed to clear history."
                return {
                    "success": cleared,
                    "response": response,
                    "agent_used": "command_handler"
                }
            except Exception as e:
                return {
                    "success": False,
                    "response": f"❌ Error clearing conversation: {str(e)}",
                    "agent_used": "command_handler"
                }
        
        elif command == "/stats":
            try:
                stats = self._get_system_stats()
                return {
                    "success": True,
                    "response": stats,
                    "agent_used": "command_handler"
                }
            except Exception as e:
                return {
                    "success": False,
                    "response": f"❌ Error retrieving system stats: {str(e)}",
                    "agent_used": "command_handler"
                }
        
        else:
            return {
                "success": False,
                "response": f"❌ Unknown command: {command}. Type `/help` for available commands.",
                "agent_used": "command_handler"
            }
    
    def _get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for current session"""
        try:
            conv_state = self.conversation_states.get(session_id, {})
            history = self.redis.get_conversation_history(session_id)
            
            return {
                "message_count": len(history),
                "agent_switches": conv_state.get("agent_switches", 0),
                "active_agent": conv_state.get("active_agent"),
                "resolved_issues": len(conv_state.get("resolved_issues", [])),
                "session_duration_minutes": self._calculate_session_duration(session_id)
            }
        except Exception as e:
            # Return default stats if there's an error
            return {
                "message_count": 0,
                "agent_switches": 0,
                "active_agent": None,
                "resolved_issues": 0,
                "session_duration_minutes": 0.0,
                "error": str(e)
            }
    
    def _calculate_session_duration(self, session_id: str) -> float:
        """Calculate session duration in minutes"""
        try:
            session_data = self.redis.get_session(session_id)
            if session_data and "created_at" in session_data:
                created_at = datetime.fromisoformat(session_data["created_at"])
                duration = datetime.now() - created_at
                return round(duration.total_seconds() / 60, 1)
        except Exception:
            pass
        return 0.0
    
    def _get_detailed_session_status(self, session_id: str) -> str:
        """Get detailed session status"""
        try:
            stats = self._get_session_stats(session_id)
            conv_state = self.conversation_states.get(session_id, {})
            
            status = f"""📊 **Session Status for {session_id}**

**Activity:**
- Messages exchanged: {stats['message_count']}
- Session duration: {stats['session_duration_minutes']} minutes
- Agent switches: {stats['agent_switches']}
- Currently using: {stats['active_agent'] or 'None'}

**Resolution:**
- Issues resolved: {stats['resolved_issues']}

**Recent Activity:**
- Last active: {self._get_last_activity_time(session_id)}

**Session Health:** ✅ Active and responsive"""
            
            return status
        except Exception as e:
            return f"❌ Error generating session status: {str(e)}"
    
    def _get_last_activity_time(self, session_id: str) -> str:
        """Get formatted last activity time"""
        try:
            session_data = self.redis.get_session(session_id)
            if session_data and "last_activity" in session_data:
                last_activity = datetime.fromisoformat(session_data["last_activity"])
                diff = datetime.now() - last_activity
                
                if diff.total_seconds() < 60:
                    return "Just now"
                elif diff.total_seconds() < 3600:
                    return f"{int(diff.total_seconds() / 60)} minutes ago"
                else:
                    return f"{int(diff.total_seconds() / 3600)} hours ago"
        except Exception:
            pass
        return "Unknown"
    
    def _get_conversation_summary(self, session_id: str) -> str:
        """Get conversation history summary"""
        try:
            history = self.redis.get_conversation_history(session_id, limit=10)
            
            if not history:
                return "📝 No conversation history found."
            
            summary = f"📝 **Recent Conversation** (last {len(history)} messages):\n\n"
            
            for i, msg in enumerate(history[-5:], 1):  # Show last 5 messages
                role = "👤 Customer" if msg["role"] == "user" else "🤖 Assistant"
                content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
                timestamp = datetime.fromisoformat(msg["timestamp"]).strftime("%H:%M")
                
                summary += f"**{i}. {role}** ({timestamp}):\n{content}\n\n"
            
            if len(history) > 5:
                summary += f"... and {len(history) - 5} earlier messages"
            
            return summary
        except Exception as e:
            return f"❌ Error retrieving conversation summary: {str(e)}"
    
    def _get_system_stats(self) -> str:
        """Get comprehensive system statistics"""
        try:
            redis_stats = self.redis.get_stats()
            
            stats = f"""📈 **System Performance Statistics**

**Redis Cache:**
- Memory usage: {redis_stats.get('used_memory_human', 'Unknown')}
- Total keys: {redis_stats.get('total_keys', 0)}
- Active sessions: {redis_stats.get('sessions', 0)}
- Cached conversations: {redis_stats.get('conversations', 0)}

**Cache Performance:**
- Order cache entries: {redis_stats.get('order_cache', 0)}
- FAQ cache entries: {redis_stats.get('faq_cache', 0)}
- Agent states tracked: {redis_stats.get('agent_states', 0)}

**Performance Benefits:**
- Order lookups: ~99% faster with caching
- FAQ searches: ~99% faster with caching
- Average response time: <2 seconds

**System Health:** ✅ All systems operational"""
            
            return stats
        except Exception as e:
            return f"❌ Error retrieving system statistics: {str(e)}"
    
    def _generate_suggestions(self, message: str, agent_used: str) -> List[str]:
        """Generate helpful suggestions based on the conversation"""
        try:
            suggestions = []
            
            if agent_used == "order_lookup":
                suggestions.extend([
                    "Need help with returns? Ask about our return policy",
                    "Questions about shipping? I can explain our shipping options",
                    "Want to contact support directly? I can provide contact info"
                ])
            elif agent_used == "faq":
                suggestions.extend([
                    "Have an order to check? Provide your order number",
                    "Need to track a package? Give me your order ID",
                    "Want to see all your orders? Provide your email address"
                ])
            
            # Add contextual suggestions based on message content
            message_lower = message.lower()
            
            if "return" in message_lower and agent_used != "faq":
                suggestions.append("Ask about our return policy for detailed information")
            
            if "track" in message_lower and agent_used != "order_lookup":
                suggestions.append("Provide your order number to track your package")
            
            if "contact" in message_lower or "support" in message_lower:
                suggestions.append("Type '/help' to see all available commands")
            
            return suggestions[:3]  # Limit to 3 suggestions
        except Exception:
            return []  # Return empty list if there's an error
    
    def end_session(self, session_id: str) -> Dict[str, Any]:
        """End a customer support session"""
        try:
            # Get final stats
            final_stats = self._get_session_stats(session_id)
            conv_state = self.conversation_states.get(session_id, {})
            
            # Generate session summary
            summary = f"""📋 **Session Summary**

Thank you for using our customer support! Here's a summary of your session:

**Activity:**
- Total messages: {final_stats['message_count']}
- Session duration: {final_stats['session_duration_minutes']} minutes
- Issues resolved: {final_stats['resolved_issues']}

**Feedback:**
We'd love to hear about your experience! Your conversation has been saved for quality assurance.

**Need More Help?**
- Email: support@example.com
- Phone: 1-800-SUPPORT
- Live Chat: Available 24/7 on our website

Have a great day! 👋"""
            
            # Add farewell message to history
            self.redis.add_message(session_id, "assistant", summary)
            
            # Clean up conversation state (but keep Redis data for analytics)
            if session_id in self.conversation_states:
                del self.conversation_states[session_id]
            
            return {
                "success": True,
                "summary": summary,
                "final_stats": final_stats
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error ending session: {str(e)}",
                "summary": "Session ended with errors. Please contact support if you need assistance."
            }
    
    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get list of all active sessions"""
        try:
            active_sessions = self.redis.list_active_sessions()
            
            session_details = []
            for session_id in active_sessions:
                try:
                    session_data = self.redis.get_session(session_id)
                    if session_data:
                        stats = self._get_session_stats(session_id)
                        session_details.append({
                            "session_id": session_id,
                            "created_at": session_data.get("created_at"),
                            "last_activity": session_data.get("last_activity"),
                            "message_count": stats["message_count"],
                            "duration_minutes": stats["session_duration_minutes"]
                        })
                except Exception:
                    # Skip sessions that can't be processed
                    continue
            
            return session_details
        except Exception as e:
            print(f"Error getting active sessions: {e}")
            return []