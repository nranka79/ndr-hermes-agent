# Gmail Blacklist / Spam Mover

Two complementary approaches to redirect unwanted senders to SPAM when the Gmail API token lacks `gmail.settings.sharing` scope for native filter creation.

## Approach A: Native filters + periodic script (RECOMMENDED)

Even without `gmail.settings.sharing`, you CAN create filters that skip the inbox. Pair this with a periodic sweep script for full spam placement.

### How it works

1. **Native Gmail filter** — created via API with `removeLabelIds: ["INBOX"]` only (no `addLabelIds: ["SPAM"]` — that's forbidden by the API). New mail from blacklisted senders skips inbox instantly and lands in All Mail.
2. **Periodic sweep script** — runs every 15 minutes, searches All Mail (not just inbox) for blacklisted senders, and batch-moves them to SPAM via `batchModify(addLabelIds: ["SPAM"])`.

This gives you zero inbox clutter (instant) + eventual spam folder placement (within 15 min).

### Gmail API filter limitation

Filter creation fails with `HttpError 403: Request had insufficient authentication scopes` or `Invalid label SPAM in AddLabelIds` when the token lacks `gmail.settings.sharing` scope. The modify scope IS sufficient to read/search messages and batch-modify labels, which enables the workaround.

### Script (no_agent watchdog)

Location: `/data/hermes/scripts/blacklist_spam_mover.py`

Key features:

```python
# Searches ALL mail not already in spam/trash (catches auto-filtered items too)
results = service.users().messages().list(
    userId='me',
    q=query + " -in:spam -in:trash",  # NOT "in:inbox" — native filters skip inbox
    maxResults=25
).execute()

# Moves found messages to SPAM
service.users().messages().batchModify(
    userId='me',
    body={'ids': ids, 'removeLabelIds': ['INBOX'], 'addLabelIds': ['SPAM']}
).execute()
```

### Cron setup

```bash
cronjob action=create name="Gmail blacklist spam mover" \
  schedule="every 15m" \
  no_agent=true \
  script=blacklist_spam_mover.py
```

`no_agent=true` means the script IS the job — non-empty stdout = message delivered, empty stdout = silent (nothing to report).

### Cross-account support

The script covers ALL 3 of NDR's accounts in a single run:

| Account | Service name | Vault key |
|---|---|---|
| ndr@draas.com | `google-draas` | Primary |
| ndr@ahfl.in | `google-ahfl` | Secondary |
| nishantranka@gmail.com | `google-gmail` | Personal |

Each account gets its own `build_service()` and `scan_and_move()` call.

### Identity handling

Scripts running under `cronjob` or `terminal()` resolve the vault user via `HERMES_SESSION_USER_ID`. Force NDR's identity:

```python
os.environ['HERMES_SESSION_USER_ID'] = '7449813913'  # NDR's telegram uid
```

## Approach B: Script-only (15-min latency, no native filters)

Use when you can't or don't want to re-authorize. Same script but with `"in:inbox " + query`. New mail sits in inbox up to 15 minutes before being moved.

## Google Groups forwarded senders (Reply-To matching)

Some spam arrives via DRAAS Google Groups forwarding. The `From:` header shows the group address (e.g. `marketing@draas.com`), not the original sender. Match via `Reply-To` header instead:

| Forwarded via | Original sender | Match query |
|---|---|---|
| marketing@draas.com | Internshala <employer@internshala.com> | `replyto:employer@internshala.com` |
| subscription@draas.com | Adobe Stock <noreply@adobe.com> | `replyto:noreply@adobe.com` |
| info@draas.com | Vibro Springs <enquiry@vibrosprings.com> | `replyto:enquiry@vibrosprings.com` |

**Warning**: Reply-To addresses can change. Adobe Stock was previously `mail@mail.adobe.com` — verify by checking recent email headers when a sender stops being caught.

## Adding new senders to blacklist

When the user says "also blacklist X":
1. Find an example email from that sender (search by subject / sender name)
2. Check headers — direct (`From:`) or forwarded via group (`Reply-To:`)?
3. Add query to BLACKLIST array in script
4. Also create a native filter with `removeLabelIds: ["INBOX"]` for instant skip-inbox
5. Update script on disk and run once to catch existing messages

## Current blacklist (NDR's accounts, Aug 2026)

| Sender | Match field | Query value |
|---|---|---|
| CQRA Private Limited | from | marketing@cqra.acts-int.com |
| Amit Saparia / Outline PR | from | amit@outlinepr.com |
| World HRD Congress / Secretariat | from | secretariat1@worldhrdcongress.com |
| Chelsea / IFTTT | from | chelsea.c@ifttt.com |
| Mritunjay Anand / Reliable Ispat Udyog | from | mritunjay.anand@reliablegroup.net |
| Internshala | replyto | employer@internshala.com |
| Adobe Stock | replyto | noreply@adobe.com |
| Vibro Springs | replyto | enquiry@vibrosprings.com |

## Limitations

- **15-minute latency to SPAM**: native filters skip inbox instantly, but sweep to SPAM runs every 15 min. Gmail's ML may learn from repeated moves and route directly.
- **Not retroactive for bounces**: if senders already got bounce notifications before blacklisting, those already happened.
- **Reply-To addresses change**: vendors change email infrastructure. Periodically verify known senders still get caught.
