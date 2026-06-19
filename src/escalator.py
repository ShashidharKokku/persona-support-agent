"""
escalator.py — Decides whether to escalate a query to a human agent.

Escalation triggers:
  1. Best retrieval score < CONFIDENCE_THRESHOLD (AI doesn't know enough)
  2. Message contains sensitive keywords (billing, legal, refunds, etc.)
  3. No context chunks were retrieved at all
"""

import json
from src.config import CONFIDENCE_THRESHOLD, SENSITIVE_KEYWORDS


def should_escalate(user_message: str, context_chunks: list[dict]) -> tuple[bool, str]:
    """
    Returns (escalate: bool, reason: str).
    """
    # Trigger 1: No documents found
    if not context_chunks:
        return True, "No relevant documents found in the knowledge base."

    # Trigger 2: Low retrieval confidence
    best_score = max(c["score"] for c in context_chunks)
    if best_score < CONFIDENCE_THRESHOLD:
        return True, f"Low retrieval confidence (best score: {best_score:.2f} < {CONFIDENCE_THRESHOLD})."

    # Trigger 3: Sensitive keywords detected
    lower_msg = user_message.lower()
    for keyword in SENSITIVE_KEYWORDS:
        if keyword in lower_msg:
            return True, f"Sensitive topic detected: '{keyword}'."

    return False, ""


def generate_handoff_json(
    user_query:     str,
    persona:        str,
    context_chunks: list[dict],
    reason:         str
) -> str:
    """
    Builds a structured JSON payload to hand off to a human support agent.
    """
    best_score = max((c["score"] for c in context_chunks), default=0.0)

    handoff = {
        "escalation_reason":    reason,
        "customer_persona":     persona,
        "original_query":       user_query,
        "confidence_score":     round(best_score, 4),
        "retrieved_sources":    list({c["source"] for c in context_chunks}),
        "recommended_action":   (
            "Review the customer's account history. "
            "If billing-related, involve the billing team. "
            "If technical, loop in a senior engineer. "
            "Respond to the customer within 1 business hour."
        ),
        "partial_context_found": [c["text"][:200] for c in context_chunks]
    }

    return json.dumps(handoff, indent=2)
