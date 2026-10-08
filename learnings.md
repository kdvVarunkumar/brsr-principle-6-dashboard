# Learnings

Plain-English notes on everything this project uses, written for someone new to programming. It is organised **by topic** (what you need to know),
not by date. The history of what was decided and when lives in `context.md` (decision log D1, D2, ...) and in `git log`; it is not repeated here.

**How to use it.** Read one part, close the file, and explain it out loud in your own words. Part 7 is the interview checklist (questions with short
answers); Part 8 has small exercises. For the demo itself use `demo.md`; for copy-paste commands use `commands.md`.

| Part | What it covers |
|---|---|
| 1 | The basics: terminal, Python, libraries, virtual environment, git, tests |
| 2 | The problem and the data: NSE, XBRL, and the messy things inside real filings |
| 3 | The flow, step by step: download, read, clean, decide, print, errors, trace |
| 4 | The dashboard: what makes it clear and honest |
| 5 | The extensions: trends, year-on-year, comparison, the two viewer pages, the one command |
| 6 | Habits that kept the numbers right |
| 7 | Interview checklist: questions and short answers |
| 8 | Try it yourself |
| 9 | Glossary |

---

# Part 1. The basics

## 1.1 The terminal

A **terminal** is a window where you control the computer by typing **commands** instead of clicking (on Windows: PowerShell; PyCharm has one built in at the bottom).

- A **command** is an instruction, for example `python flow.py --help`.
- The terminal has a **current folder** ("where you are"). `python flow.py` looks for `flow.py` in that folder. PyCharm's terminal starts in the project folder.
- An **option** is extra information after a command. In `python flow.py --company "Tata Steel"`, `--company` is the option and `"Tata Steel"` its value. Quotes are needed when the value has spaces.
- Every program ends with an **exit code**: `0` means success, anything else means something went wrong (argparse uses `2` for "you typed it wrong").

## 1.2 Python, libraries and `pip`

- **Python** is the language the project is written in. A **library** (package) is code written by other people that we reuse. **pip** is Python's "app store" for libraries.
- The project uses only **three** libraries:

| Library | Used for |
|---|---|
| `requests` | Download filings from NSE over HTTP |
| `Jinja2` | Fill HTML templates with data to build the pages |
| `pytest` | Run the automatic tests |

Reading the XBRL (XML) files needs no library: Python's built-in `xml.etree.ElementTree` does it. Fewer libraries means fewer things that can break on a stranger's computer.

## 1.3 Virtual environment (`.venv`) and `requirements.txt`

