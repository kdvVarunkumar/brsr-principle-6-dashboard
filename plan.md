# Plan: BRSR Principle 6 Report Generator & Dashboard

> Read `context.md` first for the assignment summary, verified facts and decisions.
> This file is the **to-do list in priority order**. We go **one phase at a time**, and no phase starts until the previous one is "Done when ..." true.
> Status: **PLANNING ONLY. No code is written until you confirm this plan.**

---

## 1. The goal in plain words

Build a tool where you type **a company** (e.g. `Tata Steel` or `TATASTEEL`) and **a financial year** (e.g. `2023-24`), and it produces **one HTML page** with two tabs:

1. **SEBI-format report**: Principle 6 (environment) laid out *exactly* like SEBI's official template (same question numbers, tables, row labels, units, current + previous year columns).
2. **Dashboard**: the same data re-explained for a non-expert (investor, journalist, student): what each metric means, whether it got better or worse, and why it matters.

Golden rules from the assignment:
- **Never invent numbers.** Every figure must trace back to a filing. Missing, converted or estimated values must be labelled on the page.
- **Be polite to NSE.** Cache downloads, add delays, never hammer the site.
- **Dashboard clarity is the biggest grade (30%)**, then data accuracy (25%). A solid core beats four half-finished parts.

## 2. The big picture: your three questions answered

You asked: *how to fetch, how to store, how to show.* This is the whole pipeline:

```
 user input                 FETCH                    STORE                  UNDERSTAND                  SHOW
 ----------                 -----                    -----                  ----------                  ----
 "Tata Steel"  --> find NSE symbol --> download BRSR  --> save raw file  --> parse XBRL/XML  --> normalise units --> SEBI view  --\
 "2023-24"     --> check FY valid       filing from       in data/raw/       into "facts"      + flag missing      Dashboard   ---> ONE HTML
                                        NSE (polite)      (cache)            map to P6 rows    + compute better/worse              page
                                                          save parsed JSON in data/parsed/
```

| Question | Our answer | Why |
|---|---|---|
| **How to fetch?** | Python `requests` with a browser-like session (headers + cookies), delays between calls, cache-first. If NSE blocks us, fall back to filings you download by hand into `data/raw/` (the assignment allows this if documented). | NSE loads data through background requests; we discover the exact request in Phase 1 using browser DevTools. |
| **How to store?** | Plain **files**: raw downloads in `data/raw/<SYMBOL>/<FY>/`, parsed results as **JSON** in `data/parsed/`. No database. | Simple, inspectable, git-friendly, and it *is* our cache. A database is overkill for a handful of filings. |
| **How to show?** | Python script fills **Jinja2 HTML templates** and writes a single self-contained `.html` file (CSS inline, charts as inline SVG/CSS, no internet needed). | Opens in any browser with zero setup (an explicit requirement). Keeps *extraction* separate from *presentation* (a grading item). |

## 3. Key technical decisions (recommended defaults, change if you disagree)

| Decision | Recommendation | Reason |
|---|---|---|
| Language | **Python 3** (your venv has 3.14) | You are learning it; the assignment allows it; libraries are mature. |
| App style | **CLI script that generates static HTML** (not Flask/Django) | Fewer moving parts, easier to explain in the interview, sample outputs can be committed to the repo. |
| Data format | **XBRL/XML first, PDF only as a last resort** | The hint says structured data is far more reliable than PDF tables. We verify in Phase 1. |
| XML parsing | Python standard library `xml.etree.ElementTree` | Zero extra dependency. (`lxml` may lack wheels for brand-new Python versions.) |
| Dependencies | `requests`, `Jinja2`, `pytest` (maybe `rapidfuzz` or stdlib `difflib` for name matching) | "Keep dependencies reasonable." |
| Charts | Inline SVG / CSS bars generated in Python | Works offline, no JS library needed, accessible. |
| Storing numbers | A `Metric` object = `value + unit + status + source + note` | One place to enforce "never invent numbers": status is one of `REPORTED`, `NOT_REPORTED`, `CONVERTED`, `CALCULATED`. |

## 4. Project structure

*(This was a sketch in Phase 0. The code grew to about 40 modules, so in Phase 12 it was reorganised into the layers below; the reasons are in `context.md` D69-D71 and `learnings.md` §12.)*

