# AI Agent Repository

This repository contains an **AI Technical Interview Agent** - a production-quality adaptive interviewing system powered by Claude AI.

## 📁 Project Structure

```
ai-agent-/
├── interview-agent/                 # Main application
│   ├── backend/                     # FastAPI backend (Python)
│   │   ├── api/                     # API routes and endpoints
│   │   ├── engines/                 # Core interview engines
│   │   ├── llm/                     # LLM provider (Claude)
│   │   ├── models/                  # Data models (Candidates, Curriculum)
│   │   ├── prompts/                 # LLM prompts
│   │   ├── rag/                     # RAG knowledge retrieval
│   │   ├── mcp/                     # MCP tool execution
│   │   ├── data/                    # Data files (candidates.json, curriculum.json)
│   │   ├── tests/                   # Test suite
│   │   ├── main.py                  # FastAPI application entry
│   │   ├── config.py                # Configuration management
│   │   ├── requirements.txt         # Python dependencies
│   │   ├── .env.example             # Environment template
│   │   └── pytest.ini               # Test configuration
│   │
│   ├── frontend/                    # Frontend UI (HTML)
│   │   └── index.html               # Single-page application
│   │
│   ├── Dockerfile                   # Docker container definition
│   ├── docker-compose.yml           # Docker Compose configuration
│   ├── start.bat                    # Windows startup script
│   └── README.md                    # Detailed documentation
│
├── .env.example                     # Root environment template
├── .gitignore                       # Git ignore rules
└── README.md                        # This file
```

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+**
- **Anthropic API Key** ([Get one here](https://console.anthropic.com))
- **Docker** (optional, for containerized deployment)

### Local Setup

1. **Clone & Navigate**
   ```bash
   cd interview-agent
   ```

2. **Setup Environment**
   ```bash
   # Copy environment template
   cp backend/.env.example backend/.env
   
   # Edit and add your API key
   # Edit backend/.env and set: ANTHROPIC_API_KEY=sk-ant-...
   ```

3. **Install Dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Run Application**
   ```bash
   python main.py
   ```
   
   Visit: **http://localhost:8000**

### Docker Setup

```bash
# Set API key
export ANTHROPIC_API_KEY=sk-ant-your-key-here

# Run with Docker Compose
docker-compose up --build
```

## 🛠️ Configuration

All settings are managed via environment variables. See `backend/.env.example` for all available options:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | ✅ | — | Anthropic API key |
| `DEBUG` | ❌ | `false` | Debug mode |
| `PORT` | ❌ | `8000` | Server port |
| `LLM_FAST_MODEL` | ❌ | `claude-3-5-haiku-20241022` | Question generation model |
| `LLM_SMART_MODEL` | ❌ | `claude-3-5-sonnet-20241022` | Evaluation model |
| `MIN_QUESTIONS_REQUIRED` | ❌ | `8` | Minimum questions |
| `MIN_CURRICULUM_DAYS` | ❌ | `4` | Minimum curriculum coverage |

## 📚 Key Features

- ✅ **Deterministic State Machine** - Interview flow controlled by code, not LLM
- ✅ **Adaptive Questions** - Difficulty adjusts based on performance
- ✅ **Prompt Injection Defense** - Safe candidate answer handling
- ✅ **RAG Integration** - Knowledge base retrieval
- ✅ **MCP Tools** - Extensible tool execution
- ✅ **Real-time Evaluation** - Immediate scoring and feedback
- ✅ **Structured Reports** - Comprehensive evaluation summaries

## 🧪 Testing

Run the test suite:

```bash
cd backend
pytest tests/ -v
```

Run golden acceptance tests (prove all requirements):

```bash
pytest tests/test_golden.py -v
```

## 📡 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/interviews` | Start new interview |
| `GET` | `/api/interviews/{id}` | Get interview state |
| `POST` | `/api/interviews/{id}/respond` | Submit answer |
| `GET` | `/api/interviews/{id}/report` | Get evaluation report |
| `GET` | `/api/candidates` | List candidates |
| `GET` | `/api/curriculum` | List curriculum |
| `GET` | `/api/health` | Health check |

## 🌐 Deployment

### Vercel Deployment

The project is configured for Vercel deployment at: **https://interview-agent-opal.vercel.app**

**Deployment Checklist:**
- [ ] Set `ANTHROPIC_API_KEY` in Vercel Environment Variables
- [ ] Verify Vercel can access your GitHub repository
- [ ] Check deployment logs for errors
- [ ] Test `/api/health` endpoint

### Local Docker Deployment

```bash
docker build -t interview-agent:latest .
docker run -p 8000:8000 -e ANTHROPIC_API_KEY=sk-ant-... interview-agent:latest
```

## 📖 Architecture

```
Landing → Candidate Selection → Interview → Results Dashboard
              │
              ▼
         FastAPI Backend
              │
    ┌─────────┴──────────┐
    │ Interview Controller│
    └─────────┬──────────┘
              │
   ┌──────────┼──────────────┐
   ▼          ▼              ▼
State     Curriculum    Candidate
Machine   Engine        Engine
   │          │              │
   └──────────┼──────────────┘
              ▼
       Interview Planner
              │
              ▼
       Question Engine
              │
              ▼
           Claude API
              │
   ┌──────────┼──────────────┐
   ▼          ▼              ▼
Answer   Follow-up      Skill
Evaluator Engine        Tracker
              │
              ▼
       Final Evaluator
              │
              ▼
     Structured Report
```

## 🔐 Security

- **Prompt Injection Defense**: Answers wrapped in `<CANDIDATE_ANSWER>...</CANDIDATE_ANSWER>` delimiters
- **No Secret Leakage**: API keys only via environment variables
- **Input Validation**: Pydantic validation on all inputs
- **State Protection**: Duplicate submissions rejected
- **Post-Completion Protection**: Completed interviews locked

## 📝 Scoring System

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Technical Correctness | 30% | Content accuracy |
| Technical Depth | 20% | Understanding level |
| Problem Solving | 20% | Systematic reasoning |
| Practical Application | 15% | Real-world applicability |
| Communication | 10% | Clarity and logic |
| Consistency | 5% | Internal consistency |

### Recommendations
- **STRONG_HIRE**: Score ≥ 85 (5+ topics, high confidence)
- **HIRE**: Score ≥ 70 (4+ topics covered)
- **BORDERLINE**: Score 55-70 (some gaps)
- **NO_HIRE**: Score < 55 (critical weaknesses)

## 📞 Support & Issues

For bugs or feature requests, open an issue on GitHub: 
[github.com/Kamal811500/ai-agent-/issues](https://github.com/Kamal811500/ai-agent-/issues)

## 📄 License

MIT License - See LICENSE file for details

## 🚦 Status

- **Repository**: Active Development
- **Deployment**: https://interview-agent-opal.vercel.app
- **Last Updated**: 2026-08-09
