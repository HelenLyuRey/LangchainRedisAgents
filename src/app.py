# src/app.py - STEP 8: Production-ready main application
import sys
import os
import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import uuid
from dataclasses import dataclass
from enum import Enum

# Add src to path
sys.path.append(os.path.dirname(__file__))

from main_router import CustomerSupportRouter
from config import Config
from redis_manager import RedisManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/customer_support.log'),
        logging.StreamHandler()
    ]
)

class SessionStatus(Enum):
    """Session status enumeration"""
    ACTIVE = "active"
    IDLE = "idle"
    ENDED = "ended"
    ERROR = "error"

@dataclass
class UserProfile:
    """User profile data structure"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    customer_id: Optional[str] = None
    preferred_language: str = "en"
    timezone: str = "UTC"

class CustomerSupportApp:
    """Enhanced production-ready customer support application"""
    
    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        
        # Initialize core components
        self.router = CustomerSupportRouter()
        self.redis = self.router.redis
        
        # Application state
        self.sessions = {}
        self.analytics = AnalyticsManager(self.redis)
        self.monitor = SystemMonitor(self.redis)
        
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        self.logger.info("Customer Support App initialized")
        
    def create_enhanced_session(self, user_profile: UserProfile, metadata: Dict = None) -> Dict[str, Any]:
        """Create an enhanced session with full user profile and metadata"""
        
        session_id = self._generate_session_id()
        
        # Prepare enhanced user data
        user_data = {
            "name": user_profile.name,
            "email": user_profile.email,
            "phone": user_profile.phone,
            "customer_id": user_profile.customer_id,
            "preferred_language": user_profile.preferred_language,
            "timezone": user_profile.timezone,
            "session_metadata": metadata or {},
            "created_via": "customer_support_app",
            "app_version": "1.0.0"
        }
        
        try:
            # Create session through router
            result = self.router.start_session(session_id, user_data)
            
            if result["success"]:
                # Track session in app state
                self.sessions[session_id] = {
                    "status": SessionStatus.ACTIVE,
                    "user_profile": user_profile,
                    "created_at": datetime.now(),
                    "last_activity": datetime.now(),
                    "message_count": 0,
                    "agent_usage": {},
                    "satisfaction_score": None
                }
                
                # Log session creation
                self.logger.info(f"Session created: {session_id} for user: {user_profile.email or 'anonymous'}")
                
                # Track analytics
                self.analytics.track_session_created(session_id, user_data)
                
                return {
                    "success": True,
                    "session_id": session_id,
                    "welcome_message": result["welcome_message"],
                    "user_profile": user_profile,
                    "session_info": self._get_session_info(session_id)
                }
            else:
                self.logger.error(f"❌ Failed to create session: {result.get('error')}")
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error")
                }
                
        except Exception as e:
            self.logger.error(f"❌ Exception creating session: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID"""
        timestamp = int(datetime.now().timestamp())
        unique_id = uuid.uuid4().hex[:8]
        return f"session_{timestamp}_{unique_id}"
    
    def send_message(self, session_id: str, message: str, message_type: str = "user") -> Dict[str, Any]:
        """Send a message with enhanced tracking and analytics"""
        
        if session_id not in self.sessions:
            return {
                "success": False,
                "error": "Session not found"
            }
        
        try:
            # Update session activity
            self.sessions[session_id]["last_activity"] = datetime.now()
            self.sessions[session_id]["message_count"] += 1
            
            # Process message through router
            start_time = datetime.now()
            result = self.router.process_message(session_id, message)
            processing_duration = (datetime.now() - start_time).total_seconds()
            
            if result["success"]:
                # Track agent usage
                agent_used = result.get("agent_used", "unknown")
                if agent_used in self.sessions[session_id]["agent_usage"]:
                    self.sessions[session_id]["agent_usage"][agent_used] += 1
                else:
                    self.sessions[session_id]["agent_usage"][agent_used] = 1
                
                # Enhanced response with app-level metadata
                enhanced_response = {
                    **result,
                    "session_id": session_id,
                    "message_id": self._generate_message_id(),
                    "timestamp": datetime.now().isoformat(),
                    "processing_duration": processing_duration,
                    "session_stats": self._get_session_stats(session_id),
                    "recommendations": self._generate_smart_recommendations(session_id, message, result)
                }
                
                # Track analytics
                self.analytics.track_message_processed(
                    session_id, message, result, processing_duration
                )
                
                # Log successful interaction
                self.logger.info(
                    f"Message processed - Session: {session_id}, "
                    f"Agent: {agent_used}, Time: {processing_duration:.2f}s"
                )
                
                return enhanced_response
            else:
                # Handle and log errors
                self.logger.error(f"❌ Message processing failed - Session: {session_id}, Error: {result.get('error')}")
                self.analytics.track_error(session_id, message, result.get("error"))
                
                return result
                
        except Exception as e:
            self.logger.error(f"❌ Exception processing message - Session: {session_id}, Error: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id
            }
    
    def _generate_message_id(self) -> str:
        """Generate unique message ID"""
        return f"msg_{uuid.uuid4().hex[:12]}"
    
    def _get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get enhanced session statistics"""
        if session_id not in self.sessions:
            return {}
        
        session = self.sessions[session_id]
        duration = (datetime.now() - session["created_at"]).total_seconds() / 60
        
        return {
            "duration_minutes": round(duration, 1),
            "message_count": session["message_count"],
            "agent_usage": session["agent_usage"],
            "status": session["status"].value,
            "satisfaction_score": session["satisfaction_score"]
        }
    
    def _generate_smart_recommendations(self, session_id: str, message: str, result: Dict) -> List[str]:
        """Generate smart recommendations based on conversation context"""
        
        recommendations = []
        agent_used = result.get("agent_used", "")
        session = self.sessions.get(session_id, {})
        
        # Contextual recommendations based on agent and conversation
        if agent_used == "order_lookup":
            if "delivered" in result.get("response", "").lower():
                recommendations.append("Need to return an item? Ask about our return policy")
            if "shipped" in result.get("response", "").lower():
                recommendations.append("Want delivery updates? I can explain our tracking system")
        
        elif agent_used == "faq":
            if "return" in message.lower():
                recommendations.append("Have a specific order to return? Provide your order number")
            if "contact" in message.lower():
                recommendations.append("Need immediate help? Try our live chat for instant support")
        
        # Session-based recommendations
        if session.get("message_count", 0) > 5 and not session.get("satisfaction_score"):
            recommendations.append("How are we doing? Let us know if you need anything else!")
        
        # Time-based recommendations
        if session.get("message_count", 0) > 10:
            recommendations.append("Consider bookmarking our FAQ page for quick future reference")
        
        return recommendations[:2]  # Limit to 2 recommendations
    
    def end_session(self, session_id: str, satisfaction_score: Optional[int] = None, feedback: str = "") -> Dict[str, Any]:
        """End session with enhanced analytics and feedback collection"""
        
        if session_id not in self.sessions:
            return {
                "success": False,
                "error": "Session not found"
            }
        
        try:
            # Update session with feedback
            if satisfaction_score:
                self.sessions[session_id]["satisfaction_score"] = satisfaction_score
            
            self.sessions[session_id]["status"] = SessionStatus.ENDED
            self.sessions[session_id]["feedback"] = feedback
            self.sessions[session_id]["ended_at"] = datetime.now()
            
            # Get final stats
            final_stats = self._get_session_stats(session_id)
            
            # End session through router
            result = self.router.end_session(session_id)
            
            if result["success"]:
                # Enhanced session summary
                session_summary = self._generate_session_summary(session_id, final_stats)
                
                # Track analytics
                self.analytics.track_session_ended(session_id, final_stats, satisfaction_score, feedback)
                
                # Log session end
                self.logger.info(f"📱 Session ended: {session_id}, Duration: {final_stats['duration_minutes']}min, Score: {satisfaction_score}")
                
                return {
                    "success": True,
                    "session_id": session_id,
                    "summary": session_summary,
                    "final_stats": final_stats,
                    "satisfaction_score": satisfaction_score
                }
            else:
                return result
                
        except Exception as e:
            self.logger.error(f"❌ Exception ending session {session_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_session_summary(self, session_id: str, stats: Dict) -> str:
        """Generate comprehensive session summary"""
        session = self.sessions[session_id]
        user_name = session["user_profile"].name or "Valued Customer"
        
        summary = f"""📋 **Session Complete - Thank You {user_name}!**

