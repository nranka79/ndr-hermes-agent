# Vehicle Research & Disposition

Research a personal/company vehicle's technical specs, fuel compatibility, resale value, and decide sell-vs-keep.

## Trigger

User asks about a specific vehicle:
- "Check the RC for the [car name]"
- "Is [car] compatible with E20 / flex fuel?"
- "What's my [car] worth / what can I sell it for?"
- "Should I keep or sell [car]?"

## Step 1: Find & Read the RC (Registration Certificate)

Search Drive with the skill bridge — **note the `raw_query=True` + `query=...` parameter quirk**:

```python
from tools.gws_skill_bridge import call
results = call('drive_search', service_name='google-draas',
               query="fullText contains 'Vento'", raw_query=True, max=20)
```

The skill's `drive_search` function checks `args.raw_query` first — pass it as truthy and supply the full Drive query string in `query`.

**Key files to look for:**
- `{REG_NO}_Vento_RC.pdf` or similar pattern (e.g. `KA05MT9001_Vento_RC.pdf`)
- Also search for `"{make}" + "RC"`, `"{model}" + "registration"`, `"{reg_no}"`

**Download & extract text:**
```python
call('drive_download', service_name='google-draas',
     file_id="FILE_ID", output="/tmp/rc.pdf")
```

Then run `pdftotext` (available on system) to extract text from the RC PDF.

**What to extract from RC:**
- Engine No, Chassis No
- Model variant (e.g. "VENTO 1.2 COMFORTLINE TSI BSIN")
- Engine CC & cylinders
- Fuel type
- MFG date
- Owner name
- Registration validity

## Critical First Check: Fuel Type

**E20 is a PETROL blend — Diesel engines are completely unaffected.** Before any E20 research:

- **DIESEL** → Stop. No E20 compatibility issue exists. The user has been running normal diesel and will continue to do so. India does not mandate ethanol blending in diesel (Govt abandoned ethanol-in-diesel trials years ago; isobutanol-diesel blending is only being discussed, not mandated).
- **PETROL** or **PETROL HYBRID** → Proceed with E20 analysis below.

This is the single most important triage when doing a fleet-wide analysis — in this session 3 of 4 vehicles (BMW X1 20d, Jaguar XJ 3.0L, Vento) were checked, but 2 were diesel and had zero concern, saving significant research effort.

## Step 2: Fuel Compatibility Research (E20/E85/Flex-Fuel)

**E20 is now the standard fuel in India nationwide (since April 2026).**

| Year | Status |
|------|--------|
| April 2023+ | Fully compatible |
| 2020 – Mar 2023 | Generally compatible — verify with manual |
| 2017 – 2019 | Partial/variable — consult service centre |
| Pre-2017 | Risk of issues — rubber seals/fuel lines most vulnerable |
| Pre-2010 (carb) | High risk |

### Manufacturer data:

- **Volkswagen**: E20 certified from April 2023 onwards. Only **1.0 TSI** and **1.5 TSI** engines certified. The **1.2 TSI (EA211)** used in Vento, Polo GT TSI, and older Rapid was **never E20 certified**. No official retrofit/conversion kit exists for pre-2023 VW models.<br>**Volkswagen FAQ** (volkswagenlabs.co.in): Confirms no conversion kit is planned for older vehicles. Advises contacting dealership for model-specific guidance. Helpline: 1800 102 0909 / customer.care@volkswagen.co.in
- **BMW**: E20 certified from April 2023 onwards. Diesel models (like X1 20d with B47 engine) are unaffected.
- **Jaguar Land Rover**: E20 certified from April 2023. Diesel models (like the 3.0L AJD-V6 / Ford Lion V6 in XJ) are unaffected.
- **Toyota**: E20 certified from April 2023. Innova Hycross (2.0L Atkinson hybrid) is fully E20 compatible. All Toyota post-2023 models certified.
- Most other manufacturers (Maruti, Hyundai, Tata, Honda) also E20 certified from April 2023.
- Maruti Suzuki announced E20 upgrade kits (~₹4K-6K) for older models in Apr 2026 — but other OEMs have not followed.

### Diesel-Specific Note

While E20 doesn't affect diesel, there's ongoing discussion about **isobutanol-diesel blending** (not ethanol). As of mid-2026, this is not mandated. BS4 and BS6 diesel vehicles (including BMW X1 20d and Jaguar XJ 3.0L) run fine on current BS6 diesel — sulfur content reduction was managed in the BS4→BS6 transition without compatibility issues.

### Risks of running E20 in a non-compatible car:

- Ethanol is **hygroscopic** (absorbs moisture from air) — causes rust in metal tanks
- Degrades rubber fuel lines, seals, O-rings, gaskets → leaks → fire risk
- Direct Injection Turbo engines (like VW TSI) are more complex to convert than MPI engines
- 3-5% fuel efficiency drop (ethanol has ~30% less energy by volume)

## Step 3: Flex-Fuel Conversion Options & Cost

