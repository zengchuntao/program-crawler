# Data Quality Standards

## What Counts as a Valid Finding

A finding must contain a **concrete, verifiable fact** from the source page.

### Good findings (extract these)

| Field | Example | Why it's good |
|-------|---------|---------------|
| deadlines | "Application deadline: 31 March 2026" | Specific date |
| language_requirement | "TOEFL iBT: 79; IELTS: 6.0" | Specific scores |
| tuition_fees | "HK$ 493,200 (Local)" | Specific amount with currency |
| materials | "3 recommendation letters, SOP, transcripts" | Concrete list |
| gpa_requirement | "Minimum GPA 3.0/4.0" | Specific threshold |
| curriculum_summary | "42 credits, core: Financial Accounting, Corporate Finance" | Actual course structure |

### Bad findings (never extract these)

| Field | Example | Why it's bad |
|-------|---------|--------------|
| curriculum_summary | "The WORLD is a STONE'S THROW from HERE" | Marketing slogan |
| curriculum_summary | "We nurture leaders with vision" | Vague tagline |
| curriculum_summary | "Gain a competitive edge" | Promotional copy |
| deadlines | "Applications are now open" | No specific date |
| tuition_fees | "Competitive tuition" | No actual number |

## Decision Rules

1. **If the page only lists program names** without detail → report the names as
   `useful_links` to their individual pages, not as findings
2. **If a field genuinely doesn't exist** (e.g. MIT doesn't publish minimum GPA) →
   the agent should report "Not published" as the value with a note, then move on
3. **If data comes from a third-party aggregator** (yocket, mastersportal) → lower
   confidence to 0.7 and note the source is unofficial
4. **Deduplication**: if the same entity + field already has a finding with higher
   confidence, do not replace it with a lower-confidence one

## Confidence Scoring

| Source | Confidence |
|--------|-----------|
| Official university `.edu` page | 0.95 - 1.0 |
| Official department subdomain | 0.90 - 0.95 |
| University FAQ / admissions portal | 0.85 - 0.95 |
| Third-party aggregator (topuniversities, etc.) | 0.60 - 0.75 |
| Forum / blog / unofficial source | 0.30 - 0.50 |
