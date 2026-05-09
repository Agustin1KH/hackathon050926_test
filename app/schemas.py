"""Schemas for WhatsApp Reply Copilot."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any


@dataclass
class IncomingMessage:
    sender_name: str
    message_text: str
    source: str = "whatsapp"
    sender_phone: Optional[str] = None
    timestamp: Optional[str] = None
    chat_type: str = "direct"  # "direct" or "group"
    message_id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IncomingMessage":
        return cls(
            source=data.get("source", "whatsapp"),
            sender_name=data.get("sender_name", "Unknown"),
            sender_phone=data.get("sender_phone"),
            message_text=data.get("message_text", ""),
            timestamp=data.get("timestamp"),
            chat_type=data.get("chat_type", "direct"),
            message_id=data.get("message_id"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SuggestedReplies:
    casual: str
    warmer: str
    short: str

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


@dataclass
class ReplyPackage:
    sender_name: str
    message_text: str
    summary: str
    classification: str
    suggested_replies: SuggestedReplies
    recommendation: str
    manual_review: bool = False
    manual_review_reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sender_name": self.sender_name,
            "message_text": self.message_text,
            "summary": self.summary,
            "classification": self.classification,
            "suggested_replies": self.suggested_replies.to_dict(),
            "recommendation": self.recommendation,
            "manual_review": self.manual_review,
            "manual_review_reason": self.manual_review_reason,
        }
