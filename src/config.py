"""
config.py — Central configuration and thresholds for the support agent.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── API ────────────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# ── Models ─────────────────────────────────────────────────────────────────────
CHAT_MODEL      = "gemini-2.5-flash"
EMBEDDING_MODEL = "models/text-embedding-004"

# ── RAG Pipeline ───────────────────────────────────────────────────────────────
CHUNK_SIZE        = 400   # characters per chunk
CHUNK_OVERLAP     = 40    # overlap between adjacent chunks
TOP_K_RESULTS     = 3     # how many chunks to retrieve per query
CHROMA_DB_DIR     = "./chroma_db"
COLLECTION_NAME   = "support_kb"

# ── Escalation ─────────────────────────────────────────────────────────────────
CONFIDENCE_THRESHOLD = 0.40   # below this → escalate to human

# Keywords that always trigger escalation regardless of confidence score
SENSITIVE_KEYWORDS = [
    "refund", "chargeback", "legal", "lawyer", "sue", "lawsuit",
    "fraud", "charge back", "duplicate charge", "stolen", "unauthorized charge"
]

# ── Data Directory ─────────────────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
