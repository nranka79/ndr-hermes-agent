# Daily Email Review Workflow

Class-level pattern for reviewing today's emails from Gmail and producing a structured summary. Trigger when the user asks "check my emails", "summarize today's emails", "what's in my inbox today".

## Workflow

### Step 1: Get today's emails

Search Gmail for all messages received today:
```
query = 'after:YYYY/MM/DD'
```

Get total count:
```
results = service.users().messages().list(userId='me', q=query).execute()
```

For scanning, pull metadata (Subject, From, Date) on all results. For detailed body content, fetch `format='full'` on individual messages.

### Step 2: Categorize

**Work emails** — any email related to:
- Projects, vendors, contractors, consultants
- Legal, RERA, property, land
- Company operations, recruitment, HR, payroll
- Internal team comms (Nishant, Anbu, Prakash, Roshini, Vinod, etc.)
- External business partners (Embassy, Godrej, Kotak, etc.)
- Client/customer related

**Non-work emails** — everything else, typically:
- Bank alerts (Kotak, HDFC, IndusInd — balance updates, offers, maintenance)
- Marketing/newsletters (BMW, ET, McKinsey, WGSN, IndiGo, IPO offers, industry news)
- Automated notifications (Google Maps, LinkedIn, etc.)
- Attendance tracking auto-emails (Please sign in / sign out)

### Step 3: Sub-categorize Work Emails

| Category | Definition |
|----------|------------|
| **Action Required** | Emails where the user needs to reply, approve, decide, or take an explicit action. Contains a clear ask. |
| **Already Acted** | Emails where the user has already replied or taken action. Confirm what was done. |
| **For Noting** | Information-only emails the user should be aware of but no action is needed. |
| **Borderline / Industry Reading** | Industry news, webinars, events, reports — informational but professionally relevant. |

### Step 4: Structure the Response

```
TOTAL EMAILS RECEIVED TODAY: {count}

## WORK EMAILS — ACTION REQUIRED
{list with brief context}

## WORK EMAILS — ALREADY ACTED
{list with confirmation of action taken}

## WORK EMAILS — FOR NOTING
{list}

## BORDERLINE WORK
{industry reading, events, news}

## NON-WORK
{bank alerts, marketing, notifications}
```

### Step 5: Summarize each email

For each work email:
- **From:** Person name (email)
- **Subject:** as-is
- **Summary:** 1-2 sentences capturing what it's about, what's being asked, and any deadlines
- **Context:** relevant prior thread context if available from session history

## Pitfalls

- **Date boundary:** Use `after:` with today's date in YYYY/MM/DD format. Do not use `today` keyword as Gmail search syntax — it may fail.
- **Total count includes sent mail:** Gmail's `after:` query returns both received AND sent items in a single-day search. The count will include the user's own sent replies.
- **Attendance auto-emails:** These appear in bulk (10-20 per day, "Please sign in" / "Please sign out" for all team members). Group them as a single bullet — don't list individually.
- **Bank/alert fatigue:** Group bank alerts by bank name rather than listing each one individually unless the user asks for detail.
- **Thread grouping:** Multiple replies on the same thread should be grouped as one item (e.g., "Ranka Amber — UDS Column Update" with sub-bullets for each reply).
- **Senders known from memory:** Use the memory store to identify people — Eshwari is accounts, Gowri Singh is marketing, Vivek Chanda is creative vendor, etc.