```
BRSR Principle 6 .../
├── plan.md  context.md  learnings.md  commands.md  README.md  requirements.txt  .gitignore  pytest.ini
├── main.py  trends.py  summary.py  download_filings.py  extract_report.py  make_samples.py   # thin entry points: read args, call a command
├── brsr_p6/                 # (no src/ folder: keeps `python main.py` and `pytest` working with zero extra setup)
│   ├── core/                # data model + small helpers: models, errors, fiscal_year, units, formatting, friendly, sebi_template, paths
│   ├── download/            # 1. NSE -> files on disk: nse_client, company_lookup, filings, downloader
│   ├── parsing/             # 2. XBRL file -> raw facts: xbrl_reader, p6_mapping
│   ├── extraction/          # 3. raw facts -> one clean Principle6Report: extractor, checks, values, report_io
│   ├── analysis/            # 4. comparing years, pure logic: comparison, warning_kinds, trend_model
│   ├── views/               # 5. what each page says: dashboard, SEBI form, trends, summary, errors
│   ├── rendering/           # 6. Jinja2 templates + render.py
│   ├── workflows/           # whole jobs end to end: pipeline, trend_loader, summary_loader, samples
│   └── cli/                 # the commands behind the entry points
├── data/raw/  data/parsed/  # cache (raw files you hand-download also live here)
├── samples/                 # generated HTML (committed)
└── tests/                   # folders mirror brsr_p6/; helpers/ holds the shared test helpers
```

**Why this split?** Each package does one job, and a package may only import from the packages *above* it in the list (`core` first). `parsing` knows nothing about HTML; `views` knows nothing about NSE; `rendering` knows nothing about how a filing is read. That separation is exactly what "extraction separated from presentation" means in the grading table, and `tests/test_architecture.py` keeps it true.

---

## 5. The phases (in priority order)

Time estimates are rough hours for you working with my help. Core (Phases 0-7) is about **26 h**, which leaves room inside the 48 h window.

### Phase 0: Setup (~1 h) ✅ DONE (git deferred to the end by your choice)
**Why:** A clean, reproducible project from the start. "Runs from a clean checkout" is a deliverable.
- [x] Confirm PyCharm uses the project `.venv` (Python 3.14.2)
- [x] `git init` → deferred to the end by your choice, then done in Phase 11 (git installed, repository with commits; see `learnings.md` Phase 11)
- [x] Create `.gitignore` (`.venv/`, `__pycache__/`, `.idea/`), create the folders above
- [x] Create `requirements.txt` (`requests`, `Jinja2`, `pytest`) and install
- [x] Create `README.md` skeleton and start an **AI-usage log** (the assignment requires telling them which AI tools were used and for what)
- [x] Write `learnings.md` (concepts explained in plain English)
- **You'll learn:** virtual environments, pip, modules/imports, `if __name__ == "__main__":`
- **Done when:** `python main.py --help` prints usage and `pytest` runs one dummy test. ✅ Verified, including a clean-checkout test in a brand-new venv.

### Phase 1: Discovery spike: "look before you build" (~3 h)  ✅ DONE (signed off by you)
**Why:** Everything depends on what NSE actually gives us. Spending 3 hours looking now saves 10 hours of rework.
- [x] Open NSE's BRSR filings page in your browser and search a company (Tata Steel)
- [x] Open DevTools → Network → find the request that returns the filing list. **You found it:** `/api/corporate-bussiness-sustainabilitiy?index=equities&symbol=…`
- [x] Work out why only the latest filing came back: NSE's page defaults to the **last 365 days**; older years need `from_date` / `to_date` (DD-MM-YYYY) ✅ (read from NSE's own page script)
- [x] Prove a Python script can reach it politely (home page cookies → API → file download) ✅
- [x] Download & inspect XBRL: Tata Steel FY22-23 → FY25-26, Infosys FY21-22 + FY23-24, HDFC Bank FY23-24 (10 files in `data/raw/`) ✅
- [x] Compare tag names/units across the **four taxonomy releases** (2021-09-30 legacy; 2024-04-30, 2025-05-31, 2026-02-28 modern) ✅
- [x] Cross-check XBRL numbers against the PDF ✅ match, with traps found
- [x] Revised filings ✅ (a revision replaces the original row), boundary ✅ (`ReportingBoundary`, can change between years), company search endpoint ✅
- [x] Record everything in `context.md` §4a-4e ✅
- **You'll learn:** HTTP requests, headers/cookies, JSON, XML structure, what an XBRL "fact/context/unit" is.
- **Decision gate:** XBRL path or PDF path? → **XBRL** ✅
- **Done when:** findings are written down and ≥ 3 real filings are in `data/raw/`. ✅ (10 XML + 1 PDF)

