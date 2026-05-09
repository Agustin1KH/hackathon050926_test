"""CLI entry point for the WhatsApp Reply Copilot MVP."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

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


def run(sample_path: str, output_path: str) -> List[ReplyPackage]:
    messages = load_messages(sample_path)
    packages = [draft_reply_package(m) for m in messages]
    for pkg in packages:
        print(format_package(pkg))
        print("-" * 60)
    saved_to = save_reply_packages(packages, output_path)
    print(f"Saved {len(packages)} draft package(s) to {saved_to}")
    return packages


def main() -> None:
    parser = argparse.ArgumentParser(
        description="WhatsApp Reply Copilot — local prototype."
    )
    parser.add_argument(
        "--sample",
        required=True,
        help="Path to a JSON file with simulated incoming WhatsApp messages.",
    )
    parser.add_argument(
        "--output",
        default=str(Path("data") / "generated_replies.json"),
        help="Where to write generated draft replies (JSON).",
    )
    args = parser.parse_args()
    run(args.sample, args.output)


if __name__ == "__main__":
    main()
