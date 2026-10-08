"""Foundation: the data model and the small helpers every other package builds on.  Imports nothing from the other packages.

    models          Cell, Metric, Principle6Report: the shape of the clean data; Origin: where a value came from in the filing
    errors          every error we raise on purpose, each with a message written for the user
    fiscal_year     financial years such as "2023-24": reading them and counting forwards and backwards
    units           one standard unit per topic, and a note whenever we convert
    formatting      numbers as people read them (lakh / crore digit grouping)
    friendly        numbers in words ("4.7% less than last year")
    sebi_template   SEBI's official Principle 6 layout, written as data
    paths           where files live on disk
"""
