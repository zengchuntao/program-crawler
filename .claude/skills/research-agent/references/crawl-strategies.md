# Crawl Strategies by Region

## General Rules

- **Short queries**: 5-8 words max. DuckDuckGo drops results for long queries.
- **English first**: most university pages have English versions. Try local
  language only if English search returns nothing.
- **HTTP first**: most university pages are static HTML. Only use Playwright
  when HTTP returns thin content or a site is confirmed SPA.
- **One screenshot per URL**: never open a new browser instance for each finding.

## Search Engine Fallback Chain

```
DuckDuckGo → (CAPTCHA detected?) → Brave Search → (still 0?) → registry URLs
```

DuckDuckGo triggers CAPTCHA after ~5-10 rapid requests. Detect by checking
for "squares containing a duck" or "error-lite@duckduckgo.com" in response.

Google is unusable via plain HTTP (returns JS shell). Do not attempt.

## Region: Hong Kong

- Academic year: September intake, applications ~Nov-Apr
- Tuition in **HKD**
- Language: TOEFL iBT / IELTS / CET-6 commonly accepted
- Many main portals (e.g. `www.cityu.edu.hk/pg/`) use **Incapsula/Imperva WAF**
  that blocks both HTTP and headless browsers. Use department subdomains instead.
- Department subdomains (e.g. `cb.cityu.edu.hk`, `mba.cb.cityu.edu.hk`) usually
  lack WAF and work fine with HTTP or Playwright.

## Region: United States

- Fall intake primary (September), deadline Dec-Jan
- Tuition in **USD**, often per semester or per year
- GRE/GMAT: many programs went test-optional post-COVID
- Language: TOEFL iBT / IELTS / Duolingo
- Most `.edu` sites are static and work well with HTTP

## Region: United Kingdom

- October intake, many programs have rolling admissions
- Tuition in **GBP**, Home vs International rates
- Language: IELTS predominantly
- Conditional offers common

## Region: Australia

- Two intakes: February (Sem 1) and July (Sem 2)
- Tuition in **AUD**, usually per year
- Sites are generally well-structured and static

## Region: Canada

- Fall (September) primary, some Winter (January)
- Tuition in **CAD**, domestic vs international
- GRE may be required

## Region: Singapore

- August primary, some January
- Tuition in **SGD**
- Some sites are SPA-based (may need Playwright)

## Region: Europe

- Bologna system (3yr Bachelor + 2yr Master)
- Tuition varies widely (free in Germany/Norway, expensive in UK/NL)
- Many programs in English at Master's level

## Anti-Bot Notes

Sites that block HTTP fetch (return 403):
- `gotouniversity.com`, `mastersportal.com`, `engineering.mit.edu`

Sites with WAF (block even headless browsers):
- `www.cityu.edu.hk/pg/` (Incapsula)
- `www.cityu.edu.hk/international/` (Incapsula)

SPA sites requiring Playwright:
- `pg.ust.hk` (React), some NUS pages (Next.js)
