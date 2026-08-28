# Bot Response Protocol — Team Member Onboarding

## Trigger

Nishant says: send a message to [team member] explaining how to respond to "Anjali" (the Hermes bot) on Telegram.

## Context

When Nishant sends a Telegram DM to a team member via the bot, the team member needs to understand how to reply **back to Nishant through the bot**. Without these instructions, their reply goes into the ether (the bot's session, not Nishant).

## Template Message

Use this exact wording for the WhatsApp/Telegram message:

> I have sent you a Telegram message asking for [brief context]. When you respond on Telegram, please make sure you tell "Anjali" that you are responding to the above message and it is meant to be sent back to Nishant. Only then will that response be created and sent to me.

## Full Example (from June 2026 session — Anbu)

> Anbu,
>
> I have sent a follow-up email reply in the same thread (Ranka Iris — OC Shared) — please check and respond with day-wise timeline commitments on each item.
>
> Also, I sent you a Telegram message this morning asking for your plan of the day and what time you would be in the office. When you respond on Telegram, please make sure you tell "Anjali" that you are responding to the above message and it is meant to be sent back to Nishant. Only then will that response be created and sent to me.

## Key Points

- The bot's name is "Anjali" (not Hermes) when communicating with team members — use that name.
- The team member must explicitly tell the bot that their message is a response to Nishant's message.
- Without this instruction, the bot cannot route the response back to Nishant.
- Always pair this explanation with context about what was sent and why they need to respond.
