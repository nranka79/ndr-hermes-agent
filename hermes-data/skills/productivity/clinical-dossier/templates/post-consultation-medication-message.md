Copy this template and fill in the patient name, drug, and schedule details. The user sends this themselves from their own WhatsApp.

```
[Patient Name], regarding the medication Dr. [Doctor Name] prescribed today ([DD Mon YYYY]) at [Hospital]:

**[Drug Name] ([N] tablets total)** — [schedule type: tapering / fixed / as-needed] schedule:

🔹 **Days [start]-[end]** → [dosage description] ([X]/day)
🔹 **Days [start]-[end]** → [dosage description] ([X]/day)
🔹 **Days [start]-[end]** → [dosage description] ([X]/day)

[After N days / After course] → [Stop / Continue / Next step].

📅 **Next appointment:** [DD Month YYYY] — Dr. [Name] will do [Test/Review].

Please follow the schedule exactly.
```

### Real example (from session 25 Jul 2026)

```
Kanta Aunty, regarding the medication Dr. Haldipur prescribed today (25 Jul 2026) at Trustwell:

**Strujan (35 tablets total)** — tapering schedule:

🔹 **Days 1-10** → 1 tablet morning + 1 tablet night (2/day)
🔹 **Days 11-20** → 1 tablet each day (1/day)
🔹 **Days 21-30** → Half tablet at night only (0.5/day)

After 30 days → Stop Strujan completely.

📅 **Next appointment:** 25 October 2026 — Dr. Haldipur will do a PTA test.

Please follow the schedule exactly.
```

### WhatsApp click-to-chat link generator

```python
import urllib.parse
phone = "919900133634"  # patient's number without +
msg = "Your message text here"
wa_link = f"https://wa.me/{phone}?text={urllib.parse.quote(msg)}"
```
