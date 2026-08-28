# Geography Reference — Employment Generator Tracker

Used to filter articles by location. Only include entries from articles that explicitly mention one of these geographies as the project location.

## Karnataka — North Bangalore Peri-Urban

| Location | District | Notes |
|---|---|---|
| Devanahalli | Bangalore Rural | KIADB industrial area, airport vicinity |
| Doddaballapur | Bangalore Rural | Industrial zone, textile corridor |
| Kolar | Bangalore Rural | Kolar Gold Fields area, industrial |
| Tumkur | Tumkur | Tumkur Industrial Area, Hinna cluster |
| Nelamangala | Bangalore Rural | NH-48 corridor, logistics hub |
| Bidarahalli | Bangalore Rural | KIADB zone |
| Yelahanka | Bangalore North | Aerospace hub, HAL campus |
| Ramnagar | Bangalore Rural | Mysore Road corridor |

## Karnataka — South/East Bangalore

| Location | District | Notes |
|---|---|---|
| Sarjapur | Bangalore East | ORR corridor, upcoming metro |
| Whitefield | Bangalore East | IT hub, many GCCs |
| Huskur | Bangalore North | Industrial zone |
| Hosa Road | Bangalore South | Layout area |
| Jigani | Bangalore South | Anekal taluk, industrial |
| Attibele | Bangalore South | Electronic City extension |
| Electronic City | Bangalore South | Phase 1, 2, 3 |
| Anekal | Bangalore South | KIADB industrial area |
| Chandapura | Bangalore South | Peenya extension |
| Huskote | Bangalore East | Border area |
| Hebbagodi | Bangalore South | Electronic City periphery |

## Karnataka — Beyond Bangalore

| Location | District | Notes |
|---|---|---|
| Mysore | Mysore | Mysore Industrial Area |
| Mangalore | Dakshina Kannada | MRPL, industrial zone, port |
| Hubli | Dharwad | Nava Karnataka, textile |
| Dharwad | Dharwad | Airport, industrial |
| Belgaum | Belagavi | KSL gas, agricultural |
| Hassan | Hassan | Coffe region, industrial |

## Tamil Nadu — Krishnagiri District

| Location | District | Notes |
|---|---|---|
| Hosur | Krishnagiri | Major industrial hub, many MNCs |
| Krishnagiri | Krishnagiri | DPIIT focus area |
| Shoolagiri | Krishnagiri | Near Hosur |
| Berigai | Krishnagiri |工业区 |
| Denkanikottai | Krishnagiri | DG sets, industry |
| Pochampalli | Krishnagiri | textile |

## Tamil Nadu — Chennai Periphery

| Location | District | Notes |
|---|---|---|
| Sriperumbudur | Kancheepuram | MNC manufacturing, Hyundai |
| Oragadam | Kancheepuram | Industrial zone, Kia Motors |
| Maraimalai Nagar | Chengalpattu | Port, manufacturing |
| Chengalpattu | Chengalpattu | |
| Kancheepuram | Kancheepuram | |
| Kattankulathur | Chengalpattu | |

## Andhra Pradesh — Border (Anantapur District)

| Location | Notes |
|---|---|
| Hindupur | KA border, industrial |
| Lepakshi | Near Hindupur, heritage site |
| Puttaparthi | Lepakshi area |
| Kalyandurg | Rayalaseema |
| Rayadurg | mineral area |
| Tadpatri | |
| Madakasira | |

---

## Keyword-to-Geography Matching

When parsing articles, tag the geography based on explicit mentions:

- "Bangalore" → map to relevant sub-region (North/South/East)
- "Bengaluru" → same as Bangalore
- "Electronic City" → Bangalore South
- "Whitefield" → Bangalore East
- "Devanahalli" → Bangalore North / Airport
- "Hosur" → Krishnagiri District
- "Sriperumbudur" → Chennai Periphery
- "Doddaballapur" → Bangalore North
- "Hindupur" → Andhra Pradesh Border
- "Mysore" → Mysore
- "Mangalore" → Mangalore
- "Hubli" → Hubli-Dharwad cluster