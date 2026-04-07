# n8n Contact Search & Update Workflow - Architecture Plan

## 🎯 Overview
Create an n8n workflow deployed on Railway that intelligently searches and updates contact information across Google Contacts/Sheets, with fuzzy matching and rich custom data support.

**Current Data Source:** Google Sheet (ID: `1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g`)

---

## 📊 Data Structure (Current Sheet)

### Contact Fields
| Column Range | Field | Type | Index |
|---|---|---|---|
| A-C | Name (First, Middle, Last) | String | 0, 1, 2 |
| O | Notes | Text | 14 |
| S, U, W, Y, AA | Emails (1-5) | Email[] | 18, 20, 22, 24, 26 |
| AC-AH | Phones (1-6) | Phone[] | 28, 30, 32, 34, 36, 38 |
| K | Organization | String | 10 |
| CA | Projects | String/JSON | 78 |
| CB | Land Proposals | String/JSON | 79 |
| CC | Topics | String/JSON | 80 |

### Custom Fields (Future Extensions)
- Associated People/Entities (JSON)
- Work Association (JSON)
- Related Contacts (JSON)

---

## 🏗️ Workflow Architecture

### **Option A: Sheet-Based (Recommended - Start Here)**
**Why:** Leverages your existing Python code, all data already structured, easier to update

```
Input (Search Query)
    ↓
[Fetch Sheet Data] (Sheets API: range A:CC)
    ↓
[Fuzzy Match Engine] (Name + Project + Entity + People)
    ↓
[Rank Results] (Levenshtein distance, field matching)
    ↓
[Return Top Matches] (JSON with scores)
    ↓
[Optional: Update Sheet] (If provided new data)
    ↓
Output (JSON response)
```

### **Option B: Hybrid (Google Contacts + Sheet)**
**Why:** Native contact management, but Sheet as extended database

```
Input
    ↓
[Search Google Contacts] (via People API)
    ↓
[Search Google Sheet] (parallel)
    ↓
[Merge Results] (dedupe by email/phone)
    ↓
[Enrich from Sheet] (projects, associations)
    ↓
[Update Both] (Contacts + Sheet)
    ↓
Output
```

---

## 🔧 Workflow Components (Option A - Sheet-Based)

### **Node 1: Input Trigger**
- **Type:** Webhook (HTTP POST)
- **Input Schema:**
```json
{
  "query": "string (name/project/entity/person)",
  "mode": "search|update",
  "contact_data": "object (optional, for updates)"
}
```

### **Node 2: Fetch Sheet Data**
- **Type:** Google Sheets API
- **Action:** Get values from range `A:CC`
- **Output:** Array of rows with all columns
- **Service Account:** ndr@draas.com (DWD)

### **Node 3: Parse & Normalize Data**
- **Type:** Function/Script Node
- **Logic:**
  - Extract header row (row 0)
  - Build contact objects from rows
  - Map columns to fields using indices
  - Handle missing cells

```javascript
// Pseudo-code
contacts = rows.map((row, idx) => ({
  row_index: idx,
  name: `${row[0]} ${row[1]} ${row[2]}`.trim(),
  organization: row[10],
  notes: row[14],
  emails: [row[18], row[20], row[22], row[24], row[26]].filter(Boolean),
  phones: [row[28], row[30], row[32], row[34], row[36], row[38]].filter(Boolean),
  projects: row[78]?.split(',').map(p => p.trim()),
  land_proposals: row[79],
  topics: row[80]?.split(',').map(p => p.trim()),
  people_associations: row[81] ? JSON.parse(row[81]) : []
}))
```

### **Node 4: Fuzzy Search Engine**
- **Type:** Function Node
- **Fuzzy Matching Strategy:**
  - **Primary:** Name matching (Levenshtein distance)
  - **Secondary:** Project/Entity matching
  - **Tertiary:** People association matching

