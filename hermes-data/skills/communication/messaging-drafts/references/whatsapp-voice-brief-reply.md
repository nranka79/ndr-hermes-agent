# Voice Brief + Chat History → WhatsApp Reply

**Trigger:** User sends:
1. A voice message explaining the situation, their relationship with the person, the tone they want, and key points to include
2. Then shares the actual WhatsApp chat history (received messages with date/time) as text

**Class of task:** Drafting a personal WhatsApp reply where the user provides both a voice brief (tone/intent) and written source material (actual messages to respond to).

## Workflow

### Phase 1 — Parse the Brief and Context

Two separate inputs come in sequence. Treat them differently:

| Input | Role | Handling |
|-------|------|----------|
| Voice message | Intent, tone preference, relationship context, emotional color | Transcribe; note tone signals (respectful/casual/formal), language mix preference (English-only vs mix with Hindi) |
| Written WhatsApp history | **Source of truth for facts** — names, dates, events, what the other person actually said | This overrides any ambiguous details from the voice message |

### Phase 2 — Cross-Reference Voice vs Written Facts

**Voice STT often gets personal relationships wrong.** Examples from session:
- User said "beti ki shaadi" (daughter's wedding) in voice — but actual context was cousin sister's wedding
- User described tone as full Hindi at first, then corrected to "more English with a few Hindi words"

**Always** extract the factual skeleton from the written chat history — who, what, when, event names, dates — and cross-check against the voice message. If the voice says one thing and the written messages show another, **trust the written messages** and flag the discrepancy before drafting.

### Phase 3 — Draft with Explicit Tone Parameters

Confirm these with the user before writing the full draft:

```
Tone: respectful/formal/casual/warm
Language: English-only / English with few Hindi words / mostly Hindi
Salutation: [Name] / Namaste [Name] / Dear [Name]
Sign-off: Warm regards / Jai Shri Ram / Just name
```

**Pitfall — first draft too Hindi-heavy (corrected Jun 2026):** When the user says "English with a few Hindi words" and you're also given Hindi source text, it's easy to default to mostly-Hindi because the source material is in Hindi. Actively resist this — keep the draft predominantly English, with only 2-4 Hindi phrases/sentences judiciously placed.

### Phase 4 — Verify Personal Details Before Presenting

Before showing the draft, verify:
- Relationship to the person (cousin? friend? business? family elder?)
- Event name and date (confirmed from chat history, not just voice)
- Your availability reason (why you couldn't attend — confirmed from your original message, not just voice recall)
- Couple's names (extract from the received WhatsApp message, not voice)

**Common STT traps in wedding/social context:**
| Voice may mishear | Actual (verify from written) |
|-------------------|------------------------------|
| "beti ki shaadi" (my daughter's wedding) | Could be cousin's wedding, brother's wedding, or truly daughter's |
| "Parivaar" vs "parivaar" — all fine | But specific relationship nouns (beta/beti/bhai/bahan/cousin) are easily swapped |
| Date/time references | The written WhatsApp messages have exact timestamps — use those |

### Phase 5 — Present and Confirmation Structure

```
Here's a draft based on the WhatsApp history + your instructions:

[DRAFT in code block]

Key points:
• Salutation: [as requested]
• Language: English with [N] Hindi phrases
• Relationship explanation: why you couldn't attend
• Couple blessing section

Confirm or adjust?
```

Then offer one round of refinement before final delivery.
