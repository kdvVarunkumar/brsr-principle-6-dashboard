"""BRSR Principle 6 report generator: the project's main code package.

One sub-package per step of the journey from NSE to the finished page.  A package may only import from the packages ABOVE it in
this list, never from below (tests/test_architecture.py checks this), which keeps the code easy to follow and free of circular imports:

    core        the data model and small helpers every other package uses (models, errors, units, formatting, paths ...)
    download    get the filing from NSE: company lookup, filing list, polite downloads, files kept on disk
    parsing     read the XBRL file into raw facts
    extraction  turn the raw facts into one clean, checked Principle6Report
    analysis    compare years: better / worse verdicts and multi-year trends (pure logic, no HTML)
    views       decide what each page says (dashboard, SEBI form, trends, summary, errors): plain objects, the layout stays in templates
    rendering   fill the HTML templates and write the page
    workflows   whole jobs from start to finish (company + year -> page), and the sample pages
    cli         the command-line front ends behind the one command, `python flow.py` (and its sub-commands)

Having this file is what tells Python "this folder is a package", so code elsewhere can write `from brsr_p6.cli.flow_cli import main`.
"""
