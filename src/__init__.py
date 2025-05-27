# src/__init__.py
"""
Redis-powered LangChain Agents Demo
A simple customer support system with Order Lookup and FAQ agents
"""

__version__ = "1.0.0"

from .config import Config
from .redis_manager import RedisManager
from .agents import OrderLookupAgent, FAQAgent
from .main import CustomerSupportSystem

__all__ = [
    'Config',
    'RedisManager', 
    'OrderLookupAgent',
    'FAQAgent',
    'CustomerSupportSystem'
]