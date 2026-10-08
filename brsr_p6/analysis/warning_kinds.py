"""How serious is a warning?  The dashboard needs to know, because it treats the two kinds differently.

    DOUBTFUL  the number itself is probably wrong (a scale slip, parts that do not add up, a zero that is not a real zero).
              The dashboard still shows it exactly as filed, but gives no "better / worse" verdict and keeps it out of headlines.
    CHECK     the number is probably right, but something about it needs care (the unit is not stated, a zero that may mean
              "not measured", a label that is unreliable).  The dashboard shows it, with a note, and may still compare years.

The warnings are plain sentences written in units.py, checks.py, extractor.py and p6_mapping.py.  Each one is recognised here
by a phrase from its text.  A warning nobody has classified is treated as DOUBTFUL ("when in doubt, say so"), and a test makes
sure every warning in the real downloaded filings is classified, so a new sentence cannot slip through unnoticed.
"""

OK = "ok"
CHECK = "check"
DOUBTFUL = "doubtful"

_DOUBTFUL_PHRASES = (
    "too small for this company's energy use",      # checks.py: emissions scale slip (typed in thousands / millions)
    "too large for this company's energy use",
    "look mis-scaled",                              # checks.py: Scope 3 follows Scope 1+2
    "A real intensity is never exactly 0",          # checks.py: an intensity of 0 is rounding, not a measurement
    "The rows above add up to",                     # checks.py: parts do not equal the filed total
    "rounded too coarsely",                         # checks.py: an intensity filed with one digit of precision
)

COARSE = "rounded too coarsely"

_CHECK_PHRASES = (
    "does not state the unit of its energy figures",      # units.py
    "does not state the unit of this intensity figure",
    "does not state a usable unit",
    "is not one I can convert",
    "Filed as a monthly figure",
    "is unclear; metric tonnes of CO2e assumed",
    "A reported 0 can mean",                              # checks.py: 0 may be "none" or "not measured"
    "This is per unit of physical output",                # p6_mapping.py: the unit label leaves out "per tonne"
    "PPP-adjusted figures are per million US dollars",    # p6_mapping.py: the unit label says "per rupee"
    "Unexpected answer",                                  # extractor.py: a yes/no cell with another answer
)


def is_known(warning):
    """True when this warning's text is one we have classified."""
    return any(phrase in warning for phrase in _DOUBTFUL_PHRASES + _CHECK_PHRASES)


def kind_of(warning):
    """CHECK or DOUBTFUL for one warning sentence (DOUBTFUL when we do not recognise it)."""
    if any(phrase in warning for phrase in _CHECK_PHRASES):
        return CHECK
    return DOUBTFUL


def only_coarse(warnings):
    """True when the ONLY reason to doubt these figures is that they are rounded too coarsely to compare (the number itself is not wrong)."""
    doubts = [w for w in warnings if kind_of(w) == DOUBTFUL]
    return bool(doubts) and all(COARSE in w for w in doubts)


def worst_kind(warnings):
    """OK for no warnings, DOUBTFUL if any warning is doubtful, otherwise CHECK."""
    kinds = {kind_of(w) for w in warnings}
    if DOUBTFUL in kinds:
        return DOUBTFUL
    return CHECK if kinds else OK
