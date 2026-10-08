# Learnings

Plain-English notes on every concept we use, written for someone new to programming.
One section per phase. Each new term is explained the first time it appears.
**Tip for the interview:** after reading a section, close the file and try to explain it out loud in your own words.

---

# Phase 0: Project setup

## 0. What did we do in Phase 0, and why?

Before writing any "real" logic, we built the **empty house**: folders, a list of libraries we need, a way to run the program, and a way to test it. Why? So that:

- anyone (you, a teammate, the reviewer) can set the project up on a fresh computer with a few commands,
- we always have something that **runs and is tested**, and we grow it step by step instead of building everything and hoping it works.

| What we made | In one line |
|---|---|
| `.venv/` + installed libraries | A private toolbox for this project |
| `requirements.txt` | The shopping list of libraries |
| `.gitignore` | The "don't save these" list for git |
| `README.md` | The project's front page / instruction manual |
| `main.py`, `brsr_p6/cli/main_cli.py` | The program's door: reads what you type |
| `tests/cli/test_cli.py`, `pytest.ini` | Automatic checks that the door works |
| `data/`, `samples/`, `tests/` folders | Places where things will live later |
| `plan.md`, `context.md`, `learnings.md` | Our notes: the plan, the memory, and this file |

> **Git is not set up yet.** You chose to do that at the end. Section 5 explains what git is so you understand it, and shows exactly what we will run later.

---

## 1. The terminal (PowerShell)

A **terminal** is a window where you control the computer by typing **commands** instead of clicking. On Windows ours is **PowerShell**. PyCharm has one built in (bottom tool-window called *Terminal*).

- A **command** is an instruction, e.g. `python main.py --help`.
- A **folder path** is the address of a folder, e.g. `C:\Users\<your name>\PycharmProjects\...`.
- The terminal always has a **current folder** ("where you are"). Commands like `python main.py` look for `main.py` in that current folder. In PyCharm's terminal it starts in your project folder.
- An **argument / option** is extra information after a command: in `python main.py --company "Tata Steel"`, `--company` is an option and `"Tata Steel"` is its value. Quotes are needed when the value has spaces.

---

## 2. Python, libraries and `pip`

- **Python** is the programming language we write in.
- A **library** (also called *package*) is code written by other people that we reuse instead of rewriting. Example: `requests` knows how to download things from websites.
- **pip** is Python's "app store" for libraries. `pip install requests` downloads and installs `requests`.

Our three libraries and why:

| Library | Used for (later phases) |
|---|---|
| `requests` | Download filings from NSE |
| `Jinja2` | Fill HTML templates with data to build the report page |
| `pytest` | Run automatic tests |

---

## 3. Virtual environment (`.venv`)

**Problem:** Project A needs `requests` version 2.20, project B needs version 2.34. If everything is installed in one global place they fight.

**Solution:** a **virtual environment** = a private folder containing its own copy of Python and its own libraries, **for this project only**. Ours is the folder `.venv`.

- Created with: `python -m venv .venv` (already done by PyCharm for you).
- **Activating** it means "make the commands `python` and `pip` use the ones inside `.venv`". On Windows: `.venv\Scripts\Activate.ps1`. PyCharm's terminal usually does this automatically (you will see `(.venv)` at the start of the prompt).
- If PowerShell says *"running scripts is disabled on this system"* when activating, run once: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`. Or skip activation and call Python directly: `.venv\Scripts\python.exe main.py --help`.
- `.venv` is **big and specific to your computer**, so we never share it. We share the *shopping list* (`requirements.txt`) and let others rebuild it.

---

## 4. `requirements.txt`

A plain text file listing the libraries the project needs. Ours:

```
requests==2.34.2
Jinja2==3.1.6
pytest==9.1.1
```

- Install everything in one go: `pip install -r requirements.txt` (`-r` = "read the list from this file").
- `==2.34.2` means "exactly this version". We **pin** versions so everyone, including the reviewer, gets the same behaviour we tested. Without pinning, a future release could silently change something and break the project.
- Lines starting with `#` are **comments**: notes for humans, ignored by pip.
- We listed 3 libraries but 13 got installed. The other 10 (`urllib3`, `certifi`, `MarkupSafe`, ...) are **dependencies of our libraries** (libraries need libraries). pip installs them automatically. See everything with `pip freeze`.

**Why it matters for the assignment:** the brief says the code must "run from a clean checkout". This file is what makes that true.

---

## 5. Git (explained now, set up at the end)

**Git** is a tool that records the **history** of your project. Think of "save points" in a video game, or "version history" in Google Docs, but much more powerful.

What git gives you:
- **Undo:** go back to how the project looked yesterday.
- **History:** who changed what, when and why.
- **Safe experiments:** try something risky without fear.
- **Sharing:** upload the project so others can download it.

Key words:

| Word | Meaning |
|---|---|
| **Repository (repo)** | A project folder that git is tracking, plus its full history |
| **`git init`** | "Start tracking this folder." Creates a hidden folder called `.git` inside your project where git stores all the history. Before `git init`, the folder is just a folder. You run it **once per project**. |
| **Commit** | One save point: a snapshot of all tracked files plus a short message, e.g. "Phase 0: project skeleton" |
| **`git add`** | Choose which changes go into the next commit (like putting items in a box before sealing it) |
| **`git commit -m "message"`** | Seal the box: create the save point |
| **`git status`** | "What has changed since the last save point?" |
| **GitHub** | A **website** that stores git repositories online. **Git** is the tool on your computer; **GitHub** is the online home. (Not the same thing!) |
| **`git push`** | Upload your commits to GitHub |
| **`git clone`** | Download a repo from GitHub to a new computer |

**Why the assignment needs it:** you must submit a **link to a GitHub repository**.

**Current status:** git is not installed on your PC yet, and you decided to handle it at the end. When we do, the steps are:

```powershell
# 1. Install git (once), then restart PyCharm
# 2. In the project folder:
git init                              # start tracking
git status                            # see what git sees (note: .venv etc. are NOT listed, thanks to .gitignore)
git add .                             # put everything (except ignored files) in the box
git commit -m "Phase 0: project skeleton"
# 3. Create an empty repo on github.com, then:
git branch -M main
git remote add origin <the-url-github-gives-you>
git push -u origin main
```

---

## 6. `.gitignore`

A text file that tells git: **"never track these files."** One pattern per line.

Ours, line by line:

| Line | Why ignored |
|---|---|
| `.venv/` | Huge, and anyone can rebuild it from `requirements.txt` |
| `__pycache__/` and `*.pyc` | Python's automatic speed-up caches; they change constantly and are useless to others |
| `.pytest_cache/` | pytest's own cache |
| `.idea/` | PyCharm's personal settings for your computer |
| `Thumbs.db`, `.DS_Store` | Junk files Windows/macOS create |

`*` is a **wildcard** meaning "anything": `*.pyc` = every file ending in `.pyc`. A trailing `/` means "this is a folder".

We did **not** ignore `data/raw/` yet, because we might need to commit hand-downloaded filings (the assignment allows it). We decide in Phase 1.

---

## 7. `.gitkeep`

Git only tracks **files**, not empty folders. If `data/raw/` is empty, git would forget it exists and a fresh download would lack the folder. So we put an empty file named `.gitkeep` inside. The name has no special meaning to git; it is just a common convention for "keep this folder".

---

## 8. `README.md` and Markdown

- **README** = the front page of the project. GitHub shows it automatically when someone opens the repo. The reviewer reads it first, and the assignment lists exactly what it must contain (setup, run commands, inputs to try, parts completed, extraction approach, limitations, AI tools used, design note).
- **`.md` = Markdown**: a simple way to format text using plain characters: `# Heading`, `**bold**`, `- bullet`, `` `code` ``, and tables with `|`. PyCharm and GitHub display it nicely. Our `plan.md`, `context.md` and this `learnings.md` are Markdown too.

Our README is a skeleton: setup/run sections are real, the rest says *TODO* and will be filled as we build.

---

## 9. Our project notes

| File | Purpose |
|---|---|
| `plan.md` | The to-do list: phases and tasks in priority order |
| `context.md` | The project's memory: requirements, facts we verified, decisions, progress log |
| `learnings.md` | This file: concepts explained |

---

## 10. Tour of the project folder

```
BRSR Principle 6 .../
├── main.py            Entry point. Tiny on purpose.
├── brsr_p6/           Our code lives here (a "package")
│   ├── __init__.py    Marks the folder as a package
│   └── cli.py         Reads command-line input
├── tests/
│   └── test_cli.py    Automatic checks for cli.py
├── pytest.ini         Settings for pytest
├── data/raw/          Downloaded filings will go here (cache)
├── data/parsed/       Filings after we convert them to JSON
├── samples/           Example generated HTML pages
├── requirements.txt   Library shopping list
├── .gitignore         Git "don't track" list
├── README.md          Front page
├── plan.md  context.md  learnings.md
├── .venv/             Private toolbox (not shared)
└── .idea/             PyCharm settings (not shared)
```

**A change from the plan:** `plan.md` originally put the code in `src/brsr_p6/`. We put it directly in `brsr_p6/` instead. Reason: this way `python main.py` and `pytest` just work, with no extra "install your own project" step. Simpler for you and for the reviewer.

### `main.py`
The file you run. It does one thing: call `main()` from `brsr_p6.cli`. We keep it tiny so the real logic lives in the package, where it can be tested and reused.

### `brsr_p6/` and `__init__.py`
- A **module** is a single `.py` file (like `cli.py`).
- A **package** is a folder of modules that Python treats as one unit. The file `__init__.py` is what marks the folder as a package. It can be (nearly) empty.
- That is why `main.py` can write `from brsr_p6.cli import main`: "from the package `brsr_p6`, module `cli`, bring in the function `main`".

### `brsr_p6/cli/main_cli.py`: "CLI" = Command-Line Interface
It reads what the user typed after `python main.py`. It uses `argparse`, a tool that comes with Python (nothing to install). Walk-through:

- `build_parser()` describes the options we accept: `--company` and `--fy`, both `required=True`. `argparse` then gives us `--help` and clear error messages for free.
- `main(argv=None)`:
  1. `parse_args(argv)` reads the options (if `argv` is `None` it reads the real command line; tests pass in their own list).
  2. For now it just prints what it received. The real work comes in later phases.
  3. `return 0` is the **exit code**: `0` = "success" (the operating system and other programs read this). Non-zero means failure. `argparse` uses `2` for "you typed it wrong".

---

## 11. Small Python ideas you met in the code

- **Function:** a named, reusable block: `def build_parser(): ...`. `return` hands back a result.
- **Import:** `import argparse` / `from x import y` reuse code from elsewhere.
- **Docstring:** the text in triple quotes `"""..."""` right under a function or at the top of a file: documentation for humans.
- **f-string:** `f"Received company={args.company!r}"`. The `f` before the quote lets you put variables inside `{}`. The `!r` shows the value with quotes (`'Tata Steel'`), which is handy for spotting stray spaces.
- **Type hints:** `argv: list[str] | None = None` means "argv is a list of strings, or `None`; default is `None`". `-> int` says the function returns a whole number. Python does not enforce these; they are documentation that helps you and your editor.
- **`if __name__ == "__main__":`** When you **run** a file directly, Python sets a built-in variable `__name__` to `"__main__"`. When a file is **imported** by another, `__name__` is the module's name instead. So code under this `if` runs only when you run the file directly, not when tests or other files import it. That is why `main.py` uses it.
- **`sys.exit(main())`** ends the program and passes `main()`'s return value to the operating system as the exit code.

---

## 12. Tests and `pytest`

A **test** is a small piece of code that checks another piece of code works. You run all tests with one command: `pytest`. Green = pass, red = something broke.

Why bother? When we change code in Phase 6, the tests tell us in 1 second if we accidentally broke something from Phase 3. For this project, tests will also protect **data accuracy** (a graded item).

Our three tests (`tests/cli/test_cli.py`):

| Test | Checks |
|---|---|
| `test_parser_reads_company_and_fy` | Typing `--company "Tata Steel" --fy 2023-24` gives back exactly those values |
| `test_missing_arguments_exit_with_error` | Forgetting the options makes the program stop with exit code 2 |
| `test_main_returns_zero_and_echoes_input` | A valid run returns 0 and prints the company name |

Words in the tests:
- **`assert`**: "this must be true, otherwise the test fails".
- **`pytest.raises(SystemExit)`**: "I expect the code to stop the program; that is correct behaviour here".
- **`capsys`**: a pytest helper that captures what the code `print`s so we can check it.
- Test files must be named `test_*.py` and test functions `test_*`, so pytest finds them.
- **`pytest.ini`** holds pytest settings. `pythonpath = .` lets tests write `from brsr_p6.cli import ...`.

