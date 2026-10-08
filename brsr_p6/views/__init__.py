"""Step 5, deciding what each page says.  A view turns the clean data into plain objects (text, numbers, flags) that a template only
prints.  The page layout is not decided here (that is the templates' job), so every decision can be tested without a browser.

    metric_info, dashboard_cards, dashboard_view   the plain-English dashboard
    sebi_view, report_text                         the SEBI-format report (as a page, and as plain text)
    trace_view                                     the trace from every number back to the filing (element, text as filed)
    trend_view                                     the multi-year trend page
    summary_view                                   the year-on-year summary
    compare_view                                   two companies for one year, compared fairly (totals shown, not ranked)
    hub_view                                       the names and groups of the pages in the all-pages viewer
    error_view                                     the explanation page for each kind of error
"""
