from app.models import CallSession
from app.pipeline import VoiceAgent


def run_full_booking(agent: VoiceAgent, call_sid: str = "CA123") -> CallSession:
    session = CallSession(call_sid=call_sid)
    agent.handle_turn(session, b"")  # greeting
    agent.handle_turn(session, b"Jane Doe")
    agent.handle_turn(session, b"annual checkup")
    agent.handle_turn(session, b"next Tuesday at 10am")
    agent.handle_turn(session, b"yes please")
    return session


def test_happy_path_books_appointment():
    agent = VoiceAgent()
    session = run_full_booking(agent)

    assert session.appointment.confirmed is True
    assert session.appointment.caller_name == "Jane Doe"

    record = agent.crm.get_appointment(session.call_sid)
    assert record["status"] == "confirmed"
    assert record["caller_name"] == "Jane Doe"


def test_low_confidence_escalates_to_human():
    agent = VoiceAgent()
    session = CallSession(call_sid="CA999")
    agent.handle_turn(session, b"")  # greeting
    # Single-word / empty utterances score low confidence in MockSTT.
    agent.handle_turn(session, b"uh")
    agent.handle_turn(session, b"um")

    assert session.escalated is True
    record = agent.crm.get_appointment(session.call_sid)
    assert record["status"] == "escalated"


def test_confirm_rejection_loops_back_to_time_collection():
    agent = VoiceAgent()
    session = CallSession(call_sid="CA555")
    agent.handle_turn(session, b"")
    agent.handle_turn(session, b"Jane Doe")
    agent.handle_turn(session, b"annual checkup")
    agent.handle_turn(session, b"next Tuesday at 10am")
    agent.handle_turn(session, b"no that's wrong")

    from app.models import CallState

    assert session.state == CallState.COLLECT_TIME
    assert session.appointment.confirmed is False
