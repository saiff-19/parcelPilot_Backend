# ParcelPilot AI Support Copilot

An intelligent, secure, and deterministically grounded AI Support Copilot for B2B logistics.

## Features
- **Intelligent Orchestration**: Agent workflow built on LangGraph to intelligently choose between searching policies and calculating deterministic logic.
- **Source-Aware Retrieval**: Dynamically ranks documents based on authority (Customer Agreements > SOPs > Historical Data).
- **Proactive Issue Detection**: Scans live tickets to cluster emerging issues (e.g., CSV failures) and SLA risks.
- **Safe State Mutation**: Actions like escalations use a prepare-and-confirm lifecycle; the LLM prepares the payload, but mutations execute only after explicit user confirmation.
- **Enforced Security**: Role-Based Access Control is enforced at the tool execution level, blocking unauthorized account access regardless of LLM hallucinations.

## Tech Stack
- **Frontend**: React (Vite) + SCSS
- **Backend**: Python (FastAPI), LangGraph, LangChain, SQLite

## Local Setup

### 1. Prerequisites
- Node.js (v18+ recommended)
- Python 3.10+
- Groq API Key

### 2. Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Set your Groq key
# Create a .env file inside the backend directory:
# echo "GROQ_API_KEY=gsk-..." > .env

# Run server
uvicorn main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## Data Ingestion
The synthetic dataset (`ParcelPilot_Assessment_Data.xlsx`) and PDF documents must be present in the `resourcePack` folder at the root level. The backend automatically parses, chunks, and loads this data into memory on startup (`main.py` -> `startup_event`).

## Demo Scenarios

1. **Simple Retrieval**: Ask "What is the current cancellation policy?"
2. **Multi-Step**: Ask "Can Northstar cancel ORD-1001 without a fee? Explain why."
3. **Operational**: Ask "A pickup for LumenWorks is 5 hours late. What credit do they get?"
4. **Action**: Ask "Escalate ticket TKT-501." (Observe the confirmation UI).
5. **Proactive**: Check the left sidebar for real-time SLA and cluster alerts.

## Testing
```bash
cd backend
pytest test_agent.py -v
```

## Known Limitations
- The retrieval system currently relies on term frequency and strict authority sorting. In a production system, this would be replaced by semantic vector embeddings.
- State-changing actions currently mutate the in-memory dataset for demonstration purposes.
