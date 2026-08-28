# Schedule Content Style — User Preference (DRAAS)

## Core Rule

**Schedules in legal documents must be brief and factual.** They state what is being contributed, by whom, and for what purpose — nothing more.

### ✅ Correct

> Schedule B properties belonging to Ashok Kumar and Schedule C properties belonging to C.R. Nagendra shall be contributed to the reconstituted partnership.

> The Vendor is the Developer and has acquired development rights by virtue of Registered JDA dated 16.08.2025 (Doc No. SHV-1-02227-2025-26).

### ❌ Wrong (got corrected)

> These lands were also originally part of M/s. Satvik Developers, which was dissolved and its assets partitioned amongst its erstwhile partners vide the Registered Partition Cum Settlement Deed dated 16 January 2024...

> The Vendor is the absolute Landowners and in peaceful possession and enjoyment of the converted Land... acquired through Registered Sale Deed... from the original owners...

## Why

- The legal documents (JDA, Sale Deed, Partition Deed) already contain the full details
- The Schedule only needs to identify the property and its source of title
- Explanatory backstory clutters the Schedule and risks inconsistency with the underlying documents
- The user will strip it if added — saves a round-trip to keep it minimal

## Triggers

- User says "Schedule B/C/F needs updating"
- User says "just mention that [X] will be contribution"
- User says "regenerate this Schedule with [specific change]"
- User says "not to be this detailed"

## Pitfall

Don't revert to the "absolute Landowners / acquired through Sale Deed" framing when the property comes from a JDA. The developer holds development rights, not ownership — the wording should clearly say "acquired development rights and ownership entitlement by virtue of Registered JDA."

## Related References

- `agreement-of-sale-schedule-f-developer-share.md` — Schedule F when vendor is Developer via JDA
- `targeted-clause-updates.md` — Scope precision for individual clause edits
- `rera-agreement-of-sale-bank-details.md` — Bank details insertion with scope rule
