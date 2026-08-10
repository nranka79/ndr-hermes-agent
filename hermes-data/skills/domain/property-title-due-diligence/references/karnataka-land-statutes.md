# Karnataka Land Statutes — 48A/77A & the acquisition-vs-grant trap

Verified 2026-08-05 from PRS India gazette PDFs (see sourcing notes at the end).
This is the cheat-sheet for "which act/section" questions on land title clearances
(acquisition, grant, occupancy, PTCL) for Karnataka parcels.

## The two acts — never confuse them

| | Karnataka Land REFORMS Act, 1961 (Act 10 of 1962) | Karnataka Land REVENUE Act, 1964 (Act 12 of 1964) |
|---|---|---|
| Identity marker | "45. Tenants to be registered as occupants", Land Tribunal (s.48 Constitution of Tribunals) | "77. Road-side trees", Revenue Appellate Tribunal (s.40), "95. Uses of agricultural land" (conversion) |
| Grant sections | **48A** (occupancy claims), **77A** (grant of land in certain cases) | 69, 71, 91, 92, 94A/94B/94C |
| Has a 48A/77A? | YES | **NO** — s.48 = Power to make regulations, s.77 = Road-side trees |

## Section 48A — Karnataka Land Reforms Act, 1961 ("Enquiry by the Tribunal")
- Every person entitled to be registered as occupant under **s.45** may apply to the Land Tribunal (window was 6 months from 1978 amendment commencement; later extended)
- Tribunal publishes village notice, hears landlord/interested persons, and **by order grants or rejects** the occupancy claim
- s.48A(8): no application in time → the right to be registered as occupant has NO effect
- Practical meaning: a "no 48A application" endorsement = no tenant/occupant has claimed occupancy rights over the land

## Section 77A — Karnataka Land Reforms Act, 1961 ("Grant of land in certain cases")
Inserted by Act 23 of 1998 w.e.f. 01-11-1998. Operative part:
> (1) ... if the Deputy Commissioner ... is satisfied after holding such enquiry as he deems fit, that a person,—
> (i) was, immediately before the first day of March, 1974 in actual possession and cultivation of any land not exceeding one unit, which has vested in the State Government under section 44; and
> (ii) being entitled to be registered as an occupant of such land under section 45 or 49 has failed to apply for registration of occupancy rights ... under sub-section (1) of section 48A within the period specified therein; and
> (iii) has continued to be in actual possession and cultivation of such land on the date of commencement of the Karnataka Land Reforms (Amendment) Act, 1997,
> — he may grant the land to such person subject to such restrictions and conditions and in the manner, as may be prescribed.
- The **48A+77A pair** is exactly the "land is not under grant / no grant application / no pending grant proceedings" clearance buyers' counsel ask for.
- Correct endorsement ask: "land is not granted land; no application pending under s.48A and no grant proceedings/order under s.77A of the Karnataka Land Reforms Act, 1961 (and no PTCL proceedings)".

## Grant-related provisions in the Land REVENUE Act, 1964 (if anyone cites "48A of the Revenue Act" — it does NOT exist)
- s.69 Disposal of lands/property of State Govt; s.71 assignment for special purposes
- s.91 Unoccupied land may be granted on conditions; s.92 Grant of alluvial land
- s.94A/94B/94C — regularisation-type grants for unauthorised occupation (94B: pre-14-04-1990 occupation, failed 94A applicants; 94C: pre-14-04-1998 dwelling houses)
- s.95 conversion of agricultural land for other purposes

## Acquisition ≠ Grant (the trap in the SDO endorsement)
- A Sub-Division/DC endorsement that says "no acquisition of the land on record by this office under 48A" answers the ACQUISITION frame only
- It certifies NOTHING about grant/occupancy proceedings (48A/77A of the Reforms Act) or PTCL
- Applications are frequently mis-framed ("48A of the Land Revenue Act" was cited in a real 2026 application; no such section exists) — check the actual statute before accepting the frame, and tell the user plainly when the received endorsement answers the wrong question
- PTCL (Karnataka SC/ST (Prohibition of Transfer of Certain Lands) Act, 1978) is a THIRD, separate clearance — "not granted land under PTCL" — often sought alongside 48A/77A

## Sourcing statute text from a datacenter-blocked VPS (the ladder that worked)
1. Tavily `web_search`/`web_extract` share one backend — on HTTP 432 both fail; do NOT retry, switch immediately
2. Search engines from datacenter IP: Google=captcha, Bing=challenge, DDG=anomaly, Mojeek=403, searx=antibot — all dead
3. **Brave search works via plain curl**: `curl -sL -A "Mozilla/5.0 ... Chrome/125.0" "https://search.brave.com/search?q=<url-encoded>"` → results in `class="snippet"` divs; parse href + text with regex. Rate-limit: ≥5s between queries else HTTP 429
4. Browser (stealth chromium): indiankanoon = Cloudflare interstitial, indiacode = Access Denied
5. **PRS India hosts official gazette PDFs at predictable URLs** — the single most reliable source:
   - Land Revenue Act 1964: `https://prsindia.org/files/bills_acts/acts_states/karnataka/1964/1964KR12.pdf`
   - Land Reforms Act 1961: `https://prsindia.org/files/bills_acts/acts_states/karnataka/1962/1962KR10.pdf`
   - Pattern: `prsindia.org/files/bills_acts/acts_states/<state>/<year>/<year>KR<actno>.pdf`
6. Govt `*.karnataka.gov.in` / `*.nic.in` PDF paths are usually unreachable from the VPS (timeouts); don't burn time
7. After download: `pdftotext -layout file.pdf out.txt` then **verify act identity via section markers** (see table above) BEFORE trusting it — an archive.org item named "1964KR12" turned out to contain a different act's text; also grep with flexible patterns (`48[\s-]?A`) because PDF text renders section numbers variously ("48-A", "48A.")