### Phase 2: Data model + the SEBI template as data (~2 h)  ✅ DONE (together with the core of Phase 4, at your request)
**Why:** Decide *what shape the data has* before rendering, so the SEBI view and the dashboard both read the same clean data.
- [x] `models.py`: `Cell` (value + unit + status + as_filed + note + warnings), `Metric`, `ListTable`, `Facility`, `Assurance`, `Principle6Report`; `Status` = reported / not_reported / calculated / converted
- [x] `sebi_template.py`: all 12 Essential + 9 Leadership questions of the May 2021 form, official wording and row labels, as data
- [x] `errors.py` gained `UnparseableFiling`
- [x] Newer-format filings vs the 2021 template (D4/D13/D14/D19): the 2021 layout is rendered; rows that modern XBRL splits are CALCULATED; extras live in `report.extras`
- [x] Check whether the filings contain a **turnover** figure (needed to compute a fallback intensity) → **answered (Phase 12 audit): yes**, a `Turnover` tag is in all 21 downloaded filings (newer ones also `RevenueFromOperations` / `TotalRevenueOfTheCompany`). It is **not used yet**: a calculated fallback intensity for the doubtful filed ones is an optional improvement, see `context.md` §4e
- **You'll learn:** `dataclass`, `Enum`, type hints, custom exceptions, "data instead of code" (the template).
- **Done when:** a Principle6Report can be built from any downloaded filing and printed. ✅ `python extract_report.py --company Reliance --fy 2023-24`

### Phase 3: Fetch and cache (~3 h)  ✅ DONE (built early, at your request: "one script in the project that downloads any company")
**Why:** Getting the file reliably *and politely* is the foundation for all later phases. You asked for a real project script (not my throwaway probes) so that any company can be downloaded on demand, e.g. in the interview.
- [x] `python download_filings.py --company <name or symbol> [--fy 2023-24] [--with-pdf] [--refresh]` (one command, all years by default)
- [x] `fiscal_year.py`: accepts `2023-24`, `2023-2024`, `FY2023-24`, `2023/24`; **rejects earlier than FY 2021-22 with a clear message** before any network call
- [x] `company_lookup.py`: text → NSE symbol via `/api/smart-search/eqEtf?q=` (equities only, exact symbol wins, prefer `EQ` series; several companies → `AmbiguousCompany` lists up to 10; none → `UnknownCompany`); results cached in `data/cache/company_search.json`
- [x] `nse_client.py`: one polite HTTP layer (session + cookie warm-up, **≥ 3 s between requests**, timeouts, retries only for timeouts/5xx with growing pauses, **403/429 → stop**, 404 → only that file missing, HTML block pages never saved)
- [x] `filings.py`: listing with `from_date`/`to_date` (no `issuer`), file URLs only from the JSON, `/null` PDF links ignored, one row per FY (latest revision wins), listing cached 24 h in `data/raw/<SYMBOL>/filings_index.json`
- [x] `downloader.py`: files under `data/raw/<SYMBOL>/<FY>/` + `filing.json` note; reuses anything already on disk (also **hand-downloaded files**, as the assignment allows); reports missing years
- [x] Specific errors: `UnknownCompany`, `AmbiguousCompany`, `UnsupportedYear`, `InvalidFiscalYear`, `NoFilingFound`, `NSEUnavailable`, `FileNotAvailable`
- [x] Tests: 72 offline tests pass (fake NSE; no internet needed)
- [x] **Live proof:** Reliance (4 filings, 20 s), re-run = 0 requests; HDFC Bank FY22-23 + PDF; `M&M`; Sakuma Exports (no BRSR); 6 error cases
- [x] The main report command calls this same code (`pipeline.load_report`, Phase 5)
- [ ] *(left open on purpose)* Minimal headers/cookies are not stripped down: only worth doing if NSE changes its requirements
- **You'll learn:** `requests`, `pathlib`, exceptions, `dataclass`, `time.sleep`, caching, dependency injection for tests.
- **Done when:** `python download_filings.py --company Reliance` downloads the first time and a second run sends no request to NSE. ✅

