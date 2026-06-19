"""
classifier.py — Detects the customer persona from their message using Gemini.

Returns a dict:
  {
    "persona":    "Technical Expert" | "Frustrated User" | "Business Executive",
    "confidence": 0.0 – 1.0,
    "reasoning":  "..."
  }
"""

import json
from google import genai
from google.genai import types
from src.config import GEMINI_API_KEY, CHAT_MODEL


def classify_customer_persona(user_message: str) -> dict:
    """
    Analyzes the user's message and classifies it into one of three personas.
    Falls back to 'Frustrated User' if the API call fails.
    """
    client = genai.Client(api_key=GEMINI_API_KEY)

    system_instruction = (
        "You are an advanced classification engine. Your task is to analyze the "
        "sentiment, vocabulary, and tone of an incoming customer support message "
        "and classify it into exactly one of three personas:\n\n"
        "1. 'Technical Expert'     — Uses technical jargon, asks about APIs, code, "
        "   configs, error codes, or system architecture.\n"
        "2. 'Frustrated User'      — Uses emotional language, exclamation marks, "
        "   expresses urgency, mentions wasted time, or sounds impatient.\n"
        "3. 'Business Executive'   — Focuses on business impact, ROI, SLAs, "
        "   timelines, and wants brief, outcome-oriented answers.\n\n"
        "Return ONLY a valid JSON object. No extra text."
    )

    response_schema = {
        "type": "OBJECT",
        "properties": {
            "persona": {
                "type": "STRING",
                "enum": ["Technical Expert", "Frustrated User", "Business Executive"]
            },
            "confidence": {"type": "NUMBER"},
            "reasoning":  {"type": "STRING"}
        },
        "required": ["persona", "confidence", "reasoning"]
    }

    try:
        response = client.models.generate_content(
            model=CHAT_MODEL,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=response_schema,
                temperature=0.1
            )
        )
        return json.loads(response.text)

    except Exception as e:
        # Safe fallback so the app never crashes on a classifier error
        return {
            "persona":    "Frustrated User",
            "confidence": 0.5,
            "reasoning":  f"Classifier error — defaulting to Frustrated User. Error: {e}"
        }


# ── Quick test ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    samples = [
        "Our production API key stopped working with a 401 Unauthorized block. Check the logs.",
        "I've been trying to log in for an hour! Nothing works! This is ridiculous!",
        "What is the projected timeline for resolving the current billing dispute backlog?"
    ]
    for msg in samples:
        result = classify_customer_persona(msg)
        print(f"\nMessage : {msg[:60]}...")
        print(f"Persona : {result['persona']}  (confidence: {result['confidence']:.2f})")
        print(f"Reason  : {result['reasoning']}")