**Your Support Session Summary:**
- Duration: {stats['duration_minutes']} minutes
- Messages exchanged: {stats['message_count']}
- Specialists consulted: {len(stats['agent_usage'])}

**What We Helped With:**"""
        
        # Add agent usage details
        for agent, count in stats["agent_usage"].items():
            agent_name = agent.replace("_", " ").title()
            summary += f"\n• {agent_name}: {count} interactions"
        
        if stats.get("satisfaction_score"):
            summary += f"\n\n**Your Rating:** {stats['satisfaction_score']}/5 ⭐"
            if stats["satisfaction_score"] >= 4:
                summary += " - Thank you for the excellent rating!"
            else:
                summary += " - We appreciate your feedback and will work to improve."
        
        summary += """

**Stay Connected:**
- Email: support@example.com
- Phone: 1-800-SUPPORT (Mon-Fri, 9AM-6PM EST)
- Live Chat: 24/7 on our website
- Help Center: support.example.com

**Your conversation has been saved for quality assurance.**

Thank you for choosing our support! 🙏"""
        
        return summary
    
    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive session information"""
        return self._get_session_info(session_id)
    
    def _get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Internal method to get session info"""
        if session_id not in self.sessions:
            return {"error": "Session not found"}
        
        session = self.sessions[session_id]
        
        return {
            "session_id": session_id,
            "status": session["status"].value,
            "user_profile": {
                "name": session["user_profile"].name,
                "email": session["user_profile"].email,
                "customer_id": session["user_profile"].customer_id
            },
            "created_at": session["created_at"].isoformat(),
            "last_activity": session["last_activity"].isoformat(),
            "stats": self._get_session_stats(session_id),
            "conversation_preview": self._get_conversation_preview(session_id)
        }
    
    def _get_conversation_preview(self, session_id: str) -> List[Dict]:
        """Get recent conversation messages for preview"""
        history = self.redis.get_conversation_history(session_id, limit=3)
        
        preview = []
        for msg in history[-3:]:  # Last 3 messages
            preview.append({
                "role": msg["role"],
                "content": msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"],
                "timestamp": msg["timestamp"]
            })
        
        return preview
    
    def get_all_sessions(self, status: Optional[SessionStatus] = None) -> List[Dict[str, Any]]:
        """Get all sessions with optional status filter"""
        sessions = []
        
        for session_id, session_data in self.sessions.items():
            if status is None or session_data["status"] == status:
                sessions.append(self._get_session_info(session_id))
        
        return sessions
    
    def get_system_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive system dashboard data"""
        return {
            "system_health": self.monitor.get_health_status(),
            "performance_metrics": self.monitor.get_performance_metrics(),
            "analytics_summary": self.analytics.get_summary(),
            "active_sessions": len([s for s in self.sessions.values() if s["status"] == SessionStatus.ACTIVE]),
            "redis_stats": self.redis.get_stats(),
            "recent_activity": self._get_recent_activity()
        }
    
    def _get_recent_activity(self) -> List[Dict]:
        """Get recent system activity"""
        activity = []
        
        # Get recent sessions
        recent_sessions = sorted(
            self.sessions.items(),
            key=lambda x: x[1]["last_activity"],
            reverse=True
        )[:5]
        
        for session_id, session_data in recent_sessions:
            activity.append({
                "type": "session_activity",
                "session_id": session_id,
                "user": session_data["user_profile"].email or "anonymous",
                "last_activity": session_data["last_activity"].isoformat(),
                "message_count": session_data["message_count"],
                "status": session_data["status"].value
            })
        
        return activity

