from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class CallState(str, Enum):
    GREETING = "greeting"
    COLLECT_NAME = "collect_name"
    COLLECT_REASON = "collect_reason"
    COLLECT_TIME = "collect_time"
    CONFIRM = "confirm"
    ESCALATED = "escalated"
    COMPLETED = "completed"


@dataclass
class Appointment:
    caller_name: Optional[str] = None
    reason: Optional[str] = None
    requested_time: Optional[str] = None
    confirmed: bool = False


@dataclass
class CallSession:
    call_sid: str
    state: CallState = CallState.GREETING
    appointment: Appointment = field(default_factory=Appointment)
    transcript: list[dict] = field(default_factory=list)
    low_confidence_turns: int = 0
    escalated: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)

    def log_turn(self, speaker: str, text: str, confidence: float | None = None) -> None:
        self.transcript.append(
            {
                "speaker": speaker,
                "text": text,
                "confidence": confidence,
                "ts": datetime.utcnow().isoformat(),
            }
        )
