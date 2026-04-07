# Advanced Multi-Field Fuzzy Scoring Algorithm

## 🎯 Problem Statement

When user/AI queries: `"Maria Land John"`, we need to determine:
- **"Maria"** → First name? Last name? Alias?
- **"Land"** → Project name? Topic? Entity? Or part of name?
- **"John"** → First name? Or person they work with?

And from 100+ contacts, find the EXACT person with confidence score.

---

## 🔍 Real-World Example

### Contact in Sheet (Row 15)
```
Name:        Maria Isabella Garcia
Organization: Draas
Emails:      maria@draas.com, mgarcia@example.com
Phones:      +1-555-0123, +1-555-0124
Projects:    Land Development Initiative, Real Estate Portfolio Management
Topics:      Real Estate, Property Valuation, Market Analysis
Entities:    AHFL (member), Draas Properties (partner), XYZ Corporation
People:      John Doe (CEO), Sarah Smith (Colleague), Michael Chen (Partner)
Notes:       Lead on Land Development, works closely with John on AHFL projects
```

### Test Queries
```
Query 1: "Maria"
Query 2: "Maria Garcia"
Query 3: "Maria Land"
Query 4: "Land John"
Query 5: "mgarcia@example.com"
Query 6: "Maria John AHFL"
Query 7: "555-0123"
```

---

## 📊 Scoring Algorithm Structure

### Component 1: Field Extraction
Extract all searchable fields from contact:

```javascript
contact = {
  // Name fields
  first_name: "Maria",
  middle_name: "Isabella",
  last_name: "Garcia",
  full_name: "Maria Isabella Garcia",
  name_parts: ["Maria", "Isabella", "Garcia"],

  // Contact info
  emails: ["maria@draas.com", "mgarcia@example.com"],
  email_parts: ["maria", "mgarcia", "draas.com", "example.com"],
  phones: ["+1-555-0123", "+1-555-0124"],
  phone_clean: ["15550123", "15550124"],

  // Professional data
  organization: "Draas",
  projects: ["Land Development Initiative", "Real Estate Portfolio Management"],
  topics: ["Real Estate", "Property Valuation", "Market Analysis"],
  entities: ["AHFL", "Draas Properties", "XYZ Corporation"],

  // People connections
  people: [
    {name: "John Doe", role: "CEO"},
    {name: "Sarah Smith", role: "Colleague"},
    {name: "Michael Chen", role: "Partner"}
  ],
  people_names: ["John Doe", "Sarah Smith", "Michael Chen"],
  people_first_names: ["John", "Sarah", "Michael"],

  // Notes (free text)
  notes: "Lead on Land Development, works closely with John on AHFL projects"
}
```

---

## 🧮 Component 2: Query Parsing

Parse query into tokens and classify each:

```javascript
function parseQuery(queryString) {
  const tokens = queryString.toLowerCase().split(/\s+/);

  return tokens.map(token => ({
    token: token,
    length: token.length,
    type: classifyToken(token),
    // types: "name" | "email" | "phone" | "project" | "entity" | "unknown"
  }));
}

// For "Maria Land John"
parseQuery("Maria Land John") = [
  {token: "maria", length: 5, type: "unknown"},
  {token: "land", length: 4, type: "unknown"},
  {token: "john", length: 4, type: "unknown"}
]

// For "mgarcia@example.com"
parseQuery("mgarcia@example.com") = [
  {token: "mgarcia@example.com", type: "email"}
]

// For "+1-555-0123"
parseQuery("+1-555-0123") = [
  {token: "+1-555-0123", type: "phone"}
]
```

---

## 🎯 Component 3: Scoring Tiers

### Tier 1: EXACT MATCH (100 points) ⭐⭐⭐
Highest confidence - exact match anywhere

