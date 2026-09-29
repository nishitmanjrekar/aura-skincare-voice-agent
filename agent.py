import json
import os
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq
from orders_db import get_order_details

# Load .env explicitly from the script directory
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

groq_key = os.getenv("GROQ_API_KEY")
if not groq_key:
    raise ValueError(f"GROQ_API_KEY is missing! Checked file: {env_path.resolve()}")

client = Groq(api_key=groq_key)

MODEL_NAME = "openai/gpt-oss-120b"

SYSTEM_PROMPT = """You are Aria, a friendly, professional, and concise Indian customer support specialist for Aura Skincare, a premium organic Indian skincare brand.

AURA SKINCARE BRAND POLICIES:
1. Shipping Policy: Free delivery on orders above ₹499. Orders below ₹499 have a ₹50 shipping fee. Standard delivery takes 3-5 business days.
2. Return & Refund Policy: Returns are accepted within 7 days of delivery ONLY for unopened, unused products in original packaging. Damaged or defective products must be reported within 48 hours of delivery with photos for replacement.
3. Cancellation Policy: Orders can ONLY be cancelled while their status is 'Processing'. Once an order is 'Shipped' or 'Out for Delivery', it CANNOT be cancelled (politely tell the customer they may refuse delivery at the doorstep).
4. Cash on Delivery (COD): COD is available for orders up to ₹2,500. Customers can pay by cash or UPI at the doorstep.

BEHAVIORAL RULES:
- Concise Spoken Voice: Keep responses between 1 to 3 natural sentences. Do not use bullet points or markdown tables since this will be spoken aloud.
- Tool Calling: When a user mentions or asks about an order status, ALWAYS call get_order_details with the provided order ID.
- Policy Enforcement: If a customer requests a return for an opened product or after 7 days, or requests a cancellation for an order that is already 'Out for Delivery' (like ORD-101) or 'Delivered' (ORD-102), politely explain why it violates policy rather than promising an exception.
- Graceful Degradation: If an order ID is missing or invalid, or audio/input is unclear, politely ask for clarification.
- Strict Scope: You only assist with Aura Skincare inquiries. Politely decline any outside requests (e.g., flight bookings, general knowledge).
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_order_details",
            "description": "Look up live order information, delivery status, and notes using an order ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order ID formatted as ORD-XXX, e.g. ORD-101"
                    }
                },
                "required": ["order_id"]
            }
        }
    }
]

def handle_tool_call(tool_name: str, arguments: dict):
    if tool_name == "get_order_details":
        order_id = arguments.get("order_id", "")
        return get_order_details(order_id)
    return {"error": "Unknown tool"}

def run_agent_turn(messages: list) -> tuple[str, list]:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto"
    )
    
    response_msg = response.choices[0].message
    
    # Tool call requested
    if response_msg.tool_calls:
        messages.append({
            "role": "assistant",
            "content": response_msg.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                } for tc in response_msg.tool_calls
            ]
        })

        for tool_call in response_msg.tool_calls:
            function_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            
            tool_output = handle_tool_call(function_name, args)
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(tool_output)
            })

        second_response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages
        )
        final_text = second_response.choices[0].message.content
        messages.append({"role": "assistant", "content": final_text})
        return final_text, messages

    messages.append({"role": "assistant", "content": response_msg.content})
    return response_msg.content, messages