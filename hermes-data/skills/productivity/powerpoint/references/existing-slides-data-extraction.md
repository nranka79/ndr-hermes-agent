# Extracting Data from Existing Google Slides

Use this when you need to rebuild, analyse, or bulk-edit an existing Google Slides presentation whose content you don't have structured access to.

## Technique: Export as plain text

Drive API's `files.export()` with `mimeType=text/plain` dumps every text element from every slide into a single flat text file, preserving only content (no formatting, no position, no images).

```python
from tools.gws_skill_bridge import call

result = call('drive_download', service_name='google-draas',
              file_id='<SLIDE_FILE_ID>',
              output='/tmp/slides_content.txt',
              export_mime='text/plain')
```

The output is a stream of all text frames in slide order, with line breaks between each text element and slide/page separators.

## What you get

- Every text box, title, subtitle, and shape text from every slide
- Content appears **in slide order** with page breaks
- Line-art content (shapes without text) is silently dropped
- Tables become concatenated text rows

## What you DON'T get

- Font sizes, colours, positions, or formatting
- Slide backgrounds, images, charts, or diagrams
- Which text belonged to which slide (only sequential ordering)
- Speaker notes (text/plain export drops these)

## Workflow

1. Export existing slides as text
2. Manually parse the export into structured data objects (one per project/slide)
3. Use that structured data as input for the new presentation build

## Limitations

- For presentations with 40+ slides, the text output can be 30-50KB. Read it in sections.
- Some Google-native text elements (bullets, numbered lists) come through with leading whitespace/dash markers.
- If a slide is entirely image-based, it produces no text at all.
