# Nishant TMP Staging Rule (Hard Constraint)

**Rule (quoted from user voice message):**  
"Always, always, always. Put it in the TMP folder. Don't create anything in the root. [...] anything new that you create for me, whether it's a document spreadsheet, PowerPoint, uploaded file, anything, always first put it in the TMP folder only. From there, we will move it around anywhere else. And with the TMP folder, at least I can clean it up every once in a while."

**Implementation requirements for all productivity skills:**

1. **Never** create files directly in Drive root (`parents="root"` or omitted parents).
2. **Always** set the initial parent to the TMP folder ID: `18p74II2uL32sNDzDDwXzmlOUdJJOTmE-`.
3. After creation, the document link should still be returned, but the file must physically live in TMP until Nishant moves it.
4. This rule applies to:
   - Google Docs (HTML import or Docs API)
   - Google Sheets
   - Google Slides
   - Any uploaded files (PDFs, images, CSVs, etc.)
   - Exported reports, session archives, gbrain exports
   - Any artifact created via `write_file`, Drive API, or productivity tools

**Preferred pattern in code:**
```python
file_metadata = {
    'name': 'YYYYMMDD_DescriptiveName',
    'mimeType': 'application/vnd.google-apps.document',
    'parents': ['18p74II2uL32sNDzDDwXzmlOUdJJOTmE-']   # TMP folder
}
```

This rule has been added to `google-doc-formatting-template` and should be propagated to all other productivity/document-creation skills (google-workspace, productivity-workflows, document-dossier-compilation, etc.).

**Why this matters:** Nishant uses TMP as a deliberate inbox/staging area for cleanup. Creating in root pollutes his Drive root and breaks his workflow.

Last updated: 2026-07-10