---

## 13. What we tested, and the results

| Check | Result |
|---|---|
| PyCharm project interpreter is the project's `.venv` (Python 3.14.2) | OK |
| `python main.py --help` shows usage | OK |
| `python main.py --company "Tata Steel" --fy 2023-24` | OK: prints inputs, exit code 0 |
| Missing `--fy` | OK: clear error, exit code 2 |
| `pytest` | OK: 3 passed |
| **Clean-checkout test:** copy only the project files to a new folder, build a brand-new `.venv`, `pip install -r requirements.txt`, then run `pytest` and `main.py` | OK: same 13 packages and versions, 3 passed, program runs |
| Git (`git init`) | **Not done: git not installed, deferred by your choice** |

---

## 14. Things that went wrong (and what we learned)

1. **Git was not installed.** Tools like git are separate programs; being a programmer on Windows means installing them yourself. Deferred to the end.
2. **A "pip is broken" error in our first clean-checkout attempt.** The folder was nested so deeply that the full file path went over Windows' **260-character path limit**, and Windows silently dropped some files. Same commands worked in a short path. Lesson: keep project paths short; and when something is "mysteriously broken", change one variable at a time (we compared a long path vs. a short path) to find the cause. Your own project is fine.
3. **`main.py` already existed.** PyCharm creates a sample `main.py`. We replaced it with our real entry point.

---

## 15. Try it yourself (10 minutes)

1. In PyCharm's terminal run `python main.py --help`. Read every line and match it to `cli.py`.
2. Run `python main.py --company "Tata Steel"` (no `--fy`). What does the error say? What is the exit code? (`echo $LASTEXITCODE`)
3. Open `tests/cli/test_cli.py`, change `"2023-24"` in the first test to `"2024-25"`, run `pytest`, read the red failure message, then change it back and re-run.
4. Open `.gitignore` and `requirements.txt` and say each line out loud in plain English.

## 16. Interview self-check for Phase 0

Can you answer these without looking?
1. What is a virtual environment and why do we use one?
2. What does `requirements.txt` do and what does `==` mean in it?
3. What is the difference between **git** and **GitHub**? What does `git init` do?
4. Why have a `.gitignore`? Name three things in ours.
5. Why does `main.py` use `if __name__ == "__main__":`?
6. What does the exit code `0` mean?
7. Why is `main.py` tiny while the logic is in `brsr_p6/`?
8. What does a test give us that running the program by hand does not?

## 17. Mini glossary

**CLI** command-line interface · **argument/option** extra info after a command · **library/package** reusable code from others · **dependency** a library our code needs · **pin** fix a library to an exact version · **venv** private Python environment · **repo** a git-tracked project · **commit** a saved snapshot · **module** one `.py` file · **package** a folder of modules · **exit code** number telling the OS if the program succeeded · **docstring** documentation text inside code · **assert** a statement that must be true in a test.

---
---

# Phase 1: Discovery spike ("look before you build")

## 1.1 Why a "spike"?

A **spike** is a short, throw-away investigation to answer *"what are the facts?"* before committing to a design. Our big unknowns: *where does NSE keep the filings, in what format, and how are the numbers labelled inside?* If we guessed wrong, we would rewrite Phases 3-4. Three hours of looking now can save ten hours later.

## 1.2 How a website really gets its data

When you open the NSE BRSR page, two things happen:

1. Your browser downloads the **page itself** (HTML, the layout). It is mostly empty.
2. The page's **JavaScript** then quietly asks NSE's server for the data in the **background** ("background requests", also called **XHR / Fetch** requests) and draws the table from the reply.

Our Python program can skip the page and ask for the data **directly, the same way**. The only trick is finding out *what* it asks for. The browser's **DevTools** shows exactly that.

## 1.3 Words you need

| Word | Plain meaning |
|---|---|
| **Request / response** | You ask a server something (request), it answers (response). |
| **URL** | The address. Often `https://site/api/thing?symbol=TATASTEEL`. The part after `?` is the **query string**: extra options as `name=value`, joined by `&`. |
| **HTTP method** | The kind of request. **GET** = "give me this" (what we expect). **POST** = "here is data, process it". |
| **Headers** | Small labels sent with the request or response, like the writing on an envelope: `User-Agent` (who is asking, e.g. "Chrome"), `Accept` (what format I want), `Referer` (which page I came from), `Cookie`. |
| **Cookie** | A small token a site gives your browser on the first visit; the browser sends it back on later requests, like a visitor badge. NSE may refuse API calls that have no valid badge. In Python, `requests.Session()` remembers cookies for us. |
| **Status code** | The server's one-number verdict. **200** OK · **403** forbidden (blocked) · **404** not found · **429** too many requests (slow down!) · **5xx** server problem. |
| **API** | A door on a server meant for programs, not people. It returns data, not pretty pages. |
| **JSON** | The usual API data format. Looks just like Python: `{"symbol": "TATASTEEL", "year": "2023-24"}`. `{}` = dictionary, `[]` = list. |
| **Rate limit / being polite** | Servers block clients that ask too often. So we cache, wait between requests, and never loop wildly. |

## 1.4 PDF vs XML

- **PDF** is made for human eyes. Tables inside a PDF are just text positioned on a page. Extracting them is fragile.
- **XML** is made for programs. Data is wrapped in labelled **tags** that can be nested:

```xml
<energy unit="GJ">
  <electricity>1200</electricity>
</energy>
```
`energy` and `electricity` are **elements**; `unit="GJ"` is an **attribute**; `1200` is the **value**. Python can read this with the built-in `xml.etree.ElementTree`.

## 1.5 XBRL in simple words

**XBRL** = "XML for business reports". NSE requires every company to file the BRSR **both** as PDF and as XBRL. The main parts:

| Part | Meaning | Analogy |
|---|---|---|
| **Taxonomy** | The official **dictionary** of allowed tags (concepts) and what they mean, published by the regulator | A form with fixed field names |
| **Instance document** | The **filled-in form** a company submits (the `.xml` file we download) | One company's filled form |
| **Fact** | One reported value, e.g. "Total Scope 1 emissions = 1,234" | A single answer |
| **Context** | *Who and when* a fact is about: the company, and the period (e.g. 1 Apr 2023 - 31 Mar 2024). This is how we tell **current year vs previous year** apart | The "date" label on the answer |
| **Unit** | What the number is measured in (INR, tonnes...) | The "unit" label |
| **Dimension (axis / member)** | Extra labels that let one tag represent table **rows**, e.g. one tag "waste generated" + member "plastic waste" | The row label in a table |
| **Scale / decimals** | Hints about how the number is rounded or multiplied (e.g. in crores) | Fine print |

So reading a filing = collecting facts, then using each fact's **context** (which year? which row?) and **unit** to decide where it belongs in the SEBI table.

## 1.6 Known data-quality traps (from a published analysis of FY 2022-23 BRSR XBRL filings)

*Source: xbrl.org, "Unearthing Insights from India's ESG Disclosures". We will verify these ourselves on the real files.*

1. **Wrong scale:** some companies typed values in crore/lakh instead of plain rupees.
2. **Zeros for mandatory metrics** (e.g. Scope 2, water withdrawal): is `0` real, or "didn't bother"? We must be careful to never present a suspicious `0` as certain truth.
3. **Free-text units** for emissions ("Metric tonnes of CO2 equivalent", "CO2 in MT", ...): we must normalise unit strings.
4. **Scaled intensity denominators:** "per rupee of turnover" is often really "per crore/million rupees", explained only in the PDF.
5. **PDF and XBRL can disagree.**

What this means for our design: keep original value and unit next to the cleaned one, mark conversions, add **sanity-check warnings** instead of silently trusting numbers. This is directly the assignment's "honest handling of messy data".

## 1.7 Hands-on steps (you do these in your browser)

