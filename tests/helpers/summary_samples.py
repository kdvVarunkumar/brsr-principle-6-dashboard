"""Helpers for the year-on-year summary tests (the view and the page): a report built so the ranking has something to decide."""

from dashboard_samples import blank_report, put


def demo_report():
    """FY 2023-24 against FY 2022-23, built so the ranking has something to decide.

    improved:  waste -66.7 %, VOC -50 %, renewable share +15 POINTS (but +150 % in percent), energy per sales -2.4 %
    worse:     SOx +45.7 %, greenhouse gases per sales +33.3 %, NOx +12.5 %, PM +12.5 %
    the total energy rose 25 %: it must not take a place of its own, because energy per sales exists.
    """
    r = blank_report("Test Company Limited")
    put(r, "E8.total", 100, 300, unit="tonnes")
    put(r, "E5.voc", 10, 20, unit="tonnes")
    put(r, "L1.re_total", 25, 10)
    put(r, "L1.nre_total", 75, 90)
    put(r, "E1.intensity", 8.0e-05, 8.2e-05, unit="GJ per ₹")
    put(r, "E5.sox", 67_000, 46_000, unit="tonnes")
    put(r, "E6.intensity", 2.0e-05, 1.5e-05, unit="tCO2e per ₹")
    put(r, "E5.nox", 27_000, 24_000, unit="tonnes")
    put(r, "E5.pm", 9_000, 8_000, unit="tonnes")
    put(r, "E1.total", 500, 400)
    return r


def last_years_own_report(sox):
    """What the company filed for FY 2022-23 in its own report, giving SOx as `sox` (the later filing says 46,000)."""
    previous = blank_report("Test Company Limited")
    previous.fy, previous.previous_fy = "2022-23", "2021-22"
    put(previous, "E5.sox", sox, None, unit="tonnes")
    return previous
