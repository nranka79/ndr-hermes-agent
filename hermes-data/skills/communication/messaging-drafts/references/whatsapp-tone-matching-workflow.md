# WhatsApp Tone Matching from Chat History

**Trigger:** User says "I'll share my past chat history with [Name] — match my tone/style/vocabulary and draft a message."

**Context:** The user has an established WhatsApp relationship with the recipient and expects drafts to match their existing conversational style. They will provide screenshots or text of past chats as a reference.

## Workflow

### 1. Collect the Reference Material
When the user says "I'll give you my past chat history, first understand it, then ask me":
- Acknowledge and ask them to share
- Once received, study these specific signals:
  - **Salutation:** "Hi" vs "Dear" vs "Good morning" vs none
  - **Honorifics:** "Sir" / "Uncle" / "Bhaiya" / first-name only
  - **Emoji use:** 🙏, 😊, 👍, etc. — frequency and placement
  - **Sentence length:** Short bursts vs full paragraphs
  - **Follow-up style:** "Just checking" vs "Gentle reminder" vs direct
  - **Apology/deference:** "Sorry to bother", "Whenever convenient", etc.
  - **Sign-off:** "Thanks", "Regards", "🙏", or no sign-off
  - **Punctuation:** Full stops, exclamation marks, ellipsis (...)

### 2. Draft Matching Their Style
Pattern-match the signals above into the draft. Examples from verified sessions:

**Jitu Virwani style (Nishant → elder/family mediator):**
- Salutation: "Good morning Jitu Sir🙏"
- Deferential: "Whenever it is convenient for you, sir🙏"
- Soft follow-up: "I believe you have spoken to..."
- Collaborative framing: "I would be keen on meeting you to discuss how we can bring this to a conclusion"
- Uses 🙏 after key sentences, not just at sign-off

**Nagaveni style (Nishant → Embassy contact):**
- Salutation: "Hi Nagaveni, I hope all is well🙏"
- Apologetic deferral: "I didn't bother you for quite some time because... I didn't want to keep bothering you at all"
- References shared context: "Jitu Sir in fact spoke to me..."
- Offers help: "If there is anything you need from me or Umita, please do let me know🙏"

**Ashwin Pai style (Nishant → Century Real Estate contact):**
- Casual: "Hey Ashwin"
- Short: One question, no preambles
- Direct: "just checking — how's your schedule looking today?"
- Deferring: "as per your convenience"

### 3. Deliver the Draft
- Show the full draft in a code block first
- Ask the user to confirm tone/accuracy before generating the WhatsApp link
- Once confirmed, generate the wa.me deep link

### 4. Update User Memory
If the user says "this is exactly how I write to him", note the style in memory so future sessions for the same contact start with the right tone without needing a repeat reference.

## Pitfall — One Chat Stub Is Not Enough
A single message pair ("Hi" → "Will do") gives no style signal. Ask for at least 3-4 exchanges with the recipient's responses visible so you can see the full conversational rhythm.
