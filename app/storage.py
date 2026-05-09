"""Local JSON storage for incoming messages and generated reply packages."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List, Dict, Any

from app.schemas import IncomingMessage, ReplyPackage


def load_messages(path: str | Path) -> List[IncomingMessage]:
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    if not isinstance(raw, list):
        raise ValueError(f"Expected a JSON array in {p}, got {type(raw).__name__}")
    return [IncomingMessage.from_dict(item) for item in raw]


def save_reply_packages(
    packages: Iterable[ReplyPackage], path: str | Path
) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload: List[Dict[str, Any]] = [pkg.to_dict() for pkg in packages]
    with p.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return p
