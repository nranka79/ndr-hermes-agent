# gws_skill_bridge Calendar Operations — kwarg/arg-name mismatch trap

**Status:** Working pattern, confirmed Jul 2026.

## What the bridge does

`tools.gws_skill_bridge.call(operation, **kwargs)` creates a `types.SimpleNamespace` from kwargs, then passes it to the skill function which reads attributes like `args.summary`, `args.start`, `args.location`. The parameter names differ from the Google Calendar v3 API — and **every optional parameter MUST be passed** (even as empty string) because SimpleNamespace raises `AttributeError` on missing attributes.

## Operations & the kwarg names that ACTUALLY work

| Operation | Working kwargs | Notes |
|---|---|---|
| `calendar_create` | `summary=...`, `start='ISO_DT'`, `end='ISO_DT'`, `location=''`, `attendees=''`, `calendar='primary'`, `description=''` | All optional params (`location`, `attendees`, `calendar`) must be passed explicitly as empty/falsy values to avoid `AttributeError`. `start`/`end` are ISO datetime strings with timezone, not dicts. |
| `calendar_list` | `calendar='primary'`, `max=10`, `start='ISO_DT'`, `end='ISO_DT'` | `calendar` is required. `start`/`end` are optional ISO datetime strings. |
| `calendar_delete` | `event_id='...'`, `calendar='primary'` | Both required. `event_id` is the Calendar API event ID, not a human-friendly label. |

## What bit me (AttributeError)

### `calendar_create` requires ALL optional kwargs

**Problem:** The skill function checks `if args.location:`, `if args.description:`, `if args.attendees:` with direct attribute access — NOT `getattr()` or `hasattr()`. If the kwarg was not passed to `call()`, the attribute doesn't exist on the SimpleNamespace and Python raises:

```
AttributeError: 'types.SimpleNamespace' object has no attribute 'location'
AttributeError: 'types.SimpleNamespace' object has no attribute 'attendees'
AttributeError: 'types.SimpleNamespace' object has no attribute 'calendar'
```

**First call failed** because only `summary`, `start`, `end` were passed. Required fixes:
- Added `location=''`
- Added `attendees=''` (comma-separated emails string, or empty string)
- Added `calendar='primary'`

The `reminders` dict **is silently ignored** — the skill function doesn't read `args.reminders` at all. To set reminders, use the raw Calendar API.

### `calendar_list` also needs `calendar='primary'`

The function uses `_run_gws` or `service.events().list(calendarId=args.calendar, ...)`. Without `calendar='primary'`, it raises the same `AttributeError`.

## Working recipes

### Create a calendar event

```python
from tools.gws_skill_bridge import call

result = call("calendar_create", service_name="google-draas",
    summary="Call Nagrajappa JDTP - Inspection Scheduling",
    description="Nagrajappa (JDTP) asked to call at 10:30 AM to fix appointment.",
    start="2026-07-18T10:30:00+05:30",   # ISO 8601 with IST offset
    end="2026-07-18T11:00:00+05:30",
    location="",                          # REQUIRED — empty string to avoid AttributeError
    attendees="",                         # REQUIRED — empty string to avoid AttributeError
    calendar="primary")                   # REQUIRED — use "primary" for default calendar

# Returns: {"status": "created", "id": "...", "summary": "...", "htmlLink": "..."}
```

### List calendar events

```python
result = call("calendar_list", service_name="google-draas",
    calendar="primary",                   # REQUIRED
    max=10,
    start="2026-07-18T00:00:00+05:30",
    end="2026-07-25T23:59:59+05:30")
```

### Delete a calendar event

```python
result = call("calendar_delete", service_name="google-draas",
    calendar="primary",
    event_id="4b83krojjeqchu6pv38hc7m4bc")

# Returns: {"status": "deleted", "eventId": "..."}
```

## Pitfalls

- **`start` and `end` are plain ISO strings, not dicts.** Unlike the Google Calendar API where start/end are dicts with `dateTime`/`timeZone`, the bridge function expects flat ISO strings. The skill wraps them as `{"dateTime": args.start}` internally.
- **Timezone is your responsibility.** The ISO string must include the offset (`+05:30` for IST, `Z` for UTC). The bridge does not add timezone — it passes the string directly to the API.
- **`reminders` dict is silently ignored.** The skill function doesn't read `args.reminders`. If you need custom reminders (popup/email at specific intervals), use `build_service("calendar", "v3")` directly and create the event with the full `reminders` override structure.
- **`location` and `description` with falsy values produce no location/description** — the function only adds them to the event body when `if args.location:` / `if args.description:` evaluates truthy. Passing `location=''` means no location is set on the event, which is correct behavior.
- **`attendees=''` means no attendees** — the function splits on comma and strips whitespace. An empty string produces `[]`.
- **No color/transparency support** — the bridge doesn't expose `colorId` or `transparency`. Use the raw API for those.
- **Output is JSON on stdout** — `call()` returns a string. The result includes `htmlLink` so you can present it to the user as a clickable calendar link.
- **`service_name` defaults to `"google-draas"`** — pass explicitly for multi-account setups.

## When to bypass the bridge

Use `tools.gws_auth.build_service("calendar", "v3")` directly when you need:

- **Recurring events** — the bridge doesn't expose `recurrence` (RRULE)
- **Custom reminders** — the bridge silently drops the `reminders` kwarg
- **Conference data** (Google Meet links) — the bridge doesn't expose `conferenceData`
- **Color coding** — the bridge doesn't expose `colorId`
- **Transparency** (`opaque` vs `transparent` for free/busy) — not exposed
- **Any `event.patch()` or `event.update()`** — the bridge only supports `create`, `list`, and `delete`

```python
from tools.gws_auth import build_service
from datetime import datetime, timezone, timedelta

service = build_service("calendar", "v3", service_name="google-draas")

event = {
    "summary": "My Event",
    "description": "Full control over all fields",
    "start": {"dateTime": "2026-07-18T10:30:00+05:30", "timeZone": "Asia/Kolkata"},
    "end": {"dateTime": "2026-07-18T11:00:00+05:30", "timeZone": "Asia/Kolkata"},
    "reminders": {
        "useDefault": False,
        "overrides": [
            {"method": "popup", "minutes": 10},
            {"method": "email", "minutes": 30}
        ]
    },
    "colorId": "2",  # green
    "transparency": "opaque",
}

result = service.events().insert(calendarId="primary", body=event).execute()
print(f"Created: {result.get('htmlLink')}")
```
