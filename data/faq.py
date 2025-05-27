# data/faq.py
from typing import Dict, List, Optional, Tuple
import re

class FAQDatabase:
    """Mock FAQ database with semantic search simulation"""
    
    def __init__(self):
        self.faqs = self._load_faqs()
        self.keywords_map = self._build_keywords_map()
        
    def _load_faqs(self) -> Dict[str, Dict]:
        """Load FAQ data"""
        faqs = {
            "shipping_policy": {
                "question": "What is your shipping policy?",
                "answer": "We offer free standard shipping on orders over $50. Standard shipping takes 3-5 business days. Expedited shipping (1-2 days) is available for $9.99. International shipping is available to most countries.",
                "keywords": ["shipping", "delivery", "free shipping", "expedited", "international", "how long"]
            },
            "return_policy": {
                "question": "What is your return policy?",
                "answer": "We accept returns within 30 days of delivery. Items must be in original condition with tags attached. Return shipping is free for defective items. For other returns, return shipping costs $5.99.",
                "keywords": ["return", "refund", "exchange", "30 days", "defective", "original condition"]
            },
            "warranty": {
                "question": "What warranty do you offer?",
                "answer": "All electronics come with a 1-year manufacturer warranty. Extended warranties are available for purchase. Warranty covers manufacturing defects but not accidental damage.",
                "keywords": ["warranty", "guarantee", "defect", "broken", "malfunction", "coverage"]
            },
            "payment_methods": {
                "question": "What payment methods do you accept?",
                "answer": "We accept all major credit cards (Visa, MasterCard, American Express), PayPal, Apple Pay, Google Pay, and Buy Now Pay Later options through Klarna and Afterpay.",
                "keywords": ["payment", "credit card", "paypal", "apple pay", "google pay", "klarna", "afterpay", "buy now pay later"]
            },
            "order_cancellation": {
                "question": "Can I cancel my order?",
                "answer": "You can cancel your order within 1 hour of placing it if it hasn't entered processing. After that, you'll need to wait for delivery and return the item following our return policy.",
                "keywords": ["cancel", "cancellation", "cancel order", "stop order", "change order"]
            },
            "track_order": {
                "question": "How can I track my order?",
                "answer": "Once your order ships, you'll receive a tracking number via email. You can track your package on our website or the carrier's website (FedEx, UPS, DHL, USPS).",
                "keywords": ["track", "tracking", "where is my order", "tracking number", "shipment status"]
            },
            "customer_support": {
                "question": "How can I contact customer support?",
                "answer": "You can reach our customer support team via email at support@example.com, phone at 1-800-SUPPORT (Mon-Fri 9AM-6PM EST), or live chat on our website 24/7.",
                "keywords": ["contact", "support", "help", "phone", "email", "live chat", "customer service"]
            },
            "account_issues": {
                "question": "I'm having trouble with my account",
                "answer": "For account issues like password reset, login problems, or updating information, visit the 'My Account' section or contact support. You can reset your password using the 'Forgot Password' link.",
                "keywords": ["account", "login", "password", "forgot password", "account issues", "profile", "sign in"]
            },
            "product_availability": {
                "question": "Is a product in stock?",
                "answer": "Product availability is shown on each product page. If an item is out of stock, you can sign up for restock notifications. We typically restock popular items within 1-2 weeks.",
                "keywords": ["stock", "availability", "out of stock", "restock", "inventory", "when available"]
            },
            "bulk_orders": {
                "question": "Do you offer bulk discounts?",
                "answer": "Yes! We offer volume discounts for orders of 10+ units of the same item. Contact our sales team at sales@example.com for custom pricing on bulk orders.",
                "keywords": ["bulk", "volume", "discount", "wholesale", "large order", "quantity discount"]
            }
        }
        
        return faqs
    
    def _build_keywords_map(self) -> Dict[str, List[str]]:
        """Build a map of keywords to FAQ IDs for quick searching"""
        keywords_map = {}
        
        for faq_id, faq_data in self.faqs.items():
            for keyword in faq_data["keywords"]:
                if keyword not in keywords_map:
                    keywords_map[keyword] = []
                keywords_map[keyword].append(faq_id)
                
        return keywords_map
    
    def search_faqs(self, query: str) -> List[Tuple[str, Dict, float]]:
        """Search FAQs by query with relevance scoring"""
        import time
        time.sleep(0.2)  # Simulate search delay
        
        query_lower = query.lower()
        scores = {}
        
        # Score based on keyword matches
        for keyword, faq_ids in self.keywords_map.items():
            if keyword in query_lower:
                for faq_id in faq_ids:
                    if faq_id not in scores:
                        scores[faq_id] = 0
                    # Longer keyword matches get higher scores
                    scores[faq_id] += len(keyword.split())
        
        # Score based on direct text matches in questions and answers
        for faq_id, faq_data in self.faqs.items():
            question_text = faq_data["question"].lower()
            answer_text = faq_data["answer"].lower()
            
            # Check for exact phrase matches
            if query_lower in question_text:
                scores[faq_id] = scores.get(faq_id, 0) + 10
            elif query_lower in answer_text:
                scores[faq_id] = scores.get(faq_id, 0) + 5
            
            # Check for individual word matches
            query_words = query_lower.split()
            for word in query_words:
                if len(word) > 2:  # Ignore short words
                    if word in question_text:
                        scores[faq_id] = scores.get(faq_id, 0) + 2
                    elif word in answer_text:
                        scores[faq_id] = scores.get(faq_id, 0) + 1
        
        # Sort by score and return top results
        sorted_results = []
        for faq_id, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            if score > 0:
                sorted_results.append((faq_id, self.faqs[faq_id], score))
        
        return sorted_results[:5]  # Return top 5 results
    
    def get_faq(self, faq_id: str) -> Optional[Dict]:
        """Get specific FAQ by ID"""
        return self.faqs.get(faq_id)
    
    def get_all_faqs(self) -> Dict[str, Dict]:
        """Get all FAQs"""
        return self.faqs
    
    def get_random_faq(self) -> Tuple[str, Dict]:
        """Get a random FAQ for testing"""
        import random
        faq_id = random.choice(list(self.faqs.keys()))
        return faq_id, self.faqs[faq_id]

# Create global instance
faq_db = FAQDatabase()

# Helper functions for easy import
def search_faqs(query: str) -> List[Tuple[str, Dict, float]]:
    """Search FAQs by query"""
    return faq_db.search_faqs(query)

def get_faq(faq_id: str) -> Optional[Dict]:
    """Get FAQ by ID"""
    return faq_db.get_faq(faq_id)

def get_best_faq_answer(query: str) -> Optional[str]:
    """Get the best FAQ answer for a query"""
    results = search_faqs(query)
    if results:
        best_match = results[0]
        return best_match[1]["answer"]
    return None

def get_random_faq() -> Tuple[str, Dict]:
    """Get random FAQ for testing"""
    return faq_db.get_random_faq()

# Test the FAQ database
if __name__ == "__main__":
    print("❓ Testing FAQ Database...")
    
    # Test searches
    test_queries = [
        "How do I return something?",
        "shipping policy",
        "track my order",
        "payment methods",
        "contact support"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Search: '{query}'")
        results = search_faqs(query)
        
        if results:
            best_result = results[0]
            print(f"   Best match (score: {best_result[2]}): {best_result[1]['question']}")
            print(f"   Answer: {best_result[1]['answer'][:100]}...")
        else:
            print("   No results found")