### Phase 4: Parse → map → normalise (~5 h)  ✅ DONE (core built together with Phase 2)
**Why:** This decides the 25% "data accuracy" score. We went table by table, checking against real filings.
- [x] `xbrl_reader.py`: XML → facts; **illegal control characters removed in memory with a warning**; broken/non-BRSR file → `UnparseableFiling` naming file + line/column; tags looked up **ignoring case** (NSE spells `WithOutTreatment` and `WithoutTreatment`)
- [x] Current vs previous FY decided **from each context's end date**; `ReportingBoundary` read and carried into the report
- [x] Edition detection from the `in-capmkt` release date (**before 2024-04-30 = legacy**, else modern) (D19)
- [x] `p6_mapping.py`: every template row → tag(s) per edition. All questions covered: tables E1,E3,E5,E6,E8,L1,L2,L4; yes/no + text E2,E4,E7,E9,E12,L5,L7,L8; number L9; list tables E10,E11,L6; per-facility water blocks L3; assurance notes; 9 extras
- [x] `units.py`: GJ / kL / tonnes / tCO₂e; `MtCO2e` = `tCO2e` = metric tonnes; legacy free-text units understood; **monthly figures never turned into yearly**; unknown units shown as filed with a warning
- [x] Rows the 2021 template wants but modern XBRL splits (electricity, fuel, other sources) → **CALCULATED** with a plain-words note
- [x] `values.py`: Indian-grouped numbers (`1,83,595`), `NA`/blank → **not reported (never 0)**, Yes/No/true/NA cleaned
- [x] `checks.py` (warnings only, never changes a number): rounded-to-zero intensity, air-pollutant 0 caveat, totals that don't add up, emissions-vs-energy **scale check** (catches Tata Steel's "64" typed in millions; also Scope 3)
- [x] `report_io.py`: clean JSON in `data/parsed/<SYMBOL>/<FY>.json`; `report_text.py`: SEBI-style plain-text view; `extract_report.py`: one command
- [x] **Accuracy check:** Tata Steel FY25-26 compared to its PDF → regression tests (`tests/extraction/test_real_filings.py`); all 18 downloaded filings (5 companies, both editions) extract without crashing
- [x] 160 automated tests pass (no internet needed; real-filing tests skip if data is absent)
- [x] ~~Later refinement: **inferring a legacy energy unit** from the next year's filing~~ → **decided against** (D66, Phase 8): units are never inferred, they are shown as filed and marked
- **You'll learn:** XML parsing, dictionaries/lists, functions, unit tests.
- **Done when:** filings parse cleanly and spot-checked numbers match the PDFs. ✅

### Phase 5: SEBI-format HTML view (~3 h)  ✅ DONE
**Why:** 15% of the grade. A reviewer holds it next to the template and expects a 1-to-1 match.
- [x] Jinja2 templates with one small macro per table type (value table with/without Unit column, list table, notes, cell) in `brsr_p6/rendering/templates/sebi.html`; page shell with header facts, legend and **CSS-only tabs** in `base.html`; all styling inline in `style.css` (no JavaScript, no internet needed)
- [x] `sebi_view.py`: all decisions in Python (footnote numbers, "Not reported" text, which unit goes where) so the template only prints
- [x] Same numbering, wording, row labels and **column layout as SEBI's form** (Unit column only in E5, E6, L4 as in the official tables); "Not reported" never blank; the assurance note under each table; every converted/calculated value labelled (`calc.` / `conv.`) and every doubtful value marked with ⚠ + a note
- [x] Indian digit grouping (`2,47,98,900`), tiny numbers as 4.6×10⁻⁶ (`formatting.py`)
- [x] Extras (PPP, physical-output intensities) in their own clearly-labelled block, not mixed into SEBI's tables
- [x] `main.py --company X --fy Y [--open]` now writes `output/<SYMBOL>_<FY>.html` (the dashboard tab is a placeholder until Phase 6)
- [x] Checked in a real browser engine (headless Edge screenshots) on desktop and phone width; fixed number alignment, phone table layout, a duplicated remark
- [x] Tests: 200 pass (`test_sebi_view`, `test_render`, `test_formatting`): every official question text and row label appears in the page **in SEBI's order**; HTML is well-formed for all 18 downloaded filings; filing text cannot inject HTML
- **You'll learn:** Jinja2 templating, HTML tables, basic CSS (variables, media queries, CSS-only tabs), the "view-model" idea.
- **Done when:** side by side with the official PDF, every question/row is present in the same order. ✅

