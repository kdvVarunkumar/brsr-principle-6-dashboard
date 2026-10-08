# Demo and interview guide

For the person presenting. Plain language, in the order you would speak. It follows the assignment's scoring, so the most valuable things come first.
Everything here is true of the code as it is today (692 tests pass). Where a number can change, the command to re-check it is given.

---

## 0. Are we complete?

**The core task: yes.** Input a company and a financial year; one HTML page comes out with two views: the plain-English **Dashboard** (opens first) and the **SEBI-format report** (second tab). Beyond the core, all three extensions are built too, and you said to set them aside for now: say "also built, happy to show them" and move on.

What is still *yours* to do (nobody else can): create the GitHub repo and push (`git remote add origin <url>`, `git push -u origin main`), optionally record the 3-5 minute video, and show the dashboard to one non-technical person for two minutes.

---

## 1. The 60-second opening (say this first)

> "The tool takes a listed Indian company and a financial year, and produces one HTML page with that company's BRSR Principle 6 (environment) disclosures twice: exactly as SEBI's template lays them out, and as a dashboard a non-expert can understand.
> It uses only public data: NSE publishes each company's filing as a structured XBRL file, so I read that instead of parsing PDF tables. The pipeline is: **find the company -> download its filing politely -> read the XML -> map every value to SEBI's template rows -> clean and check it -> decide what to say -> print the HTML.**
> Three rules run through everything: *never invent a number*, *show doubt instead of hiding it*, and *separate the code that extracts data from the code that presents it*."

If you remember only one sentence: **"Python decides, the template only prints."**

---

## 2. The scoring, and where each point is earned

| Area | Weight | What to show | Where in the code |
|---|---|---|---|
| Dashboard clarity | **30%** | Open the page; walk the summary, the topic tiles, one topic card (what it is, which way is better, why it matters), the "Can I trust this?" section and the glossary | `views/dashboard_view`, `dashboard_cards`, `metric_info`; `templates/dashboard.html` |
| Data accuracy | **25%** | Doubtful figure shown as filed with a warning; "Not reported" never 0; the trace of one number back to the filing | `extraction/`, `core/units`, `views/trace_view` |
| SEBI fidelity | **15%** | Hold the SEBI tab beside the template: same question numbers (E1-E12, L1-L9), row labels, units, both year columns | `core/sebi_template`, `views/sebi_view`, `templates/sebi.html` |
| Error handling | **10%** | Unknown company, a year before BRSR began, a missing filing: each gives a specific page | `core/errors`, `views/error_view`, `cli/common` |
| Code quality | **10%** | Layered packages, extraction separate from presentation, the architecture test, 692 tests | the whole `brsr_p6/` tree, `tests/` |
| Extensions | **10%** | Trends, year-on-year, comparison, the two viewer pages (only if asked) | `trend_*`, `summary_*`, `compare_*`, `hub_*` |

So the demo order is: **dashboard -> accuracy -> SEBI tab -> errors -> code -> extensions.** Do not start with code.

---

## 3. The whole flow in one picture

```
 python main.py --company "Tata Steel" --fy 2025-26
        |
        v
 [cli]        main.py -> cli/main_cli          read what was typed; on failure write an error page
        |
        v
 [workflows]  workflows/pipeline               the order of the steps (the "manager")
        |
        v
 [download]   company_lookup -> filings -> downloader / nse_client
        |        "Tata Steel" -> TATASTEEL -> which filing for FY 2025-26 -> the XBRL file saved in data/raw/
        v
 [parsing]    xbrl_reader + p6_mapping          the XML -> plain facts (element, value, unit, period)
        |
        v
 [extraction] extractor + values + checks       facts -> a Principle6Report: every SEBI row, current and previous year,
        |        (uses core/sebi_template, core/units)   units made consistent, doubtful values flagged, origin of every number kept
        v
 [views]      sebi_view, dashboard_view, trace_view     decide every number, word and verdict (no HTML here)
        |
        v
 [rendering]  render + templates (Jinja2)       print: ONE html page, two tabs, no JavaScript
        |
        v
 output/TATASTEEL_2025-26.html
```