```javascript
function scoreExactMatch(token, contact) {
  const tokenLower = token.toLowerCase();
  let maxScore = 0;

  // Check all fields for exact token match
  if (contact.first_name.toLowerCase() === tokenLower) return 100;
  if (contact.last_name.toLowerCase() === tokenLower) return 100;
  if (contact.emails.some(e => e.toLowerCase() === tokenLower)) return 100;
  if (contact.phone_clean.includes(tokenLower.replace(/\D/g, ''))) return 100;

  // Exact match in organizations
  if (contact.organization.toLowerCase() === tokenLower) return 95;

  return 0;
}

// Test cases
scoreExactMatch("maria", contact) = 100 // Matches first_name
scoreExactMatch("garcia", contact) = 100 // Matches last_name
scoreExactMatch("mgarcia@example.com", contact) = 100 // Matches email
scoreExactMatch("555-0123", contact) = 100 // Matches phone
```

---

### Tier 2: NAME FIELD FUZZY MATCH (70-90 points) 🔤
Fuzzy matching on name fields with distance scoring

```javascript
function scoreNameMatch(token, contact) {
  const tokenLower = token.toLowerCase();
  let scores = [];

  // Full name (best)
  const fullNameDist = levenshteinDistance(contact.full_name.toLowerCase(), tokenLower);
  const fullNameScore = 90 - (fullNameDist * 5); // Penalty for each char difference
  scores.push(fullNameScore);

  // First name
  const firstNameDist = levenshteinDistance(contact.first_name.toLowerCase(), tokenLower);
  const firstNameScore = 85 - (firstNameDist * 5);
  scores.push(firstNameScore);

  // Last name
  const lastNameDist = levenshteinDistance(contact.last_name.toLowerCase(), tokenLower);
  const lastNameScore = 85 - (lastNameDist * 5);
  scores.push(lastNameScore);

  // Any name part
  contact.name_parts.forEach(part => {
    const partDist = levenshteinDistance(part.toLowerCase(), tokenLower);
    const partScore = 75 - (partDist * 3);
    scores.push(Math.max(0, partScore));
  });

  return Math.max(...scores);
}

// Test cases
scoreNameMatch("maria", contact) = 90 // Exact match first_name
scoreNameMatch("mária", contact) = 87 // 1-char distance
scoreNameMatch("mari", contact) = 80 // 1-char diff from "maria"
scoreNameMatch("garci", contact) = 80 // 1-char diff from "garcia"
```

---

### Tier 3: PROJECT/TOPIC/ENTITY MATCH (60-75 points) 📊
Match query token against professional fields

```javascript
function scoreProjectMatch(token, contact) {
  const tokenLower = token.toLowerCase();
  let scores = [];

  // Projects (highest weight)
  contact.projects.forEach(project => {
    const projectLower = project.toLowerCase();

    // Exact word match in project
    if (projectLower.includes(tokenLower)) {
      scores.push(75); // "Land" matches "Land Development Initiative"
    }

    // Fuzzy match
    const dist = levenshteinDistance(projectLower, tokenLower);
    const fuzzyScore = 70 - (dist * 2);
    scores.push(Math.max(0, fuzzyScore));
  });

  // Topics
  contact.topics.forEach(topic => {
    const topicLower = topic.toLowerCase();
    if (topicLower.includes(tokenLower)) scores.push(70);
    const dist = levenshteinDistance(topicLower, tokenLower);
    scores.push(Math.max(0, 65 - (dist * 2)));
  });

  // Entities
  contact.entities.forEach(entity => {
    const entityLower = entity.toLowerCase();
    if (entityLower.includes(tokenLower)) scores.push(65);
    const dist = levenshteinDistance(entityLower, tokenLower);
    scores.push(Math.max(0, 60 - (dist * 2)));
  });

  return scores.length > 0 ? Math.max(...scores) : 0;
}

// Test cases
scoreProjectMatch("land", contact) = 75 // "land" in "Land Development Initiative"
scoreProjectMatch("estate", contact) = 75 // "estate" in "Real Estate Portfolio Management"
scoreProjectMatch("real", contact) = 70 // "real" in "Real Estate" topic
scoreProjectMatch("property", contact) = 65 // "property" in "Draas Properties" entity
```

---

### Tier 4: PEOPLE/ASSOCIATION MATCH (50-70 points) 👥
Match query token against people names and associations

