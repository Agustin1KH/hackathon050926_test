"""CLI entry point for the WhatsApp Reply Copilot MVP."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.approval import create_confirmation, confirm_send
from app.ara_adapter import process_ara_event
from app.reply_engine import draft_reply_package
from app.schemas import ReplyPackage
from app.storage import load_messages, save_reply_packages


PENDING_PATH_DEFAULT = Path("data") / "pending_confirmations.json"


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


def format_confirmation(conf: Dict[str, Any]) -> str:
    status = conf.get("status", "")
    lines = [
        "--- Approval workflow (offline) ---",
        f"Status: {status}",
        f"To: {conf.get('recipient_name')}",
        f"Selected reply #{conf.get('selected_reply_number')} "
        f"({conf.get('selected_reply_label')}):",
        f"\"{conf.get('selected_reply_text')}\"",
    ]
    if status == "pending_confirmation":
        lines.append(
            f"To approve, re-run with --confirm \"{conf.get('requires_user_text')}\""
        )
        lines.append("No real message will be sent. This is offline only.")
    elif status == "approved_offline":
        lines.append("Marked as approved_offline.")
        lines.append("NO real WhatsApp message was sent. Offline simulation only.")
    elif status == "not_approved":
        lines.append("Confirmation text did not match — not approved.")
        lines.append("No real message was sent.")
    return "\n".join(lines) + "\n"


def _load_existing_list(path: Path) -> List[Dict[str, Any]]:
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


def _append_json_list(path: Path, item: Dict[str, Any]) -> int:
    existing = _load_existing_list(path)
    existing.append(item)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)
    return len(existing)


def handle_selection(
    pkg: ReplyPackage,
    select_reply: int,
    confirm_text: Optional[str],
    pending_path: Path,
) -> Dict[str, Any]:
    """Create a pending confirmation (and optionally approve it)."""
    confirmation = create_confirmation(pkg, select_reply)
    if confirm_text is not None:
        confirmation = confirm_send(confirmation, confirm_text)
    print(format_confirmation(confirmation))
    total = _append_json_list(pending_path, confirmation)
    print(f"Saved confirmation to {pending_path} (total: {total})")
    return confirmation


def run_sample(
    sample_path: str,
    output_path: str,
    select_reply: Optional[int],
    confirm_text: Optional[str],
    pending_path: Path,
) -> List[ReplyPackage]:
    messages = load_messages(sample_path)
    packages = [draft_reply_package(m) for m in messages]
    for pkg in packages:
        print(format_package(pkg))
        print("-" * 60)
    saved_to = save_reply_packages(packages, output_path)
    print(f"Saved {len(packages)} draft package(s) to {saved_to}")

    if select_reply is not None and packages:
        # Limitation: --select-reply with --sample only applies to the first
        # generated package. Documented in README.
        print(
            "\nNote: --select-reply with --sample applies to the FIRST message only."
        )
        handle_selection(packages[0], select_reply, confirm_text, pending_path)
    return packages


def run_ara_event(
    event_path: str,
    output_path: str,
    select_reply: Optional[int],
    confirm_text: Optional[str],
    pending_path: Path,
) -> ReplyPackage:
    with open(event_path, "r", encoding="utf-8") as f:
        event = json.load(f)
    pkg = process_ara_event(event)
    print(format_package(pkg))
    print("-" * 60)

    out = Path(output_path)
    total = _append_json_list(out, pkg.to_dict())
    print(f"Appended 1 draft package to {out} (total: {total})")

    if select_reply is not None:
        handle_selection(pkg, select_reply, confirm_text, pending_path)
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
    parser.add_argument(
        "--select-reply",
        dest="select_reply",
        type=int,
        choices=[1, 2, 3],
        help="Pick a suggested reply to put into the offline approval workflow "
             "(1=casual, 2=warmer, 3=short).",
    )
    parser.add_argument(
        "--confirm",
        dest="confirm",
        type=str,
        default=None,
        help="Confirmation text (must be 'confirm send' to mark approved_offline).",
    )
    parser.add_argument(
        "--pending-output",
        dest="pending_output",
        default=str(PENDING_PATH_DEFAULT),
        help="Where to write pending/approved confirmations (JSON).",
    )
    args = parser.parse_args()

    if args.confirm is not None and args.select_reply is None:
        parser.error("--confirm requires --select-reply")

    pending_path = Path(args.pending_output)

    if args.sample:
        run_sample(
            args.sample,
            args.output,
            args.select_reply,
            args.confirm,
            pending_path,
        )
    else:
        run_ara_event(
            args.ara_event,
            args.output,
            args.select_reply,
            args.confirm,
            pending_path,
        )


if __name__ == "__main__":
    main()
