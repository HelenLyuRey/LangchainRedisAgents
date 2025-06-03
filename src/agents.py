# src/agents.py - STEP 6: Complete agent implementation
import sys
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

# Add data directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'data'))

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage

from redis_manager import RedisManager
from order_cache_manager import OrderCacheManager
from faq_cache_manager import FAQCacheManager
from config import Config

class BaseAgent:
    """Base class for Redis-powered LangChain agents"""
    
    def __init__(self, redis_manager: RedisManager, agent_name: str):
        self.redis = redis_manager
        self.agent_name = agent_name
        self.config = Config()
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            api_key=self.config.OPENAI_API_KEY,
            model="gpt-3.5-turbo",
            temperature=0.1
        )
        
    def _get_conversation_context(self, session_id: str, limit: int = 5) -> str:
        """Get recent conversation history as context"""
        history = self.redis.get_conversation_history(session_id, limit)
        
        if not history:
            return "This is the start of the conversation."
        
        context_lines = []
        for msg in history[-limit:]:  # Get last N messages
            role = msg["role"]
            content = msg["content"]
            if role == "user":
                context_lines.append(f"Customer: {content}")
            elif role == "assistant":
                context_lines.append(f"Assistant: {content}")
        
        return "Recent conversation:\n" + "\n".join(context_lines)
    
    def _save_agent_state(self, session_id: str, state_data: Dict) -> None:
        """Save agent-specific state to Redis"""
        self.redis.set_agent_state(session_id, self.agent_name, state_data)
    
    def _get_agent_state(self, session_id: str) -> Dict:
        """Get agent-specific state from Redis"""
        state = self.redis.get_agent_state(session_id, self.agent_name)
        return state or {}
    
    def process_message(self, message: str, session_id: str) -> str:
        """Process a message with the agent - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement process_message")

class OrderLookupAgent(BaseAgent):
    """Agent specialized in order lookups with Redis caching"""
    
    def __init__(self, redis_manager: RedisManager):
        super().__init__(redis_manager, "order_lookup")
        self.order_cache = OrderCacheManager(redis_manager)
        self._setup_tools()
        self._setup_agent()
    
    def _setup_tools(self):
        """Setup order-related tools"""
        
        def lookup_order_tool(order_id: str) -> str:
            """Look up order information by order ID"""
            try:
                # Clean up order ID (remove spaces, ensure uppercase)
                clean_order_id = order_id.strip().upper()
                
                print(f"🔍 Looking up order: {clean_order_id}")
                
                # Get order with Redis caching
                order = self.order_cache.get_order(clean_order_id)
                
                if not order:
                    return f"❌ Order {clean_order_id} not found. Please check the order ID and try again."
                
                # Get status summary with caching
                summary = self.order_cache.get_order_status_summary(clean_order_id)
                
                # Format detailed response
                response = f"""📦 Order Information for {clean_order_id}:

**Product:** {order['product']} (Quantity: {order['quantity']})
**Status:** {order['status'].title()}
**Order Date:** {order['order_date']}
**Price:** ${order['price']}

**Status Summary:** {summary}"""

                if order.get('tracking_number'):
                    response += f"\n**Tracking:** {order['tracking_number']} via {order['carrier']}"
                
                if order.get('estimated_delivery'):
                    response += f"\n**Expected Delivery:** {order['estimated_delivery']}"
                
                return response
                
            except Exception as e:
                return f"❌ Error looking up order: {str(e)}"
        
        def search_orders_by_email_tool(email: str) -> str:
            """Search for orders by customer email"""
            try:
                print(f"🔍 Searching orders for email: {email}")
                
                orders = self.order_cache.search_orders_by_email(email)
                
                if not orders:
                    return f"❌ No orders found for email {email}"
                
                response = f"📧 Found {len(orders)} order(s) for {email}:\n\n"
                
                for order in orders[:5]:  # Limit to 5 most recent
                    response += f"• **{order['order_id']}** - {order['product']} - {order['status'].title()} - ${order['price']}\n"
                
                if len(orders) > 5:
                    response += f"\n... and {len(orders) - 5} more orders"
                
                response += "\n💡 Provide me with a specific order ID for detailed information."
                
                return response
                
            except Exception as e:
                return f"❌ Error searching orders: {str(e)}"
        
        self.tools = [
            Tool(
                name="lookup_order",
                description="Look up detailed information about an order using the order ID. Use this when the customer provides an order number like ORD1001.",
                func=lookup_order_tool
            ),
            Tool(
                name="search_orders_by_email", 
                description="Search for all orders associated with a customer's email address. Use this when the customer wants to see all their orders or doesn't remember their order ID.",
                func=search_orders_by_email_tool
            )
        ]
    
    def _setup_agent(self):
        """Setup the LangChain agent"""
        
        system_prompt = """You are a helpful customer service agent specialized in order lookups and tracking. 