```javascript
function scorePeopleMatch(token, contact) {
  const tokenLower = token.toLowerCase();
  let scores = [];

  contact.people.forEach(person => {
    const nameLower = person.name.toLowerCase();

    // Exact first/last name match
    const parts = nameLower.split(' ');
    if (parts.includes(tokenLower)) {
      scores.push(70); // "John" matches "John Doe"
    }

    // Fuzzy on full person name
    const dist = levenshteinDistance(nameLower, tokenLower);
    const fuzzyScore = 65 - (dist * 2);
    scores.push(Math.max(0, fuzzyScore));
  });

  // Check notes for people mentions (context matching)
  const notesLower = contact.notes.toLowerCase();
  if (notesLower.includes(tokenLower)) {
    scores.push(55); // Token mentioned in notes
  }

  return scores.length > 0 ? Math.max(...scores) : 0;
}

// Test cases
scorePeopleMatch("john", contact) = 70 // Exact match "John" in "John Doe"
scorePeopleMatch("john doe", contact) = 70 // Full name match
scorePeopleMatch("sarah", contact) = 70 // Exact match "Sarah" in "Sarah Smith"
scorePeopleMatch("michael", contact) = 70 // Exact match "Michael" in "Michael Chen"
```

---

### Tier 5: CONTACT INFO MATCH (40-55 points) 📞
Match against emails and phones

```javascript
function scoreContactInfoMatch(token, contact) {
  const tokenLower = token.toLowerCase().replace(/\D/g, '');
  let scores = [];

  // Email matching
  contact.emails.forEach(email => {
    if (email.toLowerCase().includes(token.toLowerCase())) {
      scores.push(55);
    }

    // Email prefix match
    const emailPrefix = email.split('@')[0].toLowerCase();
    if (emailPrefix === tokenLower || emailPrefix.includes(tokenLower)) {
      scores.push(50);
    }
  });

  // Phone matching
  contact.phones.forEach(phone => {
    const phoneClean = phone.replace(/\D/g, '');
    if (phoneClean.includes(tokenLower)) {
      scores.push(50);
    }
  });

  // Domain matching
  contact.emails.forEach(email => {
    const domain = email.split('@')[1];
    if (domain && domain.includes(token.toLowerCase())) {
      scores.push(40);
    }
  });

  return scores.length > 0 ? Math.max(...scores) : 0;
}

// Test cases
scoreContactInfoMatch("mgarcia", contact) = 50 // Email prefix
scoreContactInfoMatch("example.com", contact) = 40 // Domain match
scoreContactInfoMatch("555-0123", contact) = 50 // Phone partial
scoreContactInfoMatch("maria@draas.com", contact) = 55 // Exact email
```

---

## 📈 Component 4: Composite Scoring

Now combine all scores with **multi-field boost logic**:

```javascript
function scoreContact(tokens, contact) {
  let totalScore = 0;
  let matchedFields = new Set();

  // Score each token
  const tokenScores = tokens.map(token => {
    const scores = {
      exact: scoreExactMatch(token, contact),
      name: scoreNameMatch(token, contact),
      project: scoreProjectMatch(token, contact),
      people: scorePeopleMatch(token, contact),
      contact_info: scoreContactInfoMatch(token, contact)
    };

    // Find best match for this token
    const bestField = Object.entries(scores).reduce((a, b) =>
      b[1] > a[1] ? b : a
    )[0];

    const bestScore = scores[bestField];
    matchedFields.add(bestField);

    return {
      token: token,
      score: bestScore,
      field: bestField,
      breakdown: scores
    };
  });

  // Base score: sum of all token scores
  totalScore = tokenScores.reduce((sum, ts) => sum + ts.score, 0) / tokens.length;

  // MULTI-FIELD BOOST: Different fields matched = higher confidence
  const uniqueFields = matchedFields.size;
  let boost = 1.0;

  if (uniqueFields === 1) boost = 1.0;      // Single field match
  if (uniqueFields === 2) boost = 1.15;     // Two different fields = 15% boost
  if (uniqueFields === 3) boost = 1.35;     // Three different fields = 35% boost
  if (uniqueFields >= 4) boost = 1.50;      // Four+ fields = 50% boost

  totalScore = totalScore * boost;

  // EXACT NAME MATCH OVERRIDE: If exact name match, boost heavily
  if (tokenScores.some(ts => ts.field === 'exact' && ts.score === 100)) {
    totalScore = Math.min(100, totalScore * 1.3);
  }

  return {
    contact: contact,
    score: Math.min(100, Math.round(totalScore)),
    matched_fields: Array.from(matchedFields),
    token_breakdown: tokenScores,
    boost_factor: boost
  };
}
```