The layers are ordered `core -> download -> parsing -> extraction -> analysis -> views -> rendering -> workflows -> cli`. **A package may import only from itself and from packages earlier in that list.** `tests/test_architecture.py` fails the build if anyone breaks this. That is your answer to "how is it organised?"

---

## 4. "Why are there so many .py files in the root folder?"

They are **launchers, not modules.** Each one is about 10 lines: it imports `main` from the package and runs it. All the real code is inside `brsr_p6/`, in nine packages.

| Root file | What it is for | Calls |
|---|---|---|
| `main.py` | **the core command**: one company, one year -> the report page | `cli/main_cli` |
| `download_filings.py` | only download filings (no page) | `cli/download_cli` |
| `extract_report.py` | read one filing, print it as text, save the clean JSON (`--trace` shows where each number came from) | `cli/extract_cli` |
| `trends.py` | Extension 1: several years of one company | `cli/trend_cli` |
| `summary.py` | Extension 2: year-on-year best and worst | `cli/summary_cli` |
| `compare.py` | Extension 3: two companies, one year | `cli/compare_cli` |
| `hub.py` | the two viewer pages (home page, compare page) | `cli/hub_cli` |
| `make_samples.py` | rebuild the committed `samples/` | `workflows/samples` |

Why keep them in the root: the README, the assignment's "run commands" and the error pages all tell the reader to type `python main.py ...`. A reviewer cloning the repo should be able to do that without learning a package path. If someone asks "why not put them in a folder?": *"They are the user-facing commands. Moving them would change every documented command for no gain; the logic is already in packages, and a test enforces the layering."*

Honest alternative if pushed: they could live in a `scripts/` folder or be replaced by `python -m brsr_p6 main ...`. It is a taste choice, not a correctness one.

---

## 5. Suggested demo script (about 10 minutes)

