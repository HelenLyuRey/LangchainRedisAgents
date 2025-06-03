# src/agent_router.py - STEP 6: New file for routing between agents
import re
from typing import Tuple, Optional
from redis_manager import RedisManager

class AgentRouter:
    """Routes messages to appropriate agents based on content and context"""
    
    def __init__(self, redis_manager: RedisManager):
        self.redis = redis_manager
        
        # Define routing patterns
        self.order_patterns = [
            r'\bORD\d+\b',  # Order ID pattern
            r'\border\s+(id|number|#)',
            r'\btrack\w*\s+order\b',
            r'\bwhere\s+is\s+my\s+order\b',
            r'\border\s+status\b',
            r'\btracking\s+number\b',
            r'\bdelivery\s+date\b',
            r'\bshipping\s+status\b'
        ]
        
        self.faq_patterns = [
            r'\breturn\s+policy\b',
            r'\bshipping\s+policy\b',
            r'\bpayment\s+method\b',
            r'\bhow\s+to\s+return\b',
            r'\bwarranty\b',
            r'\bcancel\s+order\b',
            r'\bcontact\s+support\b',
            r'\bbusiness\s+hours\b',
            r'\bcustomer\s+service\b',
            r'\brefund\b',
            r'\bexchange\b'
        ]
    
    def route_message(self, message: str, session_id: str) -> Tuple[str, float]:
        """
        Route message to appropriate agent
        Returns: (agent_name, confidence_score)
        """
        
        message_lower = message.lower()
        
        # Calculate scores for each agent type
        order_score = self._calculate_order_score(message_lower)
        faq_score = self._calculate_faq_score(message_lower)
        
        # Consider conversation context
        context_bias = self._get_context_bias(session_id)
        
        # Apply context bias
        order_score += context_bias.get("order", 0)
        faq_score += context_bias.get("faq", 0)
        
        # Determine best agent
        if order_score > faq_score and order_score > 0.3:
            return "order_lookup", order_score
        elif faq_score > 0.2:
            return "faq", faq_score
        else:
            # Default to FAQ agent for general questions
            return "faq", 0.5
    
    def _calculate_order_score(self, message: str) -> float:
        """Calculate confidence score for order-related queries"""
        score = 0.0
        
        # Check for order patterns (higher weights for exact matches)
        for pattern in self.order_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                score += 0.4  # STEP 6: FIX - Increased from 0.3 for better confidence
        
        # Boost score for specific order-related keywords
        order_keywords = {
            "order": 0.3,  # Increased
            "tracking": 0.4,  # Increased
            "delivery": 0.3,  # Increased
            "shipped": 0.4,
            "delivered": 0.4,
            "status": 0.2  # Increased
        }
        
        for keyword, weight in order_keywords.items():
            if keyword in message:
                score += weight
        
        # Check for email pattern (might be searching orders by email)
        if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', message):
            score += 0.5  # Increased from 0.4
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _calculate_faq_score(self, message: str) -> float:
        """Calculate confidence score for FAQ-related queries"""
        score = 0.0
        
        # Check for FAQ patterns
        for pattern in self.faq_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                score += 0.3
        
        # Boost score for question words
        question_words = ["how", "what", "when", "where", "why", "can", "do", "does", "is", "are"]
        for word in question_words:
            if f" {word} " in f" {message} ":
                score += 0.1
        
        # Boost for policy-related keywords
        policy_keywords = {
            "policy": 0.3,
            "return": 0.2,
            "refund": 0.2,
            "shipping": 0.1,
            "payment": 0.2,
            "warranty": 0.3,
            "support": 0.2,
            "help": 0.1,
            "contact": 0.2
        }
        
        for keyword, weight in policy_keywords.items():
            if keyword in message:
                score += weight
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _get_context_bias(self, session_id: str) -> dict:
        """Get routing bias based on conversation context"""
        bias = {"order": 0.0, "faq": 0.0}
        
        # Get recent conversation history
        history = self.redis.get_conversation_history(session_id, limit=3)
        
        if not history:
            return bias
        
        # Look at recent messages for context clues
        recent_text = " ".join([msg["content"].lower() for msg in history[-2:]])
        
        # If recent conversation mentioned orders, bias toward order agent
        if any(word in recent_text for word in ["order", "tracking", "delivery", "shipped"]):
            bias["order"] += 0.2
        
        # If recent conversation was about policies, bias toward FAQ
        if any(word in recent_text for word in ["policy", "return", "refund", "warranty"]):
            bias["faq"] += 0.2
        
        return bias
    
    def get_routing_explanation(self, message: str, session_id: str) -> str:
        """Get explanation of why message was routed to specific agent"""
        agent, score = self.route_message(message, session_id)
        
        order_score = self._calculate_order_score(message.lower())
        faq_score = self._calculate_faq_score(message.lower())
        
        explanation = f"🤖 **Routing Decision:**\n"
        explanation += f"Selected Agent: **{agent.replace('_', ' ').title()}**\n"
        explanation += f"Confidence: {score:.2f}\n\n"
        explanation += f"**Scores:**\n"
        explanation += f"- Order Agent: {order_score:.2f}\n"
        explanation += f"- FAQ Agent: {faq_score:.2f}\n\n"
        
        # Add reasoning
        if agent == "order_lookup":
            explanation += "**Reasoning:** Message appears to be about order status, tracking, or specific order information."
        else:
            explanation += "**Reasoning:** Message appears to be a general question about policies, procedures, or support."
        
        return explanation