```javascript
// Scoring algorithm
function scoreContact(contact, query) {
  let score = 0;

  // Name matching (50%)
  const nameScore = levenshtein(contact.name.toLowerCase(), query.toLowerCase());
  score += (1 - (nameScore / Math.max(contact.name.length, query.length))) * 50;

  // Projects matching (30%)
  if (contact.projects.some(p => p.toLowerCase().includes(query.toLowerCase()))) {
    score += 30;
  }

  // People/Entities matching (20%)
  if (contact.people_associations?.some(p => p.toLowerCase().includes(query.toLowerCase()))) {
    score += 20;
  }

  return score;
}

// Return matches with score >= threshold (e.g., 50)
const matches = contacts
  .map(c => ({ ...c, score: scoreContact(c, query) }))
  .filter(m => m.score >= 50)
  .sort((a, b) => b.score - a.score);
```

### **Node 5: Format Response**
- **Type:** Mapper/Function
- **Output:**
```json
{
  "query": "string",
  "total_matches": number,
  "matches": [
    {
      "confidence": 0-100,
      "name": "string",
      "organization": "string",
      "emails": ["email@example.com"],
      "phones": ["+1234567890"],
      "projects": ["Project A", "Project B"],
      "land_proposals": "string",
      "topics": ["topic1", "topic2"],
      "people_associations": [{name: "John", role: "CEO"}],
      "notes": "string",
      "row_index": number
    }
  ]
}
```

### **Node 6: Update Sheet (Conditional)**
- **Type:** Google Sheets API (if mode == "update")
- **Actions:**
  - Merge provided data with existing row
  - Update single row via `batchUpdate`
  - Log change with timestamp

**Update Request Schema:**
```json
{
  "mode": "update",
  "row_index": 5,
  "updates": {
    "emails": ["new@email.com"],
    "phones": ["+9876543210"],
    "projects": ["New Project"],
    "people_associations": [{"name": "Jane", "role": "Founder"}]
  }
}
```

---

## 🚀 Deployment Steps

### Step 1: Create n8n Workflow
- [ ] Design in n8n UI on Railway
- [ ] Test with sample queries
- [ ] Add error handling

### Step 2: Implement Fuzzy Matching
- [ ] Add Levenshtein distance library (npm: `fast-levenshtein`)
- [ ] Test with name variations (Maria → Mary, John → Jon)
- [ ] Test with partial matches

### Step 3: Add Service Account
- [ ] Use existing credentials: `ndr@draas.com` (DWD)
- [ ] Grant Sheets API scope (already done)
- [ ] Test sheet access

### Step 4: Deploy to Railway
- [ ] Export workflow as JSON
- [ ] Create webhook endpoint
- [ ] Test with cURL

### Step 5: API Documentation
- [ ] POST `/contact-search` - Search contacts
- [ ] POST `/contact-update` - Update contact
- [ ] Response schema

---

## 📋 Enhanced Data Model (Future)

### Add to Sheet
- **Column CD (81):** People Associations (JSON)
- **Column CE (82):** Entities (JSON)
- **Column CF (83):** Work Associations (JSON)
- **Column CG (84):** Last Updated (timestamp)

**Example People Association Format:**
```json
[
  {"name": "John Doe", "role": "CEO", "company": "AHFL"},
  {"name": "Jane Smith", "role": "Colleague", "company": "Draas"}
]
```

---

## 🔍 Search Query Examples

### Simple Name Search
```
query: "Maria"
→ Returns all Marias (fuzzy match)
```

### Project Search
```
query: "Land Development"
→ Returns contacts working on Land Development
```

### People Search
```
query: "John Doe"
→ Returns contacts associated with John Doe
```

### Complex Multi-Field
```
query: "Maria John Draas"
→ Searches name (Maria) + people (John) + org (Draas)
```

### Exact Match
```
query: "exact:Maria Garcia"
→ Only exact matches
```

---

## ⚙️ Configuration Variables (Railway)

