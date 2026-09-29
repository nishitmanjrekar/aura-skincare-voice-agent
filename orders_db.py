from typing import Optional, Dict, Any

MOCK_ORDERS: Dict[str, Dict[str, Any]] = {
    "ORD-101": {
        "customer": "Priya Sharma",
        "product": "Vitamin C Serum (30ml)",
        "value": "₹699",
        "status": "Out for Delivery",
        "notes": "BlueDart - BD-982103. Expected by 6 PM today"
    },
    "ORD-102": {
        "customer": "Rahul Verma",
        "product": "Hydrating Sunscreen SPF 50",
        "value": "₹499",
        "status": "Delivered",
        "notes": "Delhivery DL-441029. Delivered 14 days ago"
    },
    "ORD-103": {
        "customer": "Ananya Patel",
        "product": "Green Tea Face Wash + Toner",
        "value": "₹850",
        "status": "Processing",
        "notes": "Ordered 3 hours ago. Eligible for cancellation"
    }
}

def get_order_details(order_id: str) -> Dict[str, Any]:
    """Retrieves order information by order ID. Case-insensitive and strips spaces."""
    cleaned_id = order_id.strip().upper()
    
    # Handle variations like "ORD 101" -> "ORD-101"
    if " " in cleaned_id and not "-" in cleaned_id:
        cleaned_id = cleaned_id.replace(" ", "-")
        
    order = MOCK_ORDERS.get(cleaned_id)
    if order:
        return {
            "found": True,
            "order_id": cleaned_id,
            "details": order
        }
    return {
        "found": False,
        "order_id": cleaned_id,
        "message": f"No order found matching ID '{order_id}'. Please ask the customer to verify the number."
    }