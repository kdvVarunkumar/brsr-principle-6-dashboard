"""Step 3, cleaning: turn the raw facts into one Principle6Report: units made standard, doubtful figures flagged (never changed).

    extractor   facts + the SEBI template -> a Principle6Report (every value remembers the filing's element it was read from)
    checks      sanity checks that only ADD warnings to a figure
    values      small cleaners for raw text (numbers, yes/no answers)
    report_io   save the clean report as JSON
"""