```bash
# Google Sheets
SHEETS_FILE_ID=1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g
SHEETS_RANGE=A:CC

# Service Account (already set)
GOOGLE_APPLICATION_CREDENTIALS=/data/hermes/service-account-key.json

# n8n Workflow
WEBHOOK_AUTH_TOKEN=<generate-secure-token>
FUZZY_MATCH_THRESHOLD=50

# Feature Flags
ENABLE_SHEET_UPDATES=true
ENABLE_PEOPLE_SEARCH=true
ENABLE_PROJECT_SEARCH=true
```

---

## 📱 Integration with Hermes (Your AI)

### AI Query Flow
```
Hermes AI: "Who is working on the Land project?"
    ↓
Calls: POST /contact-search
Body: { "query": "Land" }
    ↓
n8n Workflow:
  1. Fetch sheet
  2. Search projects field
  3. Fuzzy match results
    ↓
Returns:
{
  "matches": [
    {
      "name": "John Doe",
      "emails": ["john@example.com"],
      "phones": ["+1234567890"],
      "projects": ["Land Development", "Real Estate"]
    }
  ]
}
    ↓
Hermes: Extracts phone/email → Uses in message draft
    ↓
Optional: User provides new info → Calls /contact-update
```

---

## 🛡️ Error Handling

### Cases to Handle
1. **No matches:** Return empty array with message
2. **Ambiguous results:** Return all matches sorted by confidence
3. **Sheet API error:** Return 500 with error details
4. **Invalid update data:** Return 400 with validation error
5. **Rate limiting:** Implement exponential backoff

---

## 📊 Testing Strategy

### Unit Tests
```javascript
test('Fuzzy match: "Maria" matches "Mary"', () => {
  const score = scoreContact({name: "Mary"}, "Maria");
  expect(score).toBeGreaterThan(80);
});

test('Project search: "Land" matches "Land Development"', () => {
  const match = fuzzySearch([{projects: ["Land Development"]}], "Land");
  expect(match.length).toBe(1);
});
```

### Integration Tests
```
Test 1: Full workflow search
Test 2: Full workflow update
Test 3: Sheet data persistence
Test 4: Error cases (missing sheet, invalid auth)
```

### Manual Testing
1. Search by full name
2. Search by first name (fuzzy)
3. Search by project
4. Search by person name
5. Update email address
6. Update projects
7. Add new person association

---

## 🎯 Success Criteria

- ✅ Search finds contacts by name (exact + fuzzy)
- ✅ Search finds contacts by project/entity
- ✅ Search finds contacts by people association
- ✅ Fuzzy matching handles typos/variations
- ✅ Results ranked by confidence
- ✅ Update works for all fields
- ✅ JSON response is Hermes-AI-compatible
- ✅ Webhook secured with auth token
- ✅ Deployed on Railway, callable from Telegram bot

---

## 🚦 Next Steps (Your Choice)

**Choose One:**

### Path 1: Quick Start (Recommended)
1. ✅ Create webhook trigger in n8n
2. ✅ Add Sheets API node
3. ✅ Add parse/normalize node
4. ✅ Implement basic fuzzy match
5. ✅ Format output
6. ✅ Deploy & test

**Time: 2-3 hours**

### Path 2: Full Featured
1. All of Path 1 +
2. Advanced scoring algorithm
3. Update functionality
4. People association search
5. Enhanced error handling
6. Comprehensive logging

**Time: 4-6 hours**

### Path 3: Hybrid Integration
1. All of Path 2 +
2. Google Contacts API integration
3. Deduplication logic
4. Sync between Contacts + Sheet
5. Custom field mapping

**Time: 6-8 hours**

---

## 💡 My Recommendation

**Start with Path 1 (Sheet-Based)** because:
- You already have all data structured in Sheet
- Lower complexity = faster deployment
- You can upgrade to Hybrid later
- Easier to test and debug
- No need for Google Contacts API learning curve

Once working, you can enhance with fuzzy matching improvements, people associations, and hybrid approach.

---

**Ready to build? Let me know which path you prefer, and we'll create the n8n workflow!**
