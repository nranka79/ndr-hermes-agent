# Property Maintenance & Fixtures Documentation

Recurring pattern for documenting appliance/fixture issues across DRAAS leased properties — from initial complaint to repair-vs-replace decision to documented archive on Drive.

## Folder Structure Convention

For each property, maintenance/asset documentation lives under:

```
[Property Name]/ → [Floor]/ → Fixtures & Fittings/ → [Appliance or Issue Name]/
```

### Example (Prestige Hermitage — Flat 601, 6th Floor — Dishwasher):

```
Hermitage (PSCP)
 └── 6th Floor/
      └── Fixtures & Fittings/
           └── Dishwasher/
                ├── 📄 20260721_Quotation_Siemens_SN65HX01MI_Haritha_Enterprises.pdf
                ├── 📷 Old_Dishwasher_Label_SN615X00EE.jpg
                ├── 📷 Old_Dishwasher_Open_View.jpg
                ├── 📄 20260425_Siemens_SN615X00EE_Repair_Invoice_750.pdf
                ├── 📄 20260504_Payment_Confirmation_1295.jpg
                └── 📄 [Property]_[Floor]_[Fixture]_Analysis.html
```

### Naming Conventions

| Type | Format | Example |
|---|---|---|
| Quotation | `YYYYMMDD_Quotation_[Brand]_[Model]_[Vendor].pdf` | `20260721_Quotation_Siemens_SN65HX01MI_Haritha_Enterprises.pdf` |
| Invoice | `YYYYMMDD_[Brand]_[Model]_Repair_Invoice_[Amount].pdf` | `20260425_Siemens_SN615X00EE_Repair_Invoice_750.pdf` |
| Payment Proof | `YYYYMMDD_Payment_Confirmation_[Amount].jpg` | `20260504_Payment_Confirmation_1295.jpg` |
| Photo | `Type_Description.jpg` | `Old_Dishwasher_Label_SN615X00EE.jpg` |
| Analysis Doc | `[Property]_[Floor]_[Fixture]_Analysis.html` | `Hermitage_6thFloor_Dishwasher_Analysis.html` |

## Assessment Workflow

When a fixture/appliance issue is reported in a leased property:

### 1. Gather All Evidence
- **WhatsApp/communication history** — extract timeline from chat with site engineer
- **Repair invoices** — obtain from Siemens/technician (note: invoices may under-report actual cost paid vs billed)
- **Payment proofs** — UPI/bank confirmations
- **Technician reports** — text messages, visit notes, diagnostic findings
- **Photos/videos** — appliance label (model/serial), interior view, fault indicators, replacement parts identified

### 2. Build Timeline
Chronological order of events from purchase to latest failure. Include:
- Original purchase date (from appliance label or service records)
- Each repair visit with date, issue, cost, outcome
- Technician recommendations verbatim
- Root cause investigations (water pressure, electrical, usage)

### 3. Repair vs Replace Decision Matrix

| Factor | Repair | Replace |
|---|---|---|
| Cost | Rs X,XXX | Rs X,XX,XXX |
| Guarantee | Usually none on repairs | Full manufacturer warranty |
| Technician rec | "Beyond economical repair" = replace | |
| Age of unit | >7 years typically threshold for major appliances | |
| Recurring issues | 3+ faults in short period = replace signal | |
| Parts availability | Discontinued models = harder to source | Current model = full support |
| Tenant satisfaction | Recurrent disruption erodes good will | Reliable operation |

### 4. Fit Check (Replacement)
Verify replacement unit fits the existing opening. For built-in appliances:

| Check | Method |
|---|---|
| Size | Compare width/height/depth (mm) of old vs new model |
| Type | Same form factor (built-in, freestanding, semi-integrated) |
| Electrical | Voltage (220-240V), amperage, wattage, plug type |
| Plumbing | Inlet/outlet positions, hose lengths |
| Cabinet cutout | Standard dimensions for category (e.g. 60cm built-in dishwashers are all 598x815x550mm) |

### 5. Price Research
Check at least 3 sources:
1. **Quoted price** from the vendor/service provider
2. **Online retailers** (via web_search) — look for Kitchen Brand Store, Aditya Retail, Decure.in, Amazon, Flipkart
3. **Siemens official** MRP for reference
4. **Local showroom** price if available

### 6. Create HTML Analysis Document
Create a self-contained HTML report that includes:
- Executive summary with recommendation
- Timeline table
- Evidence images (embedded via `https://drive.google.com/thumbnail?id=FILE_ID&sz=w400`)
- Decision matrix table
- Fit check comparison
- Price comparison table
- Action items
- All files stored in the same Drive folder

Example image embed:
```html
<a href="https://drive.google.com/file/d/FILE_ID/view" target="_blank">
  <img src="https://drive.google.com/thumbnail?id=FILE_ID&sz=w400" alt="Label">
  <div class="caption">📷 Caption</div>
</a>
```

### 7. Upload to Drive
1. Create folder structure: `Property > Floor > Fixtures & Fittings > [Appliance]`
2. Upload all evidence files with standardized names
3. Upload the HTML analysis document
4. All files are co-located in one folder for easy access

## Pitfalls

- **Invoices may under-report** — actual repair cost paid may differ from invoice amount (e.g. Siemens quoted ₹10k repair but only ₹1,800 bill issued); cross-check with WhatsApp chat
- **Technician verbal recs vs official statement** — always get the recommendation in writing (WhatsApp/text) before making the replace decision
- **Root cause investigation** — don't stop at the appliance; check if building-level issues (water pressure, voltage fluctuation) caused the failure and will affect a replacement too
- **GST on quotations** — some quotes are "plus GST" (add 18%), some are all-inclusive — clarify before comparing prices
- **Photos of old label** — always photograph the model/serial label before disposal for records
- **High water pressure** — recurring cause for dishwasher/washing machine failures in high-rise buildings; consider recommending a pressure reducing valve (PRV)
