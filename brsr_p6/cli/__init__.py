"""Step 7, the command line: each command reads what the user typed, runs a workflow and says where the page was written.

    main_cli       main.py             one company, one year: the report page
    trend_cli      trends.py           one company, several years
    summary_cli    summary.py          the year-on-year summary
    compare_cli    compare.py          two companies for one financial year, side by side
    hub_cli        hub.py              every page of a folder behind a home page (choose a company) and a compare page (choose two)
    download_cli   download_filings.py only download the filings
    extract_cli    extract_report.py   read and clean one filing, print it as text and save the clean data as JSON
    common         what every command does when it fails: explain it on a page
"""