| Min | Do | Say |
|---|---|---|
| 0-1 | Show the folder; open `README.md` top | The 60-second opening in section 1 |
| 1-2 | `python main.py --company "Tata Steel" --fy 2025-26 --open` | "One command, one page. It took about ten seconds; the second run is instant because filings are cached." |
| 2-6 | **Dashboard** (30%): the one-sentence summary and scoreboard -> a topic tile -> one card -> "Can I trust this?" -> glossary | See section 6, stage 7. Point out: *which direction is better*, *why it matters*, units, "better than its own last year" only |
| 6-7 | Show the doubtful figure (Tata Steel's Scope 1) and a "Not reported" row | "Shown exactly as filed, amber, with no verdict. I never silently fix a number." |
| 7-8 | **SEBI tab** next to the SEBI template; last section "Where every number comes from" | "Same numbering E1..E12 and L1..L9, same row labels, current and previous year. Every row traces to an XBRL element." |
| 8-9 | Errors: `python main.py --company "Xyzzy Quux" --fy 2023-24 --open`, then `--fy 2019-20` | "Specific message, what to try next, no stack trace." |
| 9-10 | `pytest -q`; show `brsr_p6/` tree and `tests/test_architecture.py` | "Extraction is separate from presentation; a test enforces it." |
| if asked | `python hub.py --open` | Home page (choose a company), Compare button. Extensions |

Have these ready in a terminal: `commands.md` has every command and the one-line answers.

---

## 6. Stage by stage: what to say, the file to open, and likely questions

### Stage 1: Setup and structure

**Say:** Python, three libraries (Requests for HTTP, lxml for XML, Jinja2 for HTML). `pip install -r requirements.txt`, then run. Nine layered packages; root files are launchers. Notes: `plan.md`, `context.md` (every decision, D1...), `learnings.md`.
**Open:** `README.md` (setup, inputs to try, what is complete, limitations, AI tools), the folder tree.

| Likely question | Answer |
|---|---|
| Why Python? | Good HTTP/XML/HTML libraries, readable, and the assignment allows any stack. |
| Why only three dependencies? | "Keep dependencies reasonable." Each does one thing I would not write myself. The rest is the standard library. |
| How do I run it from a clean checkout? | Clone, create a venv, `pip install -r requirements.txt`, `python main.py --company "Tata Steel" --fy 2025-26 --open`. I tested exactly that in a fresh clone with a new venv. |
| How is the project organised? | Nine packages in a strict order (section 3); a test fails if a package imports from a later one. |
| Why a database-free design? | Files are enough: raw filings, a cache of NSE's lists, and a clean JSON per report. Nothing needs querying. |

### Stage 2: Finding the company and the filing (`download/company_lookup`, `filings`)

**Say:** The user types a name or symbol. I ask NSE's own search, get the symbol, then ask for that company's BRSR filing list and choose the filing for the requested year. The year can be typed as `2023-24`, `FY2023-24` and similar; it is checked **before** any request to NSE.
**Open:** `download/company_lookup.py`, `download/filings.py`, `core/fiscal_year.py`.

| Likely question | Answer |
|---|---|
| How do you handle a name like "Tata"? | NSE returns several matches; I raise `AmbiguousCompany` and the page lists them. A name NSE does not know is `UnknownCompany`. |
| What if a year is before 2021-22? | `UnsupportedYear`: the page says BRSR filings in scope start with FY 2021-22 and explains. It never fails silently (the brief asks for this). |
| What if the company filed no BRSR that year? | `NoFilingFound` with the years NSE does have, so the user can pick one. |
| What if the company filed a revised version? | NSE gives one row per company per year and a revision replaces the original, so I use what NSE currently lists. This is the stated rule. |
| Is it hard-coded to some companies? | No. Any NSE-listed company with a BRSR filing works. I tested on companies not used during development (NTPC, HUL, ICICI Bank, L&T). |

### Stage 3: Downloading politely (`download/nse_client`, `downloader`)

**Say:** NSE's site loads data with background requests and wants browser-like headers and cookies, so I first open the home page to get cookies, then call the same JSON endpoint the website uses. Requests are **at least 3 seconds apart**, and everything is **cached**: the list of filings under `data/cache/`, the filing files under `data/raw/<SYMBOL>/<FY>/` with a small `filing.json`. A second run for the same filing makes no download.
**Open:** `download/nse_client.py`, then show `data/raw/`.

| Likely question | Answer |
|---|---|
| How did you find the endpoint? | Browser developer tools, Network tab, on NSE's BRSR page: the page calls `/api/corporate-bussiness-sustainabilitiy` after a cookie-setting home-page request. |
| How do you avoid hammering NSE? | A fixed delay between requests, a cache of lists and files, and the downloader skips anything already on disk. |
| What if NSE is down or blocks you? | `NSEUnavailable` with a specific message. If a filing list saved earlier (older than 24 hours) is on disk and NSE cannot be reached, that saved list is used instead of failing, and a notice is printed. Filings are also committed for a few companies so the demo works offline. |
| Why XBRL and not the PDF? | The filing comes in both; XBRL is structured (named elements, units, periods), so values are exact. Parsing PDF tables is fragile. The brief's hint says the same. |
| Are the raw filings in the repo? | A small set (listed in `data/README.md`, documented as the brief allows) so tests and samples work without internet. Everything else is downloaded on demand. |

### Stage 4: Reading the XML (`parsing/xbrl_reader`, `p6_mapping`)

**Say:** An XBRL file is a list of *facts*: an element name (for example `TotalScope1Emissions`), a value, a unit and a period. I read them into plain Python objects. SEBI's form has had **five editions** (two older "legacy" ones, three "modern"), with different element names, so `p6_mapping` says which element feeds which SEBI row for each family. The current and previous year are decided from each fact's **period end date**, not from guessed labels.
**Open:** `parsing/xbrl_reader.py`, `parsing/p6_mapping.py`.

| Likely question | Answer |
|---|---|
| What is XBRL? | An XML format for financial and sustainability reports where every number has a name, a unit and a period, so software can read it reliably. |
| How do you know which year a number belongs to? | Each fact has a context with start and end dates; I match them to the financial year asked for (current) and the year before (previous). |
| What messy things did you find? | Numbers stored as text with Indian grouping ("1,87,82,249"); an XML file with illegal control characters; element names spelled differently across editions (matched case-insensitively); older filings with no unit on energy; air-pollutant units written as free text. Each is handled and tested. |
| What if the file is damaged? | `UnparseableFiling` with the specific reason; for trends, that one year becomes a flagged column and the others still show. |
| Why five editions matter? | The same question has different element names in 2021 and 2025. Without the mapping per edition, half the companies would show "Not reported" wrongly. |

### Stage 5: Mapping to SEBI's template and cleaning (`extraction/`, `core/sebi_template`, `core/units`)

**Say:** `core/sebi_template.py` holds Principle 6 as data: 12 Essential questions and 9 Leadership questions, with SEBI's own row labels and units. The extractor fills every row for the current and previous year into a `Principle6Report`. Each value is a `Cell`: the number, its unit, **where it came from** (element and text as filed), and flags. A value we add up or convert is marked "calc." or "conv."; a value not in the filing is "Not reported", never 0.
**Open:** `core/sebi_template.py`, `core/models.py`, `extraction/extractor.py`, `core/units.py`.

| Likely question | Answer |
|---|---|
| How do you handle different units? | `core/units` converts to one unit per measure (energy to gigajoules from terajoules, petajoules and megajoules; water to kilolitres; emissions to tonnes of CO2e; intensities to "per ₹") and the page says "unit changed by us". The value as filed is kept in the saved JSON. |
| Why show "Not reported" instead of 0? | A zero would claim the company measured and found none. If the filing has nothing, the honest statement is that nothing was reported. |
| What does "calc." mean? | We added reported numbers together (for example total energy from its parts). It is labelled so the reader knows it was not a filed total. |
| How do you know the number is really from the filing? | `tests/extraction/test_origin.py` opens every real filing on disk and checks, with a plain regular expression on the raw XML (independent of my reader), that each value shown exists with exactly that text. A value without a trace fails the test. |
| What if SEBI changes the form? | Add the new element names to `p6_mapping`; the template and views do not change. |

### Stage 6: Checks and warnings (`extraction/checks`)

**Say:** Filings contain mistakes. I do not fix them silently; I **flag them and show the value as filed.** Examples the checks catch: Tata Steel typed its Scope 1/2/3 emissions in *millions* (64) while the unit said tonnes, found by comparing emissions to energy; intensities rounded to zero; totals that do not equal their parts; an intensity filed with one digit of precision (too coarse to compare).
**Open:** `extraction/checks.py`, then the amber figure on the page.

| Likely question | Answer |
|---|---|
| Why not just correct Tata Steel's figure? | I cannot be sure what the company meant. "Never invent numbers": show it as filed, warn, give no verdict, and leave it out of summary sentences. |
| How do you detect a wrong figure? | Rules: emission scale against energy, zero intensities, parts not adding to the total, air figures of zero. Each rule is a small function with tests. |
| What can you NOT detect? | An error of a few percent, or a wrong figure that still looks plausible. This is in the README's limitations. |
| What is the "Can I trust this?" section? | The same warnings in plain English, per topic, so a reader sees what is doubtful and why. |

### Stage 7: Deciding what to say (`views/`, `analysis/comparison`) and the dashboard (30%)

**Say:** Views turn the clean data into plain objects: sentences, numbers, flags, verdicts. They contain **no HTML**. The dashboard is built for an investor, journalist or student who has never read a BRSR, and answers four questions in order: *How big is the footprint? Better or worse than last year? Under control? Can I trust the numbers?*
**Open:** `views/dashboard_view.py`, `views/metric_info.py` (all the wording lives here, as data), `analysis/comparison.py` (the "better/worse" rule), then the page.

What makes it clear (point at these live):
1. **One sentence first**, then a scoreboard ("1 improved, 4 about the same, 6 got worse").
2. **Six topics in story order**: energy, climate (greenhouse gases), water, air, waste, safeguards.
3. **Every figure explains itself**: a plain title, *what it measures*, *which way is better*, *why it matters*, units. The exact figure and the calculation are in fine print.
4. **Intensity beside the total**: "per ₹ 1 crore of sales", because a growing company uses more in total.
5. **Indian number words** (lakh, crore) matching the SEBI tab's digit grouping.
6. **Never colour alone**: words and symbols (✔ ✖ ≈ ?) so it is readable in black and white and by colour-blind readers; it also works on a phone.
7. **"Better" means better than the company's own last year**, nothing else.

| Likely question | Answer |
|---|---|
| How do you decide "better" or "worse"? | Each figure has a direction (lower is better for energy, emissions, water and waste per rupee of sales; higher is better for the renewable-energy share and the recycled-waste share). I compare this year with last year's figure from the same filing. A change under 1% (half a percentage point for a share) is "about the same". |
| Why not compare with an industry benchmark? | The filings contain none; inventing one would break "never invent numbers". The page says so. |
| Why "can't compare" for some figures? | A figure is not compared when it is missing, doubtful, in a different or unstated unit, or was zero last year (a percentage change cannot be worked out, and the zero probably means "not measured"). |
| Why are totals not used for the verdicts? | A larger company uses more in total. The topic tiles follow the totals today; the per-sales figure is shown next to each and is what the summary page ranks. (Known trade-off; I can explain the NTPC example.) |
| Who is the dashboard for? | A non-expert. I prototyped it first with real numbers (`design/dashboard_mockup.html`) and the design note is in the README. |
| How do you know a non-expert understands it? | Honest answer: I tested clarity by reading every sentence against the real data, and I intend to show it to one non-technical person. (If you have done the 2-minute test, say what they said.) |
| Why is the wording in a data file (`metric_info`)? | So the words can be reviewed and changed without touching logic, and each one is covered by a test. |

### Stage 8: Producing the page (`rendering/`, `templates/`)

**Say:** Jinja2 fills HTML templates with the objects the views produced. The page is **one file** with two tabs implemented in CSS only (radio buttons), so it has **no JavaScript**, opens offline and cannot be broken by a script. Dashboard first (the brief says clarity is the main thing), SEBI second. Text from filings is escaped, so a filing cannot inject HTML.
**Open:** `rendering/render.py`, `templates/base.html`, `dashboard.html`, `sebi.html`, `trace.html`.

| Likely question | Answer |
|---|---|
| Why no JavaScript? | It is not needed for a report, it makes the page safer and portable, and it opens from a file with no setup. Only the two viewer pages (the home page and compare page) use a small script, because a dropdown needs one. |
| Why Jinja2 and not building strings? | Templates keep layout out of the logic; autoescape protects against malicious text; designers can change the page without touching Python. |
| How does the SEBI tab match the template? | The question numbers, table shapes, row labels and units come from `core/sebi_template.py`, the same data the extractor fills. Same source, so they cannot drift apart. |
| How are the two views kept consistent? | Both are built from the same cleaned report object, so they always start from the same numbers. |
| Can I see where a number comes from? | Yes: hover on a SEBI number; the last section of the SEBI tab lists every number with its element and the text as filed; the header links to the filing on NSE; `extract_report.py --trace` prints it in the terminal. |

### Stage 9: Error handling (10%)

**Say:** Every known problem is its own error class in `core/errors.py` and gets its own explanation page with what happened, what to try, and a suggested command. A bug that is not one of ours also produces a page (and `--debug` shows the stack trace).

| Class | When |
|---|---|
| `InvalidFiscalYear` | the year is not a year ("abc") |
| `UnsupportedYear` | before FY 2021-22 |
| `InvalidYearRange` | trend range the wrong way round |
| `UnknownCompany` / `AmbiguousCompany` | NSE does not know it / several match |
| `NoFilingFound` | the company filed no BRSR for that year (lists the years it has) |
| `NSEUnavailable` | NSE unreachable or blocking |
| `UnparseableFiling` / `FileNotAvailable` | the XML is damaged / NSE lists it but the file is gone |
| `SameCompany` | comparison with the same company twice |

| Likely question | Answer |
|---|---|
| Show me an error. | `python main.py --company "Xyzzy Quux" --fy 2023-24 --open`, then `--fy 2019-20`. |
| Why a page, not just a terminal message? | The brief says errors should produce a clear message *on the page*, and a page is what a non-technical user sees. The terminal also prints the path. |
| What happens to one bad year in a trend? | It becomes a flagged column with its specific reason; the other years still show. Only a problem with the whole request gives an error page. |
| How do you test errors? | Every error class has a test, and the sample error pages in `samples/` are rebuilt and compared by a test, so they cannot go stale. |

### Stage 10: Tests and code quality (10%)

**Say:** About 690 tests, under a minute, no internet. They cover unit conversion, the XBRL reader, every SEBI row, the verdict and sentence rules, the HTML pages, the error pages and the command lines. Three tests are special: **architecture** (layering), **origin** (every number against the raw XML) and **samples up to date** (committed pages equal what the code builds today).

| Likely question | Answer |
|---|---|
| How is extraction separated from presentation? | Packages `parsing` and `extraction` know nothing about HTML; `views` decide; `rendering` prints. The import rule is enforced by a test. |
| Why so many tests? | Each rule on the page ("zero last year = can't compare", "unit unstated = no verdict") is a promise to the reader; a test keeps the promise when code changes. |
| What is the weakest part? | Be honest: a small error in a filing (a few percent) cannot be detected; PPP and per-tonne intensities are shown only in the SEBI tab because their unit labels are unreliable; tested in Edge on Windows. |
| What would you do with more time? | Add a benchmark only if a public source for it existed; test on more browsers; show the per-sales figure as the headline of each topic tile (instead of the total). |

### Stage 11: AI tools (the brief requires this, and "you must explain every part")

**Say:** I used Claude Code. The README table says for what: planning in phases, exploring NSE and the XBRL files, writing and testing the code, reorganising into layers, writing the docs. I read real output at every step and fixed what was wrong (double-counted energy, a mis-scaled emissions figure, false "got worse" claims).

| Likely question | Answer |
|---|---|
| What did the AI do and what did you do? | Be truthful about your part. The decisions are recorded in `context.md` (D1, D2...), and `learnings.md` explains each concept in plain words. Read the chapter for any part you are asked about. |
| Explain this function. | Open it and read it aloud in plain words. Every file has a short docstring at the top that says what it is for. |
| Did you check the AI's output? | Yes: tests, real filings, and the trace test that checks each number against the raw XML independently of our reader. |

### Stage 12: Extensions (only if asked)

One line each, then stop:
- **Trends** (`trends.py`): every metric, every year side by side; missing years flagged, never skipped or zero-filled; a change of reporting basis (standalone vs consolidated) never looks like an improvement.
- **Year-on-year** (`summary.py`): the three biggest improvements and setbacks, with the definition of "better"; a missing previous-year filing is handled (the previous-year column of the newer filing is used, and the page says why).
- **Comparison** (`compare.py`): totals shown but **never ranked** (a bigger company uses more); verdicts only on per-rupee figures and shares; one unit per row; "Not reported" says who; standalone vs consolidated warned.
- **Home and compare pages** (`hub.py`): pick a company and year, or press *Compare two companies*.

---

## 7. Hard questions that can come from anywhere

| Question | Answer |
|---|---|
| Walk me through the flow. | Section 3, left to right: command -> pipeline -> download -> parse -> extract and check -> views decide -> templates print -> one HTML file. |
| What is the single most important design decision? | Separating *what is true* (extraction) from *what to say* (views) from *how it looks* (templates). It is why every rule is testable without a browser. |
| What was the hardest data problem? | Messy filings: five form editions, units missing or wrong (Tata Steel's emissions in millions), numbers as text. The answer was to flag, not fix. |
| What if two numbers in a filing disagree? | A check warns and the page shows both as filed; the reader is told. |
| What would break if NSE changed its website? | Only `nse_client` and `filings`. Everything after the download reads local files. |
| How do you know it works for companies you did not test? | The mapping is by SEBI's element names, not by company, and I ran four never-used companies end to end plus corrupted-file cases. |
| What is NOT done? | Say it plainly: no benchmark (none exists in the filings); small errors undetectable; only Chromium tested. |
| Why should we trust the numbers? | Every number carries its origin; a test re-checks them against the raw XML; doubtful ones are shown as filed with a warning. |

---

## 8. Practice checklist (do this the day before)

- [ ] Say the 60-second opening out loud twice.
- [ ] Run the demo script in section 5 once end to end, with a timer.
- [ ] Open each file named in section 6 and read its top docstring aloud.
- [ ] Read `learnings.md` chapters for the stages you feel least sure about; their "Interview self-check" questions are at the end of each chapter.
- [ ] `pytest -q` passes; `git status` is clean; the README commands work in a fresh clone.
- [ ] Push to GitHub (your step) and open the repo page once to check the README renders and the `samples/` pages are there.
- [ ] Know the limitations list by heart (README, "Known limitations").