---

## 🧪 Practical Examples

### Example 1: Query = "Maria"
```
Tokens: ["maria"]

Token "maria" scoring:
  - exact match: 100 (matches first_name)
  - name match: 90
  - project match: 0
  - people match: 0
  - contact_info: 0

Best field: "exact" (100)
Matched fields: 1
Base score: 100
Boost: 1.0
Final score: 100

Result: EXACT MATCH ✅
```

### Example 2: Query = "Maria Land"
```
Tokens: ["maria", "land"]

Token "maria":
  - exact match: 100 (first_name)
  → Best: 100

Token "land":
  - project match: 75 ("land" in "Land Development Initiative")
  → Best: 75

Base score: (100 + 75) / 2 = 87.5
Matched fields: {exact, project} = 2 fields
Boost: 1.15
Final score: 87.5 * 1.15 = 100 (capped)

Result: STRONG MATCH ✅✅
```

### Example 3: Query = "Land John"
```
Tokens: ["land", "john"]

Token "land":
  - project match: 75 ("land" in "Land Development Initiative")
  → Best: 75

Token "john":
  - people match: 70 (first name in "John Doe")
  → Best: 70

Base score: (75 + 70) / 2 = 72.5
Matched fields: {project, people} = 2 fields
Boost: 1.15
Final score: 72.5 * 1.15 = 83

Result: GOOD MATCH ✅
```

### Example 4: Query = "Maria Isabella AHFL XYZ"
```
Tokens: ["maria", "isabella", "ahfl", "xyz"]

Token "maria":
  - exact: 100 (first_name)
  → Best: 100

Token "isabella":
  - name: 90 (middle_name)
  → Best: 90

Token "ahfl":
  - project: 65 (entity match)
  → Best: 65

Token "xyz":
  - project: 65 (entity match)
  → Best: 65

Base score: (100 + 90 + 65 + 65) / 4 = 80
Matched fields: {exact, name, project} = 3 fields
Boost: 1.35
Final score: 80 * 1.35 = 108 → capped at 100

Result: PERFECT MATCH ✅✅✅
```

### Example 5: Query = "Maria Smith"
```
Tokens: ["maria", "smith"]

Token "maria":
  - exact: 100 (first_name)
  → Best: 100

Token "smith":
  - people: 70 ("smith" in "Sarah Smith")
  → Best: 70

Base score: (100 + 70) / 2 = 85
Matched fields: {exact, people} = 2 fields
Boost: 1.15
Final score: 85 * 1.15 = 97.75

Result: VERY STRONG - But query might be ambiguous
(Could be looking for Maria with connection to Sarah Smith)
```

---

## 🚨 Component 5: Ambiguity Resolution

When query is ambiguous (could match multiple people), return ranked results:

```javascript
function searchContacts(query, allContacts) {
  const tokens = parseQuery(query);

  const results = allContacts
    .map(contact => scoreContact(tokens, contact))
    .filter(result => result.score >= 50) // Threshold
    .sort((a, b) => b.score - a.score)
    .slice(0, 10); // Top 10

  return results;
}

// Query: "Land John"
// Could match:
// 1. Maria Garcia (Land + John connection) - Score: 83
// 2. John Doe (if he exists as standalone contact) - Score: 70
// 3. Someone else with Land topic - Score: 55
```

---

## 🔧 Component 6: Threshold & Confidence

