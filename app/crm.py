"""CRM sync layer.

Ships an in-memory CRM so the pipeline is runnable/testable standalone. Swap
`InMemoryCRM` for a real client (e.g. HubSpot, Salesforce, a custom REST CRM)
by implementing the same `upsert_appointment` / `get_appointment` interface.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.models import Appointment


class CRMClient(ABC):
    @abstractmethod
    def upsert_appointment(self, call_sid: str, appointment: Appointment, status: str) -> None: ...

    @abstractmethod
    def get_appointment(self, call_sid: str) -> dict | None: ...


class InMemoryCRM(CRMClient):
    def __init__(self) -> None:
        self._records: dict[str, dict] = {}

    def upsert_appointment(self, call_sid: str, appointment: Appointment, status: str) -> None:
        self._records[call_sid] = {
            "caller_name": appointment.caller_name,
            "reason": appointment.reason,
            "requested_time": appointment.requested_time,
            "confirmed": appointment.confirmed,
            "status": status,
        }

    def get_appointment(self, call_sid: str) -> dict | None:
        return self._records.get(call_sid)


_default_crm = InMemoryCRM()


def get_crm_client() -> CRMClient:
    return _default_crm
