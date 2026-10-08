# Commands cheat-sheet (for the demo)

Every command here was run and checked. Replace the company name and the year with whatever the interviewer asks for.
**Run all commands from the project folder**, in the **PyCharm Terminal** (it activates the project's environment, so you see `(.venv)` at the start of the line).

> **Project status:** download ✅ · clean/parse ✅ · SEBI-format HTML page ✅ · plain-English dashboard ✅ (opens first) · error pages ✅ · `samples/` ✅ · README ✅ · **several years side by side (`trends.py`, Extension 1) ✅** · **what got better / worse (`summary.py`, Extension 2) ✅** · code in nine layered packages ✅. Extension 3 (company comparison) is not built.

---

## 1. Quick reference

| I want to... | Command |
|---|---|
| **Make the report page** (does everything: download → clean → page) | `python main.py --company "Reliance" --fy 2023-24 --open` |
| Only **download** the filings | `python download_filings.py --company "Reliance"` |
| Only **clean/parse** and print the data | `python extract_report.py --company "Reliance" --fy 2023-24` |
| **Several years side by side** (Extension 1) | `python trends.py --company "Tata Steel" --from 2021-22 --to 2025-26 --open` |
| **What got better / worse since last year** (Extension 2) | `python summary.py --company "Tata Steel" --open` |
| Rebuild the pages in `samples/` | `python make_samples.py` |
| Run all automatic tests | `pytest -q` |

Pattern to remember: **`--company "<name or NSE symbol>"`** and **`--fy <year>`**, e.g. `--company "Tata Steel" --fy 2025-26`.

---

## 2. The commands in detail

### 2.1 Download from NSE: `download_filings.py`
Downloads a company's BRSR filing files (XBRL) into `data\raw\<SYMBOL>\<FY>\`. Anything already on disk is reused.

```powershell
python download_filings.py --company "Reliance"                       # every year NSE has (FY 2021-22 onwards)
python download_filings.py --company "Tata Steel" --fy 2023-24         # only one year
python download_filings.py --company "HDFC Bank" --fy 2022-23 --with-pdf   # also the PDF (optional)
python download_filings.py --company "Reliance" --refresh              # ignore the saved filing list, ask NSE again
```
| Option | Meaning |
|---|---|
| `--company` | company name or NSE symbol (required) |
| `--fy` | one financial year; leave out for all years |
| `--with-pdf` | also download the PDF (not needed for the report) |
| `--refresh` | ask NSE for the filing list again instead of using the saved one (valid 24 h) |

What you see: the company NSE matched, the years NSE has, one line per file (`downloaded` / `already on disk, skipped`), a summary, and **`Requests sent to NSE in this run: N`**.
Talking point: a second run sends **0 requests**.

### 2.2 Clean the data: `extract_report.py`
Reads the downloaded XML, fills SEBI's 21 Principle 6 questions, prints them as text and saves clean JSON in `data\parsed\<SYMBOL>\<FY>.json`. If the filing is not on disk yet, it downloads it first.

```powershell
python extract_report.py --company "Reliance" --fy 2023-24                    # whole report as text
python extract_report.py --company "TATASTEEL" --fy 2025-26 --questions E1,E6  # only some questions
python extract_report.py --company "Infosys" --fy 2021-22 --quiet              # only save the JSON
```
| Option | Meaning |
|---|---|
| `--questions E1,E6,L4` | print only those questions (`E1`-`E12` = Essential, `L1`-`L9` = Leadership) |
| `--quiet` | do not print, only save the JSON |

Marks in the printout: `c` = calculated by us · `k` = converted by us · `!` = doubtful (note below the table).

### 2.3 Make the page: `main.py`  ← the main one
```powershell
python main.py --company "Tata Steel" --fy 2025-26 --open
```
Downloads if needed, cleans, saves the JSON **and** writes one self-contained HTML page: **`output\<SYMBOL>_<FY>.html`**
(two tabs: the plain-English **Dashboard**, which opens first, and the **SEBI-format report**). `--open` opens it in your browser; without it, double-click the file.

| Option | Meaning |
|---|---|
| `--open` | open the page (or the error page) in your browser |
| `--output-dir samples` | write the page into another folder (default `output`) |
| `--debug` | on an *unexpected* problem, show the full Python traceback (normally you get an explanation page instead) |

**If something goes wrong, the same command still writes a page**: `output\error_<company>_<year>.html` (see section 6).

### 2.4 Several years side by side: `trends.py`  ← Extension 1
```powershell
python trends.py --company "Tata Steel" --from 2021-22 --to 2025-26 --open
python trends.py --company "Wipro" --from 2023-24 --to 2025-26          # the reporting basis flips between years
python trends.py --company "Reliance"                                   # no years given = FY 2021-22 up to the newest filing
```
| Option | Meaning |
|---|---|
| `--from` / `--to` | first and last financial year (optional; default FY 2021-22 up to the newest filing NSE has) |
| `--open`, `--output-dir`, `--debug` | the same as `main.py` |

Writes **`output\<SYMBOL>_trend_<from>_to_<to>.html`**: a column per year, the five topics with a mini bar per year and a trend verdict, then **every figure of SEBI's Principle 6
tables** year by year, then the figures later filings changed. Downloads the years it needs (3 s apart, cached); a company already downloaded takes about 3 seconds.

What to point at (2 minutes):
1. **The column headers:** each year says *Standalone* or *Consolidated*. A year NSE does not have (Tata Steel FY 2021-22) is shaded and says *"no filing on NSE; figures from the FY 2022-23 filing"*: real data from the next filing's previous-year column, never a zero.
2. **"Read this before comparing years":** the missing year, the change of basis, the older layout with no units, the restatements.
3. **The Trend column:** the verdict only compares years on the **same basis and unit**. Tata: *"▲ 14.3% higher than FY 2023-24 ... earlier years use another basis and are not included"*. Wipro: only the two consolidated years. Mis-scaled emissions: *"Can't compare"*.
4. **The marks:** ⟲ restated by the next filing (hover for the later figure), ⚠ a note or a doubtful figure, ≠ the next filing is on a different basis, u a different unit.
5. **"Every figure, year by year"** (collapsible per SEBI question) and **"Figures changed by a later filing"**.

If one year's filing is damaged, only that column is flagged. Errors give a page too: `--from 2025-26 --to 2021-22` ("That range of years cannot be used"), an unknown company, a year before FY 2021-22.

### 2.5 What got better and worse: `summary.py`  ← Extension 2
```powershell
python summary.py --company "Tata Steel" --open                  # newest year NSE has, against the year before
python summary.py --company "Wipro" --fy 2025-26                 # a named year
python summary.py --company "Reliance" --fy 2022-23              # NSE has no FY 2021-22 filing: the page says so and still works
```
| Option | Meaning |
|---|---|
| `--fy` | the year to summarise (optional; default = the newest filing NSE has, chosen automatically) |
| `--open`, `--output-dir`, `--debug` | the same as `main.py` |

Writes **`output\<SYMBOL>_summary_<FY>.html`**. Downloads only the two years it needs (3 s apart, cached); a company already downloaded needs no download at all and takes a second or two.

What to point at (2 minutes):
1. **The sentence and scoreboard on top:** *"We compared 8 figures for Tata Steel between FY 2024-25 and FY 2025-26: 1 improved, 3 stayed about the same and 4 got worse."*
2. **"How we decide what is better":** against the company's *own* last year only; the direction of each figure; under 1% (a share: under half a point) is "about the same"; amounts ranked by percent, shares by percentage points; per-₹-of-sales figure ranked instead of its total.
3. **The 3 improvements and 3 setbacks:** each has a headline, last year's and this year's number, "Lower is better here, so this is a step backwards", and the dashboard card. Tata: SOx +45.7%, NOx and PM +12.5%. Wipro: all nine improved, so *"Nothing got worse by more than the 'about the same' margin"*.
4. **"Every figure we compared"** (starred = shown above) and **"Not ranked, and why"**: a total replaced by its per-sales figure (with the total's own change quoted, nothing hidden), a doubtful figure, zero last year, zero in both years.
5. **"Where last year's figures come from":** the previous-year column of the same filing, so both years are on the same basis; last year's own filing is checked for restated figures; if NSE has none (Reliance FY 2021-22) the page says so instead of failing.

Errors give a page too, with suggested commands that use `summary.py`: an unknown company, a year NSE does not have (lists the years it does), a year before FY 2021-22, a damaged newest filing.

---

## 3. A 5-minute demo flow

| Step | Command | What to say |
|---|---|---|
| 1 | `pytest -q` | "About 470 automatic tests pass, with no internet needed." |
| 2 | `python download_filings.py --company "<NEW COMPANY>"` | "It finds the company on NSE, downloads each year politely (3 s apart), and flags years NSE does not have." |
| 3 | *(run step 2 again)* | "Second run: 0 requests. Everything is cached." |
| 4 | `python extract_report.py --company "<NEW COMPANY>" --fy 2024-25 --questions E1,E6` | "XML → clean SEBI rows. Calculated, converted and doubtful values are marked, and nothing is invented: missing = Not reported." |
| 5 | `python main.py --company "<NEW COMPANY>" --fy 2024-25 --open` | "One HTML page, two tabs. It opens on the plain-English **Dashboard**; the second tab is the **SEBI-format report**, same question numbers and wording as SEBI's form." |
| 6 | click the **SEBI-format report** tab, then back | "Same data, two audiences. Every dashboard number comes from this table." |
| 6b | `python trends.py --company "<COMPANY>" --open` | "Extension 1: the same company over every year NSE has. Missing years flagged, basis changes and restatements marked." |
| 6c | `python summary.py --company "<COMPANY>" --open` | "Extension 2: the 3 biggest improvements and setbacks against last year, with the definition of 'better' stated on the page, and everything it could not rank listed with the reason." |
| 7 | the error commands in section 6 | "Specific messages instead of crashes." |

### 3a. What to point at on the Dashboard (about 2 minutes)

1. **"At a glance" box**: one plain sentence, the scoreboard (improved / same / worse) and six topic tiles.
2. **One card**: plain title, "Lower is better", big number in lakh/crore, verdict chip + arrow, bars from zero, *What it is*, *Why it matters*, **Fine print** (full number, how we calculated it), and the badge saying where the number came from.
3. **"How to read better and worse" box**: it compares the company with *itself last year* only. No invented benchmark.
4. **Show the honesty** with a second company:
   - `Tata Steel 2025-26`: Climate section is dashed amber: *"The greenhouse gas figure looks doubtful, so we do not quote it."* (the company typed millions of tonnes as tonnes).
   - `HDFC Bank 2022-23`: older filing: "unit not stated", "Last year's figure was 0, so a percentage change cannot be worked out", air pollutants "reported as 0 in both years".
   - `Wipro 2025-26`: energy filed in megajoules; shown in GJ with "unit changed by us"; open **Fine print** to see the original.
5. **"Can I trust these numbers?"** panel: counts of reported / calculated / unit-changed / not reported / noted.

---

## 4. Swapping in the interviewer's company and year

**Template (copy, then edit the two highlighted parts):**
```powershell
python main.py --company "COMPANY NAME OR SYMBOL" --fy YEAR --open
```

**Company** can be a name (`"Tata Steel"`, `"hdfc bank"`, `Reliance`) or the NSE symbol (`TATASTEEL`, `INFY`). Use **double quotes** if the name has a space or `&` (for example `"M&M"`). If several companies match (e.g. `Tata`), it lists them: re-run with the symbol it suggests.

**Year** can be written `2023-24`, `2023-2024`, `FY2023-24` or `2023/24`. Only **FY 2021-22 and later** are covered; the latest filed year is **2025-26**.

**Copy-paste examples**
```powershell
python main.py --company "Tata Steel" --fy 2025-26 --open     # a doubtful figure: shown as filed, warned, never compared
python main.py --company "Reliance" --fy 2023-24 --open       # the cleanest example
python main.py --company "Infosys" --fy 2021-22 --open        # old-style filing + a file that needed cleaning + monthly air figures
python main.py --company "HDFC Bank" --fy 2022-23 --open      # a bank: older layout, no units, little environmental data
python main.py --company "Wipro" --fy 2025-26 --open          # energy filed in megajoules, shown in GJ
python main.py --company "ITC" --fy 2024-25 --open
python main.py --company "M&M" --fy 2024-25 --open
```

**Timing you can expect:** a brand-new company takes about **10 s** for one year (about **20-30 s** to download every year); anything already downloaded takes **under 1 s**.

---

## 5. What is already downloaded on this PC

Folders under `data\raw\`. NSE itself has more years than these (all years from FY 2021-22 that the company filed).

| Company | NSE symbol | Years on disk |
|---|---|---|
| Tata Steel | `TATASTEEL` | 2022-23, 2023-24, 2024-25, 2025-26 *(NSE has no FY 2021-22 filing)* |
| Reliance Industries | `RELIANCE` | 2022-23, 2023-24, 2024-25, 2025-26 *(none for 2021-22)* |
| Infosys | `INFY` | 2021-22, 2023-24 |
| HDFC Bank | `HDFCBANK` | 2022-23, 2023-24 |
| Wipro | `WIPRO` | 2021-22 to 2025-26 |
| Mahindra & Mahindra | `M&M` (folder `M_M`) | 2024-25 |
| ITC | `ITC` | 2024-25 |
| TCS | `TCS` | 2024-25 |
| ONGC | `ONGC` | 2023-24 *(files its air pollutants as concentrations, not tonnes)* |

Any other company works too: it is fetched from NSE the first time. **Tip: run each company you plan to demo once on the same day, so a flaky connection cannot hurt.** A *new* company always needs internet.

---

## 6. Showing the error handling

```powershell
python main.py --company "Xyzzy Quux" --fy 2023-24         # unknown company
python main.py --company "Tata" --fy 2023-24                # ambiguous: lists 10 matches and says to use a symbol
python main.py --company "Reliance" --fy 2019-20            # before FY 2021-22: refused with a clear message
python main.py --company "Reliance" --fy banana             # not a year
python main.py --company "Tata Steel" --fy 2021-22          # valid year, but NSE has no filing: lists the years it does have
python main.py --company "Sakuma Exports" --fy 2023-24      # listed company with no BRSR filing
python trends.py --company "Reliance" --from 2025-26 --to 2021-22      # years the wrong way round
python trends.py --company "Tata Steel" --from 2019-20                # a year before BRSR reporting began
python summary.py --company "Reliance" --fy 2021-22                   # NSE has no filing for that year: lists the years it does have
python summary.py --company "Xyzzy Quux"                              # unknown company
```
Each one prints `Error: ...` with the specific reason, **and writes an explanation page** `output\error_<company>_<year>.html` (add `--open` to show it). Exit code 1, never a Python traceback.

What the page shows: the exact message, what you typed, "What you can try", and **ready-to-run commands** where we know them (the companies that matched an ambiguous name; the years NSE does have). Error pages never overwrite a report page.

```powershell
python main.py --company "Tata Steel" --fy 2021-22 --open       # page lists FY 2022-23 ... 2025-26, each with a command
```

| Situation | Page title |
|---|---|
| unknown company | We could not find that company on NSE |
| several companies match | Please choose one company |
| year not understood / before FY 2021-22 | We could not read that financial year / BRSR filings start with FY 2021-22 |
| NSE has no filing for the year | NSE has no BRSR filing for that company and year |
| NSE unreachable or blocking | We could not get the data from NSE |
| damaged or wrong kind of file | The filing on NSE could not be read |
| a bug in the tool | Something unexpected went wrong (run again with `--debug`) |

Ready-made examples of six of these are in `samples\` (`error_*.html`): unknown company, year before FY 2021-22, year NSE does not have, damaged file, trend years the wrong way round, and a `summary.py` request for a missing year.

---

## 7. Where to look at the results

| What | Where | How to show it |
|---|---|---|
| Downloaded filings (XBRL) | `data\raw\<SYMBOL>\<FY>\*.xml` + `filing.json` | open the folder in PyCharm |
| Clean data (JSON) | `data\parsed\<SYMBOL>\<FY>.json` | open in PyCharm; find `E6.scope1`: it has `value`, `unit`, `status`, `as_filed`, `warnings` |
| The report page | `output\<SYMBOL>_<FY>.html` | `python main.py ... --open`, or double-click |
| An error page | `output\error_<company>_<year>.html` | written by the same command when something fails |
| The trend page | `output\<SYMBOL>_trend_<from>_to_<to>.html` | `python trends.py ... --open` |
| The summary page | `output\<SYMBOL>_summary_<FY>.html` | `python summary.py ... --open` |
| Sample pages (5 company reports, 3 trend pages, 3 summaries, 6 error pages) | `samples\` + `samples\README.md` | open in a browser; rebuild with `python make_samples.py` |

Handy PowerShell lines:
```powershell
Get-ChildItem data\raw -Directory | ForEach-Object { "{0,-10} {1}" -f $_.Name, ((Get-ChildItem $_.FullName -Directory).Name -join ", ") }   # what is downloaded
Get-ChildItem output\*.html                                                                                                                  # pages generated so far
Get-Content data\parsed\RELIANCE\2023-24.json -TotalCount 40                                                                                 # peek at the clean JSON
```
How to read a page: *Not reported* = the filing has nothing (never shown as 0) · `calc.` = we added reported numbers · `conv.` = we changed the unit · ⚠ = doubtful value, explained in the note under the table.

---

## 8. Tests

```powershell
pytest -q                              # everything (about 470 tests, a few seconds, no internet)
pytest tests/views -q                  # one layer: the test folders mirror brsr_p6/ (core, download, parsing, extraction, analysis, views, ...)
pytest tests/extraction/test_extractor.py -v      # one file, one line per test
pytest tests/test_architecture.py -q   # only the "layers import downwards" rule
pytest -k "scale" -v                   # only tests with "scale" in their name
```

---

## 9. Starting fresh (to show the download from zero)

This deletes only files that can be downloaded again:
```powershell
Remove-Item -Recurse -Force data\raw\ITC          # forget one company's downloads
Remove-Item -Recurse -Force data\cache            # forget saved company searches
```
Then run `python download_filings.py --company "ITC"` again to show a real download.

---

## 10. If something goes wrong

| Problem | Fix |
|---|---|
| `python` is not recognised, or `ModuleNotFoundError: requests` | You are not in the project's environment. Use the **PyCharm Terminal**, or run `.\.venv\Scripts\python.exe main.py ...` |
| PowerShell says "running scripts is disabled" when activating | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, or skip activating and use `.\.venv\Scripts\python.exe` |
| `Error: NSE refused the request (HTTP 403/429)` | NSE is limiting automated access. Wait a few minutes and retry. (We never retry hard; that is by design.) |
| `Error: Could not get ... from NSE` | No internet or NSE is down. A company you have downloaded before still works: the tool uses the saved filing list and says so ("... may be out of date"). A company you never downloaded needs the internet. |
| `Error: ... matches several companies` | Re-run with the exact NSE symbol it suggests, e.g. `--company TCS` |
| `Error: NSE has no BRSR filing for ... for FY ...` | That company did not file that year; the message lists the years it did. |
| The page opens but looks unstyled | Open the `.html` file itself in Chrome/Edge (not a preview inside an editor) |
| A quoted name with `&` breaks | Always use double quotes: `--company "M&M"` |

---

## 11. One-line answers for likely questions

- **How does it work end to end?** Company text → NSE symbol (NSE's own search) → filing list → XBRL file (cached) → read facts → fill SEBI's template rows → units cleaned, checks add warnings → JSON + HTML page.
- **Why XBRL and not the PDF?** It is NSE's structured version of the same filing; far more reliable than PDF tables. We cross-checked numbers against a company PDF.
- **Is it polite to NSE?** Yes: at least 3 seconds between requests, cache for everything, stop at once on a block, never hammer.
- **What if a value is missing or odd?** Missing → "Not reported" (never 0). Converted or calculated → labelled. Doubtful (e.g. a figure typed in millions under a "tonnes" unit) → shown exactly as filed with a warning.
- **Does it work for any company?** Yes, any NSE-listed company that filed a BRSR for FY 2021-22 or later; nothing is hard-coded.
- **Two formats of filing?** Yes: filings before April 2024 use an older layout than later ones; the code detects which one and uses the matching tag mapping.
- **Who is the dashboard for?** A non-expert. It answers four questions: how big is the footprint, better or worse than last year, is it under control, can I trust the numbers.
- **What does "better" mean?** Better than the company's *own* figure last year, nothing more. The filing has no industry benchmark or legal limit, so we do not rate or score.
- **What if a number looks wrong?** (Tata Steel typed Scope 1 as 64 instead of 64 million.) It is shown exactly as filed, in amber, with the reason; it gets no better/worse verdict and is kept out of the summary sentences.
- **Why per ₹ crore?** The filed intensity (0.0000807 GJ per ₹) is unreadable. Only the unit changes; the filed number stays in the Fine print.
- **How do you stop it inventing things?** Missing is "Not reported" (never 0), a zero last year gives "can't compare", figures with no unit are not quoted in sentences, and a test checks every warning in every real filing is classified.
- **What happens on bad input?** The same command writes an *error page* instead of a report: the exact reason, what you typed, what to try, and commands you can copy (for example the years NSE does have). A real bug gets a page too, and `--debug` shows the traceback.
- **What if NSE is down during a demo?** Companies already downloaded still work: an older saved filing list is used (and the console says so). Only a never-seen company needs the internet.
- **What does the trend page do with a missing year?** It flags it ("No filing", never 0). If the next filing exists, that filing's previous-year column holds the company's own figures for the missing year, so they are shown and marked.
- **How do you handle a change from consolidated to standalone?** Every column shows its basis; trend verdicts only compare years on the same basis and unit, and the page says which years were left out.
- **What is a restatement?** The next filing gives a different figure for the same year (more than 0.5% apart). We keep the figure as filed in its own year and mark it ⟲ with the later figure.
- **How do you define "better" in the summary?** Against the company's own last year only, with a direction per figure (lower is better for energy, gases, water, waste per ₹ of sales and every pollutant; higher for the renewable and recycled shares). Under 1% (a share: under half a point) is "about the same". The page states all of this.
- **Why rank shares in percentage points?** A renewable share rising from 0.07% to 0.24% is +269% in percent but only 0.18 of a point; ranked in percent it would beat a real improvement.
- **Why is a total missing from the best / worst lists?** A total grows when a company grows, so the figure per ₹ of sales is ranked instead and the total is quoted as context. Nothing is hidden: the "not ranked" list says why.
- **What if last year's report is missing?** Every filing carries its previous-year column, so the summary still works; the page says NSE has no filing of its own for that year. If the newest filing cannot be read, there is nothing to summarise and an error page says so.
- **How is the code organised?** Nine packages, one per step: `core` (data model) → `download` → `parsing` → `extraction` → `analysis` → `views` → `rendering` → `workflows` → `cli`. A package may only import from the ones before it; `tests/test_architecture.py` fails if that is broken. See section 12.
- **Does it run from a clean checkout?** Yes: tested in a brand-new virtual environment: `pip install -r requirements.txt`, one command, and the page is written (about 11 seconds for a new company).
- **Why Python + a template?** Python decides (verdicts, sentences, warnings), the HTML template only prints. That makes every rule testable without a browser.

---

## 12. Where is the code? (for "show me the ..." questions)

The code is in `brsr_p6/`, one folder per step. Open the file in the right-hand column.

| "Show me ..." | Folder | Start with |
|---|---|---|
| how it **downloads** from NSE (polite: 3 s pause, cache, stop on 403/429) | `brsr_p6/download/` | `nse_client.py`, then `downloader.py` |
| how it finds the company and the filing for a year | `brsr_p6/download/` | `company_lookup.py`, `filings.py` |
| how it **parses** the XBRL file | `brsr_p6/parsing/` | `xbrl_reader.py`, and `p6_mapping.py` (tag → SEBI row) |
| how it **cleans** the data (units, warnings, nothing invented) | `brsr_p6/extraction/` and `brsr_p6/core/units.py` | `extractor.py`, `checks.py` |
| the **SEBI template** as data | `brsr_p6/core/sebi_template.py` | the whole file |
| how "better / worse" is decided | `brsr_p6/analysis/` | `comparison.py` |
| the year-by-year logic (basis change, restatement) | `brsr_p6/analysis/` | `trend_model.py` |
| what the **dashboard** says, and its wording | `brsr_p6/views/` | `dashboard_cards.py`, `metric_info.py` |
| the **3 best / 3 worst** ranking | `brsr_p6/views/` | `summary_view.py` |
| how the **HTML** is made | `brsr_p6/rendering/` | `render.py` and `templates/` |
| the error pages | `brsr_p6/views/error_view.py` and `brsr_p6/rendering/templates/error.html` | |
| how a command runs end to end | `brsr_p6/workflows/` and `brsr_p6/cli/` | `pipeline.py`, `main_cli.py` |
| the rule that keeps the layers apart | `tests/test_architecture.py` | the whole file |

The tests live in folders with the same names (`tests/download/`, `tests/views/`, ...). `python make_samples.py` rebuilds `samples/`.

---

## 13. Git cheat-sheet

Git was installed in Phase 11. If PyCharm says "git is not recognized", close and reopen PyCharm. Everything here is read-only except `commit` and `push`.

```powershell
git status                      # what changed since the last commit
git log --oneline               # the history, one line per commit
git diff                        # exactly what you changed (before committing)
git add -A ; git commit -m "Describe what changed"      # save a new snapshot
git push                        # send new commits to GitHub (after the first push has been done once)
git ls-files                    # every file the repository tracks
```

First publication (once, needs your GitHub login): create an **empty** repository on github.com, then
```powershell
git remote add origin https://github.com/<your-username>/<repository-name>.git
git push -u origin main
```
Before every commit that touches pages or rules, run `python make_samples.py` and `pytest -q`: a test fails if a sample page is out of date.
