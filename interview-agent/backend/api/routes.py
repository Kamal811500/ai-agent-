"""Main API routes for the interview system."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api", tags=["api"])

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

@router.get("/candidates")
async def list_candidates():
    """List available candidates."""
    return {"candidates": []}

@router.get("/curriculum")
async def list_curriculum():
    """List curriculum topics."""
    return {"curriculum": []}

@router.post("/interviews")
async def start_interview(candidate_id: str):
    """Start a new interview."""
    return {"interview_id": "test-123", "status": "WAITING_FOR_ANSWER"}

@router.get("/interviews/{interview_id}")
async def get_interview(interview_id: str):
    """Get interview state."""
    return {"interview_id": interview_id, "status": "WAITING_FOR_ANSWER"}

@router.post("/interviews/{interview_id}/respond")
async def submit_answer(interview_id: str, answer: str):
    """Submit an answer to a question."""
    return {"interview_id": interview_id, "status": "PROCESSING"}

@router.get("/interviews/{interview_id}/report")
async def get_report(interview_id: str):
    """Get interview evaluation report."""
    return {"interview_id": interview_id, "report": "pending"}
