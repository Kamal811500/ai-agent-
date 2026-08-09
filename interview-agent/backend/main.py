"""
FastAPI application entry point.
"""
from __future__ import annotations

import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from config import get_settings

# Configure structured logging before imports
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()

# ─── Dependency setup ─────────────────────────────────────────────────────────

_controller = None  # Singleton interview controller


def get_interview_controller():
    global _controller
    if _controller is None:
        raise RuntimeError("Controller not initialized. Application startup incomplete.")
    return _controller


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    global _controller

    logger.info("Starting AI Interview Agent...")

    # Resolve data directory
    backend_dir = Path(__file__).parent
    data_dir = backend_dir / settings.data_dir

    # Initialize repositories
    from models.candidate import CandidateRepository
    from models.curriculum import CurriculumRepository
    candidate_repo = CandidateRepository(str(data_dir / "candidates.json"))
    curriculum_repo = CurriculumRepository(str(data_dir / "curriculum.json"))

    # Initialize LangChain LLM provider
    from llm.langchain_provider import LangChainProvider, set_mcp_executor
    llm = LangChainProvider()

    # ── RAG: Build knowledge base index in thread (TF-IDF is CPU-bound) ────────
    logger.info("Initializing RAG knowledge base...")
    from rag.retriever import RAGRetriever
    import asyncio as _asyncio
    rag_retriever = await _asyncio.get_event_loop().run_in_executor(None, RAGRetriever)

    # ── MCP: Initialize tool executor and register ──────────────────────────────
    from mcp.tools import MCPToolExecutor
    mcp_executor = MCPToolExecutor(rag_retriever)
    set_mcp_executor(mcp_executor)  # Registers in AnthropicProvider

    # ── Register RAG in engines ────────────────────────────────────────────────
    from engines.question_engine import set_rag_retriever as qe_set_rag
    from engines.answer_evaluator import set_rag_retriever as ae_set_rag
    qe_set_rag(rag_retriever)
    ae_set_rag(rag_retriever)
    logger.info(f"RAG+MCP ready: {len(rag_retriever._docs)} knowledge entries indexed")

    # Initialize engines
    from engines.answer_evaluator import AnswerEvaluator
    from engines.difficulty_selector import DifficultySelector
    from engines.final_evaluator import FinalEvaluator
    from engines.interview_controller import InterviewController
    from engines.interview_planner import InterviewPlanner
    from engines.question_engine import QuestionEngine
    from engines.skill_tracker import SkillTracker

    _controller = InterviewController(
        candidate_repo=candidate_repo,
        curriculum_repo=curriculum_repo,
        planner=InterviewPlanner(llm, curriculum_repo),
        question_engine=QuestionEngine(llm),
        answer_evaluator=AnswerEvaluator(llm),
        difficulty_selector=DifficultySelector(llm),
        skill_tracker=SkillTracker(),
        final_evaluator=FinalEvaluator(llm),
    )

    logger.info(
        "AI Interview Agent ready",
        extra={
            "candidates": len(candidate_repo.list_all()),
            "curriculum_days": curriculum_repo.total_days(),
        },
    )

    yield  # Application runs

    logger.info("AI Interview Agent shutting down.")


# ─── FastAPI App ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="AI Technical Interview Agent",
    description="Adaptive AI-powered technical interview system with evidence-based evaluation",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
from api.routes import router
from api.auth import router as auth_router
app.include_router(router)
app.include_router(auth_router)

# Serve frontend
frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    @app.get("/", include_in_schema=False)
    async def serve_frontend():
        return FileResponse(str(frontend_dir / "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
