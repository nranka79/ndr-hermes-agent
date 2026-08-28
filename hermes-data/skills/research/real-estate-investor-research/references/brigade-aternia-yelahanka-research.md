# Brigade Aternia — Yelahanka, Bangalore (Research Log)

**Date:** 2026-05-31  
**User:** Nishant Ranka (DRAAS)  
**Goal:** Get unit configs (3BHK/4BHK sizes), floor plans, brochures, RERA number, inventory

---

## ✅ Confirmed Data

| Field | Value | Source |
|-------|-------|--------|
| RERA Number | `PRM/KA/RERA/1251/310/AG/171113/000598` | 360realtors.com footer |
| Developer | Brigade Group | General knowledge |
| Location | Yelahanka, Bangalore (North Bangalore) | General knowledge |

---

## ❌ Failed Access Paths

All major property portals and the developer website blocked programmatic access:

| URL | Result | Notes |
|-----|--------|-------|
| `brigadegroup.com/projects/bangalore/brigade-aternia/` | 403 Forbidden | User-Agent blocking |
| `99acres.com/brigade-aternia-yelahanka-bangalore` | 403 Forbidden | CDN-level blocking |
| `magicbricks.com/brigade-aternia-yelahanka-bangalore` | 403 Forbidden | CDN-level blocking |
| `nobroker.in/property/brigade-aternia-yelahanka-bangalore` | Returns generic homepage | JS-rendered SPA, no project data |
| `commonfloor.com/brigade-aternia-yelahanka-bangalore` | Landing page only | Project content not populated |
| `360realtors.com/brigade-aternia-yelahanka-bangalore` | Page shows "missing" | RERA number in footer only |
| `rera.karnataka.gov.in/projectDetails` (direct API) | Times out | Requires authenticated session |

## ✅ Working Paths

## ✅ Working Paths

1. **User-provided authenticated RERA URL** — RERA Karnataka requires login. User (Nishant) offered to log in and share the link. This is the confirmed working path for accessing approved plans and project documents.
   - RERA URL pattern: `https://rera.karnataka.gov.in/projectDetails/PRM/KA/RERA/1251/310/AG/171113/000598`
2. **Web search snippets** — `web_search` / `ddgs` return title + URL + 2-3 line snippets. Primary working data source for configs/pricing until portal blocks resolved.
3. **360realtors.com** — Always check here even when the main page shows "missing" — the RERA registration number is reliably embedded in the footer carousel.

## Next Step

Await user's authenticated RERA URL to extract:
- Approved floor plans
- Unit configurations with carpet/built-up areas
- Inventory availability
- Brochure download links
