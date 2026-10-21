# TN EC Tamil → English Transliteration Glossary

Sevaganapalli (Hozur/Bagalur SRO) EC party names, institutional names, and
register abbreviations. Built 2026-08-13; converted 580 cells across 6
spreadsheet tabs with 0 leftover Tamil.

## Technique summary

1. PRE-PASS regex on full cell text for abbreviations (they contain ASCII
   punctuation that splits Tamil runs — a run-level map alone mangles them).
2. Run-level map: exact full-run match first → substring for len≥2 keys
   (longest-first) → single Tamil char ONLY as exact leftover fallback.
   Never single-char-replace inside an unmapped run (produces garbage like
   "Guardianொ..." from missing கொத்தப்பள்ளி, or "NAரயணReddy" from missing
   நாரயணரெட்டி because நா→NA fires inside).
3. Phrase keys with spaces (பலவித நோக்க → Multi-purpose) applied before
   run matching.
4. Verify: read back tabs, assert no cell matches `[\u0B80-\u0BFF]`.

## EC register abbreviations (PRE-PASS, with parens/dots/pluses)

| Tamil | English | Meaning |
|---|---|---|
| (முத.) / முதல்வர் | (First party) | executant/principal in the EC |
| (முக.) / முகவர் | (Agent) | attorney/agent party |
| (இ.க.) | (Natural Guardian) | இயற்கை காவலர் — guardian of a minor |
| த+கா / த.கா (with or without parens) | Father & Guardian | guardian marker |
| (மைனர்) / மைனர்கள் | (minor) / (minors) | |
| (கார்டியன்) | (Guardian) | |
| (பவர்ஏஐண்ட்) | (Power Agent) | power-of-attorney agent |
| (ஏஜண்டு) | (Agent) | |
| (எ) / (அ) | (alias) | "லக்ஷ்மம்மா (எ) அம்மையம்மா" |
| என்கிற | alias | "ருக்குமணியம்மா என்கிற ருக்மணியம்மாள்" |
| மேற்படி நபர்கள் | the above persons | "1. மேற்படி நபர்கள்" = same parties as prior entry |
| ரூ. | Rs. | consideration prefix |

## Common name tokens (Reddy-family, Telugu/Kannada names in Tamil script)

- ரெட்டி → Reddy (also ரெடடி, ரெட்டீ OCR variants)
- கிருஷ்ணா / கிருஷ்ணாரெட்டி / கிருஷ்ணரெட்டி → Krishna / Krishnareddy
- நாராயணரெட்டி → Narayana Reddy (note: நாரயணரெட்டி variant ALSO exists —
  both must be in the map)
- ராமசந்திரரெட்டி / ராமசந்திராரெட்டி / ராமசந்திரா ரெட்டி → Ramachandra Reddy
- ராமசுவாமிரெட்டி → Ramaswamy Reddy; ராமசாமிசெட்டி → Ramasamy Chetty
- வெங்கடேசப்பா / வெங்கடேஷ் / வெங்கடேஷ்ரெட்டி → Venkatasappa / Venkatesh /
  Venkatesh Reddy
- லக்ஷ்மணரெட்டி → Lakshmana Reddy; லக்ஷ்மம்மா / லஷ்மம்மா / லக்ஷமம்மா →
  Lakshmamma (multiple OCR spellings)
- எல்லாரெட்டி → Ellareddy; புட்டரெட்டி → Puttareddy; பாபிரெட்டி → Babi
  Reddy; பாபரெட்டி → Babareddy
- ஸ்ரீனிவாசரெட்டி → Srinivasa Reddy; சுரேஷ்ரெட்டி → Suresh Reddy;
  மஞ்சுநாதா / மஞ்சுநாத ரெட்டி → Manjunatha Reddy
- கௌரம்மா → Gowramma; ரத்னம்மா / ரத்தினம்மா → Rathnamma
- புட்டம்மா → Puttamma; ராமப்பா → Ramappa; கிருஷ்ணப்பா → Krishnappa;
  நாராயணப்பா → Narayanappa; சீனப்பா → Seenappa
- முனிவெங்கடம்மா → Munivenkatamma; வெங்கடராமணப்பா / வெங்கடரமணப்பா →
  Venkataramanappa
- மைனர் prefix to a name = minor (e.g. "மைனர் முரளி கார்த்திக்" → minor
  Murali Karthik)
- "9 மாத பெண் குழந்தை" → "9 month girl child"

## Institutional names

| Tamil | English |
|---|---|
| அரசு (தமிழ் நாடு) | Government (Tamil Nadu) |
| ஒசூர் கூட்டுறவு நிலவள வங்கி லிட் | Hosur Co-operative Land Development Bank Ltd |
| கக்கனூர் கிராமத்தில் ஸ்தாபிக்கப்பட்டிருக்கும் கொத்தப்பள்ளி கோ ஆப்ரேடிவ் கிரெடிட் சொசைட்டி எஸ்.948 | Kothapalli Co-operative Credit Society S.948 established in Kakanur village |
| எஸ்948 கொத்தப்பள்ளி பலவித நோக்க கூட்டுறவு நாணயம் சங்கம் தற்போது எஸ் 948 ... தொடக்க வேளாணமை கூட்டுறவு சங்கம் லிட் | S948 Kothapalli Multi-purpose Co-operative Thrift Society, presently S948 Kothapalli Primary Agricultural Co-operative Society Ltd |
| கிளவர் எஸ்டேட் / க்ளவர் எஸ்டேம் பிரவேட் லிமிடெட் | Clover Estate Private Limited |
| பிரகாஷ் சந்தர் மாகன் ( M/s. கிளவர் எஸ்டேட்ஸ் (பி) லிட்) | Prakash Chandar Mahan (M/s. Clover Estates (P) Ltd) |

## Key phrase keys

- பலவித நோக்க → Multi-purpose
- கோ ஆப்ரேடிவ் → Co-operative
- நிலவள வங்கி → Land Development Bank
- தற்போது → presently
- கூட்டுறவு → Co-operative
- ஸ்தாபிக்கப்பட்டிருக்கும் → established

## Traps

- Missing compound keys cause cascading garbage: ALWAYS add full names
  (கொத்தப்பள்ளி, நாரயணரெட்டி) before relying on token fallback.
- The `நா` single-char map entry (used for initials like "N.") fires inside
  unmapped runs — gate single-char replacement to exact leftover only.
- Empty parens `SASIDHAR()` are FAITHFUL to the source EC (no agent listed) —
  don't "fix" them.
