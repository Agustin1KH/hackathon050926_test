from app.reply_engine import (
    classify_message,
    draft_reply_package,
    generate_replies,
)
from app.schemas import IncomingMessage


def _msg(**kwargs) -> IncomingMessage:
    base = {
        "sender_name": "Sofia",
        "message_text": "hey",
        "chat_type": "direct",
    }
    base.update(kwargs)
    return IncomingMessage.from_dict(base)


def test_draft_has_exactly_three_replies():
    m = _msg(message_text="Hey are you free tonight?")
    pkg = draft_reply_package(m)
    d = pkg.suggested_replies.to_dict()
    assert set(d.keys()) == {"casual", "warmer", "short"}
    assert all(isinstance(v, str) and v.strip() for v in d.values())
    assert len(d) == 3


def test_classify_professional():
    m = _msg(
        sender_name="Daniel",
        message_text="Can you send me the deck before 3?",
    )
    assert classify_message(m) == "professional"


def test_classify_logistics():
    m = _msg(message_text="Hey, what's the plan tonight?")
    # "what's the plan" is a logistics keyword; but "hey" also matches casual.
    # Logistics is checked before casual in classify_message, so expect logistics.
    assert classify_message(m) == "logistics"


def test_classify_sensitive():
    m = _msg(message_text="I need your SSN to process the payment")
    assert classify_message(m) == "sensitive"


def test_classify_casual_social():
    m = _msg(message_text="Hey, how are you?")
    assert classify_message(m) == "casual/social"


def test_generate_replies_spanish_when_input_spanish():
    m = _msg(message_text="Hola, ¿cómo estás?")
    cls = classify_message(m)
    replies = generate_replies(m, cls)
    # At least one of the replies should look Spanish (contains accents or "¿").
    blob = " ".join(replies.to_dict().values()).lower()
    assert any(token in blob for token in ["¿", "qué", "hola", "tú", "cómo"])


def test_draft_for_group_chat_marks_manual_review():
    m = _msg(chat_type="group", sender_name="Family", message_text="quien trae postre")
    pkg = draft_reply_package(m)
    assert pkg.manual_review is True
    assert pkg.manual_review_reason
