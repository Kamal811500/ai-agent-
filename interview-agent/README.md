# AI Technical Interview Agent

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python" />
  <img src="https://img.shields.io/badge/FastAPI-0.115-green?style=flat-square&logo=fastapi" />
  <img src="https://img.shields.io/badge/Claude-3.5-orange?style=flat-square&logo=anthropic" />
  <img src="https://img.shields.io/badge/License-MIT-lightgrey?style=flat-square" />
</div>

---

## Overview

A production-quality **Adaptive AI Technical Interview Agent** that conducts conversational technical interviews, evaluates answers in real-time, and produces defensible structured evaluation reports.

**What makes it different from a chatbot:**
- Deterministic state machine controls the interview flow — LLM only provides intelligence
- Hard invariants enforced in code (≥8 questions, ≥4 curriculum days)
- Adaptive follow-up questions are genuinely based on what the candidate said
- Scoring is computed deterministically from LLM component scores — the model cannot arbitrarily inflate or deflate final scores
- Full prompt injection defense using `<CANDIDATE_ANSWER>` delimiters

---

## Architecture

```
Landing → Candidate Selection → Interview → Results Dashboard
              │
              ▼
         FastAPI Backend
              │
    ┌─────────┴──────────┐
    │  Interview Controller │
    └─────────┬──────────┘
              │
   ┌──────────┼──────────────┐
   ▼          ▼              ▼
State      Curriculum     Candidate
Machine    Engine         Engine
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
Answer    Follow-up      Skill
Evaluator  Engine        Tracker
              │
              ▼
       Final Evaluator
              │
              ▼
     Structured Report
```

---

## Quick Start

### Prerequisites
- Python 3.11+
- Anthropic API key (get one at [console.anthropic.com](https://console.anthropic.com))

### Installation

```bash
# 1. Clone / navigate to project
cd interview-agent

# 2. Create environment file
copy .env.example backend\.env
# Edit backend\.env and set your ANTHROPIC_API_KEY

# 3. Install dependencies
cd backend
pip install -r requirements.txt

# 4. Run the server
python main.py
```

Open **http://localhost:8000** in your browser.

### Docker (one command)

```bash
# Set your API key first
set ANTHROPIC_API_KEY=sk-ant-your-key-here

docker-compose up --build
```

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ Yes | — | Your Anthropic API key |
| `LLM_FAST_MODEL` | No | `claude-3-5-haiku-20241022` | Model for question/follow-up generation |
| `LLM_SMART_MODEL` | No | `claude-3-5-sonnet-20241022` | Model for evaluation and final report |
| `MIN_QUESTIONS_REQUIRED` | No | `8` | Hard minimum questions before completion |
| `MIN_CURRICULUM_DAYS` | No | `4` | Hard minimum curriculum days to cover |
| `MAX_FOLLOWUPS_PER_QUESTION` | No | `2` | Max follow-ups per primary question |
| `TARGET_QUESTIONS` | No | `10` | Target total questions per interview |
| `DEBUG` | No | `false` | Enable debug logging |
| `PORT` | No | `8000` | Server port |

---

## Running Tests

```bash
cd backend
pytest tests/ -v
```

### Golden Acceptance Test (proves all requirements)
```bash
pytest tests/test_golden.py -v
```

This test proves:
- ✅ `question_count >= 8`
- ✅ `unique_curriculum_days >= 4`
- ✅ `follow_up_count >= 1`
- ✅ Final feedback generated
- ✅ Prompt injection safe
- ✅ Duplicate submissions rejected
- ✅ Early completion prevented

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/interviews` | Start a new interview |
| `GET` | `/api/interviews/{id}` | Get interview state |
| `POST` | `/api/interviews/{id}/respond` | **Submit answer** (main endpoint) |
| `GET` | `/api/interviews/{id}/report` | Get final evaluation report |
| `GET` | `/api/candidates` | List sample candidates |
| `GET` | `/api/curriculum` | List curriculum days |
| `GET` | `/api/health` | Health check |

### Submit Answer Request

```json
POST /api/interviews/{interview_id}/respond
{
  "question_id": "uuid-of-current-question",
  "answer": "Candidate's typed response"
}
```

### Submit Answer Response

```json
{
  "interview_id": "...",
  "status": "WAITING_FOR_ANSWER",
  "current_question": "What trade-offs would you consider...",
  "current_question_id": "...",
  "question_number": 5,
  "curriculum_day": 4,
  "is_followup": true,
  "progress": {
    "question_count": 5,
    "unique_days_covered": 3,
    "follow_up_count": 2,
    "is_complete": false
  }
}
```

---

## Interview Lifecycle

```
1. Candidate selected → interview plan generated (LLM)
2. First question generated for planned curriculum day
3. Candidate submits answer
4. Answer evaluated → component scores (0-1) → deterministic final score (0-10)
5. Follow-up decision:
   - Partial answer + identified gaps → follow-up
   - Strong answer / max follow-ups → move to next topic
6. Difficulty adapts based on score window:
   - avg < 4.0 → decrease
   - avg 4.0–8.0 → maintain
   - avg > 8.0 → increase
7. Repeat until question_count ≥ 8 AND unique_days ≥ 4
8. Final report generated with deterministic recommendation
```

---

## Evaluation Scoring

| Dimension | Weight | Description |
|---|---|---|
| Technical Correctness | 30% | Is the content accurate? |
| Technical Depth | 20% | Surface vs deep understanding? |
| Problem Solving | 20% | Systematic reasoning? |
| Practical Application | 15% | Theory → real world? |
| Communication | 10% | Clear and logical? |
| Consistency | 5% | Consistent with prior answers? |

**Recommendation Thresholds:**

| Recommendation | Score | Conditions |
|---|---|---|
| STRONG_HIRE | ≥85 | 5+ topics, high confidence |
| HIRE | ≥70 | 4+ topics covered |
| BORDERLINE | 55–70 | Some gaps |
| NO_HIRE | <55 | Critical weaknesses |

---

## Security

- **Prompt injection defense:** Candidate answers wrapped in `<CANDIDATE_ANSWER>...</CANDIDATE_ANSWER>` delimiters, never inserted into system prompts
- **No secret leakage:** API keys only via environment variables, never logged or exposed in API responses
- **Input validation:** All inputs validated with Pydantic before processing
- **State protection:** Duplicate answer submissions rejected (idempotency)
- **Post-completion protection:** Completed interviews cannot accept new answers

---

## Curriculum

12-day AI/ML Engineering Bootcamp covering:

| Day | Topic |
|---|---|
| 1 | Python Fundamentals & Data Structures |
| 2 | Object-Oriented Programming & Design Patterns |
| 3 | Algorithms & Problem Solving |
| 4 | Databases & SQL |
| 5 | APIs & Backend Engineering |
| 6 | Machine Learning Fundamentals |
| 7 | Deep Learning & Neural Networks |
| 8 | Large Language Models & Transformers |
| 9 | MLOps & Production ML |
| 10 | System Design & Scalability |
| 11 | Cloud & Infrastructure |
| 12 | Security & Ethics in AI |

---

## Limitations

- Interview state is in-memory (not persisted across server restarts)
- Single-user concurrent design (suitable for demo/hackathon)
- No authentication layer

## Future Improvements

- Redis/PostgreSQL persistence for interview state
- WebSocket streaming for real-time typing effect
- Voice input support
- Authentication and multi-tenant support
- Custom curriculum upload
