"""
Explicit Interview State Machine.

Enforces valid state transitions. Invalid transitions raise InvalidStateTransitionError.
This is the gatekeeper — nothing in the application changes interview state without
going through the state machine.
"""
from __future__ import annotations

from typing import Dict, Set

from models.interview import InterviewStatus


class InvalidStateTransitionError(Exception):
    """Raised when an illegal state transition is attempted."""
    def __init__(self, from_state: InterviewStatus, to_state: InterviewStatus):
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(
            f"Invalid state transition: {from_state.value} → {to_state.value}"
        )


# ─── Valid transition graph ────────────────────────────────────────────────────
# Every transition must be explicitly listed here.
# Any transition NOT listed is FORBIDDEN.

VALID_TRANSITIONS: Dict[InterviewStatus, Set[InterviewStatus]] = {
    InterviewStatus.CREATED: {
        InterviewStatus.INITIALIZING,
    },
    InterviewStatus.INITIALIZING: {
        InterviewStatus.PLANNING,
    },
    InterviewStatus.PLANNING: {
        InterviewStatus.ASKING,
    },
    InterviewStatus.ASKING: {
        InterviewStatus.WAITING_FOR_ANSWER,
    },
    InterviewStatus.WAITING_FOR_ANSWER: {
        InterviewStatus.EVALUATING,
    },
    InterviewStatus.EVALUATING: {
        InterviewStatus.FOLLOW_UP_DECISION,
    },
    InterviewStatus.FOLLOW_UP_DECISION: {
        # Follow-up: go back to asking (follow-up question)
        InterviewStatus.ASKING,
        # New topic: go back to planning
        InterviewStatus.PLANNING,
        # Enough evidence for completion check
        InterviewStatus.FINAL_EVALUATION,
    },
    InterviewStatus.FINAL_EVALUATION: {
        InterviewStatus.COMPLETED,
    },
    # Terminal state — no outbound transitions
    InterviewStatus.COMPLETED: set(),
}


class InterviewStateMachine:
    """
    Manages and enforces interview state transitions.
    Stateless: operates on the InterviewStatus enum, not on InterviewState objects.
    """

    @staticmethod
    def transition(
        current: InterviewStatus,
        target: InterviewStatus,
    ) -> InterviewStatus:
        """
        Attempt a state transition. Returns new state on success.
        Raises InvalidStateTransitionError on invalid transition.
        """
        allowed = VALID_TRANSITIONS.get(current, set())
        if target not in allowed:
            raise InvalidStateTransitionError(current, target)
        return target

    @staticmethod
    def can_transition(
        current: InterviewStatus,
        target: InterviewStatus,
    ) -> bool:
        """Check if a transition is valid without raising."""
        allowed = VALID_TRANSITIONS.get(current, set())
        return target in allowed

    @staticmethod
    def is_terminal(status: InterviewStatus) -> bool:
        """Return True if the state is a terminal (no outbound transitions)."""
        return len(VALID_TRANSITIONS.get(status, set())) == 0

    @staticmethod
    def can_accept_answer(status: InterviewStatus) -> bool:
        """Return True only if the interview is currently waiting for an answer."""
        return status == InterviewStatus.WAITING_FOR_ANSWER

    @staticmethod
    def is_completed(status: InterviewStatus) -> bool:
        return status == InterviewStatus.COMPLETED