### Phase 6: Dashboard view (~7 h)  ✅ DONE (6.7, the plain-language test with a non-technical person, is yours to do)  ⭐ biggest grade (30%)
**Why:** "A non-expert understands each metric, its direction and its significance without reading the SEBI template."

**Design is DONE and waiting for approval:** open `design/dashboard_mockup.html` (a hand-written page using the real Reliance FY 2023-24 numbers; it also shows how doubtful / missing / unit-less data look). The decisions behind it are D37-D46 in `context.md`.

**The reader** is a non-expert (investor, student, journalist, citizen). They ask four questions, and the page is ordered to answer them:
1. *How big is the footprint?* (big numbers in plain units)  2. *Better or worse than last year?* (verdict chip + arrow + words)  3. *Is it under control?* (renewable share, recovery share, safeguards, outside audit)  4. *Can I trust the numbers?* (data badges, warnings, "Can I trust these numbers?" panel)

**Page order (top to bottom):** header → jump menu → **At a glance** (one plain sentence, scoreboard "5 improved / 4 same / 4 worse", six topic tiles) → **Energy → Climate → Water → Air → Waste → Nature & safeguards** (story: power used → gases released → water → air → rubbish → rules in place) → **Can I trust these numbers?** → glossary. Each topic = plain intro + rule-generated headline + 2-3 big cards + a "where does it go" bar + fine print.

