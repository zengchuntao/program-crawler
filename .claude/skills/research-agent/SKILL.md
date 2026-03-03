---
name: research-agent
description: Researches academic program admissions data by searching the web,
  visiting university pages, and extracting structured facts. Use when user asks to
  "find program requirements", "look up admission deadlines", "research university
  programs", "check application requirements", "find tuition fees", or any query
  about graduate/postgraduate program details at a specific university.
---

# Research Agent

Autonomous research loop that takes a natural language query about academic
programs and produces structured, evidence-backed findings.

## Step 1: Plan the research

Parse the user's query to identify:
- **Target entities**: specific programs to research (e.g. "CityU MSc Finance")
- **Fields needed**: deadlines, language_requirement, tuition_fees, gpa_requirement,
  materials, gre_gmat_requirement, curriculum_summary
- **Search hints**: short queries (5-8 words max) for web search

Before searching, check [references/university-registry.md](references/university-registry.md)
for known entry-point URLs. If the university is listed, pre-seed those URLs as
visit targets to skip search entirely.

## Step 2: Search and visit

Search strategy (see [references/crawl-strategies.md](references/crawl-strategies.md)):
1. Use short, specific search queries. Long queries return 0 results.
2. DuckDuckGo first, Brave Search as fallback if CAPTCHA detected.
3. After 3 failed searches, fall back to known URLs from the registry.

Visit strategy:
1. HTTP fetch first (fast, ~200ms). Fall back to Playwright only when content
   is too thin (<100 chars) or the site needs JS rendering.
2. Never revisit a URL already in memory.
3. Prefer official `.edu` / `.edu.hk` / `.ac.uk` domains over aggregator sites.

## Step 3: Evaluate pages and extract findings

See [references/data-quality.md](references/data-quality.md) for what counts as
a valid finding.

Core rules:
- Extract **only concrete facts**: specific dates, test scores, dollar amounts,
  document lists, credit counts.
- **Reject** marketing slogans, taglines, and vague descriptions.
- If a page lists program names without details, extract **links to detail pages**
  instead of creating low-value findings.
- A field is "done" only when found for a majority of target entities, not just one.

## Step 4: Capture evidence

Take ONE screenshot per URL (not per finding) to avoid redundant browser launches.
Tolerate screenshot timeout — partial screenshots are acceptable.

## Step 5: Know when to stop

- All requested fields found for target entities → **done**
- Visited 5+ pages with no new findings → **done** (partial is OK)
- A field genuinely does not exist (e.g. no published minimum GPA) → report that
  fact, do not keep searching
- Never waste steps revisiting failed URLs or repeating identical searches

## Quality check

Before reporting results:
- [ ] Every finding contains a concrete fact, not a slogan
- [ ] Source URL is an authoritative page (official university site preferred)
- [ ] No duplicate findings for the same entity + field
- [ ] Missing fields are genuinely unavailable, not just unfound
