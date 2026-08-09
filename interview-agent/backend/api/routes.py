"""
FastAPI HTTP routes — complete API contract.
Supports both pre-seeded candidates and dynamic user-profile interviews.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from engines.interview_controller import (
    DuplicateAnswerError,
    InterviewAlreadyCompletedError,
    InterviewController,
    InterviewControllerError,
    InterviewNotFoundError,
    InvariantViolationError,
)
from engines.state_machine import InvalidStateTransitionError
from models.candidate import CandidateProfile
from models.interview import InterviewStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["interview"])


def get_controller() -> InterviewController:
    from main import get_interview_controller
    return get_interview_controller()


# ─── Request/Response Models ──────────────────────────────────────────────────

class StartInterviewRequest(BaseModel):
    candidate_id: str


class StartWithProfileRequest(BaseModel):
    """Start an interview from a user-submitted profile form."""
    name: str
    email: str = ""
    role: str
    experience_years: int = 1
    skills: List[str] = []
    focus_areas: List[str] = []


class SubmitAnswerRequest(BaseModel):
    question_id: str
    answer: str = ""


# ─── Response builder ────────────────────────────────────────────────────────

def _build_response(state) -> Dict[str, Any]:
    current_q = state.current_question
    coverage = {
        day: {
            "topic": cov.topic,
            "questions": cov.questions_asked,
            "avg_score": round(cov.average_score, 1),
            "strength": cov.evidence_strength.value,
        }
        for day, cov in state.curriculum_coverage.items()
    }
    return {
        "interview_id": state.id,
        "status": state.status.value,
        "current_question": current_q.text if current_q else None,
        "current_question_id": current_q.id if current_q else None,
        "question_number": state.question_count,
        "curriculum_day": current_q.curriculum_day if current_q else None,
        "curriculum_topic": current_q.topic if current_q else None,
        "difficulty": current_q.difficulty.value if current_q else None,
        "question_type": current_q.question_type.value if current_q else None,
        "is_followup": current_q.is_followup if current_q else False,
        "progress": {
            "question_count": state.question_count,
            "unique_days_covered": state.unique_curriculum_days,
            "follow_up_count": state.total_follow_up_count,
            "min_questions_required": 8,
            "min_days_required": 4,
            "curriculum_coverage": coverage,
            "is_complete": state.status == InterviewStatus.COMPLETED,
        },
        "message": None,
    }


# ─── Auth check helper ───────────────────────────────────────────────────────

def _error(code: int, msg: str):
    raise HTTPException(status_code=code, detail=msg)


# ─── Routes ──────────────────────────────────────────────────────────────────

@router.post("/interviews/start", status_code=status.HTTP_201_CREATED,
             summary="Start interview from user profile form")
async def start_with_profile(
    request: StartWithProfileRequest,
    controller: InterviewController = Depends(get_controller),
):
    """
    Main entry point for the UI flow.
    Creates a dynamic candidate from user-submitted profile, then starts an interview.
    """
    if len(request.name.strip()) < 2:
        raise HTTPException(400, "Name must be at least 2 characters.")
    if len(request.skills) == 0:
        raise HTTPException(400, "Please add at least one skill.")

    exp = max(0, min(request.experience_years, 50))
    level = "junior" if exp < 2 else "mid" if exp < 6 else "senior"

    candidate = CandidateProfile(
        id=f"dyn_{uuid.uuid4().hex[:10]}",
        name=request.name.strip(),
        email=request.email.strip(),
        level=level,
        years_experience=exp,
        role_applied=request.role.strip() or "Software Engineer",
        self_reported_skills=request.skills[:20],
        focus_areas=request.focus_areas,
        interview_strategy_hint=(
            f"Focus on {', '.join(request.focus_areas)} topics. "
            f"Candidate is {level}-level with {exp} years experience."
            if request.focus_areas else
            f"Candidate is {level}-level with {exp} years experience."
        ),
    )

    try:
        controller.candidate_repo.register(candidate)
        state = await controller.start_interview(candidate.id)
        return _build_response(state)
    except Exception as e:
        logger.exception("Failed to start interview with profile")
        raise HTTPException(500, f"Failed to start interview: {str(e)}")


@router.post("/interviews", status_code=status.HTTP_201_CREATED,
             summary="Start interview with pre-seeded candidate (legacy)")
async def start_interview(
    request: StartInterviewRequest,
    controller: InterviewController = Depends(get_controller),
):
    try:
        state = await controller.start_interview(request.candidate_id)
        return _build_response(state)
    except InterviewNotFoundError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/interviews/{interview_id}", summary="Get interview state")
async def get_interview(
    interview_id: str,
    controller: InterviewController = Depends(get_controller),
):
    try:
        state = controller.get_interview(interview_id)
        return _build_response(state)
    except InterviewNotFoundError as e:
        raise HTTPException(404, str(e))


@router.post("/interviews/{interview_id}/respond", summary="Submit answer")
async def submit_answer(
    interview_id: str,
    request: SubmitAnswerRequest,
    controller: InterviewController = Depends(get_controller),
):
    if not interview_id.strip():
        raise HTTPException(400, "interview_id required")
    try:
        state = await controller.submit_answer(
            interview_id=interview_id,
            question_id=request.question_id,
            answer_text=request.answer,
        )
        resp = _build_response(state)
        if state.status == InterviewStatus.COMPLETED:
            resp["message"] = "Interview complete! Generating your evaluation report..."
        return resp
    except InterviewNotFoundError as e:
        raise HTTPException(404, str(e))
    except InterviewAlreadyCompletedError as e:
        raise HTTPException(409, str(e))
    except DuplicateAnswerError as e:
        raise HTTPException(409, str(e))
    except InvalidStateTransitionError as e:
        raise HTTPException(409, str(e))
    except InvariantViolationError as e:
        raise HTTPException(422, str(e))
    except InterviewControllerError as e:
        raise HTTPException(500, str(e))
    except Exception as e:
        logger.exception("Unexpected error")
        raise HTTPException(500, "Internal server error")


@router.get("/interviews/{interview_id}/report", summary="Get final report")
async def get_report(
    interview_id: str,
    controller: InterviewController = Depends(get_controller),
):
    try:
        state = controller.get_interview(interview_id)
        if state.status != InterviewStatus.COMPLETED:
            raise HTTPException(404, f"Report not ready. Status: {state.status.value}")
        report = controller.get_report(interview_id)
        if not report:
            raise HTTPException(404, "Report not found")
        return report.model_dump()
    except InterviewNotFoundError as e:
        raise HTTPException(404, str(e))


@router.get("/candidates", summary="List sample candidates")
async def list_candidates(controller: InterviewController = Depends(get_controller)):
    return [
        {
            "id": c.id, "name": c.name, "level": c.level,
            "years_experience": c.years_experience, "education": c.education,
            "role_applied": c.role_applied, "self_reported_skills": c.self_reported_skills,
            "projects": [{"name": p.name, "description": p.description, "tech": p.tech} for p in c.projects],
        }
        for c in controller.list_candidates()
    ]


@router.get("/curriculum", summary="List curriculum")
async def list_curriculum(controller: InterviewController = Depends(get_controller)):
    return [
        {"day": d.day, "title": d.title, "topics": d.topics, "difficulty_range": d.difficulty_range}
        for d in controller.list_curriculum()
    ]


@router.get("/health")
async def health():
    return {"status": "healthy", "service": "AI Interview Agent"}
