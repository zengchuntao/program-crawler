# Skill — University Crawling Strategies

## General Principles

### Search Strategy
- Use **short, specific** queries (5-8 words max). Long queries fail on DuckDuckGo.
- Always include the **program level** (Master, PhD, undergraduate).
- Include the **academic year** only if known; otherwise omit it.
- Try **English first**, then the local language if English fails.
- If the first search returns 0 results, **rephrase** — do not repeat the same query.

### Fetch Strategy
- **HTTP first**: Most university pages are static HTML, no need for a browser.
- **Browser fallback**: Only needed for SPAs (React/Next.js sites), or sites that return 403 to plain HTTP.
- **Thin content detection**: If HTTP returns <100 chars of text, the page likely needs JS rendering.

### Data Extraction Priorities
When visiting a page, extract data in this priority order:
1. **Deadlines** — most time-sensitive, highest value
2. **Language requirements** — TOEFL/IELTS scores, usually clearly stated
3. **Tuition fees** — usually on a separate "fees" page
4. **GPA / academic requirements** — may not be published (especially for top schools)
5. **Application materials** — typically listed on "how to apply" pages
6. **GRE/GMAT** — some programs don't require standardized tests

---

## Region: Hong Kong (香港)

### Common Patterns
- Academic year: September intake, applications open ~Nov, close ~Jan-Apr
- Most HK universities use **English** as the primary website language
- Postgraduate admissions are usually under a central graduate school portal + individual department pages
- Tuition is listed in **HKD**
- Language: TOEFL iBT / IELTS / CET-6 are commonly accepted

### University-Specific Strategies

#### City University of Hong Kong (CityU / 香港城市大学)
- **Main portal**: `www.cityu.edu.hk/pg/`
- **Program list**: `www.cityu.edu.hk/pg/taught-postgraduate-programmes/list`
- **Apply now / deadlines**: `www.cityu.edu.hk/pg/taught-postgraduate-programmes/apply-now`
- **College of Business**: `www.cb.cityu.edu.hk/postgrad/`
- **MBA**: `mba.cb.cityu.edu.hk/`
- **FAQ**: `www.cityu.edu.hk/pg/taught-postgraduate-programmes/faq`
- **Note**: Main site may return thin HTML; department sites (cb.cityu.edu.hk) work better with HTTP.
- **Search tips**: Use "CityU" or "City University Hong Kong" — the full official name is long.

#### University of Hong Kong (HKU / 香港大学)
- **Graduate school**: `www.gradsch.hku.hk/`
- **TPG admissions**: `admissions.hku.hk/tpg/`
- **Prospective students**: `www.hku.hk/prospective-students/taught-postgraduate.html`
- **Deadlines page**: `admissions.hku.hk/tpg/programmes/`
- **Note**: HKU uses a centralized admissions portal; individual departments have less detail.
- **Search tips**: "HKU" is widely recognized; "University of Hong Kong" also works.

#### Chinese University of Hong Kong (CUHK / 香港中文大学)
- **Graduate school**: `www.gs.cuhk.edu.hk/`
- **Admissions**: `www.gs.cuhk.edu.hk/admissions/`
- **Deadlines**: `www.gs.cuhk.edu.hk/admissions/admissions/application-deadline`
- **Business school**: `grad.bschool.cuhk.edu.hk/` or `masters.bschool.cuhk.edu.hk/`
- **Note**: CUHK has separate graduate school and business school portals.

#### Hong Kong Polytechnic University (PolyU / 香港理工大学)
- **Postgraduate**: `www.polyu.edu.hk/study/pg/`
- **Admissions**: `www.polyu.edu.hk/study/pg/taught-postgraduate/`
- **Note**: PolyU's site is mostly static, HTTP fetch works well.

#### Hong Kong University of Science and Technology (HKUST / 香港科技大学)
- **Postgraduate**: `pg.ust.hk/`
- **Programs**: `pg.ust.hk/prospective-students/programs`
- **Business school**: `mba.ust.hk/` or `masters.bm.ust.hk/`
- **Note**: Some pages are SPA-based, may need browser fallback.

#### Hong Kong Baptist University (HKBU / 香港浸会大学)
- **Graduate school**: `gs.hkbu.edu.hk/`
- **Admissions**: `gs.hkbu.edu.hk/admission/`

---

## Region: United States (美国)

### Common Patterns
- Academic year: Fall intake primary (September), some Spring (January)
- Applications due: December-January for Fall, September-October for Spring
- Most use English exclusively
- Tuition in **USD**, often listed per semester or per year
- GRE/GMAT widely required (but many programs went test-optional post-COVID)
- Language: TOEFL iBT / IELTS / Duolingo accepted

### University-Specific Strategies

#### MIT
- **EECS Graduate**: `www.eecs.mit.edu/academics/graduate-programs/admission-process/`
- **FAQ**: `www.eecs.mit.edu/academics/graduate-programs/admission-process/graduate-admissions-faqs/`
- **OGE**: `oge.mit.edu/programs/`
- **GradApply**: `gradapply.mit.edu/eecs`
- **Note**: MIT does NOT publish minimum GPA. Admission is "holistic."
- **Note**: EECS site is static HTML, works well with HTTP.

