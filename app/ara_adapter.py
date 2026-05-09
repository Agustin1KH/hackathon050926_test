"""Ara integration adapter.

This module is the boundary between Ara-style channel events and the
local reply engine. It accepts flexible incoming payload shapes
(nested or flattened) and normalizes them into our IncomingMessage
schema so the rest of the app stays decoupled from Ara-specific shapes.

This adapter does NOT make any network calls and does NOT auto-send.
"""
from __future__ import annotations

from typing import Any, Dict

from app.reply_engine import draft_reply_package
from app.schemas import IncomingMessage, ReplyPackage


def _first(*values: Any) -> Any:
    """Return the first non-empty value (None / '' are skipped)."""
    for v in values:
        if v is not None and v != "":
            return v
    return None


def ara_event_to_incoming_message(event: Dict[str, Any]) -> IncomingMessage:
    """Normalize a (possibly nested) Ara-style event into IncomingMessage.

    Supports both nested payloads (``sender.name``, ``message.text``,
    ``chat.type``) and flattened fallbacks (``sender_name``,
    ``message_text``, ``chat_type``).
    """
    if not isinstance(event, dict):
        raise TypeError(
            f"Ara event must be a dict, got {type(event).__name__}"
        )

    sender = event.get("sender") or {}
    message = event.get("message") or {}
    chat = event.get("chat") or {}

    if not isinstance(sender, dict):
        sender = {}
    if not isinstance(message, dict):
        message = {}
    if not isinstance(chat, dict):
        chat = {}

    sender_name = _first(
        sender.get("name"),
        sender.get("display_name"),
        event.get("sender_name"),
        event.get("from_name"),
    )
    sender_phone = _first(
        sender.get("phone"),
        sender.get("phone_number"),
        sender.get("number"),
        event.get("sender_phone"),
        event.get("from_phone"),
    )
    message_text = _first(
        message.get("text"),
        message.get("body"),
        message.get("content"),
        event.get("message_text"),
        event.get("text"),
        event.get("body"),
    )
    timestamp = _first(
        message.get("timestamp"),
        message.get("created_at"),
        event.get("timestamp"),
        event.get("created_at"),
    )
    chat_type = _first(
        chat.get("type"),
        chat.get("kind"),
        event.get("chat_type"),
    ) or "direct"
    message_id = _first(
        message.get("id"),
        event.get("message_id"),
        event.get("id"),
    )
    source = _first(
        event.get("channel"),
        event.get("source"),
    ) or "whatsapp"

    if sender_name is None and sender_phone is not None:
        sender_name = sender_phone

    return IncomingMessage(
        source=str(source),
        sender_name=str(sender_name) if sender_name is not None else "Unknown",
        sender_phone=str(sender_phone) if sender_phone is not None else None,
        message_text=str(message_text) if message_text is not None else "",
        timestamp=str(timestamp) if timestamp is not None else None,
        chat_type=str(chat_type),
        message_id=str(message_id) if message_id is not None else None,
    )


def process_ara_event(event: Dict[str, Any]) -> ReplyPackage:
    """Convert an Ara event and run it through the reply pipeline."""
    msg = ara_event_to_incoming_message(event)
    return draft_reply_package(msg)
