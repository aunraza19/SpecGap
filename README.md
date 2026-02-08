# SpecGap Documentation

## Project Overview
SpecGap is a two-part application:
- Frontend: A React + Vite UI that lets users upload documents, run audits, and review findings.
- Backend: A FastAPI service that parses documents, runs multi-agent analysis with Gemini via LangGraph, and returns structured audit results and patch packs.

The backend supports three modes:
- Council session (fast flashcards)
- Deep analysis (tech + legal + synthesis)
- Full spectrum (council + deep analysis together)

## Folder Structure
- Frontend/
  - Vite + React UI, API client, pages, layout components, and UI primitives.
- specgap/
  - Python backend (FastAPI), AI workflows, parsers, and database layer.
- and prompt templates
  - Miscellaneous folder (not referenced in code paths).
- test.json
  - Standalone file (not referenced in code paths).

### Frontend Highlights
- Frontend/src/App.tsx: Route setup and application shell.
- Frontend/src/api/client.ts: API client for backend calls.
- Frontend/src/pages/: Core screens (Upload, Audits, Results, Search, etc.).
- Frontend/src/components/: Layout, audit UI, and reusable UI components.

### Backend Highlights
- specgap/app/main.py: FastAPI app and API endpoints.
- specgap/app/services/workflow.py: Council multi-agent workflow (LangGraph).
- specgap/app/services/parser.py: Document parsing (PDF, DOCX, TXT/MD, OCR).
- specgap/app/services/tech_engine.py: Tech gap analyzer.
- specgap/app/services/biz_engine.py: Legal/negotiation analyzer.
- specgap/app/services/cross_check.py: Orchestrator synthesis.
- specgap/app/services/patch_pack.py: Output file generation.
- specgap/app/core/database.py: SQLAlchemy models + persistence.

## Architecture and Data Flow
1. Frontend upload (React UI) sends files via multipart form-data to FastAPI.
2. Parser extracts text from PDF/DOCX/TXT/MD; OCR is attempted if needed.
3. Council session (LangGraph):
   - Round 1: Independent agent drafts (legal, business, finance).
   - Round 2: Cross-check peer drafts.
   - Round 3: Generate flashcards.
4. Deep analysis (optional):
   - Tech gap analysis (architect agent).
   - Legal leverage analysis (lawyer agent).
   - Cross-check synthesis + Mermaid diagram output.
5. Patch pack can be generated from selected cards (contract addendum, spec update, negotiation email).

## Installation and Setup

### Backend (Python)
Requirements are listed in specgap/requirements.txt.

```bash
cd specgap
python -m venv .venv
. .venv/Scripts/Activate
pip install -r requirements.txt
```

### Frontend (Node)
Dependencies are managed via npm in Frontend/package.json.

```bash
cd Frontend
npm install
```

## Environment Variables

### Backend
Loaded via python-dotenv in specgap/app/core/config.py.

- GEMINI_API_KEY (required): Google Gemini API key.
- DATABASE_URL (optional): Overrides SQLite DB path.

Example .env:
```
GEMINI_API_KEY=your_key_here
DATABASE_URL=sqlite:///./specgap_audits.db
```

### Frontend
Defined in Vite and read in Frontend/src/api/client.ts.

- VITE_API_URL (optional): Base API URL. Defaults to /api which proxies to http://localhost:8000 in dev via Frontend/vite.config.ts.

Example .env:
```
VITE_API_URL=http://localhost:8000
```

## How to Run Locally

### Start Backend
```bash
cd specgap
python run_backend.py
```
Default: http://localhost:8000

### Start Frontend
```bash
cd Frontend
npm run dev
```
Default: http://localhost:8080

The dev server proxies /api to http://localhost:8000 automatically.

## API Endpoints

Implemented in specgap/app/main.py:

### Health
- GET /
  - Returns status and architecture info.

### Council Session
- POST /audit/council-session
  - Query: domain (optional, default Software Engineering)
  - Body: multipart form-data with files
  - Response: flashcards (council_verdict)

### Patch Pack Generator
- POST /audit/patch-pack
  - Body: JSON { selected_cards: [...], domain?: string }
  - Response: generated files (Contract_Addendum.txt, Spec_Update.md, Negotiation_Email.txt)

### Deep Analysis
- POST /audit/deep-analysis
  - Query: domain
  - Body: multipart form-data with files
  - Response: tech_audit, legal_audit, executive_synthesis

### Full Spectrum Analysis
- POST /audit/full-spectrum
  - Query: domain
  - Body: multipart form-data with files
  - Response: council verdict + deep analysis bundle

Note: The frontend client references additional endpoints (audits listing, comments, vector search) in Frontend/src/api/client.ts, but those routes are not present in the backend at this time.

## Contribution Guidelines
- Keep frontend code in Frontend/src/ with TypeScript, React, and Tailwind conventions.
- Keep backend code in specgap/app/ and follow async FastAPI patterns.
- Favor new endpoints and services in clearly named modules under specgap/app/services/.
- Update environment variable docs whenever introducing new config keys.
- Add unit tests where possible (frontend uses Vitest; backend currently has no test harness).
