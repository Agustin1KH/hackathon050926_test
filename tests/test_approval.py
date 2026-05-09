import pytest

from app.approval import create_confirmation, confirm_send
from app.schemas import ReplyPackage, SuggestedReplies


def _pkg() -> ReplyPackage:
    return ReplyPackage(
        sender_name="Sofia",
        message_text="Hey are you free tonight?",
        summary="Sofia is asking if you're free.",
        classification="logistics",
        suggested_replies=SuggestedReplies(
            casual="CASUAL_TEXT",
            warmer="WARMER_TEXT",
            short="SHORT_TEXT",
        ),
        recommendation="Use #1.",
        manual_review=False,
        manual_review_reason="",
    )


def test_reply_number_1_maps_to_casual():
    c = create_confirmation(_pkg(), 1)
    assert c["selected_reply_label"] == "casual"
    assert c["selected_reply_text"] == "CASUAL_TEXT"
    assert c["selected_reply_number"] == 1
    assert c["status"] == "pending_confirmation"
    assert c["would_send"] is False
    assert c["recipient_name"] == "Sofia"
    assert c["requires_user_text"] == "confirm send"


def test_reply_number_2_maps_to_warmer():
    c = create_confirmation(_pkg(), 2)
    assert c["selected_reply_label"] == "warmer"
    assert c["selected_reply_text"] == "WARMER_TEXT"


def test_reply_number_3_maps_to_short():
    c = create_confirmation(_pkg(), 3)
    assert c["selected_reply_label"] == "short"
    assert c["selected_reply_text"] == "SHORT_TEXT"


@pytest.mark.parametrize("bad", [0, 4, -1, 99])
def test_invalid_reply_number_raises(bad):
    with pytest.raises(ValueError):
        create_confirmation(_pkg(), bad)


def test_confirm_send_marks_approved_offline():
    c = create_confirmation(_pkg(), 2)
    out = confirm_send(c, "confirm send")
    assert out["status"] == "approved_offline"
    assert out["would_send"] is False
    assert out["sent"] is False
    assert out["selected_reply_text"] == "WARMER_TEXT"


def test_confirm_send_is_case_and_whitespace_tolerant():
    c = create_confirmation(_pkg(), 1)
    out = confirm_send(c, "  Confirm Send  ")
    assert out["status"] == "approved_offline"


@pytest.mark.parametrize("text", ["", "yes", "send it", "confirm", "confirm now"])
def test_other_text_marks_not_approved(text):
    c = create_confirmation(_pkg(), 1)
    out = confirm_send(c, text)
    assert out["status"] == "not_approved"
    assert out["would_send"] is False
    assert out["sent"] is False


def test_confirmation_never_sends():
    c = create_confirmation(_pkg(), 2)
    assert c["would_send"] is False
    approved = confirm_send(c, "confirm send")
    assert approved["would_send"] is False
    assert approved["sent"] is False
    rejected = confirm_send(c, "nope")
    assert rejected["would_send"] is False
    assert rejected["sent"] is False
