# Medical PAP / OTP Follow-up Email Pattern

## Trigger

User needs to follow up with a pharma Patient Assistance Program (PAP) about an outstanding OTP for medication delivery, typically after already submitting infusion confirmation forms, prescriptions, and patient details.

## Sequence

1. **Search the correct inbox first** — the user may have sent the original from a non-default account (e.g. `ndr@ahfl.in`, not `ndr@draas.com`). Resolve via `gws_resolve_account()` first. If token expired, offer re-auth URL — do NOT fall back to default account.

2. **Find the right thread** — search the named account for the pharma company domain (`kiranpapv3@medybizpharma.com`), patient name, and topic keywords (`infusion`, `OTP`, `Keytruda`, `PAP`). Extract the latest message from the user to them (to understand what was communicated) and any acknowledgment from the pharma side.

3. **Check OTP status** — search inbox for any reply from the pharma domain after the user's last sent email. Also search for any automated order/delivery emails containing OTP or delivery details. If no OTP found → proceed with follow-up.

4. **Draft the follow-up — tone and content:**

   - **Lead with the reminder** — "This is a gentle reminder regarding the OTP for Ms. [Patient]'s [Medication] delivery for her upcoming infusion."
   - **Flag the data-check request** — "If there is any discrepancy in the details — patient name, prescription, dosage, or any other data — please let us know immediately."
   - **Reference the previous incident** — "Unlike last time, we cannot afford a situation where issues come to light only on the day of the infusion, causing a delay in administering this critical, life-saving medication."
   - **Close with urgency** — "Please review the details thoroughly and confirm everything is in order. Share the OTP at your earliest convenience."
   - **No boilerplate greetings** — the user's voice is direct, no pleasantries.

5. **Create the draft in the CORRECT account** — use `draft_reply_create` with the same `service_name` as the account where the original email lives. Verify the draft is in Drafts, not Sent.

## Pitfalls

- **Wrong account is the #1 failure mode.** The user will correct you fast if you create the draft under `google-draas` instead of `google-ahfl`. Always go to the source inbox.
- **Do not assume OTP hasn't come just because the thread looks quiet** — check for auto-replies, order confirmation emails, and delivery details from the pharma domain that may arrive as separate emails (not threaded).
- **The user's previous experience with a delay** makes this emotionally charged — reference it explicitly in the draft as the user instructs ("unlike last time").
- **The pharma side may have a ticket system** — note the ticket number from their acknowledgment (e.g. `[Ticket No:7027]`) and include it in the reply for tracking.
