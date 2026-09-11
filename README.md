# Voice AI Calling Agent

A real-time voice AI pipeline (STT → LLM → TTS) that books appointments and
qualifies leads over the phone, syncs outcomes to a CRM, and hands off to a
human whenever speech-recognition confidence drops too low to trust an
automated response.

This is a portfolio/demo implementation showing the architecture and decision
logic behind a production voice-agent system: the same slot-filling dialogue
flow, confidence-based escalation, and CRM sync pattern, built with
provider-agnostic adapters so it runs standalone with no paid API keys, and
can be pointed at real Deepgram / ElevenLabs / Anthropic / Twilio / LiveKit
credentials for a live deployment.

## Architecture

```
Caller audio ─▶ STT (Deepgram / mock) ─▶ Dialogue LLM (slot-filling state machine)
                                                │
                        ┌───────────────────────┼───────────────────────┐
                        ▼                       ▼                       ▼
                 low-confidence            normal turn              booking
                 (2+ turns) ──▶ escalate    ──▶ reply           confirmed/failed
                                  │                                     │
                                  └──────────────▶ CRM sync ◀───────────┘
                                                     │
                                                     ▼
                                          TTS (ElevenLabs / mock)
```

- **STT** (`app/providers/stt.py`): pluggable — `DeepgramSTT` for production,
  `MockSTT` for local runs/tests (scores short/ambiguous utterances as
  low-confidence, the same way real ASR degrades on noisy audio).
- **Dialogue management** (`app/providers/llm.py`): a slot-filling state
  machine (name → reason → time → confirm) that a real deployment would
  delegate to an LLM via tool calling; the mock implements the identical
  state transitions so the flow is fully testable.
- **Confidence-based handoff** (`app/pipeline.py`): escalates to a human after
  2 consecutive low-confidence turns instead of looping the caller through a
  broken conversation.
- **CRM sync** (`app/crm.py`): upserts appointment status (`confirmed` /
  `incomplete` / `escalated`) whenever a call reaches a terminal state.
- **TTS** (`app/providers/tts.py`): pluggable — `ElevenLabsTTS` for
  production, `MockTTS` for local runs/tests.

## Running locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

```bash
curl -X POST localhost:8000/calls/start -H "Content-Type: application/json" -d '{"call_sid": "CA1"}'
curl -X POST localhost:8000/calls/turn  -H "Content-Type: application/json" -d '{"call_sid": "CA1", "utterance": "Jane Doe"}'
curl -X POST localhost:8000/calls/turn  -H "Content-Type: application/json" -d '{"call_sid": "CA1", "utterance": "annual checkup"}'
curl -X POST localhost:8000/calls/turn  -H "Content-Type: application/json" -d '{"call_sid": "CA1", "utterance": "next Tuesday at 10am"}'
curl -X POST localhost:8000/calls/turn  -H "Content-Type: application/json" -d '{"call_sid": "CA1", "utterance": "yes please"}'
curl localhost:8000/calls/CA1
```

## Tests

```bash
pytest
```

Covers the happy-path booking flow, low-confidence escalation, and rejected
confirmations looping back to time collection.

## Going to production

Set the relevant keys from `.env.example` (Deepgram, ElevenLabs, Anthropic,
Twilio, LiveKit) — each provider module falls back to its live implementation
automatically once its API key is present. Twilio webhooks would replace the
demo `/calls/*` REST endpoints, and LiveKit would handle the real-time audio
transport in place of the text-based `utterance` field used here for
testability.

## Tech stack

Python, FastAPI, LiveKit, Deepgram, ElevenLabs, Twilio, Anthropic Claude API.
