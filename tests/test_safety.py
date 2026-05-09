from app.schemas import IncomingMessage
from app.safety import (
    contains_conflict_keywords,
    contains_sensitive_keywords,
    is_group_chat,
    is_unknown_sender,
    requires_manual_review,
)


def _msg(**kwargs) -> IncomingMessage:
    base = {
        "sender_name": "Sofia",
        "message_text": "hey",
        "chat_type": "direct",
    }
    base.update(kwargs)
    return IncomingMessage.from_dict(base)


def test_group_chat_requires_manual_review():
    m = _msg(chat_type="group", message_text="quien trae el postre")
    needs, reason = requires_manual_review(m)
    assert needs is True
    assert "group" in reason.lower()
    assert is_group_chat(m) is True


def test_unknown_sender_requires_manual_review():
    m = _msg(sender_name="+15550009999", message_text="hi there")
    assert is_unknown_sender(m) is True
    needs, reason = requires_manual_review(m)
    assert needs is True
    assert "unknown" in reason.lower()


def test_sensitive_keywords_require_manual_review():
    m = _msg(message_text="please send your SSN and bank account")
    assert contains_sensitive_keywords(m.message_text) is True
    needs, _ = requires_manual_review(m)
    assert needs is True


def test_normal_casual_message_no_manual_review():
    m = _msg(sender_name="Sofia", message_text="hey what's up")
    needs, reason = requires_manual_review(m)
    assert needs is False
    assert reason == ""


def test_conflict_keywords_detected():
    assert contains_conflict_keywords("why did you mess this up") is True
    assert contains_conflict_keywords("hey friend") is False
