"""
app.py — Streamlit web UI for the Persona-Adaptive Customer Support Agent.

Run with:
    streamlit run app.py
"""

import streamlit as st
from src.config import GEMINI_API_KEY
from src.classifier import classify_customer_persona
from src.rag_pipeline import LocalRAGPipeline
from src.generator import generate_adaptive_response

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Support Agent",
    page_icon="🤖",
    layout="wide"
)

# ── Persona badge colors ───────────────────────────────────────────────────────
PERSONA_COLORS = {
    "Technical Expert":   "#1e88e5",   # blue
    "Frustrated User":    "#e53935",   # red
    "Business Executive": "#43a047",   # green
}

PERSONA_ICONS = {
    "Technical Expert":   "🛠️",
    "Frustrated User":    "😤",
    "Business Executive": "💼",
}

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .persona-badge {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
        color: white;
        margin-bottom: 8px;
    }
    .confidence-bar-wrap {
        background: #e0e0e0;
        border-radius: 10px;
        height: 8px;
        width: 180px;
        display: inline-block;
        vertical-align: middle;
        margin-left: 8px;
    }
    .confidence-bar-fill {
        height: 8px;
        border-radius: 10px;
        background: #43a047;
    }
    .escalated-box {
        background: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 12px 16px;
        border-radius: 6px;
        margin-top: 8px;
    }
    .handoff-box {
        background: #fafafa;
        border: 1px solid #ddd;
        border-radius: 6px;
        padding: 12px;
        font-family: monospace;
        font-size: 12px;
        white-space: pre-wrap;
        margin-top: 6px;
    }
</style>
""", unsafe_allow_html=True)


# ── Guard: API key must be present ─────────────────────────────────────────────
if not GEMINI_API_KEY:
    st.error("⚠️ GEMINI_API_KEY not found. Please add it to your .env file and restart.")
    st.stop()


# ── Load RAG pipeline once (cached) ───────────────────────────────────────────
@st.cache_resource(show_spinner="📚 Loading knowledge base…")
def get_rag_pipeline():
    pipeline = LocalRAGPipeline()
    pipeline.load_all_documents()
    return pipeline

rag = get_rag_pipeline()


# ── Session state ──────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []   # list of {role, content, meta}


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🤖 Support Agent")
    st.caption("Persona-Adaptive AI Support")

    st.divider()
    st.subheader("How it works")
    st.markdown("""
1. **Classify** — Your message is analysed to detect your persona
2. **Retrieve** — Relevant docs are fetched from the knowledge base
3. **Generate** — A response is crafted in the right style for you
4. **Escalate** — If confidence is low, a human agent is notified
""")

    st.divider()
    st.subheader("Try these examples")
    example_msgs = {
        "🛠️ Tech":  "What are the header parameters for bearer token authentication?",
        "😤 Upset": "I've been trying to log in for an hour and nothing works! Fix this!",
        "💼 Exec":  "What is the timeline for resolving our billing dispute backlog?",
        "⚠️ Escalate": "I have duplicate charges and want an immediate refund!",
    }
    for label, msg in example_msgs.items():
        if st.button(label, use_container_width=True):
            st.session_state["prefill"] = msg

    st.divider()
    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    kb_count = rag.collection.count()
    st.caption(f"📦 Knowledge base: {kb_count} chunks indexed")


# ── Main area ──────────────────────────────────────────────────────────────────
st.title("🤖 Persona-Adaptive Customer Support")
st.caption("Powered by Google Gemini · RAG · ChromaDB")

# Render chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "user":
            st.write(msg["content"])
        else:
            meta = msg.get("meta", {})

            # Persona badge
            persona    = meta.get("persona", "")
            color      = PERSONA_COLORS.get(persona, "#888")
            icon       = PERSONA_ICONS.get(persona, "🤖")
            confidence = meta.get("confidence", 0)
            escalated  = meta.get("escalated", False)

            if persona:
                bar_pct = int(confidence * 100)
                st.markdown(
                    f'<span class="persona-badge" style="background:{color}">'
                    f'{icon} {persona}</span>'
                    f'&nbsp; Confidence: {bar_pct}%'
                    f'<span class="confidence-bar-wrap">'
                    f'<span class="confidence-bar-fill" style="width:{bar_pct}%"></span>'
                    f'</span>',
                    unsafe_allow_html=True
                )

            if escalated:
                st.markdown(
                    '<div class="escalated-box">⚠️ <strong>Escalated to Human Agent</strong></div>',
                    unsafe_allow_html=True
                )

            st.write(msg["content"])

            # Show handoff JSON in expander
            if meta.get("handoff_json"):
                with st.expander("📋 View Handoff JSON (for human agent)"):
                    st.markdown(
                        f'<div class="handoff-box">{meta["handoff_json"]}</div>',
                        unsafe_allow_html=True
                    )


# ── Chat input ─────────────────────────────────────────────────────────────────
prefill = st.session_state.pop("prefill", "")
user_input = st.chat_input("Type your support question here…", key="chat_input")

# Allow sidebar button to prefill the input by injecting it directly
if prefill and not user_input:
    user_input = prefill

if user_input:
    # Show user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Process
    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            # 1. Classify persona
            classification = classify_customer_persona(user_input)
            persona        = classification["persona"]
            cls_confidence = classification["confidence"]

            # 2. Retrieve context
            chunks = rag.retrieve_context(user_input)

            # 3. Generate response
            result = generate_adaptive_response(user_input, persona, chunks)

        # Display persona badge
        color   = PERSONA_COLORS.get(persona, "#888")
        icon    = PERSONA_ICONS.get(persona, "🤖")
        rag_confidence = result["confidence"]
        bar_pct = int(rag_confidence * 100)

        st.markdown(
            f'<span class="persona-badge" style="background:{color}">'
            f'{icon} {persona}</span>'
            f'&nbsp; Confidence: {bar_pct}%'
            f'<span class="confidence-bar-wrap">'
            f'<span class="confidence-bar-fill" style="width:{bar_pct}%"></span>'
            f'</span>',
            unsafe_allow_html=True
        )

        if result["escalated"]:
            st.markdown(
                '<div class="escalated-box">⚠️ <strong>Escalated to Human Agent</strong></div>',
                unsafe_allow_html=True
            )

        st.write(result["response"])

        if result.get("handoff_json"):
            with st.expander("📋 View Handoff JSON (for human agent)"):
                st.markdown(
                    f'<div class="handoff-box">{result["handoff_json"]}</div>',
                    unsafe_allow_html=True
                )

    # Save to history
    st.session_state.messages.append({
        "role":    "assistant",
        "content": result["response"],
        "meta": {
            "persona":      persona,
            "confidence":   rag_confidence,
            "escalated":    result["escalated"],
            "handoff_json": result.get("handoff_json")
        }
    })