class AnalyticsManager:
    """STEP 8: Enhanced analytics and tracking"""
    
    def __init__(self, redis_manager: RedisManager):
        self.redis = redis_manager
        self.logger = logging.getLogger(f"{__name__}.Analytics")
    
    def track_session_created(self, session_id: str, user_data: Dict):
        """Track session creation"""
        analytics_data = {
            "event_type": "session_created",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "user_type": "returning" if user_data.get("customer_id") else "new",
            "user_data": {
                "has_email": bool(user_data.get("email")),
                "has_phone": bool(user_data.get("phone")),
                "preferred_language": user_data.get("preferred_language", "en")
            }
        }
        
        self._store_analytics_event(analytics_data)
    
    def track_message_processed(self, session_id: str, message: str, result: Dict, duration: float):
        """Track message processing"""
        analytics_data = {
            "event_type": "message_processed",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "agent_used": result.get("agent_used"),
            "confidence": result.get("confidence", 0),
            "processing_duration": duration,
            "success": result.get("success", False),
            "message_length": len(message),
            "message_type": self._classify_message_type(message)
        }
        
        self._store_analytics_event(analytics_data)
    
    def track_session_ended(self, session_id: str, stats: Dict, satisfaction_score: Optional[int], feedback: str):
        """Track session end"""
        analytics_data = {
            "event_type": "session_ended",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "duration_minutes": stats.get("duration_minutes", 0),
            "message_count": stats.get("message_count", 0),
            "agent_usage": stats.get("agent_usage", {}),
            "satisfaction_score": satisfaction_score,
            "has_feedback": bool(feedback),
            "feedback_length": len(feedback) if feedback else 0
        }
        
        self._store_analytics_event(analytics_data)
    
    def track_error(self, session_id: str, message: str, error: str):
        """Track errors"""
        analytics_data = {
            "event_type": "error",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "error_message": str(error)[:200],  # Limit error message length
            "user_message_length": len(message)
        }
        
        self._store_analytics_event(analytics_data)
    
    def _classify_message_type(self, message: str) -> str:
        """Classify message type for analytics"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["ord", "order", "track"]):
            return "order_inquiry"
        elif any(word in message_lower for word in ["return", "refund", "policy"]):
            return "policy_question"
        elif any(word in message_lower for word in ["help", "support", "contact"]):
            return "support_request"
        elif message.startswith("/"):
            return "command"
        else:
            return "general_question"
    
    def _store_analytics_event(self, event_data: Dict):
        """Store analytics event in Redis"""
        try:
            event_key = f"analytics:{datetime.now().strftime('%Y%m%d')}:{uuid.uuid4().hex[:8]}"
            self.redis.cache_set(event_key, event_data, ttl=86400 * 30)  # 30 days
        except Exception as e:
            self.logger.error(f"Failed to store analytics event: {e}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get analytics summary"""
        try:
            # Get today's analytics keys
            today = datetime.now().strftime('%Y%m%d')
            analytics_keys = self.redis.redis_client.keys(f"analytics:{today}:*")
            
            summary = {
                "today_events": len(analytics_keys),
                "cache_performance": self._get_cache_performance(),
                "agent_usage": self._get_agent_usage_stats(),
                "error_rate": self._get_error_rate()
            }
            
            return summary
        except Exception as e:
            self.logger.error(f"Failed to get analytics summary: {e}")
            return {"error": str(e)}
    
    def _get_cache_performance(self) -> Dict[str, Any]:
        """Get cache performance metrics"""
        redis_stats = self.redis.get_stats()
        return {
            "order_cache_entries": redis_stats.get("order_cache", 0),
            "faq_cache_entries": redis_stats.get("faq_cache", 0),
            "total_cached_items": redis_stats.get("cached_items", 0)
        }
    
    def _get_agent_usage_stats(self) -> Dict[str, int]:
        """Get agent usage statistics"""
        # This would typically query stored analytics events
        return {
            "order_lookup": 0,
            "faq": 0,
            "command_handler": 0
        }
    
    def _get_error_rate(self) -> float:
        """Get current error rate"""
        # This would typically calculate from stored events
        return 0.02  # 2% error rate example

