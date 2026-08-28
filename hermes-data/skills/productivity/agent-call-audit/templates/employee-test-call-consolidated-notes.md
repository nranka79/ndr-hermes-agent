# {Project} — Employee Test-Call Campaign: Consolidated Notes

**Campaign:** Each DRAAS employee calls the JOYZ AI robocalling agent posing as an interested buyer, records the call, and submits feedback. These notes consolidate every employee's transcript + feedback + analysis. The consolidated findings feed the JOYZ AI vendor feedback document.

**Project:** {name} — {one-line: gated plotted development, location, plots × size, price}
**Agent under test:** "{AgentName}" (JOYZ AI voice agent)
**Verified facts baseline:** see `ai-voice-agent-training` skill → `references/ranka-udaya-agent-data.md` (FAQ Excel + comparables sheet)

---

# 📋 Employee N: {Name} ({date})

**Call date:** | **Duration:** | **Role played:** interested buyer
**Files:**
- Call recording: `YYYYMMDD_{Name}_TestCall_Recording.{ext}` (TMP → "{Project} - Employee Test Calls")
- Feedback recording: `YYYYMMDD_{Name}_Feedback_Recording.{ext}`
- (optional) NDR campaign instructions memo

## 1. Transcript (Whisper base, speaker labels reconstructed — no diarization available)

| Time | Speaker | Text |
|---|---|---|

## 2. Employee's own feedback (from their recording/write-up, verbatim points)

1. ...
2. ...

## 3. Reconciliation: their feedback vs actual transcript

| Their feedback | Transcript evidence | Verdict |
|---|---|---|
| (point) | (timestamp + quote) | ✅ Valid / ⚠️ Partial / ❌ Contradicted |

**Reconciliation insight:** {what the employee caught that the transcript confirms; what they MISSED that the analyst found — employees often don't notice content errors like wrong comparables}

## 4. Compliance scoring (per agent-call-audit rubric)

| Category | Weight | Score | Notes |
|---|---|---|---|
| Opening Hook | 10% | /10 | |
| Location Accuracy | 15% | /10 | |
| Price Anchoring | 15% | /10 | |
| Project Details | 15% | /10 | |
| RERA / Regulatory | 10% | /10 | |
| Objection Handling | 15% | /10 | |
| Lead Capture / Handover | 10% | /10 | |
| Closing / Site Visit | 10% | /10 | |

**Overall: ≈ {N}%** (weighted sum)

## 5. Key findings

### Content correctness (wrong / missing)
1. ❌ **{Wrong answer}** — {quote at timestamp}. Correct: {verified content}. → {KB update action}
2. ...

### Persona / tone
- ⚠️ {tone issue}
- ✅ {what to keep}

### Technical
- ❌ {dead air / latency / glitch / setup failure}

---

# 📝 Vendor Feedback (JOYZ AI) — to be completed from ALL employees' calls

*Seeded from the first employee's call; expanded after every employee's analysis is appended above.*

## 5.1 System prompt changes
1. ...
## 5.2 FAQ / Knowledge Base to ADD
1. ...
## 5.3 Gaps to fill
- ...
## 5.4 Personality & tone
- ...
## 5.5 Technical issues
- ...

---

*Appendix: this document lives in Drive TMP → "{Project} - Employee Test Calls" and is appended per employee. Analysis artifacts per employee saved under `/data/hermes/cache/analysis/`.*