**No official OEM retrofit kit exists for most pre-2023 vehicles** (except Maruti's announced kits).

A full conversion would require replacing:
- All fuel lines → Viton/ethanol-compatible hoses
- Fuel pump & internal seals
- Fuel injectors
- Gaskets & O-rings
- ECU remap (or piggyback module like eFlexFuel)

### Estimated cost (India, 2026):

| Component | Cost |
|-----------|------|
| Basic hose replacement | ₹3K-7K |
| Fuel pump upgrade | ₹8K-15K |
| Full system overhaul | ₹25K-50K |
| Labour | ₹5K-10K |
| **Total** | **₹30K-60K+** |

### Aftermarket options:
- **eFlexFuel** (eflexfuel.com) — ethanol conversion kits, available for India. Ships customized per vehicle.
- **LIQUI MOLY E20 Additive** — mitigates corrosion/performance loss but is NOT a conversion; use as palliative only.

## Step 4: Resale Valuation

### Sources to check:

| Platform | URL | Notes |
|----------|-----|-------|
| CarWale | `carwale.com/used/{city}/{make}-{model}/` | Largest inventory; shows variant-wise avg pricing |
| Spinny | `spinny.com/used-{model}-cars-in-{city}/` | Instant buy; lower price but guaranteed |
| Cars24 | `cars24.com/buy-used-{make}-{model}-cars-{city}/` | Instant buy, 300+ quality checks |
| OLX | `olx.in/{city}/q-{model}` | Direct owner listing; best price with effort |
| CarDekho | `cardekho.com/used-car-details/` | Dealer listings |
| Mahindra First Choice | `mahindrafirstchoice.com` | Franchise used-car dealer |

### Price ranges from market (example: 2016 VW Vento 1.2 TSI Comfortline AT in Bangalore):

- Market expectation: **₹4.5L - ₹5.5L**
- Instant-buy (Spinny/Cars24): ₹4L - ₹4.5L
- Direct sale (OLX/CarWale): ₹5L - ₹5.5L

## Step 5: Sell-vs-Keep Decision Framework

**Consider selling when:**
- Car is 10+ years old and model is discontinued
- Conversion cost (₹30K-60K) is disproportionate to vehicle value
- Fuel system not designed for E20 — damage is cumulative, not immediate
- Parts availability is declining

**Consider keeping when:**
- Car is already E20-compatible (post-April 2023)
- Sentimental value / low mileage / well-maintained
- Cost of replacement vehicle would be higher than conversion + continued upkeep

## Step 6: Disposal Channels

| Method | Price | Effort | Speed |
|--------|-------|--------|-------|
| Spinny / Cars24 instant buy | Lower (₹4-4.5L) | Minimal | 24-48 hrs |
| Mahindra First Choice | Medium | Low | Days |
| CarWale / OLX self-list | Best (₹5-5.5L) | High (photos, calls, negotiation) | 1-4 weeks |
| Dealer buy (local) | Low (₹3.5-4L) | Low | Same day |

**Recommended strategy:** Get instant quotes first (Spinny, Cars24) as price floor. List on OLX/CarWale at market price simultaneously. Take the best offer within 2 weeks.

## Fleet-Wide Analysis Pattern

When the user asks about multiple vehicles at once (e.g., "check all my cars for E20"):

1. **Collect all RC docs first** — Search Drive for each known vehicle. Use `raw_query=True` with `fullText contains '{query}'`.
2. **Extract key fields** from each RC: fuel type, MFG year, model variant, engine spec.
3. **Triage by fuel type**:
   - **Diesel** → done, no E20 concern
   - **Petrol** → check MFG year against compatibility table
4. **For each at-risk petrol vehicle**: Run the full sell-vs-keep framework (conversion cost vs resale value vs age).
5. **Present as a single summary table** — user sees the whole fleet at a glance.

> See `references/draas-fleet-registry.md` for the known fleet list and pre-compiled E20 status.

## Step 7: Create a Vehicle Asset Register (output artifact)

When the user asks to "save this somewhere", "create a note", or "park this info about my cars" — compile all RC details into a structured markdown asset register file.

1. **Write locally** — `YYYYMMDD_DRA_Vehicle_Asset_Register.md`, include for each vehicle: Reg No, full model, variant, body type, colour, engine CC/cylinders, chassis no, engine no, fuel, MFG date, owner, address, RC validity, RTO
2. **Add summary sections** — E20 compliance table, ownership classification (personal vs company), RC document Drive links, estimated resale values
3. **Upload to Drive TMP folder** — use `drive_upload` with `parent="18p74II2uL32sNDzDDwXzmlOUdJJOTmE-"`. **Note:** `drive_upload` reads `args.parent` to set the Drive folder — without this param, the file lands at Drive root.
4. **Update fleet registry** — add a note in `references/draas-fleet-registry.md` pointing to the uploaded file
5. **Save compact reference to memory** — so future sessions know the register exists

## Browser Research Tips

DuckDuckGo Lite (`lite.duckduckgo.com/lite/?q=...`) works better for automated searches than Google (which triggers captchas). Use it for initial discovery, then navigate to specific pages for detail.

Key search patterns:
- `{make} {model} {year} {engine} E20 compatible`
- `{make} {model} resale value {city} {year}`
- `E20 conversion kit India {make} {model}`
- `ethanol damage pre-2017 car prevention`
