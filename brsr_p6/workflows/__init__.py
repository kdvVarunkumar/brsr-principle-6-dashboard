"""Whole jobs from start to finish.  These are the modules that do input and output in order: download, read, build, write.

    pipeline         company + year -> report -> HTML page
    trend_loader     company + range of years -> every year read (one bad year never stops the others)
    summary_loader   the latest year, and the year before it
    samples          rebuild the sample pages in samples/  (python make_samples.py)
"""