- **Problem:** project A needs `requests` 2.20, project B needs 2.34; one global install makes them fight.
- **Solution:** a **virtual environment** is a private folder with its own Python and its own libraries, for this project only. Create it with `python -m venv .venv`; **activate** it with `.venv\Scripts\Activate.ps1` (PyCharm does it for you: you see `(.venv)` at the start of the prompt). If PowerShell refuses ("running scripts is disabled"), run once `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
- `.venv` is big and specific to your computer, so it is never shared. What is shared is **`requirements.txt`**, the shopping list:

```
requests==2.34.2
Jinja2==3.1.6
pytest==9.1.1
```

`pip install -r requirements.txt` installs everything. `==` **pins** an exact version, so everybody (including the reviewer) gets the behaviour we tested. A few more libraries get installed automatically: those are the *dependencies of our dependencies*.
This file is what makes the brief's "runs from a clean checkout" true.

## 1.4 Git and GitHub

**Git** records the history of a project: save points you can go back to, who changed what and why, safe experiments. **GitHub** is a website that keeps an online copy of a git repository. (Git is the tool on your computer; GitHub is the online home. Not the same thing.)

| Word | Meaning |
|---|---|
| **Repository (repo)** | A project folder git is tracking, with its full history |
| **`git init`** | Start tracking this folder (once per project; creates a hidden `.git` folder) |
| **`git add`** | Put changes on the "tray" for the next commit |
| **`git commit -m "message"`** | Photograph the tray: one save point with a message |
| **`git status` / `git diff` / `git log`** | What changed / the exact change / the history |
| **`git push` / `git clone`** | Upload commits to GitHub / download a repo to a new computer |
| **Staging** | `add` then `commit` lets you save code and notes as separate, logical commits |

**Publishing (your step, it needs your GitHub login):** create an *empty* repository on github.com (do not tick README / .gitignore / licence), then in the project folder:

```powershell
git remote add origin https://github.com/<your-username>/<repo-name>.git
git push -u origin main
```

Reload the repository page: you should see the README with its screenshots and the `samples/` folder. Open the link once in a private window to be sure the reviewers can see it. Common problems: *"git is not recognized"* (restart PyCharm so it sees the new PATH); *"remote origin already exists"* (`git remote set-url origin <url>`); *"rejected ... fetch first"* (the GitHub repo was created with a README: create an empty one instead).

**What goes into the repository, and what does not (`.gitignore`):**

| Ignored | Why |
|---|---|
| `.venv/`, `__pycache__/`, `.pytest_cache/`, `.idea/` | Rebuildable or personal to your computer |
| `output/`, `data/parsed/`, `*.pdf` | Generated files, and the brief's own PDF (it belongs to the company, not to us) |
| `data/raw/*` **except** a few listed filings | The brief allows hand-downloaded filings "with documentation". A handful of small XML files (see `data/README.md`) make the samples and every test run offline on a fresh clone |

A later line in `.gitignore` beats an earlier one, and a folder must be re-included before its contents (`!data/raw/WIPRO/2025-26/`). Check with a dry run (`git add -n .`), never by guessing. `.gitkeep` is an empty file whose only job is to keep an otherwise empty folder in git. `.gitattributes` (`*.xml -text`) keeps the filings byte-for-byte as NSE published them.

**Before publishing:** every commit records an author name and email that anyone can read on a public repo (`git log --format="%an <%ae>"`), so check them, and search the text for your Windows user name and absolute paths. A public repository is forever.

## 1.5 Markdown and the project notes

`.md` is **Markdown**: plain text with light formatting (`# Heading`, `**bold**`, `- bullet`, tables with `|`). GitHub and PyCharm display it nicely.

| File | Purpose |
|---|---|
| `README.md` | Front page: setup, run commands, what is done, approach, limitations, AI tools, design note (the brief lists exactly what it must contain) |
| `commands.md` | Copy-paste cheat-sheet for the demo |
| `demo.md` | How to give the demo: problem, flow, architecture, script |
| `learnings.md` | This file |
| `plan.md`, `context.md` | The to-do list by phase; the project memory (facts, decisions, progress log) |

## 1.6 Tests and `pytest`

A **test** is a small piece of code that checks another piece works. `pytest` runs them all: green = fine, red = something broke. Why bother? When you change code today, the tests tell you in seconds that you did not break something from last week, and for this project they also protect **data accuracy** (a graded item).

- `assert` = "this must be true, otherwise the test fails". `pytest.raises(...)` = "I expect this error". `capsys` captures what the code prints. `tmp_path` is a throw-away folder. `@pytest.mark.parametrize` runs one test with many inputs. `monkeypatch` swaps a function for a fake during one test. `pytest.skip` skips politely (for example when a real filing is not on disk).
- Test files are named `test_*.py`, and the test folders **mirror** the code folders (`tests/views` tests `brsr_p6/views`), so `pytest tests/views` runs one layer.
- **Dependency injection** makes the internet testable: the NSE client accepts a `session`, a `sleep` and a `clock` as arguments. Real runs pass the real ones; tests pass fakes. That is why hundreds of tests run in seconds with no internet and never wait 3 real seconds.
- Four kinds of tests you should be able to name: **unit tests** (one small rule), **page tests** (the HTML), **guard tests** (they fail when someone forgets a step: unclassified warning, out-of-date samples, a wrong import direction) and **evidence tests** (the trace test checks every number against the raw XML).

## 1.7 Python ideas you meet in the code

| Idea | In one line |
|---|---|
| **Function, import, docstring** | `def name(...)`, `from x import y`, and the `"""text"""` under a function or at the top of a file (documentation for humans) |
| **f-string** | `f"Company: {name}"`: variables inside `{}` |
| **Type hints** | `argv: list[str] | None = None`, `-> int`: documentation Python does not enforce |
| **`if __name__ == "__main__":`** | Code under it runs only when the file is run directly, not when imported (tests, other files) |
| **Module / package / `__init__.py`** | One `.py` file / a folder of modules / the file that marks the folder as a package |
| **`dataclass`** | A short way to write a class that only holds data (`frozen=True` = read-only). `field(default_factory=list)` gives each object its own list |
| **`Enum`** | A fixed set of allowed values (`Status.CALCULATED`), so you cannot misspell it |
| **dict, list, tuple, set** | `{key: value}`, `[...]`, `( , )` (cannot change), `{...}` (unique items). A **list comprehension** builds a list by filtering: `[f for f in facts if f.end == wanted]` |
| **Exceptions** | `raise` stops a function and hands an error upward; `try/except` catches it where you know what to do. `class UnknownCompany(BrsrError)` means "is a" BrsrError, so one `except BrsrError` catches all our deliberate errors while real bugs still crash loudly |
| **`pathlib.Path`** | File paths as objects: `raw_dir / "RELIANCE" / "2023-24"`, `.exists()`, `.write_text()` |
| **Regular expression (`re`)** | A pattern language for text: `\d{4}` = exactly four digits |
| **Default and keyword arguments** | `download_filings(query, fy=None, include_pdf=False)` |
| **Callback** | A function passed in to be called later (`notify=print`): the callee does not know about printing, the caller decides |
| **Never reuse built-in names** | A field named `list` hid Python's own `list` and crashed the program. Avoid `list`, `str`, `id`, `type` as your own names |

---

# Part 2. The problem and the data

## 2.1 The task in one paragraph

**BRSR** (Business Responsibility and Sustainability Report) is SEBI's mandatory ESG report for India's top 1,000 listed companies. **Principle 6** is the environment part: energy, water, air emissions, greenhouse gases, waste, protected areas, impact assessments, legal compliance. The raw filings are dense and hard to read. The task: given a **company** and a **financial year**, produce **one HTML page** with the company's Principle 6 disclosures twice: **(1)** exactly in SEBI's official format, and **(2)** as a **dashboard a non-expert can understand**. Public data only (NSE filings and SEBI's template), filings from FY 2021-22 onwards, no hard-coding to one company, never invent a number, be polite to NSE.

| Graded area | Weight | What a strong submission shows |
|---|---|---|
| Dashboard clarity | **30%** | A non-expert understands each metric, its direction and why it matters |
| Data accuracy | **25%** | Figures match the filing; missing or converted values are flagged; works beyond the samples |
| SEBI-format fidelity | 15% | Same question numbers, tables, row labels, units |
| Error handling | 10% | Specific, helpful messages |
| Code quality | 10% | Readable, sensibly organised, extraction separate from presentation |
| Extensions | 10% | Depth and correctness of those attempted |

## 2.2 How a website really gets its data

Open the NSE BRSR page and two things happen: your browser downloads the **page** (mostly empty HTML), and then the page's **JavaScript** quietly asks NSE's server for the data in the **background** ("XHR / Fetch" requests) and draws the table from the reply. Our Python program can skip the page and ask for the same data **directly**. The trick is finding out *what* the page asks for: the browser's **DevTools** (F12, Network tab, filter Fetch/XHR) shows exactly that. We also learned that **JavaScript is just text**: we read NSE's own script to find how the page asks for older years.

| Word | Plain meaning |
|---|---|
| **Request / response** | You ask a server something; it answers |
| **URL, query string** | The address; the part after `?` is extra options as `name=value` joined by `&` |
| **GET / POST** | "Give me this" / "here is data, process it" |
| **Headers** | Labels sent with a request, like writing on an envelope: `User-Agent` (who is asking), `Referer`, `Cookie` |
| **Cookie** | A badge the site hands you on the first visit and expects back later. NSE refuses API calls without one, so we visit its home page first. `requests.Session()` remembers cookies for us |
| **Status code** | **200** OK, **403** forbidden (blocked), **404** not found, **429** slow down, **5xx** server trouble |
| **API / JSON** | A door meant for programs; it answers in JSON: `{"symbol": "TATASTEEL", "year": "2023-24"}` (`{}` dictionary, `[]` list) |

## 2.3 What NSE gives us

- **Find the company:** `GET /api/smart-search/eqEtf?q=<text>` turns "Tata Steel" into the symbol `TATASTEEL`.
- **List its filings:** `GET /api/corporate-bussiness-sustainabilitiy?index=equities&symbol=TATASTEEL&from_date=DD-MM-YYYY&to_date=DD-MM-YYYY` (yes, NSE's own spelling). It returns JSON with, for each filing: the year (`fyFrom`, `fyTo`), submission date, revision date, and **links** to the PDF and the XBRL file. Without dates the page quietly asks for the last 365 days only; asking from `01-04-2021` returns every year.
- **One row per company per year; a revised filing replaces the original.** That is the rule we state for "which filing do we use": the one NSE currently lists.
- **We always use the links from the answer.** File names follow no pattern, and a PDF link may literally end in `/null`.

## 2.4 PDF vs XML, and XBRL in simple words

A **PDF** is made for eyes: a table is just text placed on a page, so extracting it is fragile. **XML** is made for programs: values wrapped in named tags (`<electricity unit="GJ">1200</electricity>`). NSE requires both for each BRSR; we use the XML. **XBRL** is "XML for business reports":

| Part | Meaning | Analogy |
|---|---|---|
| **Taxonomy** | The regulator's dictionary of allowed tags and what they mean | A form with fixed field names |
| **Instance document** | The filled-in form a company submits (the `.xml` we download) | One company's filled form |
| **Fact** | One reported value, e.g. `TotalScope1Emissions = 64` | A single answer |
| **Context** | *Who and when* a fact is about (company, period): how we tell current year from previous year | The date label on the answer |
| **Unit** | What the number is measured in | The unit label |
| **Dimension** | Extra labels that let one tag represent table rows | The row label |

Reading a filing therefore means collecting facts, then using each fact's **context** (which year?) and **unit** to decide where it belongs in SEBI's table. We decide the year from the **period end dates**, never from the context's id text. A filing holds **two** years: its own and the year before (this matters in Part 5). Its **element names** are what makes every number traceable: a PDF table gives you nothing to point at.

## 2.5 Five editions, two lookup tables

Every filing names the version of SEBI's form it used (the `.../xbrl/2021-09-30/in-capmkt` part). We met five: 2021-09-30 and 2023-06-30 (**legacy**), 2024-04-30, 2025-05-31 and 2026-02-28 (**modern**). Legacy filings have about 400 tags, no proper units (energy has none at all; emissions units are free text such as "Kg/Month"). Modern ones have about 660-700 tags with real unit labels and a richer layout (renewable / non-renewable split, PPP). So the program has **two mapping tables** and picks one by reading the edition date. (The fifth edition only appeared when a second company was tested: **test on more than one company**.)

## 2.6 The messy-data traps (each one became a rule)

| What we found in real filings | What the program does |
|---|---|
| Tata Steel's Scope 1 is `64` under unit `MtCO2e` (which means *metric tonnes*), but the PDF says 64 **million** tonnes: typed in millions | Cross-check against energy use (next section); show as filed with a "doubtful" note, **never silently rescale** |
| A `0` can mean a real zero, "not measured", "not material", or "rounded away" | A reported 0 gets a note; an intensity of 0 whose total is not 0 is "not a real zero" |
| Units differ by company (kg, kilotonnes, tCO2e, MtCO2e; Terajoule and Megajoule for energy) | Convert to one unit per topic and show the original in the fine print |
| Legacy energy has no unit at all; some air figures are "per month" | Show "(unit not stated)"; never turn "per month" into "per year" |
| Numbers stored as text with Indian grouping (`1,83,595`); answers like `true`, `NA` | Clean before use; `NA`/blank means *nothing*, not 0 |
| An XML file with illegal invisible characters (a strict reader refuses the whole file) | Clean them in memory and add a warning; if still broken, a clear "unparseable filing" page |
| Tag spelling differs in the same file (`WithOutTreatment` / `WithoutTreatment`) | Look tags up ignoring capitals |
| The company has no filing for that year; a PDF link ends in `/null` | "No report for that year" is a normal case with its own message; the PDF is optional |
| Standalone vs consolidated changes between years (Wipro flips almost every year) | Always print the reporting boundary; never compare across a change |
| A later filing restates last year's figure | Keep each figure as filed in its own year; mark restatements |
| An intensity written with **one digit** (`0.0000000004`) is rounded: `4e-10` means "between 3.5e-10 and 4.5e-10" | "Too coarse to compare": shown as filed, never given a percentage |
| The same XBRL numbers and the PDF can disagree (a PPP intensity labelled "per rupee" is really per million US dollars) | Say so; PPP and per-tonne intensities appear only in the SEBI tab |

## 2.7 "Does this number make sense?"

A unit label tells you what the company *says*; it does not prove the number was typed in that unit. Burning fuel releases a fairly predictable amount of CO2 per unit of energy (roughly 0.01 to 0.5 tonnes per gigajoule). So divide Scope 1+2 (tonnes) by total energy (GJ):

| Company | Emissions (t) | Energy (GJ) | Ratio | Verdict |
|---|---|---|---|---|
| Reliance (Scope 1) | 36,350,070 | 478,033,842 | 0.076 | plausible |
| Infosys | 63,031 | 839,448 | 0.075 | plausible |
| HDFC Bank | 586,080 | 3,032,974 | 0.193 | plausible |
| Tata Steel (as typed) | 69 | 623,812,739 | 0.0000001 | **implausible**; x1,000,000 gives 0.11, so it was typed in millions |

Decision: when the ratio is implausible, **show the number exactly as filed, with a note, and no verdict**.

## 2.8 Being polite to NSE

Cache everything (company search, the filing list for 24 hours, the files themselves), wait at least **3 seconds** between requests, stop at once on 403/429, retry only temporary failures (timeouts, 5xx) with growing pauses, never loop wildly, and do not paste cookie values anywhere.

---

# Part 3. The flow, step by step

## 3.1 The big picture

The program is a **conveyor belt**: a filing goes in at one end and a web page comes out at the other. Each step has its own folder (a Python **package**):

```
python flow.py --company "Tata Steel" --fy 2025-26
   cli          read what was typed; on failure write an error page         cli/flow_cli.py
   workflows    the order of the steps (the "manager")                      workflows/pipeline.py
   download     company text -> NSE symbol -> filing list -> the XML file   download/
   parsing      the XML -> plain facts (element, value, unit, period)       parsing/
   extraction   facts -> ONE clean Principle6Report, doubts flagged         extraction/
   views        decide every number, word and verdict (no HTML)             views/
   rendering    fill the HTML templates, write ONE page                     rendering/
   output/TATASTEEL_2025-26.html
```

| Package | Its job in one line |
|---|---|
| `core/` | Shared words and tools: the data model (`Cell`, `Metric`, `Principle6Report`), errors, financial years, units, number formatting, file locations, SEBI's template |
| `download/` | Talk to NSE politely and keep the files on disk |
| `parsing/` | Open the XBRL file and read its raw facts (no cleaning yet) |
| `extraction/` | Clean the facts into one report; flag doubtful numbers, never change them |
| `analysis/` | Compare years: better / worse / same, trends (pure logic) |
| `views/` | Decide *what each page says* (sentences, numbers, flags) |
| `rendering/` | Fill the HTML templates and write the file |
| `workflows/` | Whole jobs: company + year in, page out |
| `cli/` | The commands you type; each calls a workflow |

**The layer rule.** The table is ordered from the bottom up. *A package may import only from itself and from packages earlier in the list.* `core` knows nothing about `views`; `views` knows nothing about how a page is saved. Why: circular imports crash Python at start-up; you can change the top layers without breaking the bottom; and "where does this new function go?" always has an answer. A rule that lives only in a README gets broken in a hurry, so **`tests/test_architecture.py` enforces it**: it reads every file's `import` lines (Python's `ast` module turns code into a tree you can inspect) and fails with the exact file and line of any upward import. It also fails if a loose module appears in `brsr_p6/` outside a package. Code that checks code.

**One command.** The root folder holds a single file, `flow.py` (ten lines, no logic). With `--company` and `--fy` it is *the flow*; the first word can instead name a step or an extra: `download`, `extract`, `trends`, `summary`, `compare`, `hub`, `samples` (like `git commit` / `pip install`). In `cli/flow_cli.py` a dictionary `COMMANDS` maps each name to the function to run, and only the **first** word counts, so `--company trends` is still a company.

## 3.2 Step 1: Download (`download/`)

| File | Job |
|---|---|
| `nse_client.py` | **The only code that touches the internet**: pacing, retries, block detection, safe saving |
| `company_lookup.py` | `"Reliance"` -> `RELIANCE` (several matches -> `AmbiguousCompany` with the list) |
| `filings.py` | Ask NSE for the filing list, parse it, choose the row for the year |
| `downloader.py` | The manager: validate -> find the company -> list filings -> pick -> download -> write `filing.json` |

In order, `download_filings()` does: **(1)** check the year text (a typo never costs a request), **(2)** company text -> symbol, **(3)** list the filings (cached 24 h), **(4)** choose which to fetch, **(5)** for each: XML already on disk? skip, else download. Files land in `data/raw/<SYMBOL>/<FY>/` with a small `filing.json` (company name, dates, links).

Ideas to be ready to explain:
1. **Cache first.** Three caches: company search, filing list (24 h), the files. A second run sends 0 requests.
2. **Throttle.** `_wait_turn` guarantees 3 seconds between any two requests.
3. **Retry only what is worth retrying.** Timeouts and 5xx are temporary; 403/429 mean "stop".
4. **One bad file must not ruin the batch.** A 404 on one file marks only that file missing.
5. **Never save garbage as data.** Check the first bytes: XML must start with `<?xml`, a PDF with `%PDF`; a block page is refused.
6. **Write safely.** Write to `name.xml.part`, rename when finished, so a crash never leaves a half file that looks valid.
7. **Take links from the answer, never invent them.**
8. **Fallback.** If NSE cannot be reached and a saved filing list exists (even older than 24 h), use it and print a notice; with `--refresh` a failure is reported, not hidden.

## 3.3 Step 2: Read the file (`parsing/`)

`xbrl_reader.read_filing(path)` opens the XML (cleaning forbidden characters first, remembering a warning), reads the **contexts** (who/when), works out the **current and previous year from the dates**, finds the **form's release date** in the header to pick the legacy or modern family, and returns simple `Fact` objects you can look up by tag name. `p6_mapping.py` says **which tag feeds which SEBI row**, separately for each family. It knows nothing about units or warnings: it only reads.

## 3.4 Step 3: Clean it into one report (`extraction/`, `core/`)

The XML is a **box of raw ingredients**: about 3,000 loose facts, two editions, units missing or wrong. Neither page should deal with that, so we prepare the ingredients **once** and hand both pages the same clean result.

**A number never travels alone.** Every number is a `Cell`:

| Field | Meaning | Example (Tata Steel Scope 1) |
|---|---|---|
| `value` | the number (or text) | `64.0` |
| `unit` | the standard unit shown | `tCO2e` |
| `status` | how we got it | `reported` |
| `as_filed` | exactly what the filing said | `64 MtCO2e` |
| `note`, `warnings` | harmless explanation / reasons to doubt it | "about 1,000,000 times too small ... not corrected" |
| `origin` | **where in the file it came from** (element, text, unit, year) | `TotalScope1Emissions = 64 MtCO2e` |

`status` is one of **reported** (the filing gave it), **not_reported** (the filing has nothing: *never* shown as 0), **calculated** (we added reported numbers, e.g. electricity = renewable + non-renewable) or **converted** (we changed the unit). A table row is a `Metric` (label + current-year `Cell` + previous-year `Cell`); the whole result is a `Principle6Report` (header facts, a dictionary of metrics, list tables, facilities, assurance, extras).

**Data instead of code.** SEBI's form is a *list* in `core/sebi_template.py` (12 Essential and 9 Leadership questions with the official wording and row labels); the *mapping* in `p6_mapping.py` says where each row's number comes from. To support a new filing format you edit data, not logic; the SEBI page simply loops over the template; the official wording lives in one place.

| File | Job |
|---|---|
| `extractor.py` | The loop that fills the template: for each row -> find tag -> clean -> convert -> `Cell` |
| `values.py` | Cleaning small bits of text: `"1,83,595"` -> `183595`; `"NA"` -> nothing; counting significant digits |
| `core/units.py` | One unit per topic (energy GJ from Terajoule/Petajoule/Megajoule, water kL, waste and air tonnes, greenhouse gases tCO2e, intensities "per ₹") and an explanation of every change |
| `checks.py` | Looks for numbers that do not make sense and **adds warnings** (never changes a number) |
| `report_io.py` | Saves the report as JSON in `data/parsed/` |

**What `checks.py` looks for:**

| Check | Example | What the reader sees |
|---|---|---|
| Scale | Scope 1 = 64 for 624 million GJ of energy | "about 1,000,000 times too small ... may have been typed in millions. Shown as filed; not corrected" |
| Rounded-away intensity | Intensity `0` while the total is not 0 | "not a real zero" |
| Air pollutant zero | POP/VOC/HAP = 0 (the PDF says "not material") | "A reported 0 can mean none, or not measured" |
| Totals add up | A filed total differs from its rows by more than 1% | "The rows above add up to X but the filing's own total is Y" |
| One digit of precision | `0.0000000004` | "Too coarse to compare" |
| Unit missing / monthly | Legacy energy; "Kg/Month" | "(unit not stated)"; labelled "per month", never x12 |

## 3.5 Step 4: Decide what to say (`views/`)

**Python decides, the template only prints.** `sebi_view.py`, `dashboard_view.py` and `trace_view.py` turn the report into plain objects (`CellView`, `RowView`, `TableView`, `CardView`...): ready-to-print text, numbers and flags. This pattern is called a **view-model**. Why: a decision like "which footnote number does this note get?" or "is this figure better or worse?" is easy to write and **test** in Python and awkward inside HTML. Every sentence and verdict can be tested without a browser, and the two pages cannot disagree because both are built from the same report.

## 3.6 Step 5: Print the page (`rendering/`)

`render.render_page()` builds the three views and hands them to the Jinja2 template `base.html`, which writes **one self-contained HTML file** (CSS inline, no JavaScript, opens offline).

**HTML in five minutes.** Text with tags: `<h1>`-`<h3>` headings, `<p>` paragraph, `<table> <thead> <tbody> <tr> <th> <td>` tables (`colspan` makes a cell span columns), `<ul><li>` lists, `<sup>` superscript, `<a href="#fn-E1-1">` a link (`#...` jumps to the element with that `id`), `class="..."` / `id="..."` names for styling and pointing.

**Jinja2 in five minutes.** `{{ value }}` prints; `{% for %}...{% endfor %}` repeats; `{% if %}` chooses; `{% macro %}` is a reusable mini-template; `{% include "sebi.html" %}` pastes another template; `{# ... #}` is a comment. **Autoescape** turns `<`, `>`, `&` in your data into `&lt;`, `&gt;`, `&amp;`, so text from a filing can never be mistaken for HTML (the filing is data from outside; never run it as code).

**CSS in five minutes.** A rule is `selector { property: value; }`. **Variables** (`--accent: #0f6b5c;`, used as `var(--accent)`) change a colour in one place. When two rules disagree the more **specific** selector wins. `@media (max-width: 640px)` applies only on narrow screens. **CSS grid** `repeat(auto-fit, minmax(270px, 1fr))` lets cards arrange themselves into 3 columns on a laptop and 1 on a phone. **CSS-only tabs:** two hidden radio buttons plus labels, and `#view-sebi:checked ~ .panel-sebi { display: block; }`. `<details>/<summary>` gives collapsible "Fine print" with no script. Every dashboard rule starts with `.dash` so it cannot restyle the SEBI tab.

**How to read the SEBI tab:** *Not reported* (grey italic) = the filing has nothing, never shown as 0 · `calc.` = we added reported numbers · `conv.` = we changed the unit · a small `ⓘ1` = a note under the table (**Note:** something unusual; **Doubtful:** the figure may be wrong) · `(unit not stated)` = older filings do not say · numbers use Indian grouping (2,47,98,900) while the full-precision value stays in the data.

## 3.7 Errors are pages, not crashes (`core/errors.py`, `views/error_view.py`)

The brief grades "a clear, specific message on the page". So every failure writes a real page, `error_<company>_<year>.html` (named `error_...` so it can never overwrite a good report, for example when NSE is down), with the exact sentence, what you typed, what to try, and **commands to copy**.

| Error class | When |
|---|---|
| `InvalidFiscalYear` / `UnsupportedYear` / `InvalidYearRange` | not a year / before FY 2021-22 / trend range reversed |
| `UnknownCompany` / `AmbiguousCompany` | NSE does not know it / several match (one command per match) |
| `NoFilingFound` | no BRSR for that year (lists the years it has: one command per year) |
| `NSEUnavailable` | NSE unreachable or blocking |
| `UnparseableFiling` / `FileNotAvailable` | the XML is damaged / NSE lists it but the file is gone |
| `SameCompany` | comparing a company with itself |

Ideas worth knowing: **exceptions carry data, not only text** (`NoFilingFound` carries the symbol and the available years, which is how the page offers commands). **One table, looked up by class**: `ERROR_INFO` maps each class to a title and hints, looked up through `type(error).__mro__` (this class, then its parent, then its grandparent), so a new error class we forget still gets its parent's page. **Two layers of catching** in the CLI: `except BrsrError` for expected problems, `except Exception` at the very outside for *bugs* (safe only there, because the program is ending anyway); `--debug` re-raises so a developer sees the traceback. **Even the explanation can fail** (a read-only folder): print the original error plus "could not write the explanation page", never hide the first problem. **Never promise in an error message something you have not tested.**

## 3.8 Every number traces back to the filing

The brief: *"Every figure shown must trace back to a filing."* An honest audit showed we only did half: the page named the source file, but an ordinary number did not say *which part* of it came from. The fix is a chain a stranger can follow:

```
a dashboard card -> Fine print: "Where it is in the filing: TotalScope1Emissions = 64 MtCO2e"
a SEBI number    -> hover: "From the filing: ..."
last section of the SEBI tab, "Where every number comes from": value, how we got it, element(s), text as filed
the page header  -> link to the XBRL file on NSE: search for the element name, the same text is there
terminal         -> python flow.py extract --company ... --fy ... --trace
```

How it is built: **a value remembers its origin** (`Cell.origin`, filled at the one place the number is read); **quote the file's spelling**, not ours (a reader searching the XML must find it); **a cell never loses its trace** (a calculated number lists every ingredient; a value the filing lacks remembers which elements were *looked for*, nothing is made up); only `https://` links become clickable (checked twice).

**How we KNOW the trace is true** (explain this in an interview): `tests/extraction/test_origin.py` builds the report with our code, then **separately** reads the raw XML with a plain regular expression, and asserts that every value shown (4,605 on the author's machine) matches an `(element, text as filed)` pair in the file. A test that checks a program with the program's own parser only proves it agrees with itself; a second, simpler way of reading the same file is evidence.

---

# Part 4. The dashboard

## 4.1 Who it is for, and the four questions

The reader is an **investor, journalist or student who has never opened a BRSR**. The page is ordered to answer what that person asks: **How big is the footprint? Better or worse than last year? Is it under control? Can I trust these numbers?** Structure: one plain sentence and a scoreboard first, then six topics in story order (energy, climate/greenhouse gases, water, air, waste, safeguards), then "Can I trust these numbers?" and a glossary. Detail comes after the summary.

**Design first, with real numbers.** Before coding we built `design/dashboard_mockup.html` with real Reliance figures, not dummy ones: dummy data is always tidy, real files are full of awkward cases, and a design that never met them breaks on the first real company. It also let the user say "this is friendly" while changing it was still cheap.

## 4.2 The honest rules (the heart of the dashboard)

1. **"Better" means better than the company's OWN figure last year.** Not a rating, not a score. The filings contain no benchmark or legal limit; inventing one would break "never invent numbers". A box on the page says so.
2. **Each figure has a direction:** lower is better for energy, gases, water and waste per ₹ of sales and for each air pollutant; higher is better for the renewable share and the recycled share. The directions are data (`metric_info.py`).
3. **"About the same"** = within 1% (amounts) or half a percentage point (shares).
4. **A doubtful figure** is shown exactly as filed, gets **no verdict**, and is **left out of every sentence** ("The greenhouse gas figure looks doubtful, so we do not quote it").
5. **A figure that only needs care** (unit not stated, a zero that may mean "not measured") is compared, with an asterisk and a note.
6. **Missing means "Not reported"**, never 0, never an arrow.
7. **A zero last year gives no percentage** ("Last year's figure was 0, so a percentage change cannot be worked out"): the zero probably means "not measured". **0 in both years** is "no change" but does not count in the scoreboard.
8. **A figure with no unit is not quoted in a sentence.**
9. **Intensity is shown per ₹ 1 crore** (filed figure x 10,000,000), because 0.0000807 GJ per ₹ is unreadable. Only the unit changes; the filed figure stays in the Fine print.
10. **Figures we calculate** are marked "calculated by us", inherit their ingredients' warnings and say how they were built.

## 4.3 How to read a card

```
Total energy used                        Lower is better ↓      <- plain title + which direction is good
46.42 crore GJ                                                  <- big number, friendly unit (lakh / crore)
✔ Improved   ▼ 2.0% lower than last year                        <- verdict in WORDS + symbol + arrow
2023-24 ████████████████  46.42                                 <- bars start at zero (never a cut-off axis)
2022-23 █████████████████ 47.36
What it is: ...    Why it matters: ...                          <- always visible, no jargon
▸ Fine print                                                    <- full numbers, how we calculated, where in the filing
✔ Reported by the company                                       <- where the number came from
```

**Never colour alone:** every verdict is words plus a symbol (✔ ✖ ≈ ?) plus an arrow, so the page works in black and white, for colour-blind readers, and on a phone.

## 4.4 Notes are calm, not alarming

Of 22 saved reports, 21 carried notes. Almost all describe **how the company filed** (unit not stated, a 0 that may mean "not measured", one digit of precision), not a mistake in the numbers, yet each used to be a loud yellow box with a warning triangle. The design rule now:

- **One neutral grey-blue "note" style on every page, the symbol ⓘ, never a warning triangle.** (Amber is kept only on error pages.)
- **Severity is said in words, not colour:** a footnote says **"Note:"** for something unusual and **"Doubtful:"** only for a figure that may be wrong. `analysis/warning_kinds.py` sorts every warning into *check* (probably right, handle with care) or *doubtful* (probably wrong); a warning nobody has classified defaults to *doubtful* ("when in doubt, say so") and a **guard test** fails when a new warning text appears, so nobody forgets to classify it.
- **Say it once.** If the same note applies to several cards of a topic it appears once under the cards (HDFC Bank's six air pollutants would otherwise repeat it six times).
- **The numbers are unchanged.** A doubtful figure is still shown as filed with no verdict. If someone asks "why not just fix Tata Steel's 64?": we cannot know what the company meant; correcting it would be inventing a number.

## 4.5 What reading real output taught us (the habit that matters)

All the tests passed at first; the problems below appeared only when we read real pages next to the companies' own PDFs.

| Found by looking at real companies | What we did |
|---|---|
| Double counting: a filing gives a plain total **and** a breakdown row with the same value, and we added both (a "rows don't add up" note exposed it: the gap was exactly half of one row) | Use the plain total if there is one; add rows only when there is none |
| ITC and Wipro file energy in Terajoule/Megajoule; the scale check ran only for GJ and was silently skipped | Convert the exact SI multiples so the check runs for them too |
| HDFC Bank: "Water taken in ▲ Up from 0 -> Got worse" | A zero base gives "can't compare", never a guess |
| A sentence "used 19,75,098 unit not stated of energy" | A figure with no unit stays out of sentences |
| "NOx, SOx, PM... stayed about the same" when all were 0 | Zeros are named as zeros and do not count in the scoreboard |
| Shares: "1.5% ... last year 1.4%" looked like a 0.1 jump when the change was 0.05 | Small shares keep two decimals |
| ICICI Bank: "Waste per ₹ crore was 100% more", but the filing wrote the figure with one digit (`2e-10` then `4e-10`): the true change is anywhere from +40% to +200% | **False precision.** Count significant digits; one digit = "Too coarse to compare"; the exact total is ranked instead |
| My hand-typed mockup said "0.06 percentage points"; the exact value is 0.0547 | The code was right: compute, never type |
| A constant defined twice in one file silently replaced the first | Python does not warn about this; read your own code |

---

# Part 5. The extensions

## 5.1 Multi-year trends (`flow.py trends`)

One page with a **column per financial year**: the five topics with a mini bar per year and a verdict, then every figure of SEBI's tables year by year, then the figures later filings changed.

**The idea that makes it possible: every filing holds two years** (its own and the year before). So (1) a **missing year can still be shown**: NSE has no Tata Steel FY 2021-22 filing, but the FY 2022-23 filing's previous-year column holds the company's own FY 2021-22 figures; we show them in a shaded column marked "figures from the FY 2022-23 filing": never a zero, never a guess. (2) A year can be **checked against what the next filing says about it**; if they differ, the company **restated** the figure.

What the real data taught us before we wrote the rules:

| Found | Rule |
|---|---|
| Tata Steel FY 2022-23 energy "857" (consolidated, no unit) vs next filing 559,969,887 GJ (standalone) | A restatement only counts when **both years are on the same basis**; otherwise mark "≠ different basis, not comparable" |
| Wipro FY 2022-23 energy is exactly 1,000 times the next filing's figure | Only compare figures with the **same, stated unit**; do not guess it was a unit slip |
| Wipro 6515.4 vs 6515.0 | Differences under **0.5%** are rounding, not restatements |
| Tata Steel electricity 28.4 M GJ vs 19.5 M GJ in the next filing | A real restatement: keep the figure **as filed in its own year**, mark ⟲, show the later figure on hover |

**The verdict** takes the latest year with a figure and walks back one year at a time **while the basis and the unit stay the same**; the result is compared with the first year of that block. If earlier years were left out the sentence says why; if only one year is left the chip says "Can't compare" with the specific reason. A damaged year becomes a flagged column and the page still works; only problems with the whole request give an error page.

**Code in three layers, each testable alone:** `workflows/trend_loader.py` (files + NSE; one bad year becomes a flagged entry, not a crash), `analysis/trend_model.py` (pure logic: columns, borrowed years, restatements, basis changes), `views/trend_view.py` + `trends.html` (words and print).

**Two bugs found by LOOKING at the page:** a doubtful "64 tonnes" in a row scaled in crores rounded to **0** (a reader would see a zero for something that is not zero: now a figure too small for the row's scale is written in its own unit); and the table collapsed into a stack of boxes because its CSS class `trend` collided with `.dash .trend { display: flex }` (found by having the browser print `TABLE display=flex`). **When a layout is weird, measure instead of guessing, and keep class names specific.**

## 5.2 Year-on-year summary (`flow.py summary`)

One page that answers: *since last year, which three figures improved most and which three got worse?* You give only the company; the newest year NSE has is used. The page prints **how "better" is decided**, lists every figure it compared, and every figure it did **not** rank with the reason; it never pads the list ("Only 2 figures improved").

Three rules came from printing a text ranking for four real companies and reading it:

| What we saw | Rule |
|---|---|
| Tata Steel's renewable share went 0.0655% -> 0.2415%: **+269%**, the biggest "improvement", but only **0.18 of a percentage point** | Rank **shares in percentage points**, amounts in percent |
| Total energy and "energy per ₹ of sales" are the same story and would fill two of six places; a total rises when a company just grows | Rank the **per-sales figure instead of its total**; quote the total as context |
| HDFC's recycled share was 100% both years and the page said "reported as 0 in both years" | A result carries the **signed size of the change**; only a real 0 -> 0 is left out |

**Where last year's figures come from:** the previous-year column of the **same** filing, so both years use the same reporting basis. Last year's *own* filing is a bonus (it only marks figures restated since). Two different failures, two different results: **last year's own filing missing or damaged** is *not* an error (the page says why, e.g. "NSE has no BRSR filing of its own for FY 2021-22"); **the newest filing missing or unreadable** means nothing to summarise, so an error page with the specific reason.

## 5.3 Company comparison (`flow.py compare`)

"Which company is better?" is easy to get wrong: Tata Steel's total energy is **888 times** Wipro's, because a steel plant burns more than an office. Printing "Wipro: lower" next to a total would be true and misleading. The brief says to compare **fairly**: think of totals vs intensity, differing units, and fields one company did not report. Every rule below is a test.

| Rule | Why |
|---|---|
| **Totals are shown, never ranked** ("Depends on size" and a plain ratio like "888 times") | A total measures size as much as effort |
| **Verdicts only on the figure per ₹ 1 crore of sales and on shares** | They do not grow just because the company is bigger |
| **A share is compared in percentage points**; "N times" is said only for amounts | 0.07% -> 0.24% is "+269%" but 0.17 of a point |
| **Both numbers of a row use one unit and one scale**, but never "0 crore" (the shared scale is used only if the smaller number is still at least 0.1 of it) | You can only read across a row in the same words; a real small figure must not vanish |
| **Not reported says "Not reported" and who**, never 0 | A zero would look like a good result |
| **A different or unstated unit, a doubtful figure or a one-digit intensity is shown as filed and not compared** | The promise of the whole project |
| **Standalone vs consolidated is warned about**; no benchmark exists | A consolidated figure includes subsidiaries |

The existing `compare()` function (the one that says improved/worse between two *years*) is reused with the two *companies* in the two *years'* places; only its words changed.

## 5.4 The two viewer pages (`flow.py hub`)

`output/` fills up with pages, so the viewer gathers them behind **two simple pages**: `index.html` (pick a **company**, a **year** and what to **show**: Report / Year-on-year / Multi-year trend; a button is greyed out, with a tooltip naming the command, when that page was not made) and `compare_companies.html` (pick a year and two companies). A big **Compare two companies** button joins them. The first design had a search box, a long dropdown of every page, Previous/Next and a compare panel on one screen and the dashboard started in the middle of the page; the lesson: **one job per screen, the rest one click away.**

- **Why JavaScript here (and only here):** a dropdown that changes what you see cannot be done with HTML and CSS alone. The report pages inside still have none. Each viewer is one self-contained file when embedded (the two link to each other, so keep them in one folder); without a script they show a plain list of links.
- **Keeping it safe:** pages travel as JSON with every `<` written `<`, so a `</script>` inside a page cannot end the block early; names go in with `textContent`, never `innerHTML`; the shown page lives in `<iframe sandbox="allow-popups ...">` without `allow-scripts`, so even a page with a script could not run it.
- **In-page links in a framed page:** a page shown through `srcdoc` takes the *viewer's* address, so a link such as `#dash-energy` tried to load the viewer into the frame (a 404). Fix: add `<base href="about:srcdoc">` for the frame only. This was reproduced in Edge before fixing.
- **The picker keeps the order you chose.** The file `RELIANCE_vs_TATASTEEL...` is alphabetical, so showing it used to flip "A = Tata Steel, B = Reliance" and the next change opened the wrong pair. Anything that "syncs" a control to a page must not undo what the user just chose.
- **Offline filling (`workflows/missing_pages.py`):** `hub` first makes, from saved filings only, the comparisons, year-on-year summaries and trends that would otherwise be greyed out, **never overwriting** a page made by `summary`/`trends`, never inventing a year (a trend covers only years in a row that are all saved), and saying "not saved on this computer" when last year's own filing is absent. `--only-existing` skips this.
- **How JavaScript was tested without a JavaScript test tool:** pytest checks everything that is plain Python (names, groups, the JSON, the written file, the safety checks). The behaviour was checked in **real Edge** by a throw-away copy of the page with a script that acts like a user (picks, clicks, changes the address) and prints what happened, captured in a screenshot. A test can be wrong too: the first such script came out blank because *it* was broken.

## 5.5 The samples and the "freshness" test

`python flow.py samples` rebuilds everything in `samples/` (5 report pages, trend, summary and comparison pages, error pages, and the two viewers) from one list in `workflows/samples.py`; reports are built from filings already on disk, and the error samples are made by **really triggering the errors**. The test `committed_..._are_up_to_date` rebuilds every sample and compares it character for character with the committed file, so a stale sample fails the build until someone re-runs the command. (Twice we judged a design on an out-of-date page by mistake.)

---

# Part 6. Habits that kept the numbers right

1. **Look before you build.** A short spike (DevTools, a few downloads, a script that prints facts) answered "what are the facts?" before any design. Three hours of looking saved ten of rewriting.
2. **Test on more than one company.** A second company revealed the fifth form edition; four never-used companies (NTPC, HUL, ICICI Bank, L&T) proved "not hard-coded".
3. **Read real output next to the PDF.** Tests prove the code does what you *thought*; reading real output shows whether what you thought was *right*. Both are needed.
4. **Judge a design on output made by the current code.** Regenerate before looking at a screenshot (stale pages misled us several times). The samples test now enforces this.
5. **A test (or a check) can be wrong too.** When a result surprises you, check the checker. An assertion that can never fail (`text[:0]`) proves nothing; ask "what change to the code would make this fail?".
6. **Guard tests for things people forget:** every warning is classified; samples are up to date; imports only go one way; every error class has a page; no ⚠ or yellow creeps back.
7. **Evidence tests, not agreement tests:** check output with a *second, simpler* reader (the raw-XML test).
8. **Measure, do not guess:** when a layout is weird, have the browser print what it computed.
9. **Change one variable at a time:** the "pip is broken" clean-checkout failure was Windows' 260-character path limit (a deeply nested folder silently lost files); the same commands worked in a short path. Keep paths short; run clean-clone checks in `%TEMP%\x`.
10. **Safe renames:** commit first; look at the real import graph; `git mv` so history follows; rewrite imports with a script that reads each file's syntax tree (a find-and-replace breaks multi-line imports); let the tests and the freshness test be the safety net; run the real commands from another folder. Code that finds files from its own position (`Path(__file__).parent.parent`) breaks silently when files move: keep **one** place (`core/paths.py`) that knows the project root. When many files mention an old name, search for **every** mention (code, docstrings, page text, tooltips, tests, docs, committed samples).
11. **Say what is true.** If the page and command exist but the viewer does not offer them yet, the answer to "is it done?" is "not completely". Never promise in a message something you have not tested.
12. **Tool traps:** in PowerShell a backtick is an escape character (a backtick inside a double-quoted string silently inserted an invisible NUL into a document); after scripted edits to text files, search for strange characters. A script that "does everything" can undo a decision you already made (it re-created two companies the user had removed): check its result against earlier decisions.
13. **Where a module lives is decided by its users.** `friendly.py` ("4.7% less than last year") sits in `core`, not `views`, because `analysis` uses it; putting it in `views` would make `analysis` import *upwards*.

---

# Part 7. Interview checklist

First practise the **60-second answer** to "walk me through the project":

> "Give it a listed Indian company and a financial year and it produces one HTML page with that company's BRSR Principle 6 environment disclosures twice: exactly in SEBI's format, and as a plain-English dashboard. It uses NSE's structured XBRL filing instead of PDF tables. The flow is: find the company, download its filing politely, read the XML, map each value to SEBI's template rows, clean and check it, decide what to say, and print the HTML. Three rules run through everything: never invent a number, show doubt instead of hiding it, and keep extraction separate from presentation."

If you remember one sentence: **"Python decides, the template only prints."**

## 7.1 Flow and architecture

| Question | Short answer |
|---|---|
| Walk me through what happens when I run the command. | `flow.py` -> `cli/flow_cli` reads the options -> `workflows/pipeline` orders the steps -> `download` finds the company and saves the XML (**first**) -> `parsing` reads it into facts -> `extraction` fills SEBI's rows, converts units, adds warnings -> `views` decide the words and verdicts -> `rendering` prints one HTML page. |
| How is the code organised? | Nine packages in a strict order (`core`, `download`, `parsing`, `extraction`, `analysis`, `views`, `rendering`, `workflows`, `cli`); a package imports only from itself and earlier ones; a test enforces it. |
| Why separate views from templates? | Decisions are testable in Python and awkward in HTML; both pages are built from the same report so they cannot disagree. |
| Why one `flow.py`? | One entry point like `git`/`pip`: the whole flow by default, each step or extra a sub-command with its own `--help`. The root has no logic. |
| Why no database? | Files are enough: raw filings, cached lists, a clean JSON per report. Nothing needs querying. |
| Why only three libraries? | "Keep dependencies reasonable." The XML reader is Python's built-in; fewer libraries, fewer ways to break on a stranger's computer. |
| How do I run it from a clean checkout? | Clone, create a venv, `pip install -r requirements.txt`, `python flow.py --company "Tata Steel" --fy 2025-26 --open` (tested in a fresh clone). |

## 7.2 Data, NSE and accuracy

| Question | Short answer |
|---|---|
| How did you find the data source? | DevTools Network tab on NSE's BRSR page: the page calls `/api/corporate-bussiness-sustainabilitiy` after a cookie-setting home-page request; NSE's own JavaScript showed the `from_date`/`to_date` trick for older years. |
| Why XBRL, not the PDF? | Structured (named elements, units, periods), so values are exact and traceable; PDF tables are fragile. The PDF stays optional. |
| What is XBRL? | An XML format where every number has a name, a unit and a period. |
| How do you know which year a number is? | From each fact's context **period end date**, matched to the year asked for and the year before. |
| What is hard about the data? | Five form editions, units missing or wrong (Tata Steel typed millions as tonnes), numbers as text with Indian grouping, zeros that mean "not measured", illegal characters in one file, revisions, standalone vs consolidated. Each is handled and tested; the policy is **flag, never fix**. |
| How do you handle a company with a revised filing? | NSE keeps one row per company per year and a revision replaces the original; we use the row NSE lists and print the dates. |
| How polite are you to NSE? | Cache lists and files, 3 seconds between requests, stop on 403/429, retry only temporary failures; a second run sends 0 requests. |
| Is it hard-coded to some companies? | No: the mapping is by SEBI's element names. Four never-used companies were run end to end. |
| How do you handle different units? | `core/units` converts to one unit per topic (GJ, kL, tonnes, tCO2e, per ₹), says "unit changed by us" and keeps the original in the fine print. |
| Why "Not reported" and not 0? | A zero claims the company measured and found none. If the filing has nothing, the honest statement is that nothing was reported. |
| How do you know a number really comes from the filing? | Every `Cell` keeps its `origin`; a test re-reads the raw XML with a plain regex and checks every value shown. A value without a trace fails the test. |
| What can you not detect? | A small error (a few percent) or a wrong figure that still looks plausible. It is in the README's limitations. |

## 7.3 Dashboard and SEBI fidelity

| Question | Short answer |
|---|---|
| Who is it for? | A non-expert: investor, journalist, student. Four questions in order: how big, better or worse, under control, can I trust it. |
| How do you decide "better"? | Against the company's **own last year**: each figure has a direction (lower is better for energy, emissions, water, waste per ₹; higher for renewable and recycled shares); within 1% (half a point for shares) is "about the same". |
| Why not compare with an industry benchmark? | The filings contain none; inventing one would break "never invent numbers". The page says so. |
| When is a figure "can't compare"? | Missing, doubtful, different or unstated unit, one-digit precision, or zero last year (a percentage cannot be worked out). |
| Why intensity per ₹ crore beside totals? | A bigger company uses more in total; the per-sales figure is fairer. |
| What does the page do with Tata Steel's Scope 1 = 64? | Shows it as filed, with a note, no verdict, left out of sentences; the trace line shows `TotalScope1Emissions = 64 MtCO2e`. It never rescales it. |
| Why are the notes grey and not yellow? | Most describe how the company filed, not a mistake; a calm ⓘ note with severity in words ("Note" vs "Doubtful") informs without alarming. |
| How does the SEBI tab match the template? | Question numbers (E1-E12, L1-L9), tables, row labels and units come from `core/sebi_template.py`, the same data the extractor fills; a test checks every question and row label appears in SEBI's order. |
| Why CSS-only tabs? | No JavaScript needed; the page is safe, portable and opens from a file. |
| How do you know a non-expert understands it? | Honest answer: by reading every sentence against real data, and by the two-minute test with a non-technical person (do it and report what they said). |

## 7.4 Errors, tests and code quality

| Question | Short answer |
|---|---|
| Show me an error. | `python flow.py --company "Xyzzy Quux" --fy 2023-24 --open`, then `--fy 2019-20`. |
| Why an error *page*? | The brief wants the message on the page; a page is what a non-technical user sees. The file is named `error_...` so it never overwrites a good report. |
| What happens if one year of a trend is damaged? | It becomes a flagged column with its reason; the rest still shows. Only a problem with the whole request is an error page. |
| What if last year's report is missing (summary)? | Not an error: the previous-year column of the newer filing is used and the page says why. |
| What do the tests cover? | Unit conversion, the XBRL reader, every SEBI row, the verdict and sentence rules, HTML well-formedness and escaping, error pages, the command lines; plus the architecture, trace and samples-freshness tests. |
| How is extraction separated from presentation? | `parsing`/`extraction` know nothing about HTML; `views` decide; `rendering` prints; the import rule is a test. |
| Weakest part / what would you do with more time? | Small errors are undetectable; PPP and per-tonne intensities are unreliable so they appear only in the SEBI tab; tested in Edge on Windows only; dashboard topic tiles follow totals while the summary uses the per-sales figure (a decision left open). More time: a benchmark if a public source existed; more browsers. |

## 7.5 AI use and the extensions

| Question | Short answer |
|---|---|
| Which AI tools and for what? | Claude Code: planning in phases, exploring NSE and the XBRL files, writing and testing the code, reorganising into layers, writing the docs. Every result was run and checked against real filings (README lists it). |
| What did the AI do and what did you do? | Be truthful about your part. The decisions are in `context.md`; this file explains each concept; read the part for whatever you are asked about. |
| Explain this function. | Open it, read the docstring at the top, then read it aloud in plain words. |
| Trends / summary / comparison in one line each | Trends: every metric, every year, missing years flagged, basis changes never look like improvements. Summary: three best and three worst vs last year with "better" defined. Comparison: totals shown not ranked, verdicts only on per-₹ figures and shares, one unit per row, "Not reported" says who. |

## 7.6 Hard questions that can come from anywhere

| Question | Short answer |
|---|---|
| Most important design decision? | Separating *what is true* (extraction) from *what to say* (views) from *how it looks* (templates). |
| Hardest data problem? | Messy filings; the policy is to flag, not fix. |
| What if NSE changes its website? | Only `nse_client` and `filings` change; everything after the download reads local files. |
| What if SEBI changes the form? | Add the new element names to `p6_mapping`; the template and views do not change. |
| Why should we trust the numbers? | Every number carries its origin, a test re-checks them against the raw XML, doubtful ones are shown as filed with a note. |
| What is not done? | Say it plainly: no benchmark (none in the filings); small errors undetectable; Chromium/Windows only. |

---

# Part 8. Try it yourself

1. `python flow.py --help` and `python flow.py trends --help`: read every line and match it to `cli/flow_cli.py`. What does a bare `python flow.py` print?
2. `python flow.py --company "Tata Steel" --fy 2025-26 --open`. Read the terminal lines in order: which step prints first? Then run it again: how many requests were sent?
3. `python flow.py download --company Infosys`, then open `data\raw\INFY` and look at the folders and `filing.json`.
4. `python flow.py extract --company TATASTEEL --fy 2025-26 --questions E6 --trace`: read the `↳` lines under Scope 1. Search the XML (link in the page header) for `TotalScope1Emissions`.
5. Open `core/sebi_template.py` (find question E6) and `parsing/p6_mapping.py` (find which tag feeds `E5.nox` in the two editions).
6. Open `data\parsed\RELIANCE\2023-24.json` and read each field of `E1.electricity`.
7. Open the Tata Steel Climate section: find the dashed grey card, the "Can't compare" chip and the headline that refuses to quote the figure. Compare with HDFC Bank FY 2022-23 ("unit not stated", "Last year's figure was 0").
8. In `views/metric_info.py` change the *Why it matters* line of "Water taken in", re-run, and see it change. In `analysis/comparison.py` change `SAME_WITHIN_PERCENT` from 1.0 to 5.0, re-run Reliance, then change it back and run `pytest` (the dashboard tests notice).
9. Break the layer rule on purpose: add `from brsr_p6.views.summary_view import build_summary_view` at the top of `core/models.py` and run `pytest tests/test_architecture.py`. Read the failure, then undo.
10. `python flow.py summary --company "Wipro"` (why is the setbacks box empty?) and `python flow.py compare --company-a "Tata Steel" --company-b "Wipro" --fy 2025-26`: which rows say "Depends on size"?
11. `python flow.py hub --open`: pick a company with no summary page and hover the greyed button; press **Compare two companies**.
12. **The two-minute test:** show the dashboard to someone who knows nothing about ESG and ask them to explain the Water section back to you. Anything they cannot explain is a sentence to rewrite.
13. Make a clean clone in a short folder (`%TEMP%\x`), create a new venv, `pip install -r requirements.txt`, run `pytest`. What would you check if it failed only there?

---

# Part 9. Glossary

**API** a door on a server meant for programs · **assert** a statement that must be true in a test · **autoescape** Jinja turning `<` into `&lt;` so data cannot become HTML · **BRSR** Business Responsibility and Sustainability Report · **cache** a saved copy so we do not ask again · **Cell** one number with its unit, status, origin and warnings · **CLI** command-line interface · **commit** a saved snapshot in git · **context (XBRL)** who and when a fact is about · **cookie** a visitor badge a site gives your browser · **dataclass** a class that only holds data · **dependency** a library our code needs · **dependency injection** passing in fakes so tests need no internet · **edition (form)** the version of SEBI's form a filing used · **element** the XBRL name of a number (`TotalScope1Emissions`) · **exit code** 0 = success · **fact** one reported value · **false precision** claiming accuracy the filing does not contain · **FY** financial year (FY 2025-26 = 1 Apr 2025 to 31 Mar 2026) · **GJ / kL / tCO2e** gigajoule / kilolitre / tonnes of CO2 equivalent · **guard test** a test that fails when someone forgets a step · **intensity** a figure per unit of sales (per ₹ crore) · **JSON** the usual data format of APIs · **layer rule** a package imports only from itself and earlier packages · **legacy / modern** the two families of form editions · **module / package** one `.py` file / a folder of them · **mro** the order Python searches a class and its parents · **origin** where in the filing a number was read · **pin** fix a library to an exact version · **PPP** purchasing-power-parity adjusted (per million US dollars) · **Principle 6** the environment part of BRSR · **repo** a git-tracked project · **restated** a later filing changed an earlier year's figure · **sandbox (iframe)** a frame that may not run scripts · **standalone / consolidated** the company alone / with its subsidiaries · **taxonomy** the regulator's dictionary of XBRL tags · **template (Jinja)** an HTML file with placeholders · **unit status** reported / not_reported / calculated / converted · **venv** a private Python environment · **view-model** plain objects holding ready-to-print values · **XBRL** XML for business reports · **XHR / Fetch** background requests a web page makes for its data
