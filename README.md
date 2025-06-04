# Redis-Powered LangChain Customer Support System 🤖

A production-ready, intelligent customer support system built with **LangChain agents**, **Redis caching**, and **OpenAI GPT models**. This system demonstrates how to build scalable AI applications with persistent conversation memory, intelligent agent routing, and high-performance caching.

## 🌟 Features

### **Core AI Capabilities**
- 🤖 **Multi-Agent Architecture** - Specialized agents for order lookup and FAQ support
- 🧠 **Intelligent Routing** - Context-aware agent selection with confidence scoring
- 💬 **Conversation Memory** - Persistent chat history across sessions using Redis
- 🔄 **Seamless Agent Switching** - Maintain context when switching between specialists

### **Performance & Scalability**
- ⚡ **99% Faster Responses** - Redis caching for order lookups and FAQ searches
- 📊 **Real-time Analytics** - Comprehensive session tracking and performance metrics
- 🔄 **Session Management** - Multi-user support with TTL-based session handling
- 📈 **Performance Monitoring** - Built-in health checks and system monitoring

### **Production-Ready Features**
- 🛡️ **Error Handling** - Graceful error recovery and user feedback
- 📝 **Comprehensive Logging** - Structured logging for debugging and analytics
- 🎯 **Multiple Interfaces** - CLI, demo mode, and programmatic APIs
- 🔧 **System Commands** - Built-in help, status, and management commands

## 🏗️ Architecture

The system follows a **layered architecture** with clear separation of concerns:

**Application Layer**
- Enhanced CLI interface with user profiles
- Production-ready logging and monitoring
- Multiple operation modes (interactive, demo, API)

**Business Logic Layer**
- Main router for orchestrating conversations
- Agent router for intelligent message routing
- Session management with user profiles

**Agent Layer**
- OrderLookupAgent: Handles order status, tracking, and customer order queries
- FAQAgent: Manages policy questions, support info, and general inquiries
- Base agent class with conversation context and state management

**Data & Cache Layer**
- RedisManager: Core Redis operations and connection management
- OrderCacheManager: Optimized order data caching with 30-minute TTL
- FAQCacheManager: FAQ search result caching with preloading

**Data Sources**
- Mock order database with realistic delay simulation
- FAQ knowledge base with semantic search and scoring
- User profiles and session metadata



## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Redis server
- OpenAI API key
- Docker/Podman (optional, for Redis)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd redis-langchain-agents
```

2. **Set up Python environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```
3. **Start Redis server**
```bash
# Using Docker/Podman
podman run -d --name redis-ai -p 6379:6379 redis:alpine

# Or install Redis locally
# macOS: brew install redis && brew services start redis
# Ubuntu: sudo apt install redis-server && sudo systemctl start redis
```

4. **Environment Configuration**
Create a .env file with the following variables:
```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Session Configuration
DEFAULT_SESSION_TTL=3600
MAX_CONVERSATION_LENGTH=50
```

5. **Run the System**

```bash
# Interactive CLI mode (default)
python run.py
# Follow the prompts to:
# 1. Set up your user profile
# 2. Start a support session
# 3. Ask questions naturally
# 4. Use system commands


# Demo mode - see the system in action
python run.py --demo
# Watches a pre-scripted conversation showing:
# - Agent routing decisions
# - Redis caching in action
# - Performance improvements
# - Context preservation


# System health check
python run.py --health

# View system information
python run.py --info

# Run comprehensive tests
python run.py --test

# Initial system setup
python run.py --setup
```

## 🤖 Available Agents
- Order Lookup Agent
    Specializes in order-related queries with Redis caching:
    - Order Status Lookup - Real-time order status with tracking information
    - Order History Search - Find all orders by customer email
    - Delivery Tracking - Tracking numbers and estimated delivery dates
    - Order Troubleshooting - Handle order issues and concerns

    Performance: 99% faster with Redis caching (0.5s → 0.001s)

- FAQ Agent
    Handles policy and general support questions:

    - Policy Information - Returns, shipping, warranty, payment policies
    - Support Contact Info - Multiple contact methods and business hours
    - Account Help - Login issues, password resets, profile updates
    - General Questions - Any non-order-specific inquiries

    Performance: 99% faster with preloaded cache (0.2s → 0.002s)


## 🏗️ Project Structure
redis-langchain-agents/
├── src/                          # Source code
│   ├── __init__.py
│   ├── config.py                 # Configuration management
│   ├── redis_manager.py          # Redis operations and caching
│   ├── agents.py                 # LangChain agents (Order & FAQ)
│   ├── agent_router.py           # Intelligent message routing
│   ├── main_router.py            # Main conversation orchestrator
│   ├── order_cache_manager.py    # Order-specific caching
│   ├── faq_cache_manager.py      # FAQ-specific caching
│   ├── app.py                    # Production application
│   ├── cli_interface.py          # Enhanced CLI interface
│   └── main.py                   # Application controller
├── data/                         # Mock data sources
│   ├── orders.py                 # Sample order database
│   └── faq.py                    # FAQ knowledge base
├── tests/                        # Comprehensive test suite
│   ├── step_3_test_redis         # Redis connection tests
│   ├── step_4_test_mock_data.py  # Data source tests
│   ├── step_5_test_redis_integration.py # Integration tests
│   ├── step_6_test_agents.py     # Agent functionality tests
│   ├── step_7_test_main_router.py # Router system tests
├── logs/                         # Application logs
├── .env                         # Environment configuration
├── requirements.txt             # Python dependencies
├── run.py                       # Main entry point
└── README.md                    # This file


