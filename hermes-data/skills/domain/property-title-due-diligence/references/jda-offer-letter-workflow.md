# JDA Offer Letter — Build Workflow & Pitfalls

## Scope
Branded (navy/gold) 2-page offer letters for JDA landowner proposals (e.g. Gunjur Sy No 38-1).
Pipeline: branded HTML → PDF via WeasyPrint (wp_env), branded DOCX via python-docx
(build_gunjur_offer_docx.py style builder). Pandoc NOT available (ephemeral /tmp binary).

## User preferences (Prakash / DRA)
- "just as offer letter" = concise 2-page letter, NOT the 16-page Bidadi-style proposal.
- Exactly 2 pages; near-empty page 3 is rejected as unprofessional.
- All key commercial terms must appear; ZERO placeholders.
- Branding: navy (#1F3864) / gold (#C99A2E).
- Do NOT include an "Encl:" (enclosure) line unless the user asks.
- Body text: FULL justification (both margins). Short blocks stay left-aligned:
  date/ref line, addressee block, subject, "With warm regards,", signature line.
  In HTML use body { text-align: justify } + .nojust class for short blocks;
  tables keep text-align: left.
- Deliverables: matching PDF + DOCX via MEDIA: paths.

## Common JDA offer-letter content
- 50:50 revenue share of developed saleable area; deposits none.
- Landowner scope: CLU (agri→non-agri) + Kharab regularisation.
- Developer rationale paragraph: Prestige does 50 acres+ in growing corridors →
  proposal is "an extension — and an excellent opportunity" to attach small parcel.
- Tentative launch price band (e.g. ₹6,000–6,500/sqft premium plotted) as own section
  with value-implication line for the landowner's 50% share.
- DRA ground-partner role (~5% of landowner share + brokerage) for non-local owners.

## Pitfalls (learned the hard way)
1. **patch tool double-escapes `\uXXXX` in Python source.** When patching a
   python-docx builder with strings containing `\u2022`/`\u2019`, the patch can write
   `\\u2022` (literal backslash) into the .py, which Python renders as literal
   `\u2022` TEXT in the DOCX. After ANY patch to a builder script, verify:
   `grep -n '\\\\u[0-9a-fA-F]' build_*.py` and check the output doc for
   `re.findall(r"\\u[0-9a-fA-F]{4}", all_text)` — must be empty. Fix by
   replacing `\\u2022` → `\u2022` in the .py.
2. **WeasyPrint pagination fights:** a near-empty last page comes from the
   signature block spilling 1–4 lines. Tighten in this order: sig-space height
   (4mm), page bottom margin, table padding, list spacing, gold-bar margin,
   then drop decorative footer if it alone spills. Re-render + count pages after
   each change; verify visually via pdftoppm -png -r 80 + vision_analyze.
3. **Justification affects tables/li too:** body { text-align: justify } cascades
   into table cells and list items — explicitly reset td/th to left, and add
   .nojust to short one-line blocks or they stretch awkwardly.
