"""Streamlit demo UI for the WhatsApp Reply Copilot.

Run with:
    streamlit run app/ui.py

This UI is a thin wrapper around existing local functions:
- app.ara_adapter.process_ara_event
- app.approval.create_confirmation
- app.approval.confirm_send

It does NOT connect to Ara, WhatsApp, or any external API.
No real message is ever sent.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow `streamlit run app/ui.py` from the project root by ensuring the
# project root is on sys.path so `app.*` imports work.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import streamlit as st  # noqa: E402

from app.approval import confirm_send, create_confirmation  # noqa: E402
from app.ara_adapter import process_ara_event  # noqa: E402


DATA_DIR = _PROJECT_ROOT / "data"

REPLY_OPTIONS = {
    1: ("casual", "1 — Casual"),
    2: ("warmer", "2 — Warmer / more engaged"),
    3: ("short", "3 — Short / low-commitment"),
}


def _list_sample_events() -> list[Path]:
    return sorted(DATA_DIR.glob("sample_ara_event*.json"))


def _load_event(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _reset_workflow_state() -> None:
    for key in ("reply_package", "confirmation"):
        if key in st.session_state:
            del st.session_state[key]


def main() -> None:
    st.set_page_config(
        page_title="WhatsApp Reply Copilot — Demo",
        page_icon="💬",
        layout="centered",
    )

    st.title("WhatsApp Reply Copilot")
    st.caption("Hackathon MVP · offline · human-in-the-loop")
    st.warning(
        "No real WhatsApp message is sent. This is a fully offline demo.",
        icon="🛑",
    )

    sample_paths = _list_sample_events()
    if not sample_paths:
        st.error(
            f"No sample Ara events found in `{DATA_DIR}`. "
            "Add a `sample_ara_event*.json` file and reload."
        )
        return

    st.subheader("1. Pick a sample Ara event")
    labels = [p.name for p in sample_paths]
    selected_label = st.selectbox(
        "Sample event",
        labels,
        index=0,
        on_change=_reset_workflow_state,
        key="selected_label",
    )
    selected_path = sample_paths[labels.index(selected_label)]
    event = _load_event(selected_path)

    with st.expander("Raw Ara event payload", expanded=False):
        st.json(event)

    st.subheader("2. Incoming message")
    sender_block = event.get("sender") or {}
    chat_block = event.get("chat") or {}
    message_block = event.get("message") or {}
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f"**From:** {sender_block.get('name') or event.get('sender_name') or '—'}"
        )
        st.markdown(
            f"**Phone:** {sender_block.get('phone') or event.get('sender_phone') or '—'}"
        )
    with col2:
        st.markdown(
            f"**Chat type:** {chat_block.get('type') or event.get('chat_type') or 'direct'}"
        )
        st.markdown(
            f"**Timestamp:** {message_block.get('timestamp') or event.get('timestamp') or '—'}"
        )
    st.markdown("**Message:**")
    st.info(
        message_block.get("text")
        or event.get("message_text")
        or "(empty)"
    )

    st.subheader("3. Generate reply package")
    if st.button("Generate replies", type="primary"):
        st.session_state["reply_package"] = process_ara_event(event)
        st.session_state.pop("confirmation", None)

    pkg = st.session_state.get("reply_package")
    if pkg is None:
        st.caption("Click *Generate replies* to draft suggestions.")
        return

    st.subheader("4. Suggested replies")
    st.markdown(f"**Summary:** {pkg.summary}")
    st.markdown(f"**Situation:** `{pkg.classification}`")

    if pkg.manual_review:
        st.error(
            f"Manual review recommended — {pkg.manual_review_reason}",
            icon="⚠️",
        )
    else:
        st.success("No manual review flag.", icon="✅")

    st.markdown("**1. Casual**")
    st.code(pkg.suggested_replies.casual, language="markdown")
    st.markdown("**2. Warmer / more engaged**")
    st.code(pkg.suggested_replies.warmer, language="markdown")
    st.markdown("**3. Short / low-commitment**")
    st.code(pkg.suggested_replies.short, language="markdown")
    st.markdown(f"**Recommendation:** {pkg.recommendation}")

    st.subheader("5. Select a reply")
    choice = st.radio(
        "Which reply do you want to confirm?",
        options=list(REPLY_OPTIONS.keys()),
        format_func=lambda n: REPLY_OPTIONS[n][1],
        horizontal=True,
        key="reply_choice",
    )

    st.subheader("6. Create pending confirmation")
    if st.button("Create pending confirmation"):
        st.session_state["confirmation"] = create_confirmation(pkg, choice)

    confirmation = st.session_state.get("confirmation")
    if confirmation is None:
        st.caption(
            "Pick a reply number above and click *Create pending confirmation*."
        )
        return

    st.markdown("**Pending confirmation:**")
    st.json(confirmation)

    if confirmation.get("status") == "pending_confirmation":
        st.info(
            "This is still pending. Type `confirm send` exactly to approve "
            "(offline only — no real message will be sent).",
            icon="ℹ️",
        )

    st.subheader("7. Type `confirm send`")
    confirm_text = st.text_input(
        "Confirmation text",
        value="",
        placeholder="confirm send",
        key="confirm_text",
    )

    st.subheader("8. Approve offline")
    if st.button("Approve offline"):
        st.session_state["confirmation"] = confirm_send(
            confirmation, confirm_text
        )
        confirmation = st.session_state["confirmation"]

    status = confirmation.get("status")
    if status == "approved_offline":
        st.success(
            "Status: approved_offline — recorded locally. "
            "NO real WhatsApp message was sent.",
            icon="🟢",
        )
    elif status == "not_approved":
        st.error(
            "Status: not_approved — confirmation text did not match. "
            "Nothing was sent.",
            icon="🔴",
        )
    else:
        st.caption("Awaiting approval…")

    st.divider()
    st.caption(
        "Reminder: this UI is fully offline. It uses "
        "`process_ara_event`, `create_confirmation`, and `confirm_send` "
        "from the local app — no Ara, WhatsApp, or external APIs are called."
    )


if __name__ == "__main__":
    main()
