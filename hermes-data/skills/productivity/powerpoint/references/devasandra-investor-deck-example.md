# Devasandra Industrial Area — Investor Deck Reference (June 2026)

This reference documents the 14-slide comprehensive investor deck built for a KIADB-allotted commercial land at Devasandra Industrial Area, next to Garudacharpalya Metro, Whitefield, Bengaluru.

## Slide Structure

| # | Section | Key Elements |
|---|---------|-------------|
| 1 | **Title** | Full-bleed navy, gold corner accents, Metro context, "INVESTOR PRESENTATION" label |
| 2 | **Table of Contents** | 12-chapter numbered list in cream card grid |
| 3 | **Introduction** | Left: 6-point location overview. Right: Navy key metrics panel |
| 4 | **Land Survey Sketch** | Horizontal bar chart (3 components) + Sketch reference panel (navy) |
| 5 | **Location Map** | Context map image + Google Maps coordinates + highlighted landmarks |
| 6 | **Proposed Layout — Option 1** | Building layout image with setbacks, plot area, FSI |
| 7 | **Key Location Highlights** | 2x3 card grid with numbered badges |
| 8 | **Development Potential** | KIADB FAR table + Table-3.4.1 image + Development scenario table |
| 9 | **Premium A-Grade Vision** | Navy hero box + 3 pillar cards |
| 10 | **Financial Overview** | Two-column FAR 3.0 vs FAR 4.8 comparison tables |
| 11 | **Dev Layout & Site Context** | Two images side-by-side (Option 1 + Concept) |
| 12 | **Infrastructure** | Current (6-item) + Upcoming (5-item) + Social strip |
| 13 | **Market Analysis** | Rental comparables (7 props) + Lease deals (5 deals) + Key insight |
| 14 | **Disclaimer** | Dark navy, gold divider, bullet disclaimers |

## Key Data Points

- **Land:** 62,392 sqft (5,796 sqm) — 1 Acre + 17.291 Guntas
- **Jurisdiction:** KIADB (GO CI 99 SPQ 2025, Feb 2026)
- **Road Width:** 24m → FAR 3.0 base + 1.8 premium = **4.8 total FAR**
- **Built-up:** ~3,00,000 sqft (FAR 4.8) | Stilt + GF + 5 floors
- **Construction Cost:** ₹5,000/sqft
- **Rental Value:** ₹75/sqft/month
- **Capital Values:** 8% cap = ₹337 Cr | 9% cap = ₹299 Cr | 10% cap = ₹270 Cr

## Brand Colors Used

```javascript
const C = {
  navy: "0F1A33", navyMid: "1B2A4A", navyLight: "2C4270",
  gold: "C9A84C", goldBright: "D4B96A", goldPale: "E8D5A3", goldLight: "F5EDD6",
  white: "FFFFFF", cream: "F8F6F0",
  text: "1A1A2E", textMid: "4A4A5A", textLight: "7A7A8A",
  teal: "1A7A7A", tealLight: "E8F4F4",
  gray: "D5D5DC",
};
```

## Helper Functions Used

```javascript
const ms=(o)=>({type:"outer",color:"000000",blur:o?.b||8,offset:o?.o||2,angle:135,opacity:o?.p||0.1});
const gt=(s)=>s.addShape(pres.shapes.RECTANGLE,{x:0,y:0,w:10,h:0.04,fill:{color:C.gold}});
const ft=(s,n)=>{s.addShape(pres.shapes.RECTANGLE,{x:0,y:5.3,w:10,h:0.325,fill:{color:C.navyMid}});...};
const sb=(s,t)=>{s.addShape(pres.shapes.RECTANGLE,{x:0.4,y:0.2,w:0.06,h:0.5,fill:{color:C.gold}});s.addText(t,...);};
const th=(t,a)=>({text:t,options:{bold:true,color:C.white,fill:{color:C.navyMid},fontSize:7.5,fontFace:"Calibri",align:a||"left"}});
const tc=(t,b,c,a)=>({text:t||"",options:{fontSize:8,fontFace:"Calibri",bold:!!b,color:c||C.text,align:a||"left"}});
```

## Table Building Pattern (CORRECT)

```javascript
// Header as separate array
const hdr = [th("Col1"), th("Col2")];
// Data rows mapped with tc()
const rows = [["v1","v2"],["v3","v4"]].map(r=>r.map((c,i)=>tc(c,i===0,i===0?C.navy:null,i===1?"center":"left")));
// Spread header + rows
s.addTable([hdr, ...rows], { x:0.5, y:1, w:9.2, colW:[4.6,4.6], border:{pt:0.5,color:C.gray}, rowH:[0.22,0.2,0.2], autoPage:false });
```

## Key Pitfalls Avoided in This Deck

1. Jurisdiction assumed wrong (BBMP→BMRDA→KIADB) — verify before calculating FAR
2. Construction cost was ₹2K/sqft, corrected to ₹5K/sqft per user instruction
3. Rental value was ₹55/sqft, corrected to ₹75/sqft
4. Table header double-wrapping bug (documented in Common Pitfalls)
5. Skipped LibreOffice visual QA (not available on server) — used text-based XML verification
