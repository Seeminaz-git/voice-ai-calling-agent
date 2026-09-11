"""Orchestrates STT -> dialogue LLM -> TTS for one call turn, with confidence-based
human handoff and CRM sync on completion/escalation.
"""
from __future__ import annotations

from app.crm import CRMClient, get_crm_client
from app.models import CallSession, CallState
from app.providers.llm import DialogueLLM, get_dialogue_llm
from app.providers.stt import STTProvider, get_stt_provider
from app.providers.tts import TTSProvider, get_tts_provider

LOW_CONFIDENCE_THRESHOLD = 0.55
MAX_LOW_CONFIDENCE_TURNS = 2


class VoiceAgent:
    def __init__(
        self,
        stt: STTProvider | None = None,
        tts: TTSProvider | None = None,
        llm: DialogueLLM | None = None,
        crm: CRMClient | None = None,
    ) -> None:
        self.stt = stt or get_stt_provider()
        self.tts = tts or get_tts_provider()
        self.llm = llm or get_dialogue_llm()
        self.crm = crm or get_crm_client()

    def handle_turn(self, session: CallSession, audio_chunk: bytes) -> bytes:
        """Process one caller utterance and return synthesized audio for the reply.

        Escalates to a human whenever ASR confidence stays low for
        `MAX_LOW_CONFIDENCE_TURNS` consecutive turns, rather than looping the
        caller through a low-confidence dialogue indefinitely.
        """
        if session.state == CallState.GREETING and not audio_chunk:
            reply, next_state = self.llm.next_turn(session.state, session.appointment, "")
            session.state = next_state
            session.log_turn("assistant", reply)
            return self.tts.synthesize(reply)

        text, confidence = self.stt.transcribe(audio_chunk)
        session.log_turn("caller", text, confidence)

        if confidence < LOW_CONFIDENCE_THRESHOLD:
            session.low_confidence_turns += 1
        else:
            session.low_confidence_turns = 0

        if session.low_confidence_turns >= MAX_LOW_CONFIDENCE_TURNS:
            session.state = CallState.ESCALATED
            session.escalated = True
            reply = "I want to make sure I get this right for you — let me connect you with a member of our team."
            session.log_turn("assistant", reply)
            self.crm.upsert_appointment(session.call_sid, session.appointment, status="escalated")
            return self.tts.synthesize(reply)

        reply, next_state = self.llm.next_turn(session.state, session.appointment, text)
        session.state = next_state
        session.log_turn("assistant", reply)

        if session.state in (CallState.COMPLETED, CallState.ESCALATED):
            status = "confirmed" if session.appointment.confirmed else "incomplete"
            self.crm.upsert_appointment(session.call_sid, session.appointment, status=status)

        return self.tts.synthesize(reply)