#### Stanford
- **Graduate admissions**: `gradadmissions.stanford.edu/`
- **Department pages**: Individual departments have their own admission pages
- **Note**: Stanford uses a mix of static and dynamic pages.

#### UC Berkeley
- **Graduate division**: `grad.berkeley.edu/`
- **EECS**: `eecs.berkeley.edu/academics/graduate/`

#### Carnegie Mellon (CMU)
- **SCS admissions**: `www.cs.cmu.edu/academics/graduate-admissions`
- **Note**: CMU has many sub-programs under CS; each has its own page.

---

## Region: United Kingdom (英国)

### Common Patterns
- Academic year: October intake, applications often rolling (no hard deadline for many programs)
- UCAS for undergraduate; direct application for postgraduate
- Tuition in **GBP**, differentiated by Home/International
- Language: IELTS predominantly (most UK schools require IELTS, some accept TOEFL)
- Conditional offers common (offer pending final grades/language score)

### University-Specific Strategies

#### University of Oxford
- **Graduate admissions**: `www.ox.ac.uk/admissions/graduate/`
- **Course finder**: `www.ox.ac.uk/admissions/graduate/courses/`
- **Note**: Oxford has college-specific requirements in addition to department requirements.

#### University of Cambridge
- **Graduate admissions**: `www.graduate.study.cam.ac.uk/`
- **Course directory**: `www.graduate.study.cam.ac.uk/courses/`

#### Imperial College London
- **Postgraduate**: `www.imperial.ac.uk/study/postgraduate/`
- **Note**: Imperial's site is well-structured, HTTP works well.

#### UCL
- **Graduate admissions**: `www.ucl.ac.uk/prospective-students/graduate/`

---

## Region: Australia (澳大利亚)

### Common Patterns
- Two main intakes: February (Semester 1) and July (Semester 2)
- Tuition in **AUD**, usually per year
- Language: IELTS preferred, TOEFL also accepted
- Most Australian university sites are well-structured and static

### University-Specific Strategies

#### University of Melbourne
- **Graduate**: `study.unimelb.edu.au/find/courses/graduate/`
- **Note**: Excellent search and filtering on their course finder.

#### University of Sydney
- **Postgraduate**: `www.sydney.edu.au/courses/courses/pc/`

#### UNSW
- **Postgraduate**: `www.unsw.edu.au/study/postgraduate`

---

## Region: Canada (加拿大)

### Common Patterns
- Fall intake (September) primary; some Winter (January)
- Tuition in **CAD**, differentiated by domestic/international
- Language: TOEFL / IELTS
- Many programs require GRE

### University-Specific Strategies

#### University of Toronto
- **SGS**: `www.sgs.utoronto.ca/`
- **Programs**: `www.sgs.utoronto.ca/programs/`

#### UBC
- **Graduate**: `www.grad.ubc.ca/`

---

## Region: Singapore (新加坡)

### Common Patterns
- August intake primary; January intake for some programs
- Tuition in **SGD**
- English-medium instruction
- Sites are generally modern and may be SPA-based

### University-Specific Strategies

#### NUS
- **Graduate**: `nusgs.nus.edu.sg/`
- **Computing**: `www.comp.nus.edu.sg/programmes/pg/`

#### NTU
- **Graduate**: `www.ntu.edu.sg/admissions/graduate/`

---

## Region: Europe (欧洲)

### Common Patterns
- Bologna system: Bachelor (3yr) + Master (2yr)
- Many programs in English, especially at Master's level
- Tuition varies wildly (free in Germany/Norway to expensive in UK/Netherlands)
- Language: IELTS/TOEFL for English programs; local language certificates for native programs

### University-Specific Strategies

#### ETH Zurich
- **Master**: `ethz.ch/en/studies/master.html`
- **Note**: Application portal is separate from info pages.

#### TU Munich
- **Graduate**: `www.tum.de/en/studies/application/`

---

## Anti-Bot Detection Notes

### Sites That Block HTTP Fetch
These sites return 403 or require browser rendering:
- `gotouniversity.com` — 403 to plain HTTP
- `mastersportal.com` — 403 to plain HTTP
- `engineering.mit.edu` — 403 to plain HTTP
- Some CityU pages (`www.cityu.edu.hk/international/`) — return empty HTML

### Sites with SPA Rendering
These sites need Playwright/browser to get content:
- HKUST (`pg.ust.hk`) — React-based
- Some NUS pages — Next.js
- Google Search results — fully JS-rendered

### Search Engine Behavior
- **DuckDuckGo**: Triggers CAPTCHA after ~5-10 rapid consecutive requests. Use Brave as fallback.
- **Brave Search**: More tolerant of automated requests. Good fallback.
- **Google**: Returns JS-only page to HTTP requests. Unusable without browser.
- **Rate limit strategy**: Space requests 1-2 seconds apart if possible.