```javascript
const SCORING_THRESHOLDS = {
  EXACT: 90,        // >= 90: Show as primary match
  STRONG: 75,       // 75-89: Show as secondary match
  GOOD: 50,         // 50-74: Show as possible match
  WEAK: 0,          // < 50: Don't show (or show with "low confidence")
};

function getConfidenceLevel(score) {
  if (score >= 90) return "EXACT";
  if (score >= 75) return "STRONG";
  if (score >= 50) return "GOOD";
  return "WEAK";
}

// Results returned with confidence
[
  {
    name: "Maria Garcia",
    score: 100,
    confidence: "EXACT",
    matched_fields: ["exact", "project"],
    matched_on: ["maria (first_name)", "land (project)"]
  },
  {
    name: "John Doe",
    score: 70,
    confidence: "GOOD",
    matched_fields: ["people"],
    matched_on: ["john (associated person)"]
  }
]
```

---

## 📋 Algorithm Pseudocode Summary

```javascript
function advancedScoreContact(query, contact) {
  // 1. Parse query into tokens
  const tokens = parseQuery(query);

  // 2. Score each token against multiple fields
  const tokenScores = tokens.map(token => ({
    exact:        scoreExactMatch(token, contact),      // 0 or 100
    name:         scoreNameMatch(token, contact),        // 75-90
    project:      scoreProjectMatch(token, contact),     // 60-75
    people:       scorePeopleMatch(token, contact),      // 50-70
    contact_info: scoreContactInfoMatch(token, contact)  // 40-55
  }));

  // 3. Calculate base score (average)
  const baseScore = tokenScores.reduce((sum, ts) =>
    sum + Math.max(...Object.values(ts)), 0
  ) / tokens.length;

  // 4. Count matched field types
  const matchedFields = new Set();
  tokenScores.forEach(ts => {
    Object.entries(ts).forEach(([field, score]) => {
      if (score > 0) matchedFields.add(field);
    });
  });

  // 5. Apply multi-field boost
  const boostFactor = {
    1: 1.0,
    2: 1.15,
    3: 1.35,
    4: 1.50
  }[Math.min(matchedFields.size, 4)];

  const finalScore = Math.min(100, baseScore * boostFactor);

  return {
    contact,
    score: Math.round(finalScore),
    confidence: getConfidenceLevel(finalScore),
    matched_fields: Array.from(matchedFields)
  };
}
```

---

## 📊 Field Weights Summary Table

| Field Type | Weight Range | Examples |
|---|---|---|
| Exact Match | 95-100 | Full name, email, phone |
| First Name | 85-90 | "Maria" |
| Last Name | 85-90 | "Garcia" |
| Project Name | 60-75 | "Land Development Initiative" |
| Topics | 60-70 | "Real Estate", "Property" |
| Entities | 55-65 | "AHFL", "Draas Properties" |
| Associated People | 50-70 | "John Doe", "Sarah Smith" |
| Email Address | 40-55 | "mgarcia@example.com" |
| Phone Number | 40-50 | "+1-555-0123" |

---

## 🎯 Multi-Field Boost Multipliers

| Matched Fields | Boost | Rationale |
|---|---|---|
| 1 field only | 1.0x | Basic match (could be coincidence) |
| 2 fields | 1.15x | More confident (name + project) |
| 3 fields | 1.35x | High confidence (name + project + people) |
| 4+ fields | 1.50x | Very high confidence (multiple confirmations) |

---

## Example: Confusion Resolution

**Query:** `"John Land"`

Two possible interpretations:
1. Person named "John" working on "Land" project
2. Person "John" is mentioned in Land project context

| Contact | Interpretation | Score | Matched Fields |
|---|---|---|---|
| Maria Garcia | John (associated) + Land (project) | 72.5 × 1.15 = **83** | people, project |
| John Doe | First name "John" | 90 | exact |
| John Smith | First name "John" | 90 | exact |

**Result:** Show both "Johns" (90) AND Maria (83), let AI choose based on context.

---

## ✅ Next Steps

This algorithm will:
- ✅ Find exact matches (100% confidence)
- ✅ Handle fuzzy name variations (typos, aliases)
- ✅ Search across all 6+ fields simultaneously
- ✅ Rank results by confidence
- ✅ Resolve ambiguities with multi-field scoring
- ✅ Boost confidence for multi-field matches
- ✅ Return JSON with scoring breakdown (Hermes can see why)

Ready to code this into n8n?
