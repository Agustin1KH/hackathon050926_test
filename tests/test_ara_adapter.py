from app.ara_adapter import ara_event_to_incoming_message, process_ara_event
from app.schemas import IncomingMessage, ReplyPackage


def test_nested_ara_payload_converts():
    event = {
        "channel": "whatsapp",
        "sender": {"name": "Sofia", "phone": "+15551234567"},
        "message": {
            "id": "abc123",
            "text": "Hey are you free tonight?",
            "timestamp": "2026-05-09T10:45:00-07:00",
        },
        "chat": {"type": "direct"},
    }
    msg = ara_event_to_incoming_message(event)
    assert isinstance(msg, IncomingMessage)
    assert msg.source == "whatsapp"
    assert msg.sender_name == "Sofia"
    assert msg.sender_phone == "+15551234567"
    assert msg.message_text == "Hey are you free tonight?"
    assert msg.timestamp == "2026-05-09T10:45:00-07:00"
    assert msg.chat_type == "direct"
    assert msg.message_id == "abc123"


def test_flattened_ara_payload_converts():
    event = {
        "source": "whatsapp",
        "sender_name": "Sofia",
        "sender_phone": "+15551234567",
        "message_text": "Hey are you free tonight?",
        "timestamp": "2026-05-09T10:45:00-07:00",
        "chat_type": "direct",
        "message_id": "abc123",
    }
    msg = ara_event_to_incoming_message(event)
    assert msg.sender_name == "Sofia"
    assert msg.sender_phone == "+15551234567"
    assert msg.message_text == "Hey are you free tonight?"
    assert msg.chat_type == "direct"
    assert msg.message_id == "abc123"
    assert msg.source == "whatsapp"


def test_process_ara_event_returns_reply_package():
    event = {
        "channel": "whatsapp",
        "sender": {"name": "Sofia", "phone": "+15551234567"},
        "message": {"text": "Hey are you free tonight?"},
        "chat": {"type": "direct"},
    }
    pkg = process_ara_event(event)
    assert isinstance(pkg, ReplyPackage)
    assert pkg.sender_name == "Sofia"
    assert set(pkg.suggested_replies.to_dict().keys()) == {
        "casual",
        "warmer",
        "short",
    }


def test_group_ara_event_triggers_manual_review():
    event = {
        "channel": "whatsapp",
        "sender": {"name": "Mom", "phone": "+15552223333"},
        "message": {"text": "Quién trae el postre el domingo?"},
        "chat": {"type": "group", "name": "Family Group"},
    }
    pkg = process_ara_event(event)
    assert pkg.manual_review is True
    assert "group" in pkg.manual_review_reason.lower()


def test_sensitive_ara_event_triggers_manual_review():
    event = {
        "channel": "whatsapp",
        "sender": {"phone": "+15550009999"},
        "message": {"text": "Hi, I need your SSN and bank account."},
        "chat": {"type": "direct"},
    }
    pkg = process_ara_event(event)
    assert pkg.manual_review is True
    # Either the unknown-sender check or the sensitive-keyword check should fire.
    reason = pkg.manual_review_reason.lower()
    assert ("sensitive" in reason) or ("unknown" in reason)
