# Contact Resolution — Multiple-Sheet Search Anti-Pattern

**Date:** 2026-05-27
**Skill(s) touching this:** `messaging-drafts`, `whatsapp-drafter-full.md`

---

## Lesson Learned

**Anti-pattern:** When a contact is not found in the primary Google Contacts sheet, do NOT silently iterate through other Sheet IDs in the user's Drive looking for additional contacts lists.

**Correct pattern:** Ask the user immediately for the mobile number. The user is the fastest source.

---

## What Happened This Session

User asked to draft a WhatsApp to "Anbu" — expected to be a DRA employee or associate.

Steps taken:
1. Searched primary contacts sheet (`NDR DRAAS Google contacts`) — no match
2. Searched `NDR CONTACTS` sheet — empty result
3. Searched `DRA Contact Updated List 2016` and `List of contact numbers & Email ID` — no match

Total time wasted: ~8 seconds of API calls + 3 toolcall failures.

**Should have been:** "I don't have Anbu in the contacts sheet. Could you share their WhatsApp number so I can set up the link?"

---

## When to Ask Instead of Search

| Situation | Action |
|-----------|--------|
| Contact not in primary sheet on first attempt | Ask user for the number directly |
| User describes a person by relation ("my brother", "my sister") | Ask user for the number directly |
| Person is a one-time or external contact (lawyer, broker, family friend) | Ask user for the number directly |
| Multiple sheets exist but primary returned empty | Ask user for the number directly |

**Never:** Loop through 3+ sheets before asking. This is a 3-toolcallDelay anti-pattern that costs time and yields nothing extra.

---

## Relevant Sheet IDs (for reference only — do not loop through these)

| Sheet Name | Sheet ID |
|------------|----------|
| NDR DRAAS Google contacts | `1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g` |
| NDR CONTACTS | `1fYa-t2RY1siy2qBgAH8uu_Jd2chjJ716BbcpxilpOK0` |
| DRA Contact Updated List 2016 | `16LYrhAAiAib9I_lIHjdu9CNRU8nszvXQ2b0rvO7T-sY` |
| List of contact numbers & Email ID | `1GRrndy0btgF-uB_v1XqWUNu-FfbieAfS1eKqTMmSaYU` |
| Ranka Iris Related Important Contacts | `1mb3Ua5_yRB73_2G6v8Koz6HY-xb9XJ3Ig44QgKztd1Y` |
| DRA Channel Partner Contact Sheet | `1j-TGzgU3lUb_7XVf4DbAJlECfq7NZGgZbguXHQ_R2hs` |

**If the primary sheet returns empty → ask the user → do not progress to secondary sheets.**
