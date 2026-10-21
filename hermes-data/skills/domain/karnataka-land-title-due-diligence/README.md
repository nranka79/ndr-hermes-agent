# Karnataka Land Title Due Diligence Skill

Package contents:
- `SKILL.md` — agent instructions and end-to-end workflow.
- `REFERENCES.md` — official legal/record source starting points and source validation protocol.
- `MASTER_CHECKLIST.csv` — importable starter checklist.

Install/use:
1. Put this folder in the agent's skills directory or repository according to that agent's skill-loading convention.
2. Ensure the agent has access to PDF/OCR tools, spreadsheet creation, file/folder operations, and (where intended) Google Drive access.
3. Give the agent the property folder or combined PDF and instruct it to run the skill.
4. Configure the user's actual Google Drive root `TMP` location in the agent environment. This package deliberately does not invent a Drive API path or assume that a tool has Drive access.
5. Have a Karnataka property advocate validate the legal source library and approve the final opinion.

Important: This is a workflow specification, not a legal opinion or guarantee of title. Current law, amendments, notifications and case law must be checked for each property.
