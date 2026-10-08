# BRSR Principle 6 Report Generator & Environmental Dashboard

Give it a listed Indian company and a financial year. It produces **one HTML page** with two views of that company's BRSR
**Principle 6 (environment)** disclosures, built from the company's filing on NSE:

1. **Dashboard** (opens first): the same data in plain English for a non-expert. For every figure it says *what it measures*,
   *whether it got better or worse than last year* and *why it matters*.
2. **SEBI-format report**: laid out like SEBI's May 2021 template, same question numbers, wording, tables and row labels.

![The dashboard for Reliance Industries, FY 2023-24](docs/dashboard_reliance.png)

> **Demo cheat-sheet:** [`commands.md`](commands.md) has every command with copy-paste examples.
> **Sample pages** (open in a browser, no setup): [`samples/`](samples/README.md).

## Quick start

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py --company "Reliance" --fy 2023-24 --open
```

The page is written to `output/RELIANCE_2023-24.html`. The first run for a company downloads its filing from NSE (about 10 seconds,
polite and cached); after that it takes under a second.

## Requirements and setup

- Python 3.10 or newer (developed and tested on Python 3.14 on Windows 11; not tested on other versions or on macOS / Linux).
- Internet access only to download a filing the first time. Libraries: `requests`, `Jinja2`, `pytest` (pinned in `requirements.txt`).

| | Windows (PowerShell) | macOS / Linux |
|---|---|---|
| Create the environment | `python -m venv .venv` | `python -m venv .venv` |
| Activate it | `.venv\Scripts\Activate.ps1` | `source .venv/bin/activate` |
| Install | `pip install -r requirements.txt` | `pip install -r requirements.txt` |

## Run commands

```powershell
python main.py --company "Tata Steel" --fy 2025-26 --open     # the report page (downloads, cleans, writes the page)
python main.py --help                                         # all options (--output-dir, --debug as well)

