"""CLI entry point for the WhatsApp Reply Copilot MVP."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

from app.ara_adapter import process_ara_event
from app.reply_engine import draft_reply_package
from app.schemas import ReplyPackage
from app.storage import load_messages, save_reply_packages


def format_package(pkg: ReplyPackage) -> str:
    review_line = (
        f"Yes — {pkg.manual_review_reason}" if pkg.manual_review else "No."
    )
    return (
        f"New WhatsApp message from: {pkg.sender_name}\n"
        f"\n"
        f"Message:\n"
        f"\"{pkg.message_text}\"\n"
        f"\n"
        f"Summary:\n"
        f"{pkg.summary}\n"
        f"\n"
        f"Situation:\n"
        f"{pkg.classification}\n"
        f"\n"
        f"Suggested replies:\n"
        f"\n"
        f"1. Casual:\n"
        f"\"{pkg.suggested_replies.casual}\"\n"
        f"\n"
        f"2. Warmer:\n"
        f"\"{pkg.suggested_replies.warmer}\"\n"
        f"\n"
        f"3. Short:\n"
        f"\"{pkg.suggested_replies.short}\"\n"
        f"\n"
        f"Recommendation:\n"
        f"{pkg.recommendation}\n"
        f"\n"
        f"Manual review:\n"
        f"{review_line}\n"
    )


def _load_existing_packages(path: Path) -> List[dict]:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return []


def run_sample(sample_path: str, output_path: str) -> List[ReplyPackage]:
    messages = load_messages(sample_path)
    packages = [draft_reply_package(m) for m in messages]
    for pkg in packages:
        print(format_package(pkg))
        print("-" * 60)
    saved_to = save_reply_packages(packages, output_path)
    print(f"Saved {len(packages)} draft package(s) to {saved_to}")
    return packages


def run_ara_event(event_path: str, output_path: str) -> ReplyPackage:
    with open(event_path, "r", encoding="utf-8") as f:
        event = json.load(f)
    pkg = process_ara_event(event)
    print(format_package(pkg))
    print("-" * 60)

    out = Path(output_path)
    existing = _load_existing_packages(out)
    existing.append(pkg.to_dict())
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)
    print(f"Appended 1 draft package to {out} (total: {len(existing)})")
    return pkg


def main() -> None:
    parser = argparse.ArgumentParser(
        description="WhatsApp Reply Copilot — local prototype."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--sample",
        help="Path to a JSON file with simulated incoming WhatsApp messages.",
    )
    group.add_argument(
        "--ara-event",
        dest="ara_event",
        help="Path to a single Ara-style event JSON file.",
    )
    parser.add_argument(
        "--output",
        default=str(Path("data") / "generated_replies.json"),
        help="Where to write generated draft replies (JSON).",
    )
    args = parser.parse_args()

    if args.sample:
        run_sample(args.sample, args.output)
    else:
        run_ara_event(args.ara_event, args.output)


if __name__ == "__main__":
    main()
