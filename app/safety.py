"""Safety checks for WhatsApp Reply Copilot.

Determines whether a message should be flagged for manual review
before any reply is suggested or sent.
"""
from __future__ import annotations

import re
from typing import Tuple

from app.schemas import IncomingMessage


SENSITIVE_KEYWORDS = [
    # financial
    "ssn", "social security", "bank account", "routing number",
    "credit card", "wire transfer", "venmo me", "send money",
    "password", "otp", "verification code", "2fa",
    # legal
    "lawyer", "attorney", "lawsuit", "subpoena", "court",
    # medical
    "diagnosis", "prescription", "hospital", "surgery",
    # immigration
    "visa", "green card", "uscis", "immigration", "asylum",
    # work-sensitive
    "fired", "layoff", "terminated", "resign", "nda",
    "salary", "compensation", "offer letter",
]

CONFLICT_KEYWORDS = [
    "why did you", "you messed", "you screwed", "you ruined",
    "i'm angry", "im angry", "furious", "pissed",
    "this is unacceptable", "stop ignoring", "you never",
    "fuck you", "shut up", "i hate", "wtf",
]

ROMANTIC_KEYWORDS = [
    "i miss you", "miss u", "love you", "te amo", "te extraño",
    "te extrano", "kiss", "babe", "baby", "honey", "cariño", "carino",
    "sexy", "naked", "bed with me", "come over tonight",
    "i want you",
]


def is_unknown_sender(message: IncomingMessage) -> bool:
    """An unknown sender has no name or only a phone-like name."""
    name = (message.sender_name or "").strip()
    if not name or name.lower() in {"unknown", "n/a"}:
        return True
    # If the "name" is just a phone number, treat as unknown.
    if re.fullmatch(r"[+\d\s\-()]+", name):
        return True
    return False


def is_group_chat(message: IncomingMessage) -> bool:
    return (message.chat_type or "").lower() == "group"


def _contains_any(text: str, keywords) -> bool:
    t = (text or "").lower()
    return any(k in t for k in keywords)


def contains_sensitive_keywords(text: str) -> bool:
    return _contains_any(text, SENSITIVE_KEYWORDS)


def contains_conflict_keywords(text: str) -> bool:
    return _contains_any(text, CONFLICT_KEYWORDS)


def contains_romantic_keywords(text: str) -> bool:
    return _contains_any(text, ROMANTIC_KEYWORDS)


def requires_manual_review(message: IncomingMessage) -> Tuple[bool, str]:
    """Return (needs_review, reason)."""
    if is_group_chat(message):
        return True, "Group chat — manual review recommended."
    if is_unknown_sender(message):
        return True, "Unknown sender — manual review recommended."
    text = message.message_text or ""
    if contains_sensitive_keywords(text):
        return True, "Message contains legal/financial/medical/immigration/work-sensitive keywords."
    if contains_conflict_keywords(text):
        return True, "Message appears angry or conflict-heavy."
    if contains_romantic_keywords(text):
        return True, "Message appears romantic/sexual."
    return False, ""