**A. Find the background request (DevTools)**
1. Open **Chrome or Edge** and go to: `https://www.nseindia.com/companies-listing/corporate-filings-bussiness-sustainabilitiy-reports` (yes, the spelling "bussiness" and "sustainabilitiy" is NSE's own).
2. Press **F12** (or Ctrl+Shift+I). Click the **Network** tab. Tick **Preserve log** and **Disable cache**. Click the filter button **Fetch/XHR**.
3. Click the 🚫 (clear) icon to empty the list, then **search for a company** on the page (e.g. `TATASTEEL`) and pick a period if the page offers one. New rows appear in the Network list.
4. Click the row that looks like the data request (name often starts with `corporate...` or `api/...`). Look at tabs: **Headers** (Request URL, Request Method, Status Code, Request Headers) and **Response** / **Preview** (the JSON).
5. Note down: the full **Request URL**, the **query parameters**, and the **JSON field names** of one record.

**B. Download filings by hand** (into `data/raw/<SYMBOL>/<FY>/`)
Suggested set (adapt if a company did not file that year): Tata Steel FY 2021-22, 2022-23, 2023-24 · Infosys FY 2023-24 · HDFC Bank FY 2023-24 · plus any company that shows **two rows for the same year** (a revised filing). For each, download **both the PDF and the XML/XBRL file** if the page offers both. Keep the original file names.

**C. Look inside an XML file**: open it in PyCharm (double-click). Find: the first lines (namespaces), `context` blocks (periods!), `unit` blocks, and the facts. We will explore it together with a small script.

## 1.7b What we found (Tata Steel FY 2025-26)

**The request you found in DevTools was exactly the right one.** In plain words:

```
GET https://www.nseindia.com/api/corporate-bussiness-sustainabilitiy
        ?index=equities & symbol=TATASTEEL & issuer=Tata Steel Limited
```
returns JSON like `{"data": [ {symbol, companyName, fyFrom, fyTo, submissionDate, revisionDate, attachmentFile (PDF link), xbrlFile (XML link)} ]}`.
- `fyFrom: 2025, fyTo: 2026` means **FY 2025-26**.
- `revisionDate: "-"` means "never revised".
- The two links are the files to download. We always **use the links the API gives us** and never guess file names.
- This answer held **only one filing** (the latest), because NSE's page quietly asks only for the **last 365 days**. Section 1.7c shows how we found the way to ask for older years.

**Can Python do the same as the browser?** Yes. We visited the NSE home page first (to receive cookies, like a visitor badge), then called the API, then downloaded the XML and the PDF, always waiting 3+ seconds in between. All answered `200 OK`.

**What is inside the XML?** A standard XBRL file:
- ~2,800 **facts** in 791 **contexts** (one "context" = who + which period + which table row), 11 **units**.
- Principle 6 values are mostly **one named tag per row**: `TotalScope1Emissions`, `WaterWithdrawalBySurfaceWater`, `NOx`, `PlasticWaste`... each appearing twice: once with the **current-year** context, once with the **previous-year** context. That is perfect for the SEBI table's two columns.
- The period lives in the context's dates (1 Apr 2025 to 31 Mar 2026). We always read the dates and never trust the id text.

**XBRL vs the company's PDF: do the numbers match?** Mostly yes (energy, water, air, waste all matched). But we also caught **four traps**, which is exactly the "messy data" the assignment talks about:

| Trap | What happened | Lesson |
|---|---|---|
| Scaled number | Scope 1 = `64` with unit `MtCO2e` (which means *metric tonnes*). The PDF says "64 **million** tonnes": Tata Steel typed the number in millions under a unit that says tonnes. | Never trust a unit label blindly; check the size against other numbers (see §1.7e). *(An earlier version of this note wrongly said `MtCO2e` meant million tonnes; corrected after we saw Reliance and Infosys.)* |
| Lost value | Scope 1+2 intensity is `0` in the XML; the PDF says 0.0005. | A `0` is not always zero. Warn the reader. |
| Wrong unit label | PPP energy intensity `9081` labelled "GJ per rupee"; really "GJ per million USD". | Cross-check magnitudes ("is this plausible?"). |
| "Not material" stored as 0 | PDF: "Not material for steel"; XML: `0`. | The file cannot tell "measured zero" from "not applicable". |

**Another discovery: the template version.** This filing follows the **newer** BRSR format (e.g. energy is already split into renewable / non-renewable, there are PPP and physical-output intensities). Our assignment's official layout is the **2021** one. So the program has to *translate* between them, and where a 2021 row (like "total electricity") must be built by adding two newer rows, we mark it **CALCULATED**.

**Standalone vs consolidated:** a company can report for itself alone (standalone) or including subsidiaries (consolidated). The XML has a `ReportingBoundary` fact ("Standalone basis") and contains one set of numbers; the PDF shows both. We must always print which boundary we are showing.

## 1.7c Finding the way to older years (a debugging story)

You re-sent the same URL and said "check this". The URL really had nothing to change, so the answer had to be somewhere else. **A useful habit: when the data you see doesn't make sense, read the code that asks for it.**

1. The NSE page loads a small script just for this page. It only wires buttons, but it told us which bigger script builds requests.
2. In that bigger script (NSE's own public JavaScript) we found: for the BRSR page the date pickers default to **today minus 365 days → today**, and when both dates are set the code adds `&from_date=…&to_date=…` to the request. Dates use the format **DD-MM-YYYY**.
3. We tried one wide range (`from_date=01-04-2021`): Tata Steel returned **4** filings. Infosys and HDFC Bank returned **5** each. The `issuer` part of the URL was never needed.
4. The same script showed the **company search** the page uses: `/api/smart-search/eqEtf?q=<text>`. We can use it to turn "Tata Steel" into `TATASTEEL`.

New concept: **JavaScript is just text.** The browser downloads it from a URL, so we can read it like any file. It is how websites decide what to ask the server.

## 1.7d What older and different filings taught us

**Five "editions" of the form.** Every filing names the version of SEBI's form it used (the `.../xbrl/2021-09-30/in-capmkt` part). We saw 2021-09-30, 2023-06-30, 2024-04-30, 2025-05-31 and 2026-02-28. (The fifth one, 2023-06-30, only appeared when we downloaded a second company's files: Reliance FY 2022-23. Lesson: test on more than one company!)
- **2021 edition** (used for FY 2021-22 and FY 2022-23): about 400 tag names. Close to the SEBI template we must copy. But numbers have **no proper unit**; units for emissions are typed as free text ("Kg/Month", "tCO2 e", "Million tonnes of CO2 equivalent"...). Energy has no unit at all.
- **2024-2026 editions:** about 660-700 tags, real unit labels, and a richer layout (renewable / non-renewable split, PPP). The three are almost identical for Principle 6.
- So our parser needs **two lookup tables** and must pick the right one by reading that date.

**More real-world messiness we found (each one becomes a rule in our code):**

| What we found | Our rule |
|---|---|
| Tata Steel Scope 1 = 64 but really 64 *million* tonnes, while Reliance's 36,350,070 and Infosys's 180,737 are plain tonnes (same unit label `MtCO2e` = metric tonnes) | Cross-check sizes inside one filing (emissions ÷ energy); if it makes no sense, show the value as filed with a "doubtful" warning, never silently rescale |
| Units differ by company (kg vs kilotonnes, tCO2e vs MtCO2e) | Convert everything to one unit, always show the original too |
| Infosys FY21-22: air emissions per **month** | Never turn "per month" into "per year" silently |
| Old files store `1,83,595` (Indian commas) as text | Clean numbers before using them |
| Answers like `Yes`, `true`, `NA` | Normalise to Yes / No / Not applicable |
| Infosys FY21-22 file contains illegal invisible characters, so a strict XML reader refuses the whole file | Clean them in memory, remember a warning; if still broken, show a clear "unparseable filing" message |
| HDFC Bank has no NOx/SOx tags at all | That is a genuine "not reported", shown clearly (a bank has little stack emission) |
| Tata Steel has no FY 2021-22 filing; the FY 2022-23 PDF link literally ends in `/null` | "No report for that year" is a normal case. The PDF is optional, so we rely on the XML |
| Tata Steel's FY 2022-23 figures are **consolidated** (group), from FY 2023-24 they are **standalone** (company only) | Always print the reporting boundary; flag when it changes between years |
| Tata Steel FY 2023-24 energy: 545.96 million GJ in its own filing, but 569.33 million GJ as "previous year" in the next filing (restated +4.3%) | Note restatements when comparing years |
| NSE keeps one row per company per year, and a revised filing **replaces** the original (22 of 1,215 rows) | Use the row NSE gives us; show submission and revision dates |

## 1.7e The "does this number make sense?" check

A unit label tells you what the company *says*; it does not prove the number was typed in that unit. Tata Steel's Scope 1 is `64` under a unit meaning "tonnes", but a steel giant cannot emit 64 tonnes. How can a program notice that?

**Compare against another number in the same filing.** Burning fuel releases a fairly predictable amount of CO₂ per unit of energy, roughly 0.01 to 0.5 tonnes per gigajoule. So divide (Scope 1 + Scope 2, in tonnes) by (total energy, in GJ):

| Company | Emissions (t) | Energy (GJ) | Ratio | Verdict |
|---|---|---|---|---|
| Reliance (Scope 1 only) | 36,350,070 | 478,033,842 | 0.076 | plausible |
| Infosys | 63,031 | 839,448 | 0.075 | plausible |
| HDFC Bank | 586,080 | 3,032,974 | 0.193 | plausible |
| Tata Steel (as typed) | 69 | 623,812,739 | 0.0000001 | **implausible**; ×1,000,000 gives 0.11, so it was typed in millions |

Our decision: when the ratio is implausible, **show the number exactly as filed and add a "scale doubtful" warning**. We never silently "fix" a company's number.

## 1.8 Safety and politeness during discovery
- Do **not** paste cookie values or login tokens anywhere. Header **names** are enough.
- Browse at human speed: a handful of searches, no rapid-fire refreshing.
- Everything on this NSE page is public data.

## 1.9 Interview self-check for Phase 1

Try to answer without looking:
1. How does a web page get its data, and how did we find the request behind it?
2. Why did the API return only one filing at first, and how did we fix it?
3. What is a cookie and why do we visit the NSE home page before calling the API?
4. What is a taxonomy, an instance document, a fact, a context? How do we tell current year from previous year?
5. Why did we choose XBRL over parsing the PDF? Name one thing the PDF is still useful for.
6. Give two examples where the XBRL number or unit could mislead a reader, and what our program should do about each.
7. What happens when a company has no filing for the year asked? What if a filing's XML is broken?
8. Why must the page always show whether a report is standalone or consolidated?
9. Why do we need two mapping tables ("legacy" and "modern")?
10. How polite were we to NSE? (How many requests, how far apart, what do we cache?)


---
---

# Phase 3a: The download script (built early, on request)

## 3a.1 Why this exists

During Phase 1 *I* fetched files with throwaway scripts that lived outside your project. That is fine for exploring, but useless for you: tomorrow an interviewer may say "now download company X". So the project must contain its own script that anyone can run. Rule of thumb: **anything the final result depends on must live in the project and be runnable by someone who is not me.**

## 3a.2 How to use it

```powershell
python download_filings.py --company Reliance                      # every year NSE has
python download_filings.py --company "Tata Steel" --fy 2023-24      # one year
python download_filings.py --company TATASTEEL --with-pdf           # also the PDF (optional)
python download_filings.py --company Reliance --refresh             # ask NSE for a fresh filing list
python download_filings.py --help
```
Files land in `data/raw/<SYMBOL>/<FY>/`. A second run reuses what is on disk, so it sends **no** requests (the last line of the summary says how many it sent).

## 3a.3 What happens when you press Enter (the pipeline)

```
"Reliance" --> check the FY text --> search NSE for the company --> ask NSE for the filing list
                (no network)           (smart-search, cached)         (from_date..to_date, cached 24 h)
        --> pick the year(s) --> for each: XML already on disk? --> yes: skip   no: download (3 s apart)
        --> write filing.json next to the files --> print a summary
```

## 3a.4 The files and what each one is for

| File (in `brsr_p6/`) | Job | Why separate? |
|---|---|---|
| `errors.py` | All our custom error types | One place; every error carries the message we show the user |
| `fiscal_year.py` | `"FY2023-24"` → `"2023-24"`, rejects years before FY 2021-22 | Pure logic, trivial to test, no internet needed |
| `nse_client.py` | **The only code that touches the internet**: pacing, retries, block detection, safe saving | Politeness rules live in one place |
| `company_lookup.py` | `"Reliance"` → `RELIANCE` | Matching rules are tested separately from the web call |
| `filings.py` | Ask NSE for the filing list, choose the right row | Knows NSE's list format and its quirks |
| `downloader.py` | Connects the steps above and decides folders/caching | The "manager" that calls the specialists |
| `download_cli.py` + `download_filings.py` | Reads the command line and prints the summary | Same idea as `cli.py`/`main.py`: tiny entry, logic elsewhere |

## 3a.5 New Python ideas (each appears in the code)

- **Exceptions and inheritance** (`errors.py`): `class UnknownCompany(BrsrError)` means "an UnknownCompany *is a* BrsrError". The command-line code writes `except BrsrError` once and catches all of our deliberate errors, while real bugs still crash loudly (which is what we want).
- **`raise` and `try/except`**: `raise` stops the current function and hands an error upward; `try/except` catches it where we know what to do.
- **`dataclass`** (`Company`, `FilingRecord`, ...): a short way to write a class that only holds data. `frozen=True` makes it read-only. It auto-creates `__init__`, printing, and equality.
- **Type hints with `|`**: `str | None` = "a string or nothing".
- **`pathlib.Path`**: file paths as objects. `raw_dir / "RELIANCE" / "2023-24"` joins with the correct slash for your OS; `.exists()`, `.mkdir()`, `.write_bytes()` are methods on it.
- **`Path(__file__).resolve().parent.parent`**: `__file__` is the location of the current file. Going two folders up gives the project root, so the script works **whatever folder you run it from**.
- **Default arguments and keyword arguments**: `download_filings(query, fy=None, include_pdf=False, ...)`.
- **`json.loads` / `json.dumps`**: text ↔ Python dictionaries and lists.
- **`@property`** (in a test): a method you read like a variable.
- **Regular expressions** (`re`) in `fiscal_year.py`: a pattern language for text. `\d{4}` = exactly four digits.
- **Sorting with a key**: `sorted(items, key=lambda r: r.fy_from)`.

## 3a.6 Ideas behind the design (be ready to explain these)

1. **Cache first.** Before asking NSE, look on disk. This is the assignment's "cache locally, do not hammer the site" in code. Three caches: company search results, the filing list (24 h), and the files themselves.
2. **Throttle.** `_wait_turn` guarantees at least 3 seconds between any two requests.
3. **Retry only what is worth retrying.** Timeouts and NSE 5xx errors are temporary, so we retry with growing pauses (4 s, then 8 s). A 403/429 means "stop", so we stop at once and tell the user.
4. **One bad file must not ruin the batch.** HTTP 404 on one file marks only that file "missing"; the others continue.
5. **Never save garbage as data.** Before writing, we check the first bytes: an XML file must start with `<?xml`, a PDF with `%PDF`. A block page ("Access Denied", HTML) is refused.
6. **Write safely.** We write to `name.xml.part` and rename when finished, so a crash never leaves a half file that later looks valid.
7. **Validate cheap things first.** A bad year like `2019-20` fails *before* any request.
8. **Take links from the answer, never invent them.** File names on NSE follow no pattern.
9. **Dependency injection (for tests).** `NseClient` accepts `session`, `sleep` and `clock` as arguments. In real use they are the real internet and real time; in tests we pass fakes. That is why 72 tests run in half a second with no internet and never wait 3 real seconds.

## 3a.7 The tests (`tests/`)

| File | What it checks |
|---|---|
| `test_fiscal_year.py` | Spellings accepted, bad years rejected with the right error |
| `test_company_lookup.py` | Tata Steel/HDFC-style results: bonds ignored, main share series preferred, ambiguity listed |
| `test_filings.py` | NSE's list parsed, `null` PDF links, revised rows, which years are missing, cache rules |
| `test_nse_client.py` | 3-second spacing, no retry on 403, retries on 503, block pages refused, no leftover `.part` files |
| `test_downloader.py` | The whole flow with a fake NSE: folders, second run = zero requests, one missing file, a manual file reused |

Run all: `pytest` (expect 72 passed).

## 3a.8 What we proved on the real NSE

| Try | Result |
|---|---|
| `--company Reliance` | Found *Reliance Industries Limited (RELIANCE)*, downloaded FY 2022-23 to 2025-26 in 20 s; reported FY 2021-22 as not filed |
| Same command again | 0 requests, 0.4 s |
| `--company "HDFC Bank" --fy 2022-23 --with-pdf` | XML and a 9.6 MB PDF |
| `--company "M&M"` | Folder `M_M` (the `&` is not safe in folder names) |
| `--company "Sakuma Exports"` | Clear message: NSE lists no BRSR for this company |
| `--company Tata` | Lists 10 matching companies and tells you to use a symbol |
| `--fy 2019-20`, `--fy banana`, `--fy 2021-22` (Tata Steel), 1-letter company | A specific message each |

**A surprise from the new data:** Reliance FY 2022-23 uses a *fifth* edition of SEBI's form (2023-06-30), which we had not seen for Tata Steel or Infosys. It would have surprised the parser later; testing a second company found it now.

## 3a.9 Try it yourself

1. `python download_filings.py --company Infosys` then open `data\raw\INFY` and look at the folders and `filing.json`.
2. Run the same command again and read the last line.
3. Try a company of your own choice. If it says several companies match, rerun with the symbol it suggests.
4. Open `brsr_p6/download/nse_client.py` and find where the 3-second wait happens (`_wait_turn`).
5. In `tests/download/test_nse_client.py`, find the test that proves a 403 is *not* retried. What would break if we retried?

## 3a.10 Interview self-check

1. Walk through what happens between typing a company name and files appearing on disk.
2. Where in the code is "politeness to NSE" implemented? List three separate rules.
3. What is the difference between a 403 and a 503 for our retry logic, and why?
4. Why do tests use a fake client and fake clock?
5. What happens if the same command is run twice? Which three caches are involved?
6. Why do we check the first bytes of a download before saving it?
7. How does the code decide that "Tata Steel" means `TATASTEEL` and not `TATASTLPP`?
8. What would you change if NSE changed the listing URL?


---
---

# Phase 2: Clean data in the SEBI shape (this also covers the core of the old Phase 4)

## 2.1 The problem in one picture

The XML file from NSE is like a **box of raw ingredients**: ~3,000 loose facts, in two different "editions", with unit labels that are sometimes missing or wrong. Neither the SEBI page nor the dashboard should have to deal with that mess. So we **prepare the ingredients once** and hand both pages the same clean result:

```
raw XML file ──► read ──► fill SEBI template rows ──► clean + convert units ──► check for doubts ──► ONE clean report
                                                                                                        ├─► text view (now)
                                                                                                        ├─► JSON file (now)
                                                                                                        ├─► SEBI-format HTML page (Phase 5)
                                                                                                        └─► dashboard page (Phase 6)
```

## 2.2 How to run it

```powershell
python extract_report.py --company Reliance --fy 2023-24                     # whole report, printed + saved
python extract_report.py --company TATASTEEL --fy 2025-26 --questions E1,E6  # only some questions
python extract_report.py --company Infosys --fy 2021-22 --quiet              # only save the JSON
```
It downloads the filing first if it is not on disk (using the Phase 3a code), then prints the Principle 6 report in SEBI's order and saves `data/parsed/<SYMBOL>/<FY>.json`.

## 2.3 The key idea: a number never travels alone

If we passed around bare numbers like `64`, we would lose everything we learned in Phase 1 (unit? converted? doubtful?). So every number is a **`Cell`** (`models.py`):

| Field | Meaning | Example (Tata Steel Scope 1) |
|---|---|---|
| `value` | the number (or text) | `64.0` |
| `unit` | the standard unit we show | `tCO2e` |
| `status` | how we got it (below) | `reported` |
| `as_filed` | exactly what the filing said | `64 MtCO2e` |
| `note` | harmless explanation | `""` |
| `warnings` | reasons to doubt it | "looks 1,000,000 times too small for this company's energy use..." |

`status` has four values: **reported** (the filing gave it), **not_reported** (the filing has nothing; *never* shown as 0), **calculated** (we added reported numbers, e.g. electricity = renewable + non-renewable), **converted** (we changed the unit, e.g. kilotonnes → tonnes). This is how we keep the assignment's promise: *never invent numbers, say so when something is missing, converted or estimated.*

A table row is a **`Metric`** = label + a `Cell` for the current year + a `Cell` for the previous year. The whole result is a **`Principle6Report`**: header facts (company, FY, reporting boundary, form edition...), a dictionary of metrics, list tables, facility blocks, assurance notes and extras.

## 2.4 The files and what each one does (all in `brsr_p6/`)

| File | Job |
|---|---|
| `models.py` | The shapes above (`Cell`, `Metric`, `Principle6Report`, ...) |
| `xbrl_reader.py` | Opens the XML, removes forbidden characters, works out current vs previous year from dates, hands back simple `Fact` objects you can look up by tag name |
| `values.py` | Cleaning small bits of text: `"1,83,595"` → `183595`; `"NA"`/blank → *nothing* (not 0); `"true"` → `Yes` |
| `units.py` | Puts numbers into one unit per topic (energy GJ, water kL, waste/air tonnes, greenhouse gases tCO₂e) and explains every change |
| `sebi_template.py` | **SEBI's official Principle 6 form as data**: 21 questions with the official wording and row labels |
| `p6_mapping.py` | **Which XBRL tag feeds which row**, separately for the old ("legacy") and new ("modern") edition |
| `extractor.py` | The loop that fills the template: for each row → find tag → clean → convert → `Cell` |
| `checks.py` | Looks for numbers that do not make sense and **adds warnings** (never changes a number) |
| `report_text.py` | Prints the report as plain text in SEBI's layout |
| `report_io.py` | Saves the report as JSON |
| `extract_cli.py` + `extract_report.py` | The command (same "tiny launcher + package" pattern as before) |

## 2.5 "Data instead of code": the template and the mapping

Instead of writing code like "print the energy table, then the water table...", the SEBI form itself is a list in `sebi_template.py`:

```python
Question("E1", ESSENTIAL, 1, "Details of total energy consumption ...", "table", rows=(
    Row("E1.electricity", "Total electricity consumption (A)"),
    Row("E1.fuel", "Total fuel consumption (B)"),
    ...
```
and the mapping in `p6_mapping.py` says where each row's number comes from:

```python
"E1.electricity": both("energy",
                       ("TotalElectricityConsumptionFromRenewableSources", "TotalElectricityConsumptionFromNonRenewableSources"),  # new edition: ADD these two
                       "TotalElectricityConsumption"),                                                                              # old edition: one tag
```
Why this is good: to support a new filing format you edit **data**, not logic; the Phase 5 SEBI page can simply *loop over the template*; and the official wording lives in one place.

## 2.6 New Python ideas in this phase

- **Dictionaries** (`dict`): `report.metrics["E1.total"]` finds a row by its key. `{key: value}`.
- **Tuples** `( , )`: like a list that cannot change. Template rows are tuples. `*rows` "unpacks" a tuple into another one.
- **`Enum`** (`Status`): a fixed set of allowed values, so you cannot misspell `"calcualted"`.
- **`@dataclass(frozen=True)`**: a read-only data holder (`frozen`) like `Row` and `Question`.
- **`field(default_factory=list)`**: each object gets its **own** empty list (a shared default list would be a classic bug).
- **List comprehension**: `[f for f in facts if f.end == wanted_end]` = "build a list by filtering".
- **`sorted(..., key=...)`**, **`sum(...)`**, **`getattr(obj, "current")`** (read an attribute whose name is in a variable), **`isinstance`**, **sets** `{...}` (unique items).
- **Regular expressions** to find the form's release date inside the file header.
- **`try/except ET.ParseError`**: turn a cryptic XML error into our own clear message.
- In tests: **`tmp_path`** (a throw-away folder), **`@pytest.mark.parametrize`** (one test, many inputs), **`pytest.approx`** (compare decimals safely), **`pytest.skip`**.

## 2.7 Bugs we found by *reading the real output* (a habit worth keeping)

All the automatic tests passed at first. Only when we read the real report line by line, next to the company's PDF, did we find these:

| What we saw | Cause | Fix |
|---|---|---|
| "(v) Others – No treatment" said *Not reported* although the filing had it | NSE writes `WithOutTreatment` in one tag and `WithoutTreatment` in the next | Look tags up **ignoring upper/lower case** |
| Business-continuity details (L7) said *Not reported* | My reader skipped every tag containing the letters "link", which also killed `...WebLink...` tags | Skip only the real "linkbase" elements |
| Energy assurance said "Not reported" although a statement was attached | In some editions the only energy assurance tag has "UnderLeadershipIndicators" in its name | Prefer the normal tag, fall back to that one |
| Scope 3 (also typed in millions) had no warning | The scale check looked only at Scope 1+2 | A scale warning on Scope 1+2 also marks Scope 3 |
| The same warning printed 6 times under one table | One warning per row | Group identical messages under a table |

Lesson: **tests prove the code does what you thought; reading real output shows whether what you thought was right.** Both are needed.

## 2.8 What the checks do (`checks.py`)

| Check | Example | What the reader sees |
|---|---|---|
| Rounded-away intensity | Tata's Scope 1+2 intensity is `0` while emissions are not | "Reported as 0 ... not a real zero" |
| Air pollutant zero | POP/VOC/HAP = 0 (the PDF says "not material") | "A reported 0 can mean none, or not measured / not material" |
| Totals add up | The total differs from the sum of its rows by more than 1% | "The rows above add up to X but the filing's own total is Y" |
| Scale check | Tata Scope 1 = 64 for 624 million GJ of energy | "about 1,000,000 times too small ... may have been typed in millions. Shown as filed; not corrected" |
| Unit missing | Old filings: energy has no unit | "(unit not stated)" + warning |
| Monthly figure | Infosys FY21-22 air emissions "Kg/Month" | Converted to tonnes but labelled "per month"; never ×12 |

Your decision from earlier is built in: **clean what we can, report what we cannot, show doubtful values as filed with a warning.**

## 2.9 How the two pages will use this (preview of Phases 5 and 6)

- **SEBI view (Phase 5):** `for question in QUESTIONS:` print its text; for each row, `report.metrics[row.key].current` and `.previous`; show "Not reported" for empty cells; show a small mark for calculated/converted/warning cells.
- **Dashboard (Phase 6):** its own list of metrics, each with plain-English text ("what it measures", "why it matters", "lower is better"), reading the *same* cells, e.g. `report.metrics["E6.scope1"]`, so every number on the dashboard can be traced to the SEBI table and to the filing.

## 2.10 Try it yourself

1. `python extract_report.py --company Reliance --fy 2023-24 --questions E1,E3` and compare with the previous-year numbers printed in the FY 2022-23 run.
2. Open `data\parsed\RELIANCE\2023-24.json` in PyCharm. Find `E1.electricity` and read each field.
3. Run the same for `--company Infosys --fy 2021-22` and read the top warning and the "(unit not stated)" notes.
4. Open `brsr_p6/core/sebi_template.py` and find the text of question E6.
5. Open `brsr_p6/parsing/p6_mapping.py` and find which tag feeds `E5.nox` in the two editions.
6. Run `pytest` (expect 160 passed). In `tests/extraction/test_extractor.py`, read `test_emissions_far_too_small_for_the_energy_use_are_flagged_as_probably_millions`.

## 2.11 Interview self-check

1. Why does every number carry a unit, a status and an "as filed" value?
2. What do the four statuses mean? Give one real example of each.
3. Why is the SEBI template stored as data? What does the mapping file add?
4. Why do we need two mappings (legacy and modern)? How does the code know which one to use?
5. How is "current year" decided? Why not use the context names like `DCYMain`?
6. Why do checks only add warnings instead of fixing numbers? Explain the Tata Steel "64" case.
7. What is the difference between "not reported" and `0`?
8. Name two bugs we only found by reading the real output, and how we fixed them.
9. What can the structured filing *not* give us for the SEBI form (hint: waste categories, E12 table, level of treatment)? How do we show that honestly?
10. How will the dashboard and the SEBI page stay consistent with each other?


---
---

# Phase 5: The SEBI-format HTML page

## 5.1 What we built

One command now produces a real web page:

```powershell
python main.py --company "Tata Steel" --fy 2025-26 --open      # writes output\TATASTEEL_2025-26.html and opens it
```
The page has a header with the key facts (reporting boundary, filing date, form edition), two **tabs** (SEBI-format report / Dashboard; the dashboard is filled in Phase 6), and the Principle 6 report laid out like SEBI's form: same question numbers, same wording, same tables and row labels, current and previous year side by side.

## 5.2 The pipeline in one picture

```
Principle6Report ──► sebi_view.py ──► Jinja templates ──► one .html file
 (clean data)        "what to show"     "how it looks"      (opens in any browser, offline)
```
Why two steps? **The template should only print; Python should decide.** Anything like "which footnote number does this warning get?" is easy to write and test in Python, and awkward inside HTML. So `sebi_view.py` prepares simple objects (`CellView`, `RowView`, `TableView`...) and the template just loops over them. This pattern is called a **view-model**.

## 5.3 HTML in five minutes

HTML is text with tags: `<tag>content</tag>`.

| Piece | Meaning |
|---|---|
| `<h1>`, `<h2>`, `<h3>` | headings (big to small) |
| `<p>` | a paragraph |
| `<table>` `<thead>` `<tbody>` `<tr>` `<th>` `<td>` | a table: head/body, row, header cell, data cell. `colspan="3"` makes a cell span 3 columns |
| `<th scope="row">` | tells screen readers "this cell labels its row" (accessibility) |
| `<ul>` `<li>` | bullet list |
| `<sup>` | superscript (our footnote numbers) |
| `<a href="#fn-E1-1">` | a link; `#...` jumps to the element with that `id` |
| `class="..."`, `id="..."` | names we use to style things (class) or point at them (id) |

## 5.4 Jinja2 in five minutes

Jinja2 turns a **template** into a finished page by replacing placeholders:

| Syntax | Meaning | Example (from our template) |
|---|---|---|
| `{{ ... }}` | print a value | `{{ report.company_name }}` |
| `{% for ... %}` ... `{% endfor %}` | repeat | one `<tr>` per row |
| `{% if ... %}` ... `{% else %}` ... `{% endif %}` | choose | show "Not reported" or the number |
| `{% macro name(args) %}` ... `{% endmacro %}` | a reusable mini-template (like a function) | `cell(...)`, `value_table(...)` |
| `{% include "sebi.html" %}` | paste another template here | the base page includes the SEBI view |
| `{# ... #}` | a comment | |

**Autoescape:** Jinja converts `<`, `>` and `&` in your data into `&lt;`, `&gt;`, `&amp;` so text from a filing can never be mistaken for HTML. This matters: the filing is data from outside, and we must never run it as code.

## 5.5 CSS in five minutes (the `style.css` file)

- **Rules** look like `selector { property: value; }`, e.g. `td.val { text-align: right; }` = "right-align cells with class `val`".
- **Variables**: `--accent: #0f6b5c;` then `color: var(--accent);`: change the colour in one place.
- **Specificity**: when two rules disagree, the *more specific* selector wins (`table.sebi td` beats `td.val`). Our numbers were left-aligned until we made the right-align rule as specific as the left-align one.
- **Media query** `@media (max-width: 640px) { ... }`: rules that apply only on narrow screens (phones).
- **CSS-only tabs:** two hidden radio buttons + labels; `#view-sebi:checked ~ .panel-sebi { display: block; }` means "when the first radio is selected, show the first panel". No JavaScript.
- We **never rely on colour alone**: warnings are amber *and* carry the symbol ⚠ and the word "Doubtful".

## 5.6 How to read the page

| You see | Meaning |
|---|---|
| *Not reported* (grey italic) | the filing has nothing for that item (never shown as 0) |
| `calc.` label | we **calculated** it by adding reported numbers (e.g. electricity = renewable + non-renewable) |
| `conv.` label | we **converted** the unit (e.g. kilotonnes to tonnes) |
| small number ¹ ² | a note under the table |
| ⚠ + amber note | a **doubtful** value, shown exactly as filed, with the reason |
| "(unit not stated)" | old filings do not say the unit of energy figures |
| "Note from this tool" (green box) | something SEBI's form asks for that the structured filing cannot give (e.g. recovery per waste category) |

## 5.7 New Python ideas

- **Dataclasses with defaults** and `field(default_factory=list)`. **Gotcha we hit:** naming a field `list` hid Python's own `list` for the lines after it, so `default_factory=list` silently became `None` and crashed. Never reuse built-in names (`list`, `str`, `id`, `type`...) for your own fields or variables.
- **Closures/macros**: Jinja macros are like functions you call from the template.
- **`markupsafe.Markup`**: a string we promise is safe HTML (used for the small "×10⁻⁶" superscript).
- **`str.partition(".")`**, **`rstrip`**, f-string formats like `f"{x:.2f}"`, scientific notation `f"{x:.2e}"`.
- **Regular expression** to turn `4.60e-06` into `4.60×10⁻⁶`.
- **`Path(__file__).resolve().parent / "templates"`**: find the templates folder next to the code, wherever you run from.
- Testing HTML: a small `HTMLParser` subclass that checks every opening tag is closed.

## 5.8 How we checked the page (a real browser engine, no guessing)

1. Tests: every official question text and every row label must appear in the page **in SEBI's order**; all 18 downloaded filings must produce well-formed HTML; text from a filing must not inject HTML.
2. Looking at it: Microsoft Edge (already on your PC) can take screenshots without opening a window: `msedge --headless --screenshot=file.png page.html`. To test a phone, we load the page inside a 375-pixel-wide frame.
3. Reading the output as a user would. This found things no test would: numbers left-aligned, tables sticking out on a phone, a repeated remark, and a **real calculation bug**.

## 5.9 The bug the page revealed (worth remembering)

On the Reliance page, Leadership 1 showed an amber note: *"The rows above add up to 6,958,071 but the filing's own total is 6,826,744."* The gap (131,327) was exactly **half** of the "other sources" row (262,654). That pattern means *double counting*. Looking at the raw facts: the filing gives a plain total (131,327) **and** a breakdown row with the same 131,327, and our code added both. The fix: use the plain total if there is one; add rows only when there is no total. After the fix, **none of the 18 filings has any "rows don't add up" warning**, which also shows the companies' own totals are consistent.

Lesson: the sanity check we wrote to protect readers from *company* mistakes also caught a *programmer* mistake. Checks that compare numbers with each other are worth their cost.

## 5.10 Try it yourself

1. `python main.py --company Reliance --fy 2023-24 --open` and compare Essential 1 with the earlier text printout.
2. Click the ⚠ marks and footnote numbers; they jump to the note under the table.
3. Open the Infosys FY 2021-22 page (`python main.py --company INFY --fy 2021-22 --open`) and find the amber "About this filing" box and the "(unit not stated)" figures.
4. Shrink the browser window to phone width: the tables should stay on screen.
5. Open `brsr_p6/rendering/templates/sebi.html` and find the macro `value_table`; change a heading word, regenerate, and see it change.
6. Open `brsr_p6/rendering/templates/style.css` and change `--accent` to another colour; regenerate.
7. Run `pytest` (expect 200 passed) and read `test_every_official_question_and_row_label_appears_in_sebi_order`.

## 5.11 Interview self-check

1. Why is the page built in two steps (`sebi_view.py` then templates)? What would go wrong if the template made all the decisions?
2. What does Jinja2's autoescape protect us from? Give an example.
3. How does the SEBI page show a value that is missing / calculated / converted / doubtful? Why not just colours?
4. Why does the Unit column exist only for E5, E6 and L4?
5. Why are numbers grouped as 2,47,98,900? Where is the full-precision number kept?
6. How do CSS-only tabs work without JavaScript?
7. Explain the double-counting bug: how was it found, what caused it, how was it fixed?
8. How can you prove the page matches SEBI's form "one to one"? (Hint: the test with the loop over QUESTIONS.)
9. Why did a field called `list` crash the program?
10. How did we check the phone layout without a phone?


---
---

# Phase 6: The plain-English Dashboard

## 6.1 What we built

The page now opens on a **Dashboard** tab that answers four questions a non-expert asks about a company:

| The reader asks | The page answers with |
|---|---|
| How big is the footprint? | a big number in plain units: **46.42 crore GJ**, **3.77 crore tonnes CO₂e** |
| Better or worse than last year? | a chip (✔ Improved / ✖ Got worse / ≈ About the same / ? Can't compare) + an arrow + the percentage |
| Is it under control? | renewable share, waste recycled share, nine safeguard questions, outside audit |
| Can I trust the numbers? | a badge on every card, amber warnings, a "Can I trust these numbers?" section |

The SEBI-format report is still there as the second tab, untouched.

## 6.2 Design first, with real numbers (not dummy ones)

Before writing code we built `design/dashboard_mockup.html`: a hand-written page using **real Reliance numbers**. Why not dummy data? Because dummy data is always tidy. The real files are full of awkward cases (a figure typed in millions, a unit that is missing, a zero that means "not measured"), and a design that has never met them breaks on the first real company. Looking at the mockup *before* coding also let you say "yes, this is friendly" while changing it was still cheap.

## 6.3 The pipeline in one picture

```
Principle6Report ──► metric_info.py   (the WORDS: titles, what it is, why it matters, which direction is better)
 (clean data)    ──► comparison.py    (the RULES: better / worse / same / can't tell)
                 ──► dashboard_cards.py (one figure -> one card)
                 ──► dashboard_view.py  (cards -> topics, charts, sentences, safeguards, trust panel)
                          │
                          ▼
                 dashboard.html + dashboard.css  ──►  the Dashboard tab of the one HTML file
```
Same idea as Phase 5: **Python decides, the template only prints.** That is why we could test every sentence and verdict without opening a browser.

## 6.4 The new files

| File | Job |
|---|---|
| `units.py` (extended) | now converts the exact SI multiples real filings use (Terajoule, Megajoule, ktCO₂e) and "per ₹" intensity units |
| `warning_kinds.py` | sorts each warning: **doubtful** (the number is probably wrong) or **check** (probably right, handle with care) |
| `friendly.py` | how numbers are *said*: lakh/crore, 2 decimals, "0.15%", "<0.01" |
| `comparison.py` | this year vs last year, and the honest "can't tell" cases |
| `metric_info.py` | all the plain-English wording as data (so wording can change without touching logic) |
| `dashboard_cards.py` | builds one card: number, unit, verdict, bars, badge, warnings, fine print |
| `dashboard_view.py` | builds topics, charts, headline sentences, the at-a-glance summary, safeguards, trust panel |
| `templates/dashboard.html`, `dashboard.css` | print it, style it (every CSS rule starts with `.dash` so it cannot disturb the SEBI tab) |

## 6.5 The honest rules (the heart of the phase)

1. **"Better" means better than the company's OWN figure last year.** Not a rating, not a score. The filing has no industry benchmark or legal limit, and inventing one would break "never invent numbers". A box on the page says so.
2. **"About the same"** = within ±1% (amounts) or ±0.5 percentage points (shares).
3. **A doubtful figure** (scale slip, parts that do not add up, an intensity of 0) is still shown exactly as filed, in amber, but gets **no verdict** and is **left out of every sentence**. The sentence says why: *"The greenhouse gas figure looks doubtful, so we do not quote it."*
4. **A figure that only needs care** (unit not stated, zero that may mean "not measured") is compared, with an asterisk and a note.
5. **Missing means "Not reported"**, never 0, never an arrow.
6. **A zero last year gives no percentage.** HDFC Bank files 0 water last year and 21 lakh kL this year. "Got worse" would be a guess, since the 0 probably means "not measured". So the card says *"Last year's figure was 0, so a percentage change cannot be worked out."*
7. **0 in both years** is "no change", but it does not count in the scoreboard (it says nothing about improving).
8. **A figure with no unit is not quoted in a sentence** ("used 19,75,098 unit not stated of energy" is gibberish).
9. **Intensity is shown per ₹ 1 crore** (filed figure × 10,000,000), because 0.0000807 GJ per ₹ is unreadable. Only the unit changes; the filed figure stays in the Fine print.
10. **Figures we calculate** (Scope 1 + 2, renewable share, recovered share) are marked "calculated by us", inherit the warnings of their ingredients, and say how they were built.

## 6.6 How to read a card

```
Total energy used                        Lower is better ↓      <- plain title + which direction is good
46.42 crore GJ                                                  <- big number, friendly unit
✔ Improved   ▼ 2.0% lower than last year                        <- verdict in WORDS + symbol + arrow
2023-24 ████████████████  46.42                                 <- bars start at zero (never a cut-off axis)
2022-23 █████████████████ 47.36
What it is: ...    Why it matters: ...                          <- always visible, no jargon
▸ Fine print                                                    <- full numbers, how we calculated, SEBI source
✔ Reported by the company                                       <- where the number came from
```

## 6.7 New ideas in this phase

- **Data instead of code (again):** `metric_info.py` is a list of `MetricInfo(...)` entries. To improve a sentence you edit one line of data.
- **Dataclass "view" objects** (`CardView`, `TopicView`...): just bundles of ready-to-print values.
- **"Default to the cautious side":** a warning nobody has classified is treated as *doubtful*. A **guard test** fails when a new warning text appears, so nobody forgets to classify it.
- **Floating-point noise:** in Python `3.47e-8 * 1000` is `3.4700000000000004e-05`. We clean converted numbers with `float(f"{x:.12g}")`.
- **CSS grid** (`repeat(auto-fit, minmax(270px, 1fr))`): cards arrange themselves into 3 columns on a laptop and 1 on a phone, with no media query.
- **`<details>` / `<summary>`**: collapsible "Fine print" with no JavaScript.
- **Inline SVG icons** drawn once as `<symbol>` and reused with `<use href="#i-bolt">`.
- **Namespacing CSS** (`.dash .card`): the SEBI tab already used the class names `.legend` and `.panel`; without a prefix the two tabs would silently restyle each other.
- **`Counter`** (from `collections`) to count verdicts and repeated warnings; **`str.partition`** to split `"derived:ghg_scope_1_2"`.
- **Lifting shared warnings:** if the same warning appears on two or more cards of a topic, it is shown once under the cards (HDFC Bank's six air pollutants would otherwise repeat it six times).

## 6.8 What reading the real output taught us

| Found by looking at real companies | What we did |
|---|---|
| ITC and Wipro file energy in Terajoule / Megajoule; `units.py` said "I cannot convert". The emissions-vs-energy scale check **only runs for GJ**, so it was silently skipped for both | converted the exact SI multiples; the check now runs for them too |
| HDFC Bank: "Water taken in ▲ Up from 0 → Got worse" | a zero base gives "can't compare", never a guess |
| HDFC Bank sentence "used 19,75,098 unit not stated of energy" | a figure with no unit is left out of sentences, with a reason |
| "NOx, SOx, PM... stayed about the same" when all were 0 | zeros are named as zeros; they do not count in the scoreboard |
| "Largest source was other sources (100.0%)" and a grey 100% bar | a chart that only says "other" is not drawn; "100.0%" now reads "100%" |
| Shares: "1.5% … last year 1.4%" looked like a 0.1 jump when the change was 0.05 | small shares keep two decimals |
| My mockup said "0.06 percentage points"; the exact value is 0.0547 | the code was right and the hand-typed mockup was wrong: compute, never type |
| A constant defined twice in one file (`KEY_FIGURES`): the later one silently replaced the earlier | removed the duplicate. Python does not warn about this |
| Twice I looked at a **stale output page** made before my last change | regenerate before judging a screenshot |

## 6.9 Try it yourself

1. `python main.py --company "Reliance" --fy 2023-24 --open`. The Dashboard opens first; click **SEBI-format report** for the form.
2. Open `design/dashboard_mockup.html` next to the real page. Which numbers are identical?
3. `python main.py --company "Tata Steel" --fy 2025-26 --open` and read the **Climate** section: dashed amber cards, "Can't compare", and a headline that refuses to quote a doubtful figure.
4. `python main.py --company "HDFC Bank" --fy 2022-23 --open`: an older filing. Find "unit not stated", "Last year's figure was 0", and the air pollutants "reported as 0 in both years".
5. `python main.py --company "Wipro" --fy 2025-26 --open`: its energy is filed in megajoules; the page shows it in GJ marked "unit changed by us". Open **Fine print** to see the original.
6. Open `brsr_p6/views/metric_info.py`, change the *Why it matters* line of "Water taken in", regenerate, and see it change.
7. Open `brsr_p6/analysis/comparison.py` and change `SAME_WITHIN_PERCENT` from `1.0` to `5.0`; regenerate Reliance and watch verdicts turn into "About the same". Change it back.
8. **The two-minute test:** show the page to someone who knows nothing about ESG. Ask them to explain the Water section back to you. Anything they cannot explain is a sentence to rewrite.
9. `pytest -q` (expect 298 passed).

## 6.10 Interview self-check

1. Who is the dashboard for, and which four questions does the page order answer?
2. What does "better" mean on the page, and why is there no rating against other companies?
3. A company's Scope 1 is typed as 64 instead of 64 million. What does the dashboard show, and what does it deliberately NOT do?
4. Why is a "0 last year, 21 lakh this year" change not called "Got worse"?
5. What is the difference between a *doubtful* and a *check* warning? Why does an unclassified warning default to doubtful?
6. Why do we show intensity per ₹ crore, and how do we make sure nobody thinks we changed the company's number?
7. Why do bars start at zero, and why are renewable shares drawn on a 0–100 scale even though the bar is thin?
8. Why is the page built as `dashboard_view.py` (Python) + `dashboard.html` (template) instead of putting the rules in the template?
9. Why did every CSS rule need the `.dash` prefix?
10. What does the guard test in `test_warning_kinds.py` protect against?
11. How would you add a new card (say, "Hazardous waste")? Which file(s) would you touch?
12. What did the real data teach us that the mockup alone could not?


---
---

# Phase 7: Error pages, samples, README, and "does it run from scratch?"

## 7.1 What we built

| New | What it does |
|---|---|
| **Error pages** | When a command fails, `python main.py ...` still writes an HTML page (`output/error_<company>_<year>.html`) that explains what went wrong, what you typed, what to try, and gives commands you can copy |
| **`samples/`** | 5 report pages (Tata Steel, Reliance, Wipro, Infosys, HDFC Bank) and 4 error pages, all made by one command: `python make_samples.py` |
| **Offline fallback** | If NSE cannot be reached, a company you downloaded before still works from the saved filing list |
| **README v1** | Setup, run commands, inputs to try, what is completed (honestly), how the data is extracted, error handling, known limitations, AI tools used, design note |
| **A clean-checkout test** | A brand-new folder + brand-new virtual environment + `pip install` + one command, to prove the project runs from scratch |

## 7.2 Why an error PAGE and not only a message?

The assignment grades error handling as "a clear, specific message **on the page**". Someone who opens our output in a browser should never
see a blank screen or an old report. So every failure produces a real page, in the same look as the report, with:

- the exact sentence the program raised (specific, not "something went wrong"),
- what you typed,
- "What you can try", and
- **commands to copy**: for an ambiguous name, one command per matching company; for a year NSE does not have, one command per year it does have.

Error pages are named `error_<company>_<year>.html`. That start means an error page can never overwrite a good report page (imagine NSE being down
when you re-run a company you already have: your good page must survive).

## 7.3 How it is built (the same two-step idea as before)

```
an exception ──► error_view.py ──► error.html ──► the error page
                 (Python decides    (the template
                  the words)         only prints)
```

- **Exceptions carry data, not only text.** `NoFilingFound` now carries the NSE `symbol` and the `available` years; `AmbiguousCompany` already carried its
  `candidates`. That is how the page can offer commands.
- **One table, looked up by class.** `ERROR_INFO` maps each error class to a title and hints. The lookup walks `type(error).__mro__`, which is
  Python's list of "this class, then its parent, then its grandparent...". So a brand-new error class we forget to list still gets the page of its
  parent (`BrsrError`) instead of a crash. A test checks that every error class in `errors.py` is in the table.
- **Two layers of catching in `cli.py`:** `except BrsrError` is for problems we expected; `except Exception` at the very outside is for *bugs*. Catching
  everything is only safe at the outermost layer, because the program is ending anyway and the user deserves an explanation. `--debug` re-raises so a
  developer can still read the traceback.
- **Even the explanation can fail** (a read-only folder). Then we print the original error plus "could not write the explanation page", never hide the first problem.

## 7.4 When NSE is down: a graceful fallback

The filing list for a company is saved for 24 hours. Before this phase, after 24 hours even a company you had downloaded needed NSE again. Now,
if NSE cannot be reached and *any* saved list exists, we use it and say so ("the filing list saved on 07-Oct-2026 is used (it may be out of date)").

- If you ask for `--refresh`, you want NSE's latest answer, so a failure is reported, not hidden.
- With no saved list at all, it is a real error page ("We could not get the data from NSE").
- The function takes a `notify` argument, a small function it calls with a sentence. That is a **callback**: `filings.py` does not know about
  printing; the caller decides what to do with the message.
- While writing this we noticed an old error message promised "place the file by hand and the tool will use it". That was only half true (the filing
  list is needed too), so we corrected the message. **Never promise in an error message something you have not tested.**

## 7.5 The samples, and why a test guards them

`python make_samples.py` rebuilds everything in `samples/`, including `samples/README.md`, from one list in `brsr_p6/workflows/samples.py`. The page of a company is built
from the filing already on disk (no internet); only a filing that is missing is downloaded.

The error samples are made by **really triggering the errors** with offline inputs (an unknown name, the year 2019-20, a real saved filing list asked for FY 2021-22,
and a deliberately cut-off XML file). So they show exactly what a user would see.

**The test `committed_report_pages_are_up_to_date`** rebuilds every sample page and compares it, character for character, with the committed file. Twice in this
project we looked at a stale page by mistake; now a stale sample makes the test fail until someone runs `python make_samples.py`.

## 7.6 The README is part of the product

The first thing a reviewer reads. Ours says plainly what is done and **what is not** (when this was written none of the three optional extensions was built; the README has been kept in sync as each one landed), lists known limitations
(waste split by category, treatment level, errors a few percent wide that no check can catch...), discloses the AI tool and what it was used for, and has the design note.
Honest limits build more trust than a long list of features.

## 7.7 "Does it run from scratch?" (what we did)

1. Copied the project to a new folder **without** `.venv`, `data/`, `output/` and caches (what a fresh clone would contain).
2. `python -m venv .venv` and `pip install -r requirements.txt` in it.
3. `pytest`: **324 passed, 16 skipped** (the skipped ones need downloaded filings, so they skip politely).
4. `python main.py --company "ITC" --fy 2024-25`: downloaded from NSE and wrote the page in about **11 seconds**.

## 7.8 New Python and tooling ideas

- `type(error).__mro__` (method resolution order) and `isinstance`; inheritance as a safety net.
- Optional arguments on exceptions (`def __init__(self, message, symbol="", available=())`) while keeping the message.
- A callback parameter (`notify=print`-style).
- `tempfile.TemporaryDirectory()` to create a file that is deleted afterwards; `Path.write_text`, `Path.mkdir(parents=True)`.
- pytest: `monkeypatch` (swap a function for a fake during one test), `pytest.skip`, `pytest.raises`, shared helpers in `tests/helpers/html_checks.py`.
- Making one command produce many files from a list of data (`SAMPLE_COMPANIES`, `SAMPLE_ERRORS`).

## 7.9 Small things that went wrong and what they taught us

| What happened | Lesson |
|---|---|
| My first "damaged file" sample said "does not look like a SEBI filing" instead of "not valid XML (line, column)": the fake file lacked the SEBI namespace so it took a different branch | When you demonstrate an error, check you reached the branch you meant to |
| A test looked for `view-dashboard` in the error page and failed because the shared stylesheet contains that word | Test for the real element (`id="view-dashboard"`), not a word |
| A PowerShell command was blocked: in a Python script I had a line starting with `del` (PowerShell's alias for Remove-Item) | Tools can misread innocent text; use `pop()` and move on |
| `robocopy` "failed" with exit code 1 | For robocopy, 1 means "files copied", which is success |

## 7.10 Try it yourself

1. `python main.py --company "Tata Steel" --fy 2021-22 --open`: read the page, copy one of the commands, run it.
2. `python main.py --company "Xyzzy Quux" --fy 2023-24 --open` and `... --fy banana --open`: compare the two pages.
3. `python main.py --company "Tata" --fy 2024-25 --open` (needs the internet): an ambiguous name, one command per matching company.
4. Open `samples/README.md`, then open two sample pages. Which sample would you show first to an interviewer, and why?
5. Open `brsr_p6/views/error_view.py`, change a hint sentence, run `python make_samples.py`, and look at the sample page. Then run `pytest -q`: which test would
   fail if you had *not* re-run `make_samples.py`? (Hint: `test_committed_error_pages_are_up_to_date`.)
6. Switch your internet off and run a company you downloaded before. Read the console line about the saved filing list.
7. Add `--debug` to a command that you know fails on purpose. Does it behave differently for a *known* error and for a bug? (Try it with a test that raises `KeyError`.)

## 7.11 Interview self-check

1. Why does a failed run write a page instead of only printing a message? Why is the file called `error_...` and not the usual report name?
2. What does an error object need to carry so the page can offer ready-to-run commands? Give two examples from the code.
3. What is `__mro__` and why does the error lookup use it?
4. Why is `except Exception` acceptable in `cli.py` but would be a bad habit in the middle of the program? What does `--debug` do?
5. When NSE is unreachable, when do we use an old saved filing list, and when do we refuse? Why?
6. How are the sample pages produced, and what stops them from going stale?
7. What is a callback, and where do we use one in this phase?
8. Which parts of the project are *not* done, and where does the README say so?
9. How did you prove the project runs from a clean checkout? What would you do differently with git installed?
10. Name two known limitations of the data extraction and say why they exist.


---
---

# Phase 11: Git, the repository, and "does a stranger's computer run it?"

## 11.1 What git is doing for us (a recap in one paragraph)

Git is a **time machine for a folder**. Each **commit** is a labelled snapshot ("save point") with an author and a message; you can look back, compare and
undo. **GitHub** is a website that keeps a copy of your repository so other people (the reviewers) can see it. Git works on your PC; GitHub is only the copy.

## 11.2 What we did, step by step

| Step | Command / action | Why |
|---|---|---|
| Install git | `winget install --id Git.Git` | git was never installed on this PC (we postponed it to the end on purpose) |
| Create the repository | `git init -b main` | turns the folder into a repository; `main` is the name of the main line of history |
| Decide what NOT to save | `.gitignore` | big, generated or private files stay out (virtual environment, caches, PDFs, generated JSON, `output/`) |
| Check before saving | `git add -n .` (a *dry run*) | lists what would be added without adding anything: we saw 108 files and no PDFs |
| Save in logical pieces | `git add <paths>` then `git commit -m "..."` | 4 commits: code, tests, samples + data, notes. A reader can follow the story |
| Prove it | `git clone` into a new folder + new venv | a clone contains **only what was committed**, exactly what a reviewer gets |

## 11.3 Ideas worth understanding

- **Staging.** `git add` puts files on a "tray"; `git commit` photographs the tray. That is why you can commit code and notes separately.
- **`.gitignore` with exceptions.** `data/raw/*` ignores every downloaded filing; then lines like `!data/raw/WIPRO/2025-26/` bring back the few we want. Rule: *a later line beats an
  earlier one*, and a folder must be re-included before its contents can be. We checked the result with the dry run, not by guessing.
- **Why commit a few filings?** The brief allows hand-downloaded filings "with documentation". Eight small XML files (about 8 MB) make the samples and **every one of the 340
  tests** run offline on a fresh clone. The big PDFs are not needed, so they are not committed. `data/README.md` explains each file.
- **`.gitattributes`.** Windows and Linux end lines differently. `* text=auto` lets git tidy text files; `*.xml -text` tells it to leave the filings byte-for-byte as NSE published them.
  The warnings "LF will be replaced by CRLF" you saw are only git saying this; they are harmless.
- **The commit author.** Every commit records a name and email, and on a **public** repository anyone can read them. Before publishing, check `git log --format="%an <%ae>"`.
  GitHub also offers a private "no-reply" address if you do not want your real email shown.
- **Privacy scan before publishing.** We searched all text for the Windows user name, e-mail addresses and absolute paths and removed two. A public repository is forever.
- **The assignment brief (`*.pdf`) is not committed.** It belongs to the company, not to us.

## 11.4 Publishing to GitHub (you do this part: it needs your GitHub login)

1. In the browser: **github.com > New repository**. Name it, for example, `brsr-principle6-dashboard`. Choose **Public** (simplest) or **Private** (then add the reviewers under
   *Settings > Collaborators*). **Do not** tick "Add a README", ".gitignore" or "licence": the repository must be empty.
2. In the project folder, with your own repository address:
   ```powershell
   git remote add origin https://github.com/<your-username>/brsr-principle6-dashboard.git
   git push -u origin main
   ```
   The first push opens a browser window to sign in (Git Credential Manager is part of Git for Windows).
3. Reload the repository page: you should see `README.md` with the screenshots, and the `samples/` folder.
4. Put the link in your submission. Test it once from a private/incognito window (or ask a friend) to be sure the reviewers can open it.

Common problems: *"git is not recognized"* (close and reopen PyCharm so it sees the new PATH), *"remote origin already exists"* (`git remote set-url origin <url>`),
*"rejected ... fetch first"* (you created the GitHub repository with a README: either delete the repository and create an empty one, or ask for help before using any force option).

## 11.5 Try it yourself

1. `git log --oneline` (the story of the project in 4 lines) and `git log --stat -1` (what the last commit changed).
2. `git status`: it should say "nothing to commit, working tree clean". Edit one word in `README.md`, run `git status` again, then `git diff` to see the change; undo it with `git restore README.md`.
3. `git ls-files data` shows which data files are tracked; `git check-ignore -v data/raw/ITC/2024-25/filing.json` shows *which line of `.gitignore`* ignores a file.
4. Make a change, run `python make_samples.py`, then `pytest`: which test notices if a sample page was not regenerated?

## 11.6 Interview self-check

1. What is the difference between git and GitHub?
2. What does `git add` do, and how is it different from `git commit`?
3. Why is `.venv/` ignored? Why is `data/parsed/` ignored but eight raw filings are committed?
4. How did you check what would be committed *before* committing? How did you prove a stranger can run the project?
5. Why does the commit author matter on a public repository?
6. What would you do if you had accidentally committed a file with a password in it? (Think: rotating the password first.)


---
---

# Phase 8: Extension 1, several years side by side (`trends.py`)

## 8.1 What we built

```powershell
python trends.py --company "Tata Steel" --from 2021-22 --to 2025-26 --open
```
One page with a **column per financial year**: the five topics (energy, climate, water, air, waste) with a mini bar per year and a trend verdict, then **every figure of SEBI's Principle 6 tables**
year by year, then the list of figures that later filings changed. `--from` and `--to` are optional (default: FY 2021-22 up to the newest filing NSE has).

## 8.2 The idea that makes it possible: every filing holds TWO years

A filing for FY 2023-24 contains its own year (the *current* column) and FY 2022-23 (the *previous* column). That gives us two powerful tricks, both with real data only:

1. **A missing year can still be shown.** NSE has no Tata Steel filing for FY 2021-22, but the FY 2022-23 filing's previous-year column holds the company's own FY 2021-22 figures. We show them, in a shaded column
   that says "no filing on NSE; figures from the FY 2022-23 filing". It is never a zero and never a guess.
2. **A year can be checked against what the next filing says about it.** If the two differ, the company changed (**restated**) the figure.

## 8.3 What the real data taught us (we looked BEFORE designing the rules)

We compared, for every pair of neighbouring years on disk, the figure in the first filing with the same year in the next filing:

| What we found | Rule we wrote |
|---|---|
| Tata Steel FY 2022-23 says energy = 857 (consolidated, no unit). The next filing says 559,969,887 GJ (standalone). A naive check would call that a "restatement" | Only call it a restatement when **both years are on the same basis**. Otherwise mark it ≠ ("different basis, not comparable") |
| Wipro FY 2022-23 energy is exactly **1,000 times** the next filing's figure (probably megajoules vs gigajoules) | Only compare figures that have the **same, stated unit**. We do not guess that it was a unit slip |
| Tata Steel FY 2023-24 electricity (28.4 million GJ) appears in the next filing as 19.5 million GJ: a real restatement of 31% | Keep the figure **as filed in its own year**, mark it ⟲ and show the later figure in the tooltip and in a table |
| Wipro's 6515.4 vs 6515.0 | Differences under **0.5%** are rounding, not restatements |
| Wipro reports standalone, then consolidated, then consolidated again | Every column shows its basis; the verdict only compares years on the same basis |

## 8.4 How the trend verdict is decided

For each row we take the **latest year with a figure** and walk back one year at a time **while the basis and the unit stay the same and a figure exists**. The result is compared with the first year of that block:
*"▲ 14.3% higher than FY 2023-24"*. If earlier years were left out, the sentence says why. If only one year is left, the chip says "Can't compare" and gives the specific reason
("FY 2022-23 is on a different basis (Consolidated instead of Standalone)", "No figure for FY 2022-23", "FY 2022-23's figure was 0", "The figure looks doubtful").

## 8.5 The code, in three layers (each can be tested without the others)

| Layer | File | Touches | Job |
|---|---|---|---|
| Load | `trend_loader.py` | files + NSE | list what NSE has, download the years (politely, cached), read each one; **a problem in one year becomes a flagged entry, not a crash** |
| Logic | `trend_model.py` | nothing | build the columns, borrow missing years, find restatements and basis changes |
| Words | `trend_view.py` + `trends.html` | nothing | rows, cells, marks, notes, sentences; the template only prints |

Plus small changes elsewhere: `compare(..., earlier="FY 2023-24")` (so the wording can say *than FY 2023-24* instead of *than last year*), `download_filings(first=..., last=...)`,
`NoFilingFound(symbol, available)`, the error `InvalidYearRange`, `fiscal_years_between`, and error pages whose suggested commands use `trends.py` for a trend request.

## 8.6 Two bugs found by LOOKING at the page (not by the tests)

1. **A doubtful figure printed as "0".** Tata's emissions are about 8 crore tonnes in the early years and then "64 tonnes" (typed in millions). On a "crore" scale for the whole row, 64 rounds to 0. A reader would see a
   zero for something that is not zero. Fix: a figure too small for the row's scale is written in its own scale and unit ("64 tonnes CO₂e"), and a doubtful zero intensity says "Filed as 0".
2. **The table was laid out like a stack of boxes.** I named the table's CSS class `trend`, and the dashboard stylesheet already had a rule `.dash .trend { display: flex }` for the card's "▲ 2% lower" line. The table
   became a flexbox, so header cells and body cells no longer lined up. I found it by asking the browser itself: a tiny script printed `TABLE display=flex`. The class is now `trendtable`, and a test forbids the old name.
   **Lesson: when a layout is "weird", measure instead of guessing, and keep class names specific.**

## 8.7 Smaller design choices worth knowing

- **Bars start at zero** and are scaled to the row's largest figure, as on the dashboard. Doubtful figures get no bar.
- **The first column stays in place** (sticky) when a phone scrolls the table sideways.
- **Samples:** 3 trend pages (Tata Steel, Wipro, Reliance) and 1 trend error page in `samples/`; the freshness test covers them too. Tata Steel's FY 2022-23 to FY 2024-25 filings were added to the repository for this.
- **What we do NOT do:** infer a missing unit from the next filing (even where the same number is repeated with a unit), or use a later restated figure instead of the filed one.

## 8.8 Try it yourself

1. `python trends.py --company "Tata Steel" --from 2021-22 --to 2025-26 --open`. Find: the shaded FY 2021-22 column, the purple *Consolidated* → blue *Standalone* chips, a ⟲ mark (hover it), the "Can't compare" in Climate.
2. Run the same for Wipro `--from 2023-24 --to 2025-26`: which two years does each verdict compare, and why?
3. `python trends.py --company "Reliance" --from 2025-26 --to 2021-22` and read the error page.
4. Open `brsr_p6/analysis/trend_model.py` and change `RESTATEMENT_TOLERANCE` from `0.005` to `0.05`; regenerate Tata Steel: how many figures are still marked as restated? Change it back and run `pytest`.
5. In `tests/analysis/test_trend_model.py` find the test about Wipro's "1,000 times" energy. What would go wrong if we flagged it as a restatement?
6. Open the page on a phone-width window: where does the "swipe sideways" hint appear?

## 8.9 Interview self-check

1. What two years does one filing contain, and how does that let us show a year NSE has no filing for? Why is that not "making up a number"?
2. How do we decide that a later filing *restated* a figure? Name three cases we deliberately do NOT call a restatement and why.
3. Why do trend verdicts stop at a change of basis? Show an example from Tata Steel.
4. Why do we keep the figure as filed in its own year instead of replacing it with the restated one?
5. What happens to the page when one year's file is damaged? Which errors do produce a full error page?
6. How did you find the table layout bug, and what was the cause?
7. Why is the loader separate from the model? How are they tested?
8. What would you build next (Extension 2 or 3) and how would the existing pieces help?

---

# Phase 9: Extension 2, "what got better and what got worse?" (`summary.py`)

## 9.1 What we built

```powershell
python summary.py --company "Tata Steel" --open
```
One page that answers one question: **since last year, which three figures improved most and which three got worse?** You only give the company; the newest year NSE has is found by itself
(`--fy` is optional). Each of the six entries has a plain headline ("SOx (sulphur oxides) was 45.7% more than last year"), last year's and this year's number, which way is better,
and the same card as on the dashboard. The page also prints **how "better" is decided**, lists every figure it compared, and lists every figure it did **not** rank, with the reason.

## 9.2 What does "better" mean? (the hardest question of this phase)

A page that says "better" must say better *than what*. Our answer, printed on the page, is deliberately small:

| Rule | Why |
|---|---|
| Better means better than the **company's own last year** | The filings contain no industry benchmark or legal limit. Inventing one would break "never invent numbers" |
| Each figure has a **direction**: lower is better for energy, gases, water and waste per ₹ of sales and for each air pollutant; higher is better for the renewable and recycled shares | Less pollution is good, more recycling is good. The directions are data in `metric_info.py`, not code |
| Under **1%** (a share: under half a percentage point) is **"about the same"**, not ranked | Tiny changes are rounding, not news. The same margin as the dashboard, so the two pages cannot disagree |
| **Amounts** are ranked by percent change, **shares** by percentage points | See 9.3 |
| A figure **per ₹ of sales is ranked instead of its total** | See 9.3 |

## 9.3 What the real data taught us (we looked BEFORE writing the ranking)

I printed a text version of the ranking for four real companies and read it. Three things were wrong with the first idea ("sort everything by percent change"):

| What we saw | Rule we wrote |
|---|---|
| Tata Steel's renewable share went from 0.0655% to 0.2415%. In percent that is **+269%**, the biggest "improvement" on the page, but it is only **0.18 of a percentage point** (Wipro's recycled waste share showed +145%) | Rank shares in **percentage points**. A rise from 80% to 90% counts as 10 |
| Total energy and "energy per ₹ of sales" are the same story. Both would fill two of the six places, and a total rises when a company simply grows | Rank the **per-sales figure instead of its total**, and quote the total as context ("For comparison, total energy used was 6.2% more than last year"). Nothing is hidden |
| HDFC Bank's recycled share was 100% last year and 100% this year, and the page said "reported as 0 in both years". "No change" results carried no number, so the code could not tell "100 → 100" from "0 → 0" | A result now carries the **signed size of the change** (`Comparison.amount`). Only a real zero-to-zero is left out |

Figures that cannot be ranked fairly are **not dropped silently**. Each is listed under "Not ranked, and why":
- missing, or the company filed no figure → "Not reported";
- looks doubtful (a mis-scaled number) → we do not compare it, as everywhere else;
- a different unit in the two years, or **0 last year** (a percentage cannot be worked out, and the zero may mean "not measured");
- 0 in both years → nothing to compare.

When fewer than three figures improved (or got worse), the page says so ("Only 2 figures improved", "Nothing got worse by more than the 'about the same' margin"). It never pads the list.

## 9.4 Where last year's figures come from (and what if last year's report is missing)

This is the same trick as the trends (§8.2): **every filing holds two years**, its own and the year before. So the summary compares the two columns of **one filing**. That has a useful side effect: both years use
the same reporting basis (standalone or consolidated), so the basis problem of the trends cannot happen here.

Last year's *own* filing is a bonus, not a requirement. If NSE has it and it can be read, we compare it with the previous-year column only to mark figures the company has **restated** since (the comparison uses
the newer figure, and the page says so). If it is missing or damaged, nothing breaks. The page says why: Reliance's earliest filing is FY 2022-23, and the page for that year says *"NSE has no BRSR filing of its own for FY 2021-22"*.

Two different failures, two different results (the brief asks for both to be handled):

| What is missing | What happens |
|---|---|
| Last year's **own** filing (not on NSE, or damaged) | Not an error. The previous-year column of the newest filing is used, and the page explains |
| The **newest** filing (unknown company, a year NSE does not have, a damaged file) | There is nothing to summarise, so an error page with the specific reason and ready-to-run `summary.py` commands |

## 9.5 The code, in three layers (after the Phase 12 reorganisation each is in its own folder)

| Layer | File | Touches | Job |
|---|---|---|---|
| Load | `brsr_p6/workflows/summary_loader.py` | files + NSE | find the newest year, download **only that year and the one before** (politely, cached), read both |
| Logic + words | `brsr_p6/views/summary_view.py` | nothing | build the dashboard cards, rank, find what to leave out and why, write the sentences |
| Page | `brsr_p6/rendering/templates/summary.html` | nothing | only prints; reuses the dashboard's card and chip (`dashboard_macros.html`) |

Small changes elsewhere, all reusing what already existed: `download_filings(pick=...)` (the years are chosen **after** NSE's list is known, so the newest year needs no guessing), `Comparison.amount` and
`CardView.change` (the size of a change), `MetricInfo.replaces` (which total a per-sales figure stands in for), `figure_getter` (one way to read a figure, shared by the trends and the summary),
and `summary` error pages. Because the cards come from `build_card`, a figure cannot be "better" here and "worse" on the dashboard.

## 9.6 Smaller design choices worth knowing

- **Ties** keep the dashboard's order (NOx before PM when both rose 12.5%), because the sort is stable.
- **A share reads as a sentence**, not a percent: "Waste recycled or reused went up from 36.9% to 90.4%."
- **"unit not stated"** is written "(unit not stated)" so it does not read like "0.2 unit not stated".
- **"About the same" figures show both years**, and carry their total's story when the total moved more.
- **If the unit is unclear** the title says "per unit of sales", not "per ₹ 1 crore". We never dress up a number we cannot convert.
- **Samples:** Tata Steel (1 improved, 3 same, 4 worse), Wipro (all 9 improved, so the "setbacks" box says nothing got worse), Reliance FY 2022-23 (no previous filing on NSE), and one `summary.py` error page.

## 9.7 Try it yourself

1. `python summary.py --company "Tata Steel" --open`. Read "How we decide what is better", then find the figure that was **not** ranked because its per-sales figure was (Total energy used), and the sentence that still tells you it rose 6.2%.
2. `python summary.py --company "Wipro" --open`: why is the "biggest setbacks" box empty, and does the page still say something useful there?
3. `python summary.py --company "Reliance" --fy 2022-23 --open`, then read the last box. Then try `--fy 2021-22` and read the error page.
4. In `tests/views/test_summary_view.py` read `test_a_share_is_ranked_by_percentage_points_not_by_percent` and `demo_report()` in `tests/helpers/summary_samples.py`. Why were 10% to 25% and a two-thirds fall in waste chosen as the example numbers? What would the order be if shares were ranked in percent?
5. Change `TOP = 3` to `2` in `brsr_p6/views/summary_view.py` and run `pytest tests/views tests/rendering -q`. Which tests notice, and why is that a good thing? Change it back.
6. Open `brsr_p6/analysis/comparison.py` and raise `SAME_WITHIN_PERCENT` from 1 to 5. Re-run Tata Steel: which figure moves into "about the same"? (Then run `pytest`: the dashboard tests notice too. Change it back.)

## 9.8 Interview self-check

1. How do you define "better"? Why only against the company's own last year?
2. Why rank shares in percentage points and amounts in percent? Give the Tata Steel example.
3. Why is "energy per ₹ of sales" ranked instead of "total energy"? Is the total hidden anywhere?
4. What happens to a figure that cannot be ranked? Where does the reader see it?
5. What are the two kinds of "missing report", and what does the page do in each?
6. Why do both years come from the same filing? When is last year's own filing used, and for what?
7. How was the "0 in both years" bug found (HDFC Bank), and what was the cause?
8. How would you reuse these pieces to build Extension 3, the comparison of two companies?

---

# Phase 12: From one flat folder to layers

## 12.1 What was wrong

`brsr_p6/` held **39 files side by side**. Nothing in the folder said which file reads the internet, which one decides wording, which one writes HTML. A new reader (or an interviewer) had to open files to find out.
It worked, and the tests passed, but code quality is not only "does it run": it is also "can a stranger find their way?".

## 12.2 The idea: one folder per step of the journey

The program is a conveyor belt. A filing goes in at one end and a web page comes out at the other. So each step of the belt got its own folder (a Python **package**):

| Folder | Its job, in one line |
|---|---|
| `core/` | the shared words and tools: the data model (`Cell`, `Principle6Report`), errors, financial years, units, number formatting, file locations |
| `download/` | talk to NSE politely and keep the files on disk |
| `parsing/` | open the XBRL file and read its raw facts (no cleaning yet) |
| `extraction/` | clean the facts into one `Principle6Report`; flag doubtful numbers, never change them |
| `analysis/` | compare years: better / worse / same, trends. Pure logic |
| `views/` | decide *what each page says* (sentences, numbers, flags) |
| `rendering/` | fill the HTML templates and write the file |
| `workflows/` | whole jobs: company + year in, page out |
| `cli/` | the commands you type; each one calls a workflow |

Your three questions from the brief map straight onto it: *downloading* is `download/`, *parsing* is `parsing/` and `extraction/`, *generating HTML* is `rendering/`.

## 12.3 The one rule: imports only go one way

The table above is ordered from bottom to top. **A folder may use itself and the folders above it in the table, never the ones below.** `core` knows nothing about `views`; `views` knows nothing about how a page is saved.

Why a rule?
- If A imports B and B imports A (a **circular import**), Python can crash on start-up, and nobody can understand either file alone.
- You can test and change the bottom layers without worrying about the top. Changing a template cannot break the download code.
- When the rule is clear, "where does this new function go?" has an answer.

A rule that lives only in a README gets broken the first time someone is in a hurry, so **`tests/test_architecture.py` checks it**. It reads every file as *data* (Python's `ast` module turns code into a tree you can inspect), collects the `import` lines and fails with the file and line number of any upward import.
This is a nice example of "code can check code".

## 12.4 How the move was done safely

1. **Commit first.** The unfinished Phase 9 work was committed, so the move is a separate step that can be undone with one command.
2. **Look before moving.** I drew the real import graph with a small script. It had **no cycles**, which means the folders could follow the dependencies that already existed; nothing had to be redesigned.
3. **`git mv`, not copy-and-delete.** Git then records a *rename* (81 of them), so `git log --follow <file>` still shows a file's whole history.
4. **A script for the imports.** About 70 files import from `brsr_p6`. Editing them by hand would have meant typos, so a script read each file's syntax tree and rewrote only the import statements (and sorted them the way the project already did). A find-and-replace would have broken multi-line imports.
5. **The tests were the safety net.** All 467 tests had to pass, and the *freshness* tests were the strongest proof: they rebuild every sample page and compare it byte for byte with the committed one. After the move, `make_samples.py` changed **nothing**.
6. **Run the real commands, from a different folder.** Tests do not prove `python main.py` works. I ran all five entry points, once from another working directory.

## 12.5 What bites when you move files (all four happened here)

- **Code that finds files from its own position.** `PROJECT_ROOT = Path(__file__).parent.parent` meant "two levels up from `downloader.py`". When a file moves one folder deeper, "two levels up" is a different folder, and the program would silently look for `data/raw` in the wrong place. Four tests did the same with `Path(__file__).parent.parent / "data" / "raw"`. Fix: **one** place (`core/paths.py`) knows where the project root is, and everyone else asks it.
- **A hidden dependency in the wrong layer.** `render.py` (making HTML) imported `PROJECT_ROOT` and `safe_name` from `downloader.py` (downloading). That is "making a page depends on downloading", the exact thing the layers forbid. Moving the paths into `core` removed it.
- **One test file importing from another.** `test_summary_page.py` borrowed a helper from `test_summary_view.py`. Once they sit in different folders that import breaks, and it was a smell anyway: a helper used by two test files belongs in `tests/helpers/`.
- **A name that means two things.** The old `cli.py` held the main command *and* the failure handler every command shares. In a `cli/` folder that would be `cli/cli.py`, so it became `main_cli.py` (the `main.py` command) and `common.py` (what every command shares).

One judgment call worth knowing: `friendly.py` ("4.7% less than last year") sits in `core`, not `views`, because `comparison.py` in `analysis` uses it. If it lived in `views`, `analysis` would import *upwards*, breaking the rule. Putting a module where its **users** are is how you decide.

## 12.6 Try it yourself

1. `python -c "import brsr_p6; print(open(brsr_p6.__file__).read())"` and read the map of the packages. Open one `__init__.py` from each folder.
2. Break the rule on purpose: add `from brsr_p6.views.summary_view import build_summary_view` at the top of `brsr_p6/core/models.py`, run `pytest tests/test_architecture.py`, and read the failure message. Then undo it.
3. `git log --follow --oneline brsr_p6/core/units.py`: the history reaches back before the move.
4. `pytest tests/views -q` runs only the tests of one layer. Which folder would you run after changing `comparison.py`?
5. Open `brsr_p6/core/paths.py`. If you moved it into `brsr_p6/core/config/paths.py`, which single line must change, and why?
6. Run `python summary.py --company "Wipro" --output-dir C:\Temp` from a different folder (use the full path to `summary.py`). Why does it still find the filings?

## 12.7 Interview self-check

1. Why split a flat folder into packages when the program already worked? Give two concrete benefits.
2. State the layer rule in one sentence. What bug does it prevent, and how is it enforced here?
3. How did you check that the move changed no behaviour? Which test was the strongest proof, and why?
4. `PROJECT_ROOT` used `Path(__file__).parent.parent`. What risk did moving files create, and how did you remove it for good?
5. Why `git mv` instead of copying the files and deleting the old ones?
6. Why did `friendly.py` go into `core` and not `views`?
7. What would you do if a new feature needed `core` to call something in `workflows`?
8. Why do the test folders mirror the code folders?