**Card anatomy:** plain title + "Lower/Higher is better" label · big number in friendly units (lakh/crore) · verdict chip (✔ Improved / ✖ Got worse / ≈ About the same / ? Can't compare) + ▲▼ + % · this-year vs last-year bars from zero · *What it is* + *Why it matters* (always visible) · "Fine print" (as-filed number, how we calculated, SEBI row) · data badge (✔ reported / ∑ added up by us / ⇄ unit changed / ⚠ check / ∅ not reported).

- [x] **6.0 Data readiness** (found while designing; small, done first)
  - [x] `units.py`: add exact SI multiples that real filings use: Megajoule (×0.001), Terajoule (×1000), Petajoule, Kilojoule; `ktCO2e` (×1000). Today ITC and Wipro energy shows "not one I can convert". They become GJ with a `conv.` mark, the filed number stays in `as_filed`. Tests for each.
  - [x] `warning_kinds.py`: one small table that sorts every known warning into **doubtful** (value probably wrong: scale, rows don't add up) / **check** (unit not stated, monthly, unit label unreliable, zero may mean "not measured") . **Guard test:** every warning found in all downloaded filings is classified, so a new warning text can never slip through unnoticed.
  - [x] Regenerate every `data/parsed/*.json` (one was stale: it predated the double-count fix)
- [x] **6.1 `metric_info.py`** (data, not code): per card: id, plain title, what it is, why it matters, direction (lower / higher / context-only), size-caveat flag, source keys, unit style, topic, "headline?" flag (counts in the scoreboard)
- [x] **6.2 `friendly.py`**: lakh/crore numbers; intensity per ₹ crore (×10⁷, labelled as converted, as-filed kept); % change and percentage-point change; "about the same" bands (±1% for amounts, ±0.5 pt for shares); zero and previous-year-zero cases. Unit tests for every rule.
- [x] **6.3 `dashboard_view.py`** (the view-model, like `sebi_view.py`; templates only print): `CardView`, `StackView`, `SafeguardView`, `TopicView`, `GlanceView`, `TrustView`. Rules: verdict from direction + change; derived metrics (Scope 1+2, renewable share, recovered share) marked *calculated* and inheriting warnings; **doubtful ⇒ no verdict, kept out of headlines**; not reported ⇒ "Not reported", never 0, never an arrow; headline sentences built only from trustworthy numbers
- [x] **6.4 Templates + CSS**: `dashboard.html` (macros card / mini / stack / safeguard), dashboard CSS added to `style.css`, inline-SVG icon set, **Dashboard becomes the first and default tab**, SEBI tab second
- [x] **6.5 Tests**: verdict rules; "never invent" (missing stays missing); doubtful cases; every card has name + what + why + direction; all 18 filings render well-formed HTML; filing text is escaped; golden check that the Reliance numbers equal the mockup's
- [x] **6.6 Look at it**: headless-Edge screenshots, desktop and 375 px phone, for Reliance (clean), Tata Steel (doubtful scale), HDFC Bank (old layout, unit-less, sparse), Wipro (TJ/MJ units), Infosys FY21-22 (monthly air figures); fix what looks wrong
- [ ] **6.7 Plain-language test**: show it to a non-technical person for 2 minutes; if they cannot explain a section back, rewrite that section's words
- [x] **6.8 Docs**: `learnings.md` (Phase 6 + interview questions), `commands.md` (Dashboard tab is real now), `context.md` decisions, README dashboard section
- **You'll learn:** designing for a reader, HTML/CSS layout (grid, flex, sticky nav), inline SVG icons, `<details>` without JavaScript, view-models with rules.
- **Done when:** a non-technical friend can explain each section back to you after 2 minutes, **and** the awkward companies (Tata Steel, HDFC Bank, Wipro) show honest warnings instead of silent nonsense.

**Ideas noted, NOT in Phase 6 (verify first):** a water-balance check ("consumption = withdrawal − discharge") would flag Reliance, which files consumption = withdrawal while also reporting 3.46 crore kL of discharge. Confirm the definition in SEBI's guidance note before adding a warning. Leadership-only items (renewable split, Scope 3, discharge) are optional for companies, so "Not reported" there is normal and the page says so.

### Phase 7: Glue, error handling, samples, README v1 (~3 h)  ✅ DONE  🏁 MILESTONE 1: CORE COMPLETE
- [x] `main.py --company "Tata Steel" --fy 2023-24` → one HTML file with two tabs (CSS-only): **done in Phase 5**; the Dashboard tab gets its content in Phase 6
- [x] The same command must also write a **page** (not just a console message) for errors (unknown company, FY not on NSE, bad file...) so the message is shown on a page
- [x] Specific on-page messages for: unknown company, year before 2021-22, no filing for that year, unparseable filing, NSE unreachable
- [x] Generate **≥ 2 sample outputs** (plan: one heavy-industry, one IT/services, ideally one with sparse data) into `samples/` and commit them (generated with `python make_samples.py`: 5 companies + 4 error pages; committed in Phase 11)
- [x] README v1: setup, run commands, inputs to try, approach, limitations; **design note** (half a page)
- **Done when:** a fresh clone + `pip install -r requirements.txt` + one command produces the page. ✅ proven in a fresh venv (context.md D58)

> Everything below is **optional**, attempted strictly **in this order**, and only after Milestone 1 is solid.

### Phase 8: Extension 1, multi-year trends (~3 h)  ✅ DONE
- [x] Input: company, start FY, end FY. One listing call gives all years; then fetch each year's XML (cache + delay)
- [x] Per year show the **reporting boundary** and **flag boundary changes** (Tata Steel: Consolidated in FY22-23 → Standalone from FY23-24) and **restatements** (a later filing's previous-year column differs from the earlier filing's value)
- [x] Table/sparkline per metric across years; **missing years flagged, never skipped or zero-filled**
- [x] Check units are consistent across years; note when a later filing *restated* an earlier year
- [x] Specific errors: missing report, unparseable filing, unknown company

### Phase 9: Extension 2, year-on-year summary (~3 h)  ✅ DONE
- [x] Input: company; the latest FY is chosen automatically (`--fy` is optional). Only the latest year and the year before are downloaded
- [x] State clearly how we define "better": against the company's own last year, a direction per figure, under 1% (a share: under 0.5 point) = "about the same"; the page prints the definition
- [x] Rank metrics by direction-adjusted change (percent for amounts, **percentage points for shares**); show **3 best + 3 worst** with a plain-English explanation each
- [x] Prefer intensity metrics for fairness: a per-sales figure is ranked **instead of its total**, the total is quoted as context; exclude missing, doubtful, other-unit and zero-base figures **and list them with the reason**
- [x] Handle a missing previous-year report: the previous-year column of the latest filing is used and the page says why; last year's own filing, when readable, is only used to mark restated figures
- [x] Specific errors: missing report, unparseable filing, unknown company, each its own page with `summary.py` commands
- [x] Samples: 3 summary pages (Tata Steel, Wipro, Reliance FY 2022-23) + 1 summary error page; 472 tests

### Phase 10: Extension 3, company comparison (~3 h, only if time remains)
- [ ] Two companies, one FY, side by side; compare **intensity** metrics fairly; show the unit used; mark fields one company didn't report

### Phase 11: Final polish (~2-3 h)  (everything except the GitHub push and the optional screen recording is DONE)
- [x] README complete: setup, run, inputs to try, parts completed, extraction approach, limitations, **AI tools used and for what**, design note
- [x] Test from a clean checkout in a new venv; all tests pass (a real `git clone` into a new folder + new venv: 340 passed, 0 skipped; `make_samples.py` rebuilt every page byte-for-byte)
- [x] **Git (deferred from Phase 0):** git 2.55 installed, `git init -b main`, repository with 4 logical commits (108 files); steps are in `learnings.md` §5 and the Phase 11 section
- [ ] **Publish:** create an EMPTY repository on GitHub (public, or private + add the reviewers as collaborators), then `git remote add origin <url>` and `git push -u origin main`. *Needs the user's GitHub login, so the user runs it.*
- [x] Regenerate and commit samples
- [ ] Optional: 3-5 min screen recording
- [ ] **Interview prep:** for each module, write 2-3 lines "what it does and why". You must be able to explain every part.

### Phase 12: Restructure the package into layers (code quality, 10% of the grade)  ✅ DONE
*Asked for by the user: 39 modules lay in one flat folder; "downloading, parsing and generating HTML should each be a module". Done after the code of Extension 2 and before its notes were written, so those notes already describe the new layout.*
- [x] Plan from the real import graph (no cycles) and group the modules into nine packages: `core`, `download`, `parsing`, `extraction`, `analysis`, `views`, `rendering`, `workflows`, `cli`
- [x] Move with `git mv` (81 renames, history kept); rewrite imports with a script that reads the code structure; every package has an `__init__.py` that says what it is for
- [x] `core/paths.py`: the project root and every data folder in one place (it was in `downloader.py`, so "make HTML" depended on "download"); `cli.py` split into `main_cli.py` + `common.py`
- [x] Tests moved into folders that mirror the packages; shared helpers in `tests/helpers/`; the four tests that found `data/raw` from their own depth now use `core.paths`
- [x] `tests/test_architecture.py`: layer rule, no circular imports, no loose modules, test folders mirror packages
- [x] Proof: 472 tests pass, every entry point runs (also from another folder), `make_samples.py` changes no sample page
- [x] Notes brought up to date with the new layout and Phase 9: README, `commands.md` (with a "where is the code?" table), `context.md` D69-D77, `learnings.md` Phases 9 and 12
- [x] Fresh `git clone` in a short path: 472 passed, 0 skipped, `make_samples.py` changed nothing, `main.py` ran

### Phase 13: Trace every number back to the filing (the brief's own rule)  ✅ DONE
*The brief: "Never invent numbers. Every figure shown must trace back to a filing." Before this phase the page named the source file and flagged converted / calculated values, but an ordinary reported number did not say which XBRL element it came from, and the NSE link was not kept.*
- [x] `Origin` (element in the filing's own spelling, text as written, unit as written, year, number of rows added) on every `Cell`; a calculated figure lists every ingredient; a missing value remembers the elements looked for (`looked_for`)
- [x] The report keeps NSE's link to the XBRL file and the PDF (`source_url`, `pdf_url`; only `https` links are made clickable)
- [x] Where it shows: dashboard card Fine print ("Where it is in the filing"), a hover on every SEBI-tab number, a last section of the SEBI tab ("Where every number comes from": every row, both years, status, element and text as filed), the page header link, and `extract_report.py --trace`
- [x] **Proof:** `tests/extraction/test_origin.py` checks every value of every real filing on disk (21 on the author's PC: 4,605 values; the 11 committed ones: 2,178) against the raw XML with a regular expression independent of our reader
- [x] Samples regenerated; 529 tests; phone width checked
- [ ] *Not done (extensions kept aside):* the multi-year trend page shows each column's source filing but not an element per cell

### Phase 14: All pages in one place (`hub.py`)  ✅ DONE
*Asked for by the user: "in outputs there are separate html pages; I need them all in one page such that I can use a dropdown or search to get the page".*
- [x] `python hub.py [--dir output] [--link] [--open]` writes `index.html` for a folder: a search box, a dropdown grouped as Reports / Year-on-year summaries / Multi-year trends / Error pages, Previous / Next, "Open in a new tab"
- [x] Self-contained by default (every page embedded, so one file can be moved or sent); `--link` makes a small index that opens the files next to it. `make_samples.py` builds `samples/index.html` in link mode
- [x] Layers kept: `views/hub_view.py` (names, groups, safe data), `workflows/hub.py` (reads the folder), `rendering/templates/hub.html`, `cli/hub_cli.py`
- [x] Safe: the data sits in a JSON block with every `<` escaped; the frame is sandboxed (no scripts, no same-origin); labels are inserted as text; without JavaScript a list of links shows
- [x] Checked in a real browser (desktop and a 375 px frame): grouping, search, Enter, Esc, Previous / Next across three matches and at both ends, "no match", addresses `#id` and `?q=`
- [x] 35 new tests; 564 in all; samples regenerated
- [ ] *Not done:* the viewer is not refreshed automatically after `main.py` / `trends.py` / `summary.py`; run `python hub.py` again. Full-text search inside the pages is not offered (the search looks at the page's company, year and type)

### Phase 15: Evaluator audit before submission  ✅ DONE
*Asked for by the user: "check as an evaluator whether everything is as per the requirement".*
- [x] Clean install proof: fresh clone, brand-new venv, only `requests`, `Jinja2`, `pytest`: all tests pass
- [x] Four companies the tool was never built on, by name, lowercase name and symbol: all produce a page in about 11 s; the one-year, trend and summary pages work on them
- [x] The graded errors (unknown company, missing report, unparseable filing) on all three commands: each gives a specific message on the page; a corrupted filing is flagged inside a trend or summary page that can still be built
- [x] Numbers checked independently against the raw XML (water, waste, energy incl. a Terajoule conversion)
- [x] **Fix:** an intensity filed with one digit of precision is "too coarse to compare" (D84); found on ICICI Bank, present in the HDFC sample
- [ ] *Open, needs a decision:* the dashboard's topic tiles and scoreboard follow the totals, the summary page the per-sales figure. See `context.md` Phase 15
- [ ] *Not built:* Extension 3 (company comparison). Nothing of it is half-finished
---

## 6. Milestones

| Milestone | After phase | Meaning |
|---|---|---|
| M0: We know the data | 1 | Source and format settled; real filings in hand |
| M1: **Core task complete** | 7 | Company + FY → HTML with SEBI view and dashboard. *This alone can score well.* |
| M2: Trends | 8 | Extension 1 |
| M3: YoY summary | 9 | Extension 2 |
| M4: Submission-ready | 11 | README, samples, tests, GitHub |

## 7. Risks and fallbacks

| Risk | Fallback |
|---|---|
| NSE blocks scripted requests | Hand-download filings into `data/raw/`, code reads from there; document in README |
| XBRL tags differ between FY 2021-22 and later years | Keep mapping per taxonomy version; start with one year, then extend |
| 2021 template ≠ newer filing format | Render the 2021 layout as the assignment demands; show extra items from newer filings in a clearly labelled "additional disclosures" box (decide in Phase 2) |
| Units differ (GJ/MWh, kL/m³, tonnes) | `units.py` + always show original and normalised unit |
| Multiple / revised filings per year | One written selection rule, shown on the page |
| Tiny intensity numbers (per ₹) look unreadable | Display per ₹ crore / ₹ million, state the conversion, mark `CONVERTED` |
| Running out of time | Stop after M1, then do extensions in order. Never half-finish an extension |

## 8. How we will work (so you actually learn)

For **every** phase:
1. I explain the concept and *why* in plain language (no code yet).
2. We write code in **small pieces**; I add comments and explain each piece.
3. You run it and see the output.
4. You explain it back to me in your own words ("interview check").
5. We tick the boxes here and update the progress log in `context.md`.

## 9. Decisions I need from you before starting (my recommendation first)

1. **Stack:** Python + CLI + static HTML via Jinja2 (recommended) vs. a small Flask web app.
2. **Template version:** follow the **May 2021** template exactly, as the brief says, and add an "additional disclosures" box for newer-format items (recommended).
3. **Deadline reading:** the brief says "48 hours" *and* "submit within 3-5 days". I plan to finish the core within 48 h and use the remaining time for extensions and polish. Is that right, or has your recruiter clarified it?
4. **Sample companies:** suggest Tata Steel (heavy industry, rich data), Infosys (IT services, different profile), plus one bank/NBFC (sparse environmental data, good for "not reported" handling). OK?
5. **GitHub:** do you already have an account/repo ready, or should Phase 0 also cover creating one?
