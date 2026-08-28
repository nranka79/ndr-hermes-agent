# Article Skip Patterns — AI Job Loss Tracker

Article types to skip during RSS analysis. These patterns emerged from run findings (last updated June 10, 2026).

## Skip: Engineer/employee complaints, not announcements

Articles describing employees reacting to or criticizing layoffs are **reactions**, not new announcements.

**Pattern:** `[Company] engineers in [city] slam employer for...`
**Example:** "Amazon engineers in Seattle slam employer for building AI data centers while laying off 30,000 staffers" (June 4, 2026)
**Rule:** Skip unless the article adds new confirmed job numbers beyond what was already recorded.

## Skip: CEO explicitly says AI is NOT the reason

If the CEO explicitly denies AI as the driver, skip — this tracker is for AI-driven cuts only.

**Example (June 5, 2026):** "Uber slashes 23% of HR staff, CEO says AI isn't the reason" — skipped even though the article mentions AI. The explicit CEO denial is the controlling fact.

## Skip: Country or institution-level announcements

Country governments, universities, and similar institutions are not companies. Their workforce reductions (or program cuts framed as job losses) do not belong in a company layoff tracker.

**Example (June 25, 2026 run):** "China Cuts 12,200 University Programs, Replaces Many With AI" — matched the generic `Company to cut` pattern because "China" is title-case. **Fix:** add a `COUNTRY_SKIP` guard before company extraction: `re.compile(r'^(China|India|US|United States|Brazil|Indonesia|Russia|Japan|Germany|France|UK|Europe|Asia)\s', re.I)`.

## Skip: Articles where the number refers to programs/schools, not jobs

Headlines where the numeric reference is to academic programs, schools, or institutions — not workforce headcount.

**Pattern:** `re.compile(r'cuts?\s+\d+\s+(?:university|college|school|program|institution)', re.I)`

## Skip: Company-named articles that do not cite AI as the driver

A company being named in a layoff article is necessary but not sufficient. The article headline must include AI, automation, or a technology rationale — this tracker captures AI-driven cuts only.

**Example (June 9, 2026):** "Expeditors cuts 230 tech jobs in Seattle region, ending decades-long policy against layoffs" — the company is named and the article is within 48h, but the title cites a policy change, not AI. Skipped. The qualifying counter-pattern is "Company cuts X jobs amid AI shift."

## Skip: Tracker/roundup articles (recurring title patterns)

These aggregate multiple companies and contain no single-company announcement to record.

- "2026 Layoffs Tracker: [multiple companies]"
- "May sees most layoffs since 2020 as AI drives X% of job cuts"
- "US tech layoffs record single-highest month in two years"
- "Challenger Report: May Job Cuts Rise X% from April"
- "Tech Industry Loses X jobs This Year—AI Is The Most Cited Reason"
- "AI cited as top reason for US job cuts for third straight month"
- "AI-Driven Layoffs Hit Highest May Total Since 2020"
- "US Job Cuts Jump to X as AI Layoffs Mount"
- "Challenger Links AI To Most Announced Layoffs in May"
- "May Job Cuts Rise 16% from April; Highest May Total Since 2020"

## Skip: Aggregate/analytical/opinion pieces about AI and jobs

- "AI-driven tech job cuts hit two-year high"
- "AI job losses are 'complete nonsense', AI driving hiring surge instead" (Nvidia CEO)
- "AI anxiety is mostly a blue state problem"
- "Are AI tech layoffs real? New data reveals a complicated story"
- "How to Survive AI-Driven Layoffs"
- "AI won't take your job and other things CEOs say before the layoffs"
- "Enterprise AI Costs Rise as Microsoft, IBM Adjust"
- "No better opportunity than India: Citi's Ernesto Torres Cantu on layoffs, AI"
- "Govt Gears Up For AI Rollout Across Ministries; TCS Among Six Firms Selected"
- "Professional Accountability in the Age of AI"
- "A CEO told employees they won't get raises in 2026 because the budget is going to AI"
- "Canada Launches AI for All Strategy as UC Berkeley Counts the Classroom Cost"
- "Tech Industry Loses 123,000 Jobs This Year—AI Is The Most Cited Reason For Layoffs"