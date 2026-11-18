
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

from orders_db import get_order_details


# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

gemini_key = os.getenv("GEMINI_API_KEY")

if not gemini_key:
    raise ValueError(
        f"GEMINI_API_KEY is missing! Checked file: {env_path.resolve()}"
    )

client = genai.Client(api_key=gemini_key)

MODEL_NAME = "gemini-3.5-flash-lite"


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


# Gemini function declaration
ORDER_TOOL = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="get_order_details",
            description=(
                "Look up live order information, delivery status, "
                "and notes using an order ID."
            ),
            parameters={
                "type": "OBJECT",
                "properties": {
                    "order_id": {
                        "type": "STRING",
                        "description": "The order ID formatted as ORD-XXX, e.g. ORD-101",
                    }
                },
                "required": ["order_id"],
            },
        )
    ]
)


def handle_tool_call(tool_name: str, arguments: dict):
    if tool_name == "get_order_details":
        order_id = arguments.get("order_id", "")
        return get_order_details(order_id)

    return {"error": "Unknown tool"}


def run_agent_turn(messages: list) -> tuple[str, list]:
    """
    Runs one conversation turn using Gemini.
    Preserves the existing OpenAI-style message format
    expected by the frontend.
    """

    # Extract the system prompt and previous conversation
    system_prompt = SYSTEM_PROMPT
    history = []

    for message in messages[:-1]:
        role = message.get("role")
        content = message.get("content")

        if role == "system":
            if content:
                system_prompt = content

        elif role in ("user", "assistant") and content:
            gemini_role = "model" if role == "assistant" else "user"

            history.append(
                types.Content(
                    role=gemini_role,
                    parts=[types.Part.from_text(text=str(content))],
                )
            )

    # Latest user message
    user_message = messages[-1].get("content", "")

    chat = client.chats.create(
        model=MODEL_NAME,
        history=history,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            tools=[ORDER_TOOL],
        ),
    )

    response = chat.send_message(user_message)

    # Process function calls until Gemini returns a normal response
    while True:
        function_calls = [
            part.function_call
            for part in response.parts
            if part.function_call is not None
        ]

        if not function_calls:
            break

        function_responses = []

        for function_call in function_calls:
            tool_output = handle_tool_call(
                function_call.name,
                dict(function_call.args),
            )

            function_responses.append(
                types.Part.from_function_response(
                    name=function_call.name,
                    response=tool_output,
                )
            )

        response = chat.send_message(function_responses)

    final_text = response.text

    if not final_text:
        final_text = (
            "I'm sorry, I'm having trouble responding right now. "
            "Could you please repeat that?"
        )

    # Keep the existing frontend message format
    updated_messages = messages.copy()
    updated_messages.append(
        {
            "role": "assistant",
            "content": final_text,
        }
    )

    return final_text, updated_messages
