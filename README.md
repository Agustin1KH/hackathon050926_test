# hackathon050926_test — WhatsApp Reply Copilot (MVP)

A minimal, local prototype of a WhatsApp Reply Copilot designed to slot into
Ara / OpenClaw-style agent workflows.

It takes simulated incoming WhatsApp messages, classifies the situation,
drafts 3 suggested replies (casual / warmer / short), flags sensitive cases
for manual review, and saves results locally.

## What this MVP does

- Loads simulated incoming WhatsApp messages from a JSON file.
- Classifies each message into one of: `logistics`, `casual/social`,
  `professional`, `romantic/flirty`, `urgent`, `sensitive`, `unknown`.
- Generates 3 suggested replies per message (rule-based, deterministic).
- Flags messages that should go through manual review:
  - unknown senders
  - group chats
  - legal / financial / medical / immigration / work-sensitive content
  - angry or conflict-heavy messages
  - obviously romantic or sexual messages
- Prints a clean, human-readable summary to the terminal.
- Saves drafts to `data/generated_replies.json`.
- Detects Spanish input and replies in Spanish (very lightweight heuristic).

## What this MVP intentionally does NOT do

- Does **not** connect to real WhatsApp.
- Does **not** auto-send replies to anyone.
- Does **not** call any external LLM/API. The reply engine is rule-based on purpose,
  so the pipeline (load → classify → draft → safety → save) is verifiable end-to-end
  before adding model calls.
- Does **not** ship a web frontend. Terminal + JSON only.

## Project structure

```
hackathon050926_test/
  README.md
  .gitignore
  .env.example
  workspace/
    skills/
      whatsapp-reply-copilot/
        SKILL.md            # Agent behavior spec for Ara / OpenClaw
  app/
    __init__.py
    main.py                 # CLI entry point
    schemas.py              # IncomingMessage / ReplyPackage dataclasses
    reply_engine.py         # summarize, classify, generate, recommend
    safety.py               # manual-review checks
    storage.py              # load/save JSON
  data/
    sample_messages.json
  tests/
    test_reply_engine.py
    test_safety.py
```

## Requirements

- Python 3.11+
- `pytest` (only for running the test suite)

The runtime itself has **no third-party dependencies**.

## Setup

```bash
cd ~/Documents/hackathon050926_test
python3 -m venv .venv
source .venv/bin/activate
pip install pytest
cp .env.example .env   # optional; not required for the local prototype
```

## Run locally

```bash
python -m app.main --sample data/sample_messages.json
```

Optionally specify an output path:

```bash
python -m app.main --sample data/sample_messages.json --output data/generated_replies.json
```

You will see a formatted block per message in the terminal, and a JSON file
with all draft packages written to `data/generated_replies.json`.

## Run a single Ara-style event

The Ara adapter (`app/ara_adapter.py`) accepts flexible Ara-style payloads
(nested `sender.*` / `message.*` / `chat.*` or flattened fields) and
normalizes them into `IncomingMessage` before running them through the
same draft pipeline.

```bash
python -m app.main --ara-event data/sample_ara_event.json
```

This prints a formatted draft block and **appends** the result to
`data/generated_replies.json` (the `--sample` mode still overwrites with
a fresh batch).

Other example events:

```bash
python -m app.main --ara-event data/sample_ara_event_group.json
python -m app.main --ara-event data/sample_ara_event_sensitive.json
```

## Offline approval workflow

`app/approval.py` implements a fully offline two-step approval that
mirrors the future real Ara flow: draft → user picks a reply → user
must explicitly confirm → record marked as approved. **Nothing is ever
sent.** No real WhatsApp message leaves this machine.

Step 1 — pick a reply (creates a pending confirmation):

```bash
python -m app.main --ara-event data/sample_ara_event.json --select-reply 2
```

This generates the reply package, builds a pending confirmation for
reply #2 (the warmer option), prints the confirmation block, and
appends it to `data/pending_confirmations.json` with status
`pending_confirmation`.

Step 2 — approve it (must say exactly `confirm send`):

```bash
python -m app.main --ara-event data/sample_ara_event.json --select-reply 2 --confirm "confirm send"
```

The confirmation is then stored with status `approved_offline`,
`would_send: false`, `sent: false`. Any other `--confirm` value
results in `not_approved`. The CLI clearly prints that no real
message was sent.

Reply number mapping:

| Number | Label  |
|--------|--------|
| 1      | casual |
| 2      | warmer |
| 3      | short  |

`--select-reply` also works with `--sample`, but only applies to the
**first** generated package (intentional limitation for the MVP).

This is the same shape the real Ara integration will use — when
WhatsApp dispatch is eventually wired up, the only addition is an
explicit send call gated on `status == "approved_offline"` (or its
online equivalent) plus the user's `confirm send` token.

## Ara adapter milestone

`app/ara_adapter.py` is the boundary between Ara channel events and the
local reply engine. It exists so the rest of the app stays decoupled
from any Ara-specific payload shape.

- Once Ara WhatsApp QR pairing is connected, incoming events should be
  normalized through `ara_event_to_incoming_message(event)` and then
  processed via `process_ara_event(event)` (or the existing
  `draft_reply_package(message)`).
- Supports both nested payloads (`sender.name`, `message.text`,
  `chat.type`) and flattened fallbacks (`sender_name`, `message_text`,
  `chat_type`), so different Ara webhook variants work without
  changing core logic.
- This still does **not** auto-send replies. Drafts are surfaced for
  the human to review.
- This prepares the app for real channel integration without coupling
  the reply engine, safety checks, or schemas to Ara-specific shapes.

## Run tests

```bash
pytest
```

## The skill file

`workspace/skills/whatsapp-reply-copilot/SKILL.md` is the canonical behavior
spec for the agent. It defines:

- when the skill should be invoked,
- the classification taxonomy,
- the reply structure (3 options + recommendation),
- the hard rules (never auto-send, two-step confirmation, manual-review categories),
- the exact output format.

Keep this file as the source of truth — when we swap the rule-based engine
for an LLM call, the prompt should be derived from this file.

## Next steps for Ara integration

1. Connect the Ara WhatsApp channel through QR pairing.
2. Route incoming WhatsApp event payloads from Ara into the same
   `IncomingMessage` schema defined in `app/schemas.py`.
3. Use `workspace/skills/whatsapp-reply-copilot/SKILL.md` as the agent
   behavior spec — feed it as the system prompt / skill definition for
   the Ara agent.
4. Keep human-in-the-loop approval. The agent surfaces drafts; the human
   chooses.
5. Only later, add explicit two-step send approval:
   - user says `send reply 1|2|3`
   - agent shows `To: {sender}` and the exact message
   - agent waits for `confirm send` before dispatching.