python download_filings.py --company Reliance                 # only download: every year NSE has for the company
python extract_report.py --company Reliance --fy 2023-24      # only clean: print the SEBI rows as text, save the JSON
python make_samples.py                                        # rebuild the pages in samples/
pytest                                                        # the automatic tests (no internet needed)
```

- `--company` takes a name (`"Tata Steel"`) or the NSE symbol (`TATASTEEL`). `--fy` takes `2023-24`, `2023-2024`, `FY2023-24` or `2023/24`.
- Output: `output/<SYMBOL>_<FY>.html`, one self-contained file (no JavaScript, no internet needed to open it).
- Downloaded filings are kept in `data/raw/<SYMBOL>/<FY>/`; the cleaned data in `data/parsed/<SYMBOL>/<FY>.json`.
- **Eight filings are committed** (Tata Steel, Reliance, Wipro, Infosys, HDFC Bank) so that a fresh clone can rebuild `samples/` and run every
  test without the internet, as the brief allows. They are listed and explained in [`data/README.md`](data/README.md). Every other company is
  downloaded on demand.

## Inputs to try

| Command | What it shows |
|---|---|
| `--company "Reliance" --fy 2023-24` | The cleanest example: almost every card has a better / worse verdict. |
| `--company "Tata Steel" --fy 2025-26` | A figure typed in the wrong scale (emissions "64" instead of 64 million): shown as filed, warned, never compared. |
| `--company "Wipro" --fy 2025-26` | IT services. Energy filed in megajoules is shown in GJ and marked "unit changed by us". |
| `--company "Infosys" --fy 2021-22` | An older filing layout, a damaged XML file that was cleaned, monthly air figures, energy with no unit. |
| `--company "HDFC Bank" --fy 2022-23` | A bank: sparse data, many "Not reported" and "reported as 0", and the page stays honest. |
| `--company "ITC" --fy 2024-25`<br>`--company "M&M" --fy 2024-25`<br>`--company "TCS" --fy 2024-25`<br>`--company "ONGC" --fy 2023-24` | Other sectors and filing styles (for example ONGC files its air pollutants as concentrations, not tonnes). |
| `--company "Xyzzy Quux" --fy 2023-24` | An error page: unknown company. |
| `--company "Tata Steel" --fy 2021-22` | An error page: NSE has no filing for that year, and it lists the years it does have. |
| `--company "Reliance" --fy 2019-20` | An error page: before BRSR reporting began. |

## What is completed

**Core task: complete.** Input company + year, output one HTML page with a SEBI-format view and a plain-English dashboard.

| Part | Status |
|---|---|
| Works for any NSE-listed company that filed a BRSR for FY 2021-22 or later (nothing hard-coded) | ✅ |
| SEBI-format view: all 21 Principle 6 questions (12 Essential, 9 Leadership) in SEBI's order, current and previous year, units, "Not reported" shown explicitly | ✅ |
| Dashboard: six topics, headline sentences, metric cards (what / better or worse / why), charts, safeguards, trust panel, glossary | ✅ |
| Never invent numbers: missing, converted, calculated and doubtful values are all labelled | ✅ |
| Polite to NSE: 3 s between requests, cache everywhere, retries only for temporary problems, stops on 403 / 429 | ✅ |
| Error pages for every failure, not only console messages | ✅ |
| Sample pages for 5 companies and 4 error cases in `samples/` | ✅ |
| **Extension 1:** multi-year trends | ❌ not built |
| **Extension 2:** year-on-year summary (3 best + 3 worst) | ❌ not built (each card already compares with last year) |
| **Extension 3:** company comparison | ❌ not built |

## How the data is extracted

```
company text ─► NSE symbol ─► filing list ─► XBRL file (cached) ─► facts ─► SEBI template rows ─► checks ─► HTML page
```

- **Source:** the BRSR filings published on NSE. NSE's website loads them through an undocumented JSON endpoint (found with the browser's
  DevTools): one request for the company's filings with a date range, after one visit to the home page for cookies. File links are
  always taken from NSE's answer, never guessed. Each filing has a PDF and an **XBRL (XML)** version; we use the XML, which is structured
  and far more reliable than PDF tables.
- **Two layouts of the same SEBI form** exist (before and after April 2024). Both are mapped to the same SEBI rows (`p6_mapping.py`); the
  edition is detected from the file itself and shown in the page header. Which year is "current" is decided from the file's reporting
  period dates, not from labels.
- **Units are normalised and shown:** energy in GJ, water in kL, waste and air pollutants in tonnes, greenhouse gases in tCO₂e. Anything
  converted is marked and the filed figure is kept (in the JSON and in the dashboard's "Fine print"). In real filings `MtCO2e` means
  metric tonnes (not million tonnes), per-month air figures stay per month, and older filings often state no energy unit at all, so we say so.
- **Checks only add warnings, they never change a number:** an intensity of 0, a total that does not equal its parts, a pollutant reported
  as 0, and emissions that look a thousand or a million times too small for the company's energy use (this caught Tata Steel).
- **Revised filings:** NSE keeps one row per company per year and a revision replaces the original, so we always use the latest revision.
- **Standalone vs consolidated:** we do not choose. We use the filing NSE lists for that year, and the page header states its reporting
  boundary. A company can switch basis between years (Wipro does), so figures should not be compared across such years.
- **Verification:** key numbers for Tata Steel FY 2025-26 were compared by hand with the company's own PDF report and are pinned in
  tests (`tests/test_real_filings.py`); other companies are covered by the consistency checks above.

## Error handling

Every failure still produces a page, `output/error_<company>_<year>.html`, so the reason appears where the report would have been.
It names what went wrong, what you typed, what to try, and gives ready-to-run commands where possible. Error pages never overwrite a report page.

| Situation | What the user sees |
|---|---|
| Company not found on NSE | "We could not find that company on NSE", with spelling and symbol advice |
| Several companies match | The matches, each with a command using its NSE symbol |
| Year not understood / before FY 2021-22 | What formats work / that BRSR reporting began in FY 2021-22 |
| NSE has no filing for that year | The years NSE does have, each with a command |
| Company filed no BRSR at all | That only the top 1,000 listed companies must file |
| NSE unreachable or blocking | Advice to retry; companies already downloaded keep working (an older saved filing list is used and the console says so) |
| Damaged or wrong kind of filing file | The file name and the problem; "we show nothing rather than guess" |
| Any unexpected bug | A page saying so with the technical reason; `--debug` shows the traceback |

## Known limitations

- **Extensions 1 to 3 are not built.** The dashboard compares each figure with the previous-year column of the *same* filing, which can
  differ from what the company reported last year if it restated.
- **"Better / worse" is only against the company's own previous year** (within ±1% counts as "about the same"). There is no benchmark or
  legal limit in the filings, so there is no rating or score.
- **Waste recovery and disposal are totals only.** SEBI's form asks for them per waste category; the structured filing gives one total for all.
- **Some SEBI items have no XBRL field** and are always "Not reported": the non-compliance table (one free-text answer instead), the level of
  treatment of discharged water, "Others – please specify" air pollutants, and the EIA web link.
- **Older filings** (before April 2024) have no energy unit, free-text emission units and often no intensity units. They are shown as filed with a warning.
- **Mistakes we cannot detect:** an error of a few percent, or a wrong figure that still looks plausible, passes through. Only large
  scale slips, zero intensities and totals that disagree with their parts are caught.
- **PPP-adjusted and per-tonne intensities** are shown only in the SEBI tab ("additional items"); their unit labels in the filings are unreliable.
- **NSE's endpoints are undocumented** and may change. A company you have never downloaded needs internet and can be refused (HTTP 403 / 429).
- **Tested only in a Chromium-based browser (Edge) and on Windows.** The page uses no JavaScript, so other browsers should work.

## Design note

**Who it is for.** A non-expert: an investor, journalist or student who has never opened a BRSR. They want four answers, and the page is
ordered to give them: *How big is the footprint? Is it better or worse than last year? Is it under control? Can I trust these numbers?*

![A doubtful figure, shown honestly](docs/dashboard_doubtful_figure.png)

**Why it looks the way it does.**

- **A summary first, detail after.** One plain sentence and a scoreboard, then six topics in a story order: energy used, gases released,
  water, air, waste, and the rules in place. Each topic opens with a headline sentence built from the numbers.
- **Every number explains itself.** A plain title, which direction is better, *what it is* and *why it matters* are always visible; the
  exact figure and how we calculated it sit in collapsible fine print. Jargon is explained in a glossary.
- **Totals mislead, so intensity sits beside them.** A growing company uses more in total, so each topic also shows the figure per ₹ 1 crore
  of sales. Big numbers are written in lakh and crore, matching the Indian digit grouping of the SEBI tab.
- **"Better" means better than the company's own last year, nothing more.** Inventing a benchmark would break "never invent numbers".
- **Doubt is visible, never hidden.** A figure that looks wrong is shown exactly as filed, in amber, with no verdict, and is left out of the
  summary sentences, which then say why. A missing figure says "Not reported" (never 0). A zero last year gives "can't compare" because that
  zero probably means "not measured".
- **Never colour alone.** Verdicts are words plus symbols (✔ ✖ ≈ ?) plus arrows; the layout works on a phone.
- **Built to be trusted and tested.** Python decides every verdict and sentence; the HTML templates only print. That is why every rule has a
  test. The SEBI tab and the dashboard are built from the same cleaned data, so they start from the same numbers.

The design was prototyped first with real numbers: [`design/dashboard_mockup.html`](design/dashboard_mockup.html).

## Tests

```powershell
pytest
```

About 340 tests, a few seconds, no internet. They cover unit conversion, the XBRL reader, every SEBI row, the verdict and sentence rules, HTML
well-formedness, escaping of filing text, the error pages, and (when the filings are on disk) real-filing spot checks and "the committed
sample pages are up to date".

## Project structure

```
main.py              the report generator (tiny entry point)
download_filings.py  downloads filings from NSE (tiny entry point)
extract_report.py    filing -> SEBI Principle 6 data, printed as text (tiny entry point)
make_samples.py      rebuilds the pages in samples/ (tiny entry point)
brsr_p6/             the code:
                       download:   nse_client, company_lookup, filings, downloader
                       read+clean: xbrl_reader, values, units, sebi_template, p6_mapping, extractor, checks, models
                       dashboard:  warning_kinds, friendly, comparison, metric_info, dashboard_cards, dashboard_view
                       pages:      sebi_view, formatting, render, error_view, templates/ (HTML + CSS), pipeline, samples
                       other:      cli, report_io, report_text, errors, fiscal_year
tests/               automatic tests
samples/             sample report pages and error pages (+ README)
design/              the dashboard prototype
docs/                screenshots used in this README
data/                filings downloaded from NSE (8 are committed, see data/README.md) and the cleaned JSON
plan.md  context.md  learnings.md  commands.md             the plan, project notes, plain-English explanations, demo commands
```

## AI tools used

| Tool | Used for |
|---|---|
| Claude Code (Claude Sonnet 5.5) | Reading the brief and planning in phases; explaining each concept as it was introduced (`learnings.md`). Exploring NSE's endpoints and the XBRL files with throwaway probe scripts (kept outside the repository). Writing the downloader, XBRL reader, cleaner, SEBI page, dashboard, error pages, samples and tests. Reading real output to find bugs (double-counted energy, a mis-scaled emissions figure, false "got worse" claims) and fixing them. Writing this README, `commands.md` and `context.md`. |

All code was run and checked against real filings and by the tests; the decisions behind it are recorded in `context.md`.
