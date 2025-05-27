# data/orders.py
from datetime import datetime, timedelta
import random
from typing import Dict, List, Optional

class OrderDatabase:
    """Mock order database for demonstrating Redis caching"""
    
    def __init__(self):
        self.orders = self._generate_sample_orders()
        
    def _generate_sample_orders(self) -> Dict[str, Dict]:
        """Generate realistic sample orders"""
        
        statuses = ["processing", "shipped", "delivered", "cancelled", "returned"]
        products = [
            "iPhone 15 Pro", "MacBook Air M2", "AirPods Pro",
            "Samsung Galaxy S24", "Dell XPS 13", "Sony WH-1000XM5",
            "iPad Pro", "Surface Laptop", "Google Pixel 8",
            "Nintendo Switch", "Steam Deck", "PlayStation 5"
        ]
        
        carriers = ["FedEx", "UPS", "DHL", "USPS"]
        
        orders = {}
        
        # Generate 50 sample orders
        for i in range(1, 51):
            order_id = f"ORD{1000 + i}"
            
            # Random dates within last 30 days
            order_date = datetime.now() - timedelta(days=random.randint(0, 30))
            
            status = random.choice(statuses)
            
            # Set delivery date based on status
            if status == "delivered":
                delivery_date = order_date + timedelta(days=random.randint(1, 5))
            elif status == "shipped":
                delivery_date = datetime.now() + timedelta(days=random.randint(1, 3))
            else:
                delivery_date = None
                
            orders[order_id] = {
                "order_id": order_id,
                "customer_email": f"customer{i}@example.com",
                "product": random.choice(products),
                "quantity": random.randint(1, 3),
                "price": round(random.uniform(99.99, 1299.99), 2),
                "status": status,
                "order_date": order_date.strftime("%Y-%m-%d %H:%M:%S"),
                "estimated_delivery": delivery_date.strftime("%Y-%m-%d") if delivery_date else None,
                "tracking_number": f"TRK{random.randint(100000000, 999999999)}" if status in ["shipped", "delivered"] else None,
                "carrier": random.choice(carriers) if status in ["shipped", "delivered"] else None,
                "shipping_address": {
                    "street": f"{random.randint(100, 9999)} Main St",
                    "city": random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]),
                    "state": random.choice(["NY", "CA", "IL", "TX", "AZ"]),
                    "zip": f"{random.randint(10000, 99999)}"
                }
            }
            
        return orders
    
    def get_order(self, order_id: str) -> Optional[Dict]:
        """Get order by ID (simulates database query delay)"""
        import time
        # Simulate database query delay
        time.sleep(0.5)  # This is what we'll cache with Redis!
        
        return self.orders.get(order_id.upper())
    
    def search_orders_by_email(self, email: str) -> List[Dict]:
        """Search orders by customer email"""
        import time
        time.sleep(0.3)  # Simulate search delay
        
        matching_orders = []
        for order in self.orders.values():
            if order["customer_email"].lower() == email.lower():
                matching_orders.append(order)
                
        return sorted(matching_orders, key=lambda x: x["order_date"], reverse=True)
    
    def get_order_status_summary(self, order_id: str) -> Optional[str]:
        """Get a human-readable status summary"""
        order = self.get_order(order_id)
        if not order:
            return None
            
        status = order["status"]
        product = order["product"]
        
        if status == "processing":
            return f"Your order for {product} is being processed and will ship soon."
        elif status == "shipped":
            return f"Your {product} has shipped via {order['carrier']} (tracking: {order['tracking_number']}) and is expected to arrive on {order['estimated_delivery']}."
        elif status == "delivered":
            return f"Your {product} was delivered on {order['estimated_delivery']}."
        elif status == "cancelled":
            return f"Your order for {product} has been cancelled."
        elif status == "returned":
            return f"Your {product} order has been returned and is being processed for refund."
        else:
            return f"Order status: {status}"
    
    def get_all_order_ids(self) -> List[str]:
        """Get all order IDs for testing"""
        return list(self.orders.keys())

# Create global instance
order_db = OrderDatabase()

# Helper functions for easy import
def get_order(order_id: str) -> Optional[Dict]:
    """Get order by ID"""
    return order_db.get_order(order_id)

def search_orders_by_email(email: str) -> List[Dict]:
    """Search orders by email"""
    return order_db.search_orders_by_email(email)

def get_order_status_summary(order_id: str) -> Optional[str]:
    """Get order status summary"""
    return order_db.get_order_status_summary(order_id)

def get_sample_order_ids(count: int = 5) -> List[str]:
    """Get sample order IDs for testing"""
    return order_db.get_all_order_ids()[:count]

# Test the order database
if __name__ == "__main__":
    print("🛒 Testing Order Database...")
    
    # Get some sample orders
    sample_ids = get_sample_order_ids(3)
    print(f"\n📦 Sample Order IDs: {sample_ids}")
    
    for order_id in sample_ids:
        order = get_order(order_id)
        if order:
            print(f"\n📋 Order {order_id}:")
            print(f"   Product: {order['product']}")
            print(f"   Status: {order['status']}")
            print(f"   Summary: {get_order_status_summary(order_id)}")