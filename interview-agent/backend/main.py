"""
FastAPI application entry point with error handling.
"""
from __future__ import annotations

import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError

try:
    from config import get_settings
except ImportError as e:
    print(f"ERROR: Failed to import config: {e}", file=sys.stderr)
    sys.exit(1)

# Configure structured logging before imports
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

try:
    settings = get_settings()
except Exception as e:
    logger.error(f"Failed to load settings: {e}")
    settings = None

# ─── Dependency setup ───────────────────────────────────────────────────────

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

    try:
        # Resolve data directory
        backend_dir = Path(__file__).parent
        data_dir = backend_dir / settings.data_dir

        # Initialize repositories
        try:
            from models.candidate import CandidateRepository
            from models.curriculum import CurriculumRepository
            candidate_repo = CandidateRepository(str(data_dir / "candidates.json"))
            curriculum_repo = CurriculumRepository(str(data_dir / "curriculum.json"))
            logger.info(f"Loaded {len(candidate_repo.list_all())} candidates")
            logger.info(f"Loaded {curriculum_repo.total_days()} curriculum days")
        except Exception as e:
            logger.error(f"Failed to load repositories: {e}")
            candidate_repo = None
            curriculum_repo = None

        # Initialize LangChain LLM provider
        try:
            from llm.langchain_provider import LangChainProvider, set_mcp_executor
            llm = LangChainProvider()
            logger.info("LLM provider initialized")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            llm = None

        # ── RAG: Build knowledge base index ────────
        try:
            logger.info("Initializing RAG knowledge base...")
            from rag.retriever import RAGRetriever
            import asyncio as _asyncio
            rag_retriever = await _asyncio.get_event_loop().run_in_executor(None, RAGRetriever)
            logger.info(f"RAG ready: {len(rag_retriever._docs)} knowledge entries indexed")
        except Exception as e:
            logger.warning(f"RAG initialization warning: {e}")
            rag_retriever = None

        # ── MCP: Initialize tool executor ──────────
        try:
            if rag_retriever:
                from mcp.tools import MCPToolExecutor
                mcp_executor = MCPToolExecutor(rag_retriever)
                set_mcp_executor(mcp_executor)
                logger.info("MCP tools registered")
        except Exception as e:
            logger.warning(f"MCP initialization warning: {e}")

        # ── Register RAG in engines ────────────────
        try:
            if rag_retriever:
                from engines.question_engine import set_rag_retriever as qe_set_rag
                from engines.answer_evaluator import set_rag_retriever as ae_set_rag
                qe_set_rag(rag_retriever)
                ae_set_rag(rag_retriever)
        except Exception as e:
            logger.warning(f"RAG registration warning: {e}")

        # Initialize engines
        try:
            from engines.answer_evaluator import AnswerEvaluator
            from engines.difficulty_selector import DifficultySelector
            from engines.final_evaluator import FinalEvaluator
            from engines.interview_controller import InterviewController
            from engines.interview_planner import InterviewPlanner
            from engines.question_engine import QuestionEngine
            from engines.skill_tracker import SkillTracker

            if all([candidate_repo, curriculum_repo, llm]):
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
                logger.info("AI Interview Agent ready")
            else:
                logger.warning("Some components failed to initialize, running in degraded mode")
        except Exception as e:
            logger.error(f"Failed to initialize engines: {e}")
            _controller = None

    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise

    yield  # Application runs

    logger.info("AI Interview Agent shutting down.")


# ─── FastAPI App ─────────────────────────────────────────────────────────

app = FastAPI(
    title="AI Technical Interview Agent",
    description="Adaptive AI-powered technical interview system with evidence-based evaluation",
    version=settings.app_version if settings else "1.0.0",
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


# Error handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": "Invalid request", "errors": str(exc)},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# API Routes
try:
    from api.routes import router
    from api.auth import router as auth_router
    app.include_router(router)
    app.include_router(auth_router)
except Exception as e:
    logger.error(f"Failed to load API routes: {e}")

# Serve frontend
frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    @app.get("/", include_in_schema=False)
    async def serve_frontend():
        index_file = frontend_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        else:
            return JSONResponse({"error": "Frontend not found"}, status_code=404)
else:
    @app.get("/", include_in_schema=False)
    async def serve_frontend_error():
        return JSONResponse({"error": "Frontend directory not found"}, status_code=404)


if __name__ == "__main__":
    import uvicorn
    
    host = settings.host if settings else "0.0.0.0"
    port = settings.port if settings else 8000
    debug = settings.debug if settings else False
    log_level = settings.log_level.lower() if settings else "info"
    
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level=log_level,
    )
