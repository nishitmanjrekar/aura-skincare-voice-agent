from orders_db import get_order_details

print("Testing valid order:", get_order_details("ORD-101"))
print("Testing lowercase with spaces:", get_order_details("ord 102"))
print("Testing invalid order:", get_order_details("ORD-999"))