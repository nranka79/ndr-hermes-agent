# Voice Message — Action Extraction

## The Pitfall

When the user sends a voice message, **they often sandwich the actual request inside descriptive/conversational content.** The natural (but wrong) response is to engage with the descriptive part — comment on what they're describing, agree, share related info.

**This is a trap.** The user will say "I think you missed most of what I said" and have to repeat the actual request.

## The Pattern

Voice messages from this user (Nishant) follow a predictable structure:

1. **Context/Setup** — "Thank you for watching..." / "The coffee tastes fantastic..." / "I'm enjoying this..."
2. **Reaction/Emotion** — "Unfortunately I don't have an espresso machine..." / "Even as drip it tastes excellent..."
3. **⇨ THE ACTION REQUEST** — "I want a WhatsApp message for Kishan..." / "Can we find the folder where..."

**The action request is always at the end or near the end.** Skip the first 50-70% of the message — it's background color, not the task.

## Rules

- **Never respond to the descriptive/emotional content** of a voice message. No commenting, no agreeing, no sharing related information.
- **Extract the imperative sentence** — look for "I want", "Can we", "Please", "I need you to", "Send a", "Create a".
- **If there's no imperative** (rare), ask "What would you like me to do?"
- **When the user describes enjoying something** (coffee, food, a gift) and then says "I want a WhatsApp message thanking them for it" — the task is the message, not the conversation about the thing.

## Symptoms You Hit This Pitfall

- User says "I think you missed most of what I said"
- User has to repeat the actual ask in a follow-up message
- You responded to the content/topic instead of executing the action
- You ended your turn with information about the topic (coffee origins, etc.) instead of delivering the requested artifact

## Corrected Response Pattern

```
Voice message received → extract action request → execute immediately → deliver result
```

Do NOT pass through: reacting to the content, providing additional info on the topic, commenting on the user's experience.

## Related Pitfall — Multi-Recipient Name Mismatch

**The trap:** When the user asks for the same message sent to multiple people, you generate the first link correctly (e.g., "Hey Kishan, thanks for the coffee...") and then copy-paste the body to the second person without changing the greeting. The second person gets a link that says "Hey Kishan" when it should say "Hey Arjun."

**Symptoms:**
- User notices the wrong name in the message
- User has to point out the mismatch before sending

**Fix:** Generate each link from a **separate message string** with the correct recipient name. Never reuse the `quote(message_text)` variable across recipients — always create a new string variable per recipient with their own name.
