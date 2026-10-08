"""Helpers for the dashboard tests: a blank in-memory report, and a way to put exactly the figures a test needs into it."""

from brsr_p6.core.models import Assurance, Cell, ListTable, Metric, Principle6Report, Status
from brsr_p6.core.sebi_template import QUESTIONS

SCALE_SLIP = "Scope 1+2 emissions look about 1,000,000 times too small for this company's energy use (1.1e-07 tonnes per GJ)."
ZERO_MEANING = "A reported 0 can mean 'none', or 'not measured / not material'. The filing does not say which."
NO_UNIT = "This filing does not state the unit of its energy figures (the SEBI form says 'Joules or multiples'). Shown as filed."


def blank_report(name="Test Company Limited"):
    """A report with every row of the SEBI template present and empty ('not reported'), like a filing with nothing in it."""
    report = Principle6Report(name, "TEST", "2023-24", "2022-23", boundary="Standalone basis")
    for q in QUESTIONS:
        if q.kind == "table":
            for row in q.rows:
                if not row.header:
                    report.metrics[row.key] = Metric(row.key, row.label)
        elif q.kind == "yes_no":
            report.metrics[f"{q.id}.answer"] = Metric(f"{q.id}.answer", "Answer")
            report.metrics[f"{q.id}.details"] = Metric(f"{q.id}.details", "Details")
        elif q.kind == "text":
            report.metrics[f"{q.id}.details"] = Metric(f"{q.id}.details", "Details")
        elif q.kind == "number":
            report.metrics[f"{q.id}.value"] = Metric(f"{q.id}.value", "Percentage")
        elif q.kind == "list":
            report.tables[q.id] = ListTable(q.id, list(q.columns), [])
        if q.assurance:
            report.assurance[q.id] = Assurance()
    return report


def cell(value, unit="GJ", status=Status.REPORTED, warnings=()):
    return Cell(value, unit, status, f"{value} {unit}", warnings=list(warnings))


def put(report, key, current, previous=None, unit="GJ", status=Status.REPORTED, warnings=(), extra=False):
    """Fill one row for both years.  `previous=None` leaves last year not reported."""
    target = report.extras if extra else report.metrics
    metric = target.get(key) or Metric(key, key)
    metric.current = cell(current, unit, status, warnings)
    metric.previous = cell(previous, unit, status, warnings) if previous is not None else Cell()
    target[key] = metric
    return metric


def answer(report, question_id, text, details=""):
    report.metrics[f"{question_id}.answer"].current = Cell(text, "", Status.REPORTED, text)
    if details:
        report.metrics[f"{question_id}.details"].current = Cell(details, "", Status.REPORTED, details)
