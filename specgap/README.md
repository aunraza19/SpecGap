# SpecGap 🔍

**AI-Powered Specification Gap & Contract Risk Analyzer**

SpecGap uses a multi-agent AI council to analyze technical specifications, business proposals, and contracts to detect gaps, risks, and negotiation opportunities.

## 🏗️ Architecture

SpecGap employs a **3-Loop Recursive Consensus** system:

```
┌─────────────────────────────────────────────────────────────┐
│                    COUNCIL WORKFLOW                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Round 1: BLIND DRAFT                                        │
│  ┌─────────┐  ┌──────────┐  ┌─────────┐                     │
│  │  Legal  │  │ Business │  │ Finance │  (Independent)       │
│  └────┬────┘  └────┬─────┘  └────┬────┘                     │
│       │            │             │                           │
│       ▼            ▼             ▼                           │
│  Round 2: CROSS-CHECK                                        │
│  ┌─────────┐  ┌──────────┐  ┌─────────┐                     │
│  │  Legal  │◄─┤ Business ├─►│ Finance │  (Peer Review)       │
│  └────┬────┘  └────┬─────┘  └────┬────┘                     │
│       │            │             │                           │
│       ▼            ▼             ▼                           │
│  Round 3: VERDICT                                            │
│  ┌─────────────────────────────────────┐                    │
│  │         FLASHCARD GENERATION         │                    │
│  │    (Actionable, Swipeable Cards)     │                    │
│  └─────────────────────────────────────┘                    │
│                      │                                       │
│                      ▼                                       │
│  ┌─────────────────────────────────────┐                    │
│  │            PATCH PACK                │                    │
│  │  • Contract Addendum                 │                    │
│  │  • Spec Updates                      │                    │
│  │  • Negotiation Email                 │                    │
│  └─────────────────────────────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Google Gemini API Key ([Get one here](https://makersuite.google.com/app/apikey))

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/SpecGap.git
cd SpecGap/specgap

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Run the server
python run_backend.py
```

### Access the API

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/

## 📡 API Endpoints

### Audit Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/audit/council-session` | POST | Quick analysis with flashcards |
| `/api/v1/audit/deep-analysis` | POST | Comprehensive tech + legal audit |
| `/api/v1/audit/full-spectrum` | POST | Combined council + deep analysis |
| `/api/v1/audit/patch-pack` | POST | Generate fix documents |

### Document Utilities

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/documents/classify` | POST | Classify document type |
| `/api/v1/documents/extract` | POST | Extract text without analysis |

### Audit History

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/audits` | GET | List all audits |
| `/api/v1/audits/{id}` | GET | Get audit details |
| `/api/v1/audits/statistics` | GET | Dashboard statistics |

## 🤖 AI Agents

### Legal Agent (Corporate General Counsel)
- Liability and indemnification clauses
- IP ownership issues
- Termination rights
- Contract traps

### Business Agent (COO)
- Operational viability
- Feature completeness vs. promises
- Timeline realism
- Deliverable clarity

### Finance Agent (CFO)
- Hidden costs
- Payment terms
- ROI projections
- Budget risk

## 📁 Project Structure

```
specgap/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py        # Settings & Gemini config
│   │   ├── database.py      # SQLAlchemy models & repos
│   │   ├── exceptions.py    # Custom exceptions
│   │   ├── logging.py       # Logging configuration
│   │   ├── middleware.py    # Request tracking, rate limiting
│   │   └── prompts.py       # Council prompt templates
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── responses.py     # Pydantic models
│   └── services/
│       ├── __init__.py
│       ├── workflow.py      # LangGraph council workflow
│       ├── tech_engine.py   # Tech gap analyzer
│       ├── biz_engine.py    # Legal/business analyzer
│       ├── cross_check.py   # Synthesis orchestrator
│       ├── patch_pack.py    # Document generator
│       └── parser.py        # File extraction
├── requirements.txt
├── run_backend.py
├── .env.example
└── README.md
```

## 🔧 Configuration

Key environment variables (see `.env.example`):

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | Required |
| `ENV` | Environment mode | `development` |
| `GEMINI_MODEL_TEXT` | Text model | `gemini-2.0-flash` |
| `AI_REQUEST_DELAY` | Delay between AI calls | `2.0` |
| `MAX_CONTEXT_CHARS` | Max document size | `100000` |

## 📊 Example Response (Council Session)

```json
{
  "status": "success",
  "files_analyzed": ["contract.pdf", "tech_spec.docx"],
  "domain": "Software Engineering",
  "council_verdict": {
    "flashcards": [
      {
        "id": "legal_1",
        "card_type": "Risk",
        "title": "Unlimited Liability Exposure",
        "description": "Contract has no liability cap. Client could be liable for unlimited damages.",
        "fix_action": "Add Liability Cap",
        "severity": "Critical",
        "swipe_right_payload": "Liability Cap: Total liability shall not exceed the fees paid under this agreement.",
        "source_agent": "legal"
      }
    ],
    "summary": {
      "total_cards": 12,
      "by_agent": {"legal": 4, "business": 5, "finance": 3}
    }
  }
}
```

## 🧪 Testing

```bash
# Run tests (when implemented)
pytest tests/ -v

# Test with sample documents
curl -X POST "http://localhost:8000/api/v1/audit/council-session" \
  -F "files=@sample_contract.pdf" \
  -F "files=@tech_spec.docx"
```

## 🛣️ Roadmap

- [ ] WebSocket for real-time progress
- [ ] PDF annotation with highlights
- [ ] Custom agent personas
- [ ] Multi-language support
- [ ] Enterprise SSO integration
- [ ] Webhook notifications

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

