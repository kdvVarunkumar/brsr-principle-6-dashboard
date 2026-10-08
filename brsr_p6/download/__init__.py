"""Step 1, getting the data: ask NSE which BRSR filings a company has, download the right XBRL files politely, keep them on disk.

    nse_client       the only place that talks to NSE (a pause between requests, cookies, retries)
    company_lookup   what the user typed ("Tata Steel") -> one NSE symbol
    filings          a company's list of filings, and choosing the one for a year
    downloader       company + years -> files saved under data/raw/ (anything already on disk is reused)
"""
