
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai


env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

gemini_key = os.getenv("GEMINI_API_KEY")

if not gemini_key:
    raise ValueError(
        f"GEMINI_API_KEY is missing! Checked file: {env_path.resolve()}"
    )

client = genai.Client(api_key=gemini_key)

MODEL_NAME = "gemini-3.5-flash-lite"


def generate_call_summary(transcript: list) -> dict:
    """
    Takes the conversation transcript and returns a structured JSON summary.
    """

    conversation = "\n".join(
        f"{item.get('speaker', 'Unknown')}: {item.get('text', '')}"
        for item in transcript
    )

    prompt = f"""
Summarize this Aura Skincare customer support conversation.

CONVERSATION:
{conversation}

Return JSON with exactly these four fields:
- customer_intent: ORDER_TRACKING, RETURN_REFUND, CANCELLATION, PRODUCT_QUERY, OUT_OF_SCOPE, or GENERAL_INQUIRY
- order_id: order ID if mentioned, otherwise null
- resolution_status: RESOLVED, UNRESOLVED, or ESCALATED
- call_summary: concise 1-2 sentence description of the request and outcome

Return only valid JSON.
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config={
            "temperature": 0.1,
            "response_mime_type": "application/json",
        },
    )

    raw_content = (response.text or "").strip()

    try:
        result = json.loads(raw_content)

        expected_keys = {
            "customer_intent",
            "order_id",
            "resolution_status",
            "call_summary",
        }

        if not isinstance(result, dict) or set(result.keys()) != expected_keys:
            raise ValueError("Gemini returned an unexpected summary structure.")

        return result

    except (json.JSONDecodeError, ValueError):
        return {
            "customer_intent": "GENERAL_INQUIRY",
            "order_id": None,
            "resolution_status": "UNRESOLVED",
            "call_summary": raw_content or "Unable to generate call summary.",
        }
