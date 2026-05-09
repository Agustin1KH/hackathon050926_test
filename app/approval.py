"""Offline human-in-the-loop approval workflow.

This module simulates the two-step send approval that the SKILL spec
requires. It NEVER sends a WhatsApp message. Approval here just records
that the user explicitly confirmed they would send the chosen reply.
"""
from __future__ import annotations

from typing import Any, Dict

from app.schemas import ReplyPackage


REPLY_LABEL_BY_NUMBER = {
    1: "casual",
    2: "warmer",
    3: "short",
}

CONFIRMATION_PHRASE = "confirm send"


def create_confirmation(
    reply_package: ReplyPackage, reply_number: int
) -> Dict[str, Any]:
    """Build a pending confirmation for the chosen reply.

    ``reply_number`` must be 1 (casual), 2 (warmer), or 3 (short).
    Raises ``ValueError`` for any other value.
    """
    if reply_number not in REPLY_LABEL_BY_NUMBER:
        raise ValueError(
            f"reply_number must be 1, 2, or 3 (got {reply_number!r})"
        )

    label = REPLY_LABEL_BY_NUMBER[reply_number]
    selected_text = getattr(reply_package.suggested_replies, label)

    return {
        "status": "pending_confirmation",
        "recipient_name": reply_package.sender_name,
        "original_message": reply_package.message_text,
        "selected_reply_number": reply_number,
        "selected_reply_label": label,
        "selected_reply_text": selected_text,
        "requires_user_text": CONFIRMATION_PHRASE,
        "would_send": False,
    }


def confirm_send(
    confirmation: Dict[str, Any], confirmation_text: str
) -> Dict[str, Any]:
    """Validate a user's confirmation text against a pending confirmation.

    Returns a NEW dict (does not mutate the input) with one of:
    - status="approved_offline" if the text matches "confirm send"
      (case-insensitive, whitespace-trimmed)
    - status="not_approved" otherwise

    In both cases ``would_send`` and ``sent`` are False. This module
    never actually sends a message.
    """
    result = dict(confirmation)
    normalized = (confirmation_text or "").strip().lower()
    if normalized == CONFIRMATION_PHRASE:
        result["status"] = "approved_offline"
    else:
        result["status"] = "not_approved"
    result["would_send"] = False
    result["sent"] = False
    return result
