import json
import os
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL_NAME = "openai/gpt-oss-120b"

def generate_call_summary(transcript: list) -> dict:
    """
    Takes the conversation transcript and returns a structured JSON summary.
    """
    prompt = f"""
Analyze the following customer support conversation transcript for Aura Skincare and generate a structured JSON object.

TRANSCRIPT:
{json.dumps(transcript, indent=2)}

Return ONLY a valid JSON object with EXACTLY this structure:
{{
  "customer_intent": "<one of: ORDER_TRACKING, RETURN_REFUND, CANCELLATION, PRODUCT_QUERY, OUT_OF_SCOPE, GENERAL_INQUIRY>",
  "order_id": "<order ID if mentioned, or null>",
  "resolution_status": "<RESOLVED, UNRESOLVED, or ESCALATED>",
  "call_summary": "<concise 1-2 sentence description of customer request and outcome>"
}}
"""
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    
    raw_content = response.choices[0].message.content.strip()
    
    # Strip potential markdown formatting if returned
    if raw_content.startswith("```"):
        raw_content = raw_content.split("```")[1]
        if raw_content.startswith("json"):
            raw_content = raw_content[4:]
    raw_content = raw_content.strip()
    
    try:
        return json.loads(raw_content)
    except Exception:
        return {
            "customer_intent": "GENERAL_INQUIRY",
            "order_id": None,
            "resolution_status": "RESOLVED",
            "call_summary": raw_content
        }