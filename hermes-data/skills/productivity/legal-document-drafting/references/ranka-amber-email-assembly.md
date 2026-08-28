# Ranka Amber — Email Assembly to Landowner (June 2026)

**Session:** Bharat (user) asked to draft email to landowner Raghu Ayur with sharing agreement + attachments. Session interrupted — user was about to provide links to confirm exact file versions. Workflow established but not completed.

---

## Confirmed Drive Files (June 2026)

| Document | Drive ID | Type | Notes |
|----------|----------|------|-------|
| **SSA FINAL v3** (Sharing Agreement) | `1EnY77qQ-UXeMV7Pr49l6kiK_RTITK_jQ09gvljTthWI` | Google Doc | Final draft |
| **Area Statement (April 2026)** | `1PG-Gn4b0lCZCXXktksqxFXnOeImG_vb-SugMcwUwuWU` | Google Sheet | |
| **Parking Sharing Plan** | `1-7COdL_9h2hVypvklN2IiJG-niCN4-NF` | PDF | `20260529_Ranka Amber_Stilt Floor_Parking_Sharing_Plan.pdf` |
| **Sanctioned Plan** | `1aaNKuSd01zDgfiAGzELC2IQP75rghht2` | PDF | `AMBER SANCTION 07.05.2026.pdf` |

**Amber folder (master):** `1HmCPlVkdjAvoxGYTZwOShmfl3yykWR1j`

---

## Email Recipe

**To:** Raghu Ayur (landowner)
**CC:** Manohar Singh — REDSOUL (manohar@redsole.in — confirmed from WhatsApp chat)
**Subject:** Ranka Amber — Sharing Agreement Draft for Your Review

**Attachments (4 total):**
1. SSA FINAL v3 (Google Doc — export as PDF or keep as Docx link)
2. Area Statement - Ranka Amber (April 2026) — Google Sheet
3. Parking Sharing Plan PDF
4. Sanctioned Plan PDF (AMBER SANCTION 07.05.2026.pdf)

**Body:** Request review, confirm order, proceed to signing so banking docs can follow. Mention RERA number pending parallelly.

---

## Contacts (from prior sessions)

| Person | Role | Email |
|--------|------|-------|
| Raghu Iyer | Landowner | raghupreethi@gmail.com (from WhatsApp chat) |
| Farida Iyer | Co-landowner | farida.iyengar@gmail.com |
| Manohar Singh | REDSOUL | manohar@redsole.in |

---

## Workflow (Pattern for future Ranka Amber emails)

1. Search Drive for project files by name pattern (`Ranka Amber`)
2. Identify correct versions — user may provide links to confirm
3. For Google Docs/Sheets: check mimeType → use `export()` for native, `get_media()` for binary
4. For PDF attachments: download to `/tmp/` then attach to MIME draft
5. Build MIME `multipart/mixed` with HTML body → base64 → `drafts.create`
6. Verify draft after creation (`drafts.get` with `payload.parts` check)

---

## Key Project Facts (locked from prior sessions)

- **Project:** Ranka Amber, D'Silva Layout, Pattandur Agrahara, Whitefield
- **BBMP LP:** BBMP/CC/4247/26-27 (accepted 07-May-2026)
- **Sharing:** 50:50 | 20 units (LO: 101-105, 401-405; DEV: 201-205, 301-305)
- **Possession target:** 07-Nov-2028
- **Parking:** 21 slots (LO: odd numbers 1-19; DEV: even numbers 2-20; slot 21 VP)