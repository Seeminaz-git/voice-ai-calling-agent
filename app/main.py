"""FastAPI app exposing the voice agent over a Twilio-style webhook.

Run locally with:  uvicorn app.main:app --reload
"""
from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from app.models import CallSession
from app.pipeline import VoiceAgent

app = FastAPI(title="Voice AI Calling Agent")
agent = VoiceAgent()
sessions: dict[str, CallSession] = {}


class CallStart(BaseModel):
    call_sid: str


class CallTurn(BaseModel):
    call_sid: str
    utterance: str


@app.post("/calls/start")
def start_call(payload: CallStart):
    session = CallSession(call_sid=payload.call_sid)
    sessions[session.call_sid] = session
    audio = agent.handle_turn(session, b"")
    return {"call_sid": session.call_sid, "state": session.state, "reply_audio": audio.decode("utf-8")}


@app.post("/calls/turn")
def call_turn(payload: CallTurn):
    session = sessions.setdefault(payload.call_sid, CallSession(call_sid=payload.call_sid))
    audio = agent.handle_turn(session, payload.utterance.encode("utf-8"))
    return {
        "call_sid": session.call_sid,
        "state": session.state,
        "escalated": session.escalated,
        "reply_audio": audio.decode("utf-8"),
    }


@app.get("/calls/{call_sid}")
def get_call(call_sid: str):
    session = sessions.get(call_sid)
    if not session:
        return {"error": "not found"}
    return {
        "call_sid": session.call_sid,
        "state": session.state,
        "appointment": session.appointment,
        "transcript": session.transcript,
    }


@app.get("/health")
def health():
    return {"status": "ok"}
