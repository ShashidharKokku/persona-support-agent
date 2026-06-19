# 🤖 Persona-Adaptive Customer Support Agent

An intelligent customer support chatbot that detects **who** it's talking to and adapts its response style accordingly — powered by Google Gemini, ChromaDB, and Streamlit.

## Architecture

```
[User Message]
      │
      ▼
[Persona Classifier] ──► Technical Expert / Frustrated User / Business Executive
      │
      ▼
[RAG Pipeline] ──► ChromaDB Cosine Search ──► Top-3 Chunks
      │
      ▼
[Escalation Check] ──► Low confidence or sensitive keyword? ──► Human Handoff JSON
      │
      ▼
[Adaptive Generator] ──► Persona-specific Gemini response
```

## Setup Instructions

### 1. Prerequisites
- Python 3.11 or higher
- A Google Gemini API key from [aistudio.google.com](https://aistudio.google.com)

### 2. Clone / Download the project
```bash
cd persona-support-agent
```

### 3. Create a virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```

### 5. Add your API key
Rename `.env.example` to `.env` and paste your key:
```
GEMINI_API_KEY="your_actual_key_here"
```

### 6. Run the app
```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

---

## Project Structure

```
persona-support-agent/
├── data/                          # Knowledge base documents
│   ├── api_troubleshooting.md
│   ├── billing_policy.txt
│   └── password_reset_guide.txt
├── src/
│   ├── config.py                  # API keys, thresholds, model names
│   ├── classifier.py              # Persona detection via Gemini
│   ├── rag_pipeline.py            # Document ingestion + retrieval
│   ├── generator.py               # Adaptive response generation
│   └── escalator.py               # Escalation logic + handoff JSON
├── app.py                         # Streamlit UI
├── requirements.txt
├── .env.example
└── README.md
```

## Test Scenarios

| Message | Expected Persona | Expected Behaviour |
|---|---|---|
| "What are the bearer token header parameters?" | Technical Expert | Code blocks, exact parameter names |
| "I've been locked out for an hour! Fix this!" | Frustrated User | Empathetic, simple steps |
| "What's the SLA timeline for billing disputes?" | Business Executive | Brief, outcome-focused |
| "I have duplicate charges, I want a refund NOW!" | Frustrated User | **Escalated** → Handoff JSON generated |

## Configuration (src/config.py)

| Setting | Default | Description |
|---|---|---|
| `CONFIDENCE_THRESHOLD` | 0.40 | Below this score → escalate |
| `TOP_K_RESULTS` | 3 | Number of chunks to retrieve |
| `CHUNK_SIZE` | 400 | Characters per chunk |
| `CHUNK_OVERLAP` | 40 | Overlap between chunks |
