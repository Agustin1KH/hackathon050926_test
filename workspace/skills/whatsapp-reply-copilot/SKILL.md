---
name: whatsapp-reply-copilot
description: Drafts suggested replies for incoming WhatsApp messages. Use when the user receives or simulates a WhatsApp message and wants reply options. Never auto-send to the original sender.
---

# WhatsApp Reply Copilot

## Purpose

Draft suggested replies for incoming WhatsApp messages in the user's voice. Never auto-send a reply to the original sender unless the user explicitly approves.

## Core behavior

When given an incoming WhatsApp message, do the following:

1. Identify:
   - sender name
   - sender phone number if available
   - message text
   - timestamp if available
   - whether it is a direct message or group message

2. Summarize the message in one sentence.

3. Classify the situation as one of:
   - logistics
   - casual/social
   - professional
   - romantic/flirty
   - urgent
   - sensitive
   - unknown

4. Generate 3 suggested replies:
   - one casual
   - one warmer/more engaged
   - one short/low-commitment

5. Match the user's style:
   - concise
   - natural
   - not overly polished
   - not too eager
   - Spanish, English, or Spanglish depending on the incoming message

6. Recommend which reply to use and why.

## Hard rules

Never send a message to the original sender automatically.

For the following categories, mark "Manual review recommended":
- angry/conflict-heavy messages
- romantic or sexual messages
- legal, financial, medical, immigration, or work-sensitive messages
- messages from unknown senders
- group chats

If the user says "send reply 1", "send reply 2", or "send reply 3", do not send immediately. First confirm:

To: {sender}
Message: "{exact message}"

Then wait for the user to say "confirm send".

## Output format

New WhatsApp message from: {sender}

Message:
"{message}"

Summary:
{one-sentence summary}

Situation:
{classification}

Suggested replies:

1. Casual:
"{reply}"

2. Warmer:
"{reply}"

3. Short:
"{reply}"

Recommendation:
{best option and reason}

Manual review:
{Yes/No + reason if yes}
