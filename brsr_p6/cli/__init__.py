"""Step 7, the command line: ONE command, `python flow.py`.  It reads what the user typed, runs a workflow and says where the page was written.

    flow_cli       flow.py                      the whole flow for one company and one year (download -> read -> clean -> report page),
                                                and the dispatcher for the sub-commands below
    download_cli   flow.py download             only download the filings
    extract_cli    flow.py extract              read and clean one filing, print it as text and save the clean data as JSON
    trend_cli      flow.py trends               one company, several years
    summary_cli    flow.py summary              the year-on-year summary
    compare_cli    flow.py compare              two companies for one financial year, side by side
    hub_cli        flow.py hub                  every page of a folder behind a home page (choose a company) and a compare page (choose two)
    samples_cli    flow.py samples              rebuild the committed sample pages in samples/
    common         what every command does when it fails: explain it on a page
"""
