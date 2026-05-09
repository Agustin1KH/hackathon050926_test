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