Your capabilities:
- Look up specific orders by order ID (format: ORD####)
- Search for all orders by customer email
- Provide detailed order status and tracking information
- Handle order-related questions and concerns

Guidelines:
- Always be polite and professional
- If a customer provides an order ID, use the lookup_order tool
- If a customer provides an email or wants to see all orders, use search_orders_by_email tool
- If order information seems outdated, mention they can contact support for real-time updates
- Always format responses clearly with proper sections and emojis for readability

Context from conversation history:
{conversation_context}

Remember: You have access to cached order data for fast responses, but always let customers know if they need real-time updates to contact support directly."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        self.agent = create_openai_tools_agent(self.llm, self.tools, prompt)
        self.agent_executor = AgentExecutor(
            agent=self.agent, 
            tools=self.tools, 
            verbose=True,
            max_iterations=3,
            handle_parsing_errors=True
        )
    
    def process_message(self, message: str, session_id: str) -> str:
        """Process order-related message"""
        try:
            # Get conversation context
            conversation_context = self._get_conversation_context(session_id)
            
            # Get agent state (for tracking what we've looked up before)
            agent_state = self._get_agent_state(session_id)
            looked_up_orders = agent_state.get("looked_up_orders", [])
            
            print(f"🤖 OrderLookupAgent processing: {message}")
            
            # Build chat history for agent
            history = self.redis.get_conversation_history(session_id, limit=5)
            chat_history = []
            for msg in history:
                if msg["role"] == "user":
                    chat_history.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    chat_history.append(AIMessage(content=msg["content"]))
            
            # Process with agent
            result = self.agent_executor.invoke({
                "input": message,
                "chat_history": chat_history,
                "conversation_context": conversation_context
            })
            
            response = result["output"]
            
            # Extract any order IDs that were looked up (for state tracking)
            import re
            order_ids = re.findall(r'ORD\d+', message.upper())
            for order_id in order_ids:
                if order_id not in looked_up_orders:
                    looked_up_orders.append(order_id)
            
            # Update agent state
            updated_state = {
                "looked_up_orders": looked_up_orders,
                "last_activity": datetime.now().isoformat(),
                "total_queries": agent_state.get("total_queries", 0) + 1
            }
            self._save_agent_state(session_id, updated_state)
            
            return response
            
        except Exception as e:
            error_msg = f"❌ I encountered an error while processing your order request: {str(e)}"
            print(f"Error in OrderLookupAgent: {e}")
            return error_msg

class FAQAgent(BaseAgent):
    """Agent specialized in answering FAQ questions with Redis caching"""
    
    def __init__(self, redis_manager: RedisManager):
        super().__init__(redis_manager, "faq")
        self.faq_cache = FAQCacheManager(redis_manager)
        self._setup_tools()
        self._setup_agent()
        self._preload_common_faqs()
    
    def _preload_common_faqs(self):
        """Preload common FAQ searches for better performance"""
        common_queries = [
            "return policy", "shipping policy", "track order", 
            "payment methods", "contact support", "warranty",
            "cancel order", "account issues"
        ]
        self.faq_cache.preload_common_faqs(common_queries)
    
    def _setup_tools(self):
        """Setup FAQ-related tools"""
        
        def search_faq_tool(query: str) -> str:
            """Search the FAQ database for relevant answers"""
            try:
                print(f"🔍 Searching FAQs for: {query}")
                
                results = self.faq_cache.search_faqs(query)
                
                if not results:
                    return "❌ I couldn't find any relevant FAQ answers for your question. Please contact our support team for assistance."
                
                # Get the best result
                best_result = results[0]
                faq_id, faq_data, score = best_result
                
                response = f"**{faq_data['question']}**\n\n{faq_data['answer']}"
                
                # Add related questions if there are multiple good results
                if len(results) > 1 and results[1][2] > score * 0.7:  # If second result is close in score
                    response += "\n\n**Related Questions:**"
                    for i, (_, related_faq, _) in enumerate(results[1:3], 1):  # Show up to 2 related
                        response += f"\n{i}. {related_faq['question']}"
                
                return response
                
            except Exception as e:
                return f"❌ Error searching FAQ: {str(e)}"
        
        def get_contact_info_tool() -> str:
            """Get customer support contact information"""
            return """📞 **Customer Support Contact Information:**

**Email:** support@example.com
**Phone:** 1-800-SUPPORT (1-800-786-7678)
**Hours:** Monday-Friday, 9AM-6PM EST

**Live Chat:** Available 24/7 on our website
**Response Time:** 
- Live Chat: Immediate
- Email: Within 24 hours  
- Phone: Immediate during business hours

For urgent order issues, please call our phone line during business hours."""
        
        def get_business_hours_tool() -> str:
            """Get business hours and availability information"""
            return """🕒 **Business Hours & Availability:**

**Customer Support:**
- Phone: Monday-Friday, 9AM-6PM EST
- Live Chat: 24/7 available on website
- Email: Responses within 24 hours

**Order Processing:**
- Orders placed before 2PM EST ship same day
- Weekend orders processed on Monday
- Holiday schedules may vary

**Store Hours:** Online store available 24/7
**Warehouse Operations:** Monday-Friday, 8AM-5PM EST"""
        
        self.tools = [
            Tool(
                name="search_faq",
                description="Search the FAQ database for answers to common questions about policies, shipping, returns, payments, etc. Use this for any general policy or process questions.",
                func=search_faq_tool
            ),
            Tool(
                name="get_contact_info",
                description="Get customer support contact information including phone, email, and live chat options. Use when customers want to speak with support directly.",
                func=get_contact_info_tool
            ),
            Tool(
                name="get_business_hours",
                description="Get business hours and availability information. Use when customers ask about when they can contact support or when orders are processed.",
                func=get_business_hours_tool
            )
        ]
    
    def _setup_agent(self):
        """Setup the LangChain agent"""
        
        system_prompt = """You are a knowledgeable customer service agent specialized in answering frequently asked questions and providing general support information.

Your capabilities:
- Answer questions about policies (returns, shipping, warranty, etc.)
- Provide contact information and business hours
- Help with account and general website questions
- Guide customers to appropriate resources

Guidelines:
- Always search the FAQ database first for policy questions
- Be helpful and provide comprehensive answers
- If you can't find the exact answer, provide contact information
- Format responses clearly with proper sections and emojis
- For order-specific questions, direct customers to provide order details or contact support

Context from conversation history:
{conversation_context}

Note: You have access to a comprehensive FAQ database with cached responses for fast answers. Always try to be as helpful as possible while staying within your knowledge base."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        self.agent = create_openai_tools_agent(self.llm, self.tools, prompt)
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            max_iterations=3,
            handle_parsing_errors=True
        )
    
    def process_message(self, message: str, session_id: str) -> str:
        """Process FAQ-related message"""
        try:
            # Get conversation context
            conversation_context = self._get_conversation_context(session_id)
            
            # Get agent state
            agent_state = self._get_agent_state(session_id)
            answered_topics = agent_state.get("answered_topics", [])
            
            print(f"🤖 FAQAgent processing: {message}")
            
            # Build chat history for agent
            history = self.redis.get_conversation_history(session_id, limit=5)
            chat_history = []
            for msg in history:
                if msg["role"] == "user":
                    chat_history.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    chat_history.append(AIMessage(content=msg["content"]))
            
            # Process with agent
            result = self.agent_executor.invoke({
                "input": message,
                "chat_history": chat_history,
                "conversation_context": conversation_context
            })
            
            response = result["output"]
            
            # Track topics that were answered (for analytics)
            topic_keywords = ["return", "shipping", "payment", "warranty", "cancel", "track", "contact", "support"]
            for keyword in topic_keywords:
                if keyword.lower() in message.lower() and keyword not in answered_topics:
                    answered_topics.append(keyword)
            
            # Update agent state
            updated_state = {
                "answered_topics": answered_topics,
                "last_activity": datetime.now().isoformat(),
                "total_queries": agent_state.get("total_queries", 0) + 1
            }
            self._save_agent_state(session_id, updated_state)
            
            return response
            
        except Exception as e:
            error_msg = f"❌ I encountered an error while looking up that information: {str(e)}"
            print(f"Error in FAQAgent: {e}")
            return error_msg