class SystemMonitor:
    """STEP 8: System health and performance monitoring"""
    
    def __init__(self, redis_manager: RedisManager):
        self.redis = redis_manager
        self.logger = logging.getLogger(f"{__name__}.Monitor")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall system health status"""
        health = {
            "overall_status": "healthy",
            "components": {},
            "last_check": datetime.now().isoformat()
        }
        
        # Check Redis
        try:
            redis_healthy = self.redis.ping()
            health["components"]["redis"] = {
                "status": "healthy" if redis_healthy else "unhealthy",
                "response_time": self._check_redis_response_time()
            }
        except Exception as e:
            health["components"]["redis"] = {
                "status": "error",
                "error": str(e)
            }
            health["overall_status"] = "degraded"
        
        # Check memory usage
        try:
            redis_stats = self.redis.get_stats()
            memory_mb = self._parse_memory_usage(redis_stats.get("used_memory_human", "0B"))
            
            health["components"]["memory"] = {
                "status": "healthy" if memory_mb < 100 else "warning",
                "usage_mb": memory_mb,
                "usage_human": redis_stats.get("used_memory_human", "Unknown")
            }
        except Exception as e:
            health["components"]["memory"] = {
                "status": "error",
                "error": str(e)
            }
        
        return health
    
    def _check_redis_response_time(self) -> float:
        """Check Redis response time"""
        start_time = datetime.now()
        self.redis.ping()
        return (datetime.now() - start_time).total_seconds() * 1000  # milliseconds
    
    def _parse_memory_usage(self, memory_str: str) -> float:
        """Parse memory usage string to MB"""
        try:
            if "M" in memory_str:
                return float(memory_str.replace("M", ""))
            elif "K" in memory_str:
                return float(memory_str.replace("K", "")) / 1024
            elif "G" in memory_str:
                return float(memory_str.replace("G", "")) * 1024
            else:
                return 0.0
        except:
            return 0.0
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        redis_stats = self.redis.get_stats()
        
        return {
            "redis_version": redis_stats.get("redis_version", "Unknown"),
            "connected_clients": redis_stats.get("connected_clients", 0),
            "total_keys": redis_stats.get("total_keys", 0),
            "cache_hit_ratio": self._calculate_cache_hit_ratio(),
            "average_response_time": self._get_average_response_time(),
            "uptime_seconds": self._get_uptime()
        }
    
    def _calculate_cache_hit_ratio(self) -> float:
        """Calculate cache hit ratio (simplified)"""
        # In production, this would track actual hits/misses
        return 0.95  # 95% hit ratio example
    
    def _get_average_response_time(self) -> float:
        """Get average response time in milliseconds"""
        # In production, this would track actual response times
        return 150.0  # 150ms example
    
    def _get_uptime(self) -> int:
        """Get system uptime in seconds"""
        # In production, this would track actual uptime
        return 86400  # 1 day example