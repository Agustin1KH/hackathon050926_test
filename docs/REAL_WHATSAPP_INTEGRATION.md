# Real WhatsApp integration plan

This document describes how the WhatsApp Reply Copilot will eventually
connect to a real WhatsApp inbound channel through Ara, and the
guardrails that must hold before any of it is enabled.

> Status: **not implemented**. The current repo is offline-only. This
> document is the design spec and safety contract for the next phase.

## Architecture (text diagram)

```
+-----------------------------+
|   WhatsApp (real network)   |
+--------------+--------------+
               |
               | inbound only (QR-paired session)
               v
+-----------------------------+
|         Ara channel         |
|  (WhatsApp adapter, QR auth)|
+--------------+--------------+
               |
               | webhook / event push (inbound message)
               v
+-----------------------------+
|     app/ara_adapter.py      |
|  ara_event_to_incoming_msg  |
+--------------+--------------+
               |
               v
+-----------------------------+
|     app/reply_engine.py     |
|  classify + draft 3 replies |
+--------------+--------------+
               |
               v
+-----------------------------+
|       app/safety.py         |
|  manual_review flagging     |
+--------------+--------------+
               |
               v
+-----------------------------+        +----------------------------+
|     app/approval.py         |  -->   |   Owner/control channel    |
|  pending_confirmation       |        |  (drafts shown HERE only,  |
|  -> approved_offline        |        |   never to original sender)|
+-----------------------------+        +----------------------------+

                        X (no edge yet)
                        v
                +---------------+
                | Outbound send |   <-- DOES NOT EXIST. Do not build
                |  to WhatsApp  |       until inbound-only flow is
                +---------------+       stable AND human approval is
                                        explicitly gated.
```

Key property: there is **no edge from approval to outbound dispatch**.
The dispatcher box in the diagram is intentionally unbuilt.

## Setup checklist

Before turning on real-channel mode, all of the following must be true:

- [ ] Ara workspace has a dedicated WhatsApp channel for this app.
- [ ] WhatsApp QR pairing has been completed using a *test* phone number.
- [ ] A separate "owner/control" channel is configured (e.g. a Telegram
      DM, a Slack DM, or a dedicated Ara DM). Drafts will surface ONLY
      there.
- [ ] Inbound webhook URL is wired to a route that calls
      `app.ara_adapter.process_ara_event` and persists the resulting
      `ReplyPackage` (no auto-reply path).
- [ ] `.env` contains only inbound credentials. No outbound send token.
- [ ] `pending_confirmations.json` write path is verified.
- [ ] Code review confirms there is **no call site** anywhere that
      pushes a message back to the original WhatsApp sender.
- [ ] All guardrail tests in `tests/` still pass (`pytest -q`).

## Safety rules

These mirror the "Real WhatsApp channel rules" in
`workspace/skills/whatsapp-reply-copilot/SKILL.md` and are the
contract for any future implementation work in this repo.

1. The agent may process inbound WhatsApp messages.
2. The agent must never send a message to the original WhatsApp sender
   automatically.
3. Drafts are surfaced only to the owner/control channel.
4. Explicit human approval is required before any send action is even
   considered.
5. The approval phrase must be exactly: `confirm send`.
6. Even after approval, this MVP records only `approved_offline` and
   does not dispatch.
7. Unknown senders, group chats, romantic/sexual messages, professional
   conflict, legal, financial, medical, and immigration messages always
   require manual review.
8. The agent should prefer silence over accidental sending.
9. If the agent is unsure whether a message is safe, it must mark
   `Manual review: Yes`.
10. The agent must include the phrase
    `No real WhatsApp message was sent` whenever it records an approval
    in this MVP.

## Test plan

To be executed in order. Stop at the first failure and triage before
moving on. Use a test WhatsApp number that you control and a test
contact you control.

1. Pair WhatsApp through Ara QR.
2. Send a message from a test contact to the paired number.
3. Confirm the system receives and normalizes the event
   (`ara_event_to_incoming_message` produces a valid
   `IncomingMessage`).
4. Confirm three drafts are generated (`suggested_replies` has
   `casual`, `warmer`, and `short`).
5. Confirm drafts are shown only to the owner/control channel — never
   echoed to the original sender's chat.
6. Confirm no message is sent to the original sender (verify on the
   sender's WhatsApp that nothing arrives, and check Ara outbound
   logs).
7. Confirm that submitting `confirm send` only marks the confirmation
   as `approved_offline` and that the printed/logged record contains
   the phrase `No real WhatsApp message was sent`.
8. Confirm group, unknown, and sensitive messages are manual-review
   only:
   - send from a number not in contacts → `manual_review = true`
   - send from a group chat → `manual_review = true`
   - send a message containing SSN / bank / lawyer / visa keywords →
     `manual_review = true`

## Rollback plan

If anything misbehaves — duplicate sends, drafts leaking to the
original sender, runaway loops, or any unexpected outbound traffic —
roll back immediately:

1. Disconnect WhatsApp QR pairing in Ara (revoke the linked device).
2. Disable the Ara WhatsApp channel for this workspace.
3. Remove channel credentials and any cached session data from `.env`
   and from local secret stores.
4. Revert to simulated JSON events
   (`python -m app.main --ara-event data/sample_ara_event.json` and
   the Streamlit demo).
5. Open an issue capturing what happened, what was sent (if anything),
   and which rule was violated, before re-enabling anything.

## Why this is intentionally boring

Every interesting feature in this milestone is a thing we did **not**
build: no outbound client, no dispatch queue, no auto-reply heuristics.
That is the point. The cost of an accidental send to a real human on
WhatsApp is high; the cost of a few extra approval steps is zero.
Build inbound-only, prove it, then revisit.
