# Property Title Chain Research (Drive-based)

Workflow for researching a property's title chain by searching Drive for registered sale deeds, extracting prior deed references from recitals, and tracing the chain backward.

## Trigger

User asks to find/verify the title chain for a property — typically framed as "give me a link to the sale deed where [prior owner] purchased from [original owner]" or "I need the undivided share from the previous sale deed."

## Workflow

### Step 1 — Search Drive for the current deed

Use multiple search angles in parallel — property identifiers are often inconsistent:

```python
queries = [
    f"fullText contains {chr(39)}EH 914{chr(39)} or name contains {chr(39)}914{chr(39)}",
    f"fullText contains {chr(39)}{vendor_name}{chr(39)} and (fullText contains {chr(39)}sale deed{chr(39)} or name contains {chr(39)}sale{chr(39)})",
    f"fullText contains {chr(39)}{purchaser_name}{chr(39)}",
]
```

Common search axes:
- **Property ID** (e.g., "914", "EH 914", "Flat 914", "Embassy Habitat")
- **Project name** (e.g., "Embassy Habitat", "Embassy", "Magrath")
- **Party names** (vendor, purchaser — e.g., "Ravikumar Naik", "Roshni Ranka")
- **Folder names** — check for dedicated project folders like "E914 - Post Registration"

### Step 2 — Download and OCR the sale deed PDF

Registered Indian sale deeds are **always scanned PDFs** (7-8MB for ~20 pages). `fitz.open().get_text()` returns empty. Use:

```bash
# Convert to PNGs at 150 DPI
pdftoppm -png -r 150 "/path/to/sale_deed.pdf" /tmp/sd_page

# OCR key pages (first 5-10 pages cover recitals + schedules)
for f in /tmp/sd_page-01.png /tmp/sd_page-02.png /tmp/sd_page-03.png ...; do
    tesseract "$f" - 2>/dev/null
done
```

### Step 3 — Extract the prior deed reference

Indian absolute sale deeds have a **Recitals** section (lettered A, B, C, D, E...) that describes the chain of title. The critical recital is typically **Recital E**:

> "E. The Seller acquired the Schedule Property by way of a registered Sale Deed bearing Document No. **GAN-1-00865-2012-13**, registered on 14th June 2012..."

Also check **Annexure A** (List of Original Documents Handed Over) — item 1 is always the Seller's Title Deed.

### Step 4 — Search Drive for the prior document number

```python
q = f"fullText contains {chr(39)}GAN-1-00865{chr(39)} or name contains {chr(39)}00865{chr(39)}"
```

**PITFALL — Prior deeds are often not scanned.** The 2012 deed in the EH 914 chain (Doc No. GAN-1-00865-2012-13) was NOT found on Drive despite extensive searching. It was a physical original handed over to the purchaser (listed in Annexure A). The fullText search DID match the number inside other documents (reps & warranties, handover receipt) but no PDF of the deed itself existed.

When this happens, report to the user: "This document is not available as a scanned PDF on Drive — it was a physical original handed over." Provide the registered document number and registration details so they can request a certified copy from the SRO.

### Step 5 — Extract undivided share from the current deed

The undivided share is stated in two places:
1. **Recital D** (property description): `"together with an undivided share of 1116/594862 in the land (equivalent to 574.17 Square Feet)"`
2. **Schedule B** (apartment description): explicitly states `"Undivided Share in Land: 1116/594862 (equivalent to 574.17 Square Feet)"`

Since each apartment/flat has a fixed undivided share tied to its super built-up area, this is the same share the prior owner purchased. Report it directly from the current deed.

### Step 6 — Check for earlier chain documents in Drive

Sometimes an **earlier link in the chain** exists as a separate PDF (e.g., a 2010 sale deed from L.K. Trust to a prior party). Search for:
- `fullText contains "LK Trust"` or `"L.K. Trust"`
- Older dates: `"Sale Deed Dtd (02-08-2010)"` etc.
- Developer name: `"Magrath Property Developers"`, `"Embassy"`

## Known pitfalls

- **Registered document numbers have specific formats:** `GAN-1-00865-2012-13` (GAN = Gandhinagar SRO, 1 = Book I, 00865 = serial, 2012-13 = fiscal year). fullText search may partial-match.
- **Scanned PDF OCR quality varies:** tesseract output on Indian sale deeds can be garbled — but the recitals and schedules are consistently readable enough to extract deed numbers and undivided shares.
- **Chain gaps:** Older deeds in the chain (10+ years) are rarely scanned. Only the most recent transaction's deed is typically available on Drive.
- **LK Trust / Magrath connection:** In Embassy Habitat, L.K. Trust + Desraj Urs family were the original landowners, selling through Magrath Property Developers (whose partners included Dharmesh Ranka & Nishant Ranka) as POA holders. This appears in the 2010 deed. Magrath then developed the complex and sold individual flats via allotment.
