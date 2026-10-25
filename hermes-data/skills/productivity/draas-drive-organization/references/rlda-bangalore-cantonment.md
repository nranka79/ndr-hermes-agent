# RLDA Bangalore Cantonment / Bagmane Texworth — 5 FAR letter chain

Recurring NDR ask: *"find the letter BTPL/RLDA wrote to BDA requesting plan sanction
with 5 FAR, and the BDA rejection."* Everything lives in ONE Drive folder plus one
letter at Drive root. Read the chain in order — grant → rejection → appeal → new
order → CC application.

## Folder & search recipe
- Folder: **"Bangalore Cantonment Approvals"** — id `1gI05xmHExWm9zTpJjMKUY0MEIFzgFMai`
- Find it via `gws_drive_list(query="name contains 'RLDA'")` or
  `fullText contains 'Bagmane'` (the latter also surfaces the lease/payment/CCD files).
- Root-level letter: `Letter to Commissioner BDA reg FAR — 30.01.2024.pdf`
  (id `16uEcTqkQ_qdmMoenT4g00MS4VqI0EdEK`).
- Companion WhatsApp export "WhatsApp Chat RLDA cantt team (Sep 2022 - Aug 2026).txt"
  (id `1utjlFVHdTPblWC_PcbQbV-CsDtOjX7Sl`) is a good chronology source.

## The chain (dates, refs, Drive ids)
1. **GoK grant of 5 FAR on railway lands** — Cabinet-approved, G.O. **U.D.D 06 PRJ
   2019 dt 26.02.2019** (for BSRP funding via K-RIDE monetisation).
   Drive copies: `RLDA GoK UDD Gazette Order for 5 FAR.pdf` (`1RyjKOoMkkb2G9LgoGdcUMjmS4c3hkqb9`),
   `20250329 RLDA Cantt 5 FAR UDD 206 MNJ 2025.pdf` (`1CekLsih-hOX9Pcxu2ZkE4HdyoiVcHJlN`),
   `20250801 Karnataka Government NAE 206 MNJ 2025E FAR5 Railway Lands Bangalore Cant
   Vasanth Nagar Order.pdf` (`1WRhVQJ5VLeaOl_HsFvTe0g9rbN7mirtH`).
2. **BDA rejection** — dtd **28.11.2023**, ref **BDA/Nayusa/DLP-19/1819/2023-24**:
   `20231128 Bagmane Texworth BDA Development Plan Rejection Letter FAR5 Rejected Max
   FAR25 per RMP2015.pdf` (`1GRaGe1vnaCdjxMw-wGHrati1JzEqwM35`). Content: 5 FAR "not
   officialised"; development capped at max FAR 2.5 per RMP 2015. The scan is a poor
   OKEN scan — filename carries the FAR 2.5/RMP 2015 detail.
3. **RLDA appeal to BDA** — dtd **30.01.2024**, No **RLDA/Project/Bangalore/Consultancy/
   MonetizationofKRIDEProjects/2356**: `Letter to Commissioner BDA reg FAR`
   (`16uEcTqkQ_qdmMoenT4g00MS4VqI0EdEK`). From CPM RLDA Bangalore → Sri N Jayaram IAS,
   Commissioner BDA, subject "Urgent Appeal for Compliance with Cabinet-Approved FAR
   Grant for Railway lands identified for Monetisation for funding BSRP". Names the
   developer **M/s Bagmane Texworth Pvt Ltd**, cites Ref 1 (2019 GO) and Ref 4 (the
   28.11.2023 BDA refusal), urges BDA to positively entertain the plan sanction with
   5 FAR.
4. **BTPL commencement certificate application** — `20250819 Bagmane Techworth BDA
   Commencement Certificate Application FAR5 DP.pdf` (`1-cgWFmW8ZE9Vdo_N-D6d_E6t1QREz2Fn`).

## Related matter context (not the FAR letters, but same folder tree)
- WP 38186/2025 (A.T. Ramaswamy PIL) + Memoranda of Objections, caveat petition,
  biodiversity withdrawal notification — under `1KMQIhDo_1HL_tEPf1r4rphLhsmP5UePS`.
- Lease agreement b/w RLDA & BTPL (`18LTXISwe3Yov7HLSZvhl-AR63ublXfW7` folder;
  executed copies multiple places).
- BTPL→RLDA force-majeure payment/interest/period letters (29.04.2026 set).

## Delivery pattern
Give NDR the folder link + per-file links + the chain story (grant → rejection →
appeal → fresh 2025 orders → CC application). Verify links with `files().get` before
sending (Drive root letters are common candidates for re-fetch failures).