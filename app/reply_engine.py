"""Rule-based reply engine for the WhatsApp Reply Copilot MVP.

No external API calls. Deterministic, hackathon-friendly logic so the
pipeline (load -> classify -> draft -> safety check -> save) works end to end.
"""
from __future__ import annotations

import re
from typing import Tuple

from app.schemas import IncomingMessage, ReplyPackage, SuggestedReplies
from app.safety import (
    contains_conflict_keywords,
    contains_romantic_keywords,
    contains_sensitive_keywords,
    is_group_chat,
    is_unknown_sender,
    requires_manual_review,
)


URGENT_KEYWORDS = ["asap", "urgent", "right now", "emergency", "immediately"]
PROFESSIONAL_KEYWORDS = [
    "deck", "meeting", "deadline", "project", "report", "client",
    "invoice", "proposal", "review", "send me the", "by eod",
    "by 3", "before 3", "before noon", "tomorrow morning",
]
LOGISTICS_KEYWORDS = [
    "free tonight", "free later", "what time", "where", "address",
    "pick up", "drop off", "eta", "running late", "see you at",
    "on my way", "omw", "what's the plan", "whats the plan",
]
CASUAL_KEYWORDS = [
    "hey", "hola", "qué tal", "que tal", "what's up", "whats up",
    "sup", "how are you", "cómo estás", "como estas",
]


SPANISH_HINTS = [
    "hola", "qué", "que ", "cómo", "como ", "estás", "estas ",
    "gracias", "por favor", "tal", "tarde", "noche", "mañana",
    "manana", "vamos", "puedes", "podrías", "podrias", "te ",
]


def _looks_spanish(text: str) -> bool:
    t = (text or "").lower()
    return any(h in t for h in SPANISH_HINTS)


def summarize_message(message: IncomingMessage) -> str:
    """One-sentence summary using simple heuristics."""
    sender = message.sender_name or "Someone"
    text = (message.message_text or "").strip()

    if not text:
        return f"{sender} sent an empty message."

    lower = text.lower()
    if "?" in text:
        return f"{sender} is asking: \"{text}\""
    if any(k in lower for k in URGENT_KEYWORDS):
        return f"{sender} is flagging something as urgent."
    if any(k in lower for k in PROFESSIONAL_KEYWORDS):
        return f"{sender} is making a work-related request."
    return f"{sender} says: \"{text}\""


def classify_message(message: IncomingMessage) -> str:
    """Return one of: logistics, casual/social, professional,
    romantic/flirty, urgent, sensitive, unknown."""
    text = (message.message_text or "").lower()

    if is_unknown_sender(message) and not text:
        return "unknown"

    if contains_sensitive_keywords(text):
        return "sensitive"

    if any(k in text for k in URGENT_KEYWORDS):
        return "urgent"

    if contains_romantic_keywords(text):
        return "romantic/flirty"

    if any(k in text for k in PROFESSIONAL_KEYWORDS):
        # Professional requests are often also logistics; prefer professional.
        return "professional"

    if any(k in text for k in LOGISTICS_KEYWORDS):
        return "logistics"

    if any(k in text for k in CASUAL_KEYWORDS):
        return "casual/social"

    if contains_conflict_keywords(text):
        # Conflict often shows up in professional contexts; classify as professional
        # but the safety layer will flag manual review.
        return "professional"

    if not text.strip():
        return "unknown"

    return "casual/social"


def generate_replies(
    message: IncomingMessage, classification: str
) -> SuggestedReplies:
    """Return 3 deterministic replies (casual, warmer, short)."""
    spanish = _looks_spanish(message.message_text or "")

    templates = {
        "logistics": {
            "en": (
                "Yeah, potentially — what time were you thinking?",
                "Could be! What did you have in mind?",
                "Maybe, what's the plan?",
            ),
            "es": (
                "Posible, ¿a qué hora pensabas?",
                "Puede ser, ¿qué tienes en mente?",
                "Tal vez, ¿cuál es el plan?",
            ),
        },
        "casual/social": {
            "en": (
                "Hey! All good here, you?",
                "Hey, good to hear from you — how have you been?",
                "Hey, what's up?",
            ),
            "es": (
                "¡Hey! Todo bien por acá, ¿y tú?",
                "Qué bueno saber de ti, ¿cómo has estado?",
                "Hey, ¿qué tal?",
            ),
        },
        "professional": {
            "en": (
                "Got it — I can get this to you shortly.",
                "Sure, happy to help. I'll send it over and flag anything that's missing.",
                "On it.",
            ),
            "es": (
                "Listo, te lo paso en un rato.",
                "Claro, lo reviso y te aviso si falta algo.",
                "Va.",
            ),
        },
        "urgent": {
            "en": (
                "Got it — looking now.",
                "On it right now, I'll update you in a few minutes.",
                "On it.",
            ),
            "es": (
                "Lo veo ahora mismo.",
                "Lo atiendo ya, te aviso en unos minutos.",
                "Voy.",
            ),
        },
        "romantic/flirty": {
            "en": (
                "Haha, that's sweet — what are you up to?",
                "You're making me smile. What's going on with you?",
                "Hey you 🙂",
            ),
            "es": (
                "Jaja, qué lindo, ¿qué andas haciendo?",
                "Me sacaste una sonrisa, ¿cómo va tu día?",
                "Hola tú 🙂",
            ),
        },
        "sensitive": {
            "en": (
                "I'd rather not handle this over text — can we talk?",
                "Happy to help, but let's move this off WhatsApp to be safe.",
                "Let's talk in person.",
            ),
            "es": (
                "Prefiero no tratar esto por mensaje, ¿podemos hablar?",
                "Te ayudo, pero mejor lo hablamos fuera de WhatsApp.",
                "Mejor hablamos.",
            ),
        },
        "unknown": {
            "en": (
                "Sorry, who is this?",
                "Hey — I don't think I have your number saved, mind reminding me who this is?",
                "Who's this?",
            ),
            "es": (
                "Perdón, ¿quién es?",
                "Hola, no tengo guardado este número, ¿me recuerdas quién eres?",
                "¿Quién habla?",
            ),
        },
    }

    bucket = templates.get(classification, templates["casual/social"])
    casual, warmer, short = bucket["es" if spanish else "en"]
    return SuggestedReplies(casual=casual, warmer=warmer, short=short)


def recommend_reply(
    message: IncomingMessage,
    replies: SuggestedReplies,
    classification: str,
) -> str:
    """Return a one-line recommendation."""
    if classification in {"sensitive", "unknown"}:
        return "Use #1 because it keeps you in control without sharing info over text."
    if classification == "urgent":
        return "Use #1 because it acknowledges urgency without overcommitting to a timeline."
    if classification == "professional":
        return "Use #1 because it sounds responsive without overpromising."
    if classification == "romantic/flirty":
        return "Use #3 because it's warm but low-stakes — let them lead."
    if classification == "logistics":
        return "Use #1 because it sounds open without overcommitting."
    return "Use #1 because it sounds friendly without trying too hard."


def draft_reply_package(message: IncomingMessage) -> ReplyPackage:
    classification = classify_message(message)
    needs_review, reason = requires_manual_review(message)
    replies = generate_replies(message, classification)
    return ReplyPackage(
        sender_name=message.sender_name,
        message_text=message.message_text,
        summary=summarize_message(message),
        classification=classification,
        suggested_replies=replies,
        recommendation=recommend_reply(message, replies, classification),
        manual_review=needs_review,
        manual_review_reason=reason,
    )
