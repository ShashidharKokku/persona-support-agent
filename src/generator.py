"""
generator.py — Builds the persona-specific prompt and calls Gemini to generate a response.

Flow:
  1. Check for escalation (via escalator.py)
  2. If safe to answer → build a custom system prompt for the detected persona
  3. Inject retrieved context chunks into the prompt
  4. Call Gemini and return the response
"""

from google import genai
from google.genai import types

from src.config import GEMINI_API_KEY, CHAT_MODEL
from src.escalator import should_escalate, generate_handoff_json


# ── Persona prompt templates ───────────────────────────────────────────────────
PERSONA_PROMPTS = {
    "Technical Expert": (
        "You are a Senior Systems Engineer providing technical support. "
        "Give precise root-cause analysis and systematic step-by-step resolution. "
        "Include relevant configuration details, error code explanations, code snippets, "
        "and exact API parameter names where applicable. "
        "Use technical terminology — the customer understands it."
    ),
    "Frustrated User": (
        "You are a warm, empathetic Customer Care Specialist. "
        "The customer is stressed — your top priority is to make them feel heard. "
        "Start your response with a brief, genuine acknowledgment of their frustration. "
        "Then provide clear, simple numbered steps they can follow immediately. "
        "Avoid technical jargon. Keep your tone calm, friendly, and reassuring throughout."
    ),
    "Business Executive": (
        "You are a concise Client Relations Director speaking to a senior executive. "
        "Lead with the direct answer or resolution timeline. "
        "Focus on business impact, SLA implications, and what action is being taken. "
        "Keep your response brief (3–5 sentences max). "
        "Skip low-level technical details unless directly asked."
    )
}


def generate_adaptive_response(
    user_query:     str,
    persona:        str,
    context_chunks: list[dict]
) -> dict:
    """
    Generates a persona-adapted response grounded in the retrieved context.

    Returns:
      {
        "escalated":       bool,
        "response":        str,    # the message to show the customer
        "handoff_json":    str | None,
        "persona":         str,
        "confidence":      float
      }
    """
    # ── Step 1: Escalation check ────────────────────────────────────────────────
    escalate, reason = should_escalate(user_query, context_chunks)

    best_score = max((c["score"] for c in context_chunks), default=0.0)

    if escalate:
        handoff = generate_handoff_json(user_query, persona, context_chunks, reason)
        return {
            "escalated":    True,
            "response": (
                "I'm sorry you're experiencing this issue. "
                "I wasn't able to locate a precise solution in our knowledge base, "
                "so I'm connecting you with a live support specialist who can help further. "
                "You'll hear from our team shortly — thank you for your patience."
            ),
            "handoff_json": handoff,
            "persona":      persona,
            "confidence":   best_score
        }

    # ── Step 2: Build persona-specific system prompt ────────────────────────────
    persona_instruction = PERSONA_PROMPTS.get(persona, PERSONA_PROMPTS["Frustrated User"])

    context_text = "\n\n".join(
        [f"[Source: {c['source']}]\n{c['text']}" for c in context_chunks]
    )

    system_prompt = (
        f"{persona_instruction}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "CRITICAL RULES YOU MUST FOLLOW:\n"
        "- Answer ONLY using information found in the CONTEXT DOCUMENTS below.\n"
        "- Do NOT make up facts, links, or steps not present in the documents.\n"
        "- If the documents don't fully answer the question, say so honestly.\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"CONTEXT DOCUMENTS:\n{context_text}"
    )

    # ── Step 3: Call Gemini ─────────────────────────────────────────────────────
    client = genai.Client(api_key=GEMINI_API_KEY)

    try:
        response = client.models.generate_content(
            model=CHAT_MODEL,
            contents=user_query,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.3
            )
        )
        answer = response.text

    except Exception as e:
        answer = f"I encountered an error generating a response. Please try again. (Error: {e})"

    return {
        "escalated":    False,
        "response":     answer,
        "handoff_json": None,
        "persona":      persona,
        "confidence":   best_score
    }
