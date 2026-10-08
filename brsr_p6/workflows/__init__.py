"""Whole jobs from start to finish.  These are the modules that do input and output in order: download, read, build, write.

    pipeline         company + year -> report -> HTML page
    trend_loader     company + range of years -> every year read (one bad year never stops the others)
    summary_loader   the latest year, and the year before it
    compare          two companies, one year -> one page; and a page for every pair of companies in a folder
    missing_pages    the year-on-year summaries and multi-year trends a folder lacks, made from the saved filings (offline)
    hub              every page of a folder -> two viewer pages (index.html: one company; compare_companies.html: two companies)
    samples          rebuild the sample pages in samples/  (python flow.py samples)
"""
