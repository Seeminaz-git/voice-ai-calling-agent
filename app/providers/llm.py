"""Dialogue-management LLM providers.

`MockDialogueLLM` implements the same slot-filling state machine a real LLM
prompt would drive, so the booking flow is fully testable without an API key.
`AnthropicDialogueLLM` shows how a real deployment would delegate the same
decisions to Claude via tool calling.
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod

from app.models import Appointment, CallState


class DialogueLLM(ABC):
    @abstractmethod
    def next_turn(self, state: CallState, appointment: Appointment, user_text: str) -> tuple[str, CallState]:
        """Given conversation state + latest user utterance, return (assistant reply, next state)."""


class MockDialogueLLM(DialogueLLM):
    def next_turn(self, state: CallState, appointment: Appointment, user_text: str) -> tuple[str, CallState]:
        if state == CallState.GREETING:
            return ("Thanks for calling. Can I get your name, please?", CallState.COLLECT_NAME)

        if state == CallState.COLLECT_NAME:
            appointment.caller_name = user_text.strip().title()
            return (f"Thanks, {appointment.caller_name}. What's the reason for your visit?", CallState.COLLECT_REASON)

        if state == CallState.COLLECT_REASON:
            appointment.reason = user_text.strip()
            return ("Got it. What day and time works best for you?", CallState.COLLECT_TIME)

        if state == CallState.COLLECT_TIME:
            appointment.requested_time = user_text.strip()
            return (
                f"To confirm: {appointment.caller_name}, for '{appointment.reason}', "
                f"on {appointment.requested_time}. Shall I book that?",
                CallState.CONFIRM,
            )

        if state == CallState.CONFIRM:
            if user_text.strip().lower() in {"yes", "yes please", "confirm", "correct"}:
                appointment.confirmed = True
                return ("You're all set. You'll receive a confirmation shortly. Goodbye!", CallState.COMPLETED)
            return ("No problem, let's redo the time. What day and time works best?", CallState.COLLECT_TIME)

        return ("I'll connect you with a member of our team.", CallState.ESCALATED)


class AnthropicDialogueLLM(DialogueLLM):
    def __init__(self, api_key: str | None = None, model: str = "claude-sonnet-5"):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = model
        if not self.api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not configured")

    def next_turn(self, state: CallState, appointment: Appointment, user_text: str) -> tuple[str, CallState]:
        # Production implementation would call the Anthropic Messages API with
        # tool definitions for `set_caller_name`, `set_reason`, `set_time`,
        # `confirm_booking`, and `escalate_to_human`, letting Claude choose the
        # next tool call based on the transcript so far.
        raise NotImplementedError("Wire up the Anthropic SDK with a live API key")


def get_dialogue_llm() -> DialogueLLM:
    if os.environ.get("ANTHROPIC_API_KEY"):
        return AnthropicDialogueLLM()
    return MockDialogueLLM()
