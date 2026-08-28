# Marketing Collateral Gap Analysis — Video + Deck Review

## When to Use

User shares marketing materials (video + investor deck/PDF) from an agency and asks you to evaluate them against a strategic brief. Common triggers: "analyze this video," "review the deck," "what's missing," "give feedback for the agency."

## Sequential Workflow

### Step 1: Listen / Read the User's Brief Carefully

The user will often give a DETAILED voice message or text explaining:
- What the material is SUPPOSED to achieve (target investor, desired emotional response, key message)
- What they think is MISSING (narrative gap, credibility gap, factual gap)
- The context about the project/company that should be conveyed

**Do not skip this step.** The user's brief IS the evaluation criteria. Capture key points:
- Target audience (institutional investor, HNI, family office)
- Desired emotional response (wow, confidence, trust, urgency)
- Key messages that must land (location, scale, brand legacy, financial returns)
- Known gaps the user already identified
- Competitors/benchmarks mentioned (Golfshire, Embassy Boulevard, etc.)

### Step 2: Transcribe the Video (if video is provided)

If the video is a YouTube link:
1. Download audio using `uv run yt-dlp -x --audio-format mp3 -o "/tmp/audio.%(ext)s" "URL"`
   - If unlisted video, yt-dlp requires cookies/auth → skip, use local file instead
2. For local video files: `ffmpeg -i /path/to/video -vn -acodec pcm_s16le -ar 16000 -ac 1 /tmp/audio.wav -y`
3. Transcribe using whisper/transformers pipeline:
   ```bash
   /opt/data/whisper-cpu/bin/python3 -c "
   from transformers import pipeline
   pipe = pipeline('automatic-speech-recognition', model='openai/whisper-base', device=-1)
   result = pipe('/tmp/audio.wav', return_timestamps=True)
   for seg in result.get('chunks', []):
       print(f\"[{seg['timestamp'][0]:.2f}s - {seg['timestamp'][1]:.2f}s] {seg['text']}\")
   "
   ```
4. Save full transcript with timestamps — this is the primary data source for narrative analysis.

### Step 3: Extract Visual Frames

```bash
ffmpeg -i /path/to/video -vf "fps=0.1" -q:v 2 /tmp/frames/frame_%04d.jpg -y
```
This gives 1 frame every 10 seconds for a 2-min video (~12 frames). More frames for longer videos.

### Step 4: Visually Analyze Key Frames

Use `vision_analyze` on every other frame (6 frames for a 2-min video). For each frame, capture:
- Visual elements (landscape, people, buildings, text overlays)
- Color palette and mood
- Text overlays verbatim (OCR)
- What part of the story arc it represents

### Step 5: Read the Companion Deck / PDF

If there's an investor deck PDF:
1. Check if text-based: `pdftotext` test
2. If text-based: extract via PyMuPDF (`fitz`)
3. If scanned: **convert to PNG first** using PyMuPDF:
   ```python
   import fitz
   doc = fitz.open('input.pdf')
   for i, page in enumerate(doc):
       pix = page.get_pixmap(dpi=300)
       pix.save(f'/tmp/pages/page_{i+1}.png')
   ```
   Then `vision_analyze(image_url='/tmp/pages/page_1.png')` per page (vision_analyze does NOT accept PDFs directly)
4. Extract: project details, financial metrics, location data, partner mentions, brand references

### Step 6: Research the Brand / Company

When the brand credentials are part of the gap analysis:
- Search Drive for corporate profiles, brochures, project lists
- Search Gmail for brand mentions, pitch decks
- Search X/Twitter for public presence
- Use web tools if configured for external validation
- Use the user's own description of the brand (they often provide this in the brief)

**Key data points:** years in business, total portfolio value, landmark projects, marquee partnerships, track record (no defaults, no failures), current pipeline.

### Step 7: Synthesize Gap Analysis Using Deep Reasoning Model

Route the full analysis to a deep reasoning model via `call_openrouter_model`:
- Use `anthropic/claude-opus-4` or `google/gemini-2.5-pro` for strategic/brand analysis
- Set `max_tokens=8000` for comprehensive output

**Structure the prompt with:**
1. **Transcript** — full video transcript with timestamps
2. **Visual analysis** — frame-by-frame breakdown
3. **Deck analysis** — key facts and gaps in the PDF
4. **Brand research** — what exists about the company
5. **User's brief** — their feedback, expectations, what they said is missing
6. **Clear task:** identify gaps, provide specific actionable feedback for the agency

### Step 8: Deliver Findings

Structure the analysis in 4 parts:
1. **What works well** — builds credibility, don't scrap what's good
2. **Gap analysis** — 3-4 specific gaps (vision, credibility, financial trust, etc.)
3. **Actionable agency feedback** — prioritized (critical → urgent → important → nice-to-have) with specific VO suggestions, visual treatments, timing
4. **Investor journey map** — how video + deck + brand one-pager work together as a system

Save as HTML to TMP folder on Drive and share the link.

## Pitfalls

- **Unlisted YouTube videos** can't be downloaded with yt-dlp without auth. If you uploaded the video via the API, you already have it locally.
- **User's voice message is the evaluation criteria.** Don't substitute your own opinions — measure the video against THEIR brief.
- **Brand credibility gap is the most common miss** in B2B/investor marketing. Developers often forget to identify themselves in "aspirational" videos.
- **Financial placeholders** in decks (showing "1.234" or "TEXT") must be flagged as urgent — no institutional investor will accept this.
- **The "who" question** must be answered before the "what" or "why" in investor materials.
