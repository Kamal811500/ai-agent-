"""
Unit tests for the Interview State Machine.
"""
import pytest
from engines.state_machine import InterviewStateMachine, InvalidStateTransitionError
from models.interview import InterviewStatus


class TestStateMachine:
    def setup_method(self):
        self.sm = InterviewStateMachine()

    def test_valid_transitions(self):
        """All valid transitions from the whitelist should succeed."""
        assert self.sm.transition(InterviewStatus.CREATED, InterviewStatus.INITIALIZING) == InterviewStatus.INITIALIZING
        assert self.sm.transition(InterviewStatus.INITIALIZING, InterviewStatus.PLANNING) == InterviewStatus.PLANNING
        assert self.sm.transition(InterviewStatus.PLANNING, InterviewStatus.ASKING) == InterviewStatus.ASKING
        assert self.sm.transition(InterviewStatus.ASKING, InterviewStatus.WAITING_FOR_ANSWER) == InterviewStatus.WAITING_FOR_ANSWER
        assert self.sm.transition(InterviewStatus.WAITING_FOR_ANSWER, InterviewStatus.EVALUATING) == InterviewStatus.EVALUATING
        assert self.sm.transition(InterviewStatus.EVALUATING, InterviewStatus.FOLLOW_UP_DECISION) == InterviewStatus.FOLLOW_UP_DECISION
        assert self.sm.transition(InterviewStatus.FINAL_EVALUATION, InterviewStatus.COMPLETED) == InterviewStatus.COMPLETED

    def test_completed_is_terminal(self):
        """COMPLETED state must have no valid outbound transitions."""
        assert self.sm.is_terminal(InterviewStatus.COMPLETED)

    def test_completed_cannot_go_to_asking(self):
        """COMPLETED → ASKING must raise InvalidStateTransitionError."""
        with pytest.raises(InvalidStateTransitionError):
            self.sm.transition(InterviewStatus.COMPLETED, InterviewStatus.ASKING)

    def test_completed_cannot_accept_answer(self):
        """COMPLETED state cannot accept answers."""
        assert not self.sm.can_accept_answer(InterviewStatus.COMPLETED)

    def test_waiting_for_answer_can_accept(self):
        """WAITING_FOR_ANSWER is the only state that accepts answers."""
        assert self.sm.can_accept_answer(InterviewStatus.WAITING_FOR_ANSWER)

    def test_invalid_transition_raises(self):
        """Any non-whitelisted transition must raise."""
        with pytest.raises(InvalidStateTransitionError):
            self.sm.transition(InterviewStatus.CREATED, InterviewStatus.COMPLETED)

    def test_skip_states_raises(self):
        """Cannot skip states in the machine."""
        with pytest.raises(InvalidStateTransitionError):
            self.sm.transition(InterviewStatus.CREATED, InterviewStatus.ASKING)

    def test_can_transition_false_for_invalid(self):
        assert not self.sm.can_transition(InterviewStatus.COMPLETED, InterviewStatus.ASKING)

    def test_can_transition_true_for_valid(self):
        assert self.sm.can_transition(InterviewStatus.CREATED, InterviewStatus.INITIALIZING)
