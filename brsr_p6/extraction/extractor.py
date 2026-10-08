"""Fill the SEBI template from one filing.

For every row of the template (sebi_template.py) we look up its XBRL tag(s) (p6_mapping.py), read the value for the
current and the previous year, clean it (values.py), put it in a standard unit (units.py), and store it as a `Cell`
with its status and warnings (models.py).  Finally checks.py looks for numbers that do not make sense.

Nothing here knows about HTML.  The SEBI view and the dashboard both read the Principle6Report built here.
"""

from brsr_p6.core.fiscal_year import previous_fiscal_year
from brsr_p6.core.models import Assurance, Cell, Facility, ListTable, Metric, Principle6Report, Status
from brsr_p6.core.sebi_template import QUESTIONS
from brsr_p6.core.units import convert
from brsr_p6.extraction.checks import run_checks
from brsr_p6.extraction.values import clean_number, clean_text, clean_yes_no
from brsr_p6.parsing import p6_mapping as mapping
from brsr_p6.parsing.xbrl_reader import natural_order

NO_FIELD = "The structured filing has no field for this item."
NOT_FOUND = "Not found in the filing."


def build_report(filing, company_name, symbol, fy, record=None):
    """Turn a read filing (XbrlFiling) into a Principle6Report."""
    report = Principle6Report(
        company_name=company_name,
        symbol=symbol,
        fy=fy,
        previous_fy=previous_fiscal_year(fy),
        boundary=clean_text(filing.text_of("ReportingBoundary")) or "Not stated in the filing",
        taxonomy_release=filing.release.isoformat(),
        family=filing.family,
        submission_date=getattr(record, "submission_date", "") or "",
        revision_date=getattr(record, "revision_date", "") or "",
        source_file=filing.path.name,
        warnings=list(filing.warnings),
    )
    _check_year_matches(report, filing)

    for question in QUESTIONS:
        if question.kind == "table":
            for row in question.rows:
                if not row.header:
                    report.metrics[row.key] = _metric(filing, row.key, row.label)
        elif question.kind == "yes_no":
            report.metrics[f"{question.id}.answer"] = _metric(filing, f"{question.id}.answer", "Answer", years=("current",))
            report.metrics[f"{question.id}.details"] = _metric(filing, f"{question.id}.details", "Details", years=("current",))
        elif question.kind == "text":
            report.metrics[f"{question.id}.details"] = _metric(filing, f"{question.id}.details", "Details", years=("current",))
        elif question.kind == "number":
            report.metrics[f"{question.id}.value"] = _metric(filing, f"{question.id}.value", "Percentage", years=("current",))
        elif question.kind == "list":
            report.tables[question.id] = _list_table(filing, question)
        elif question.kind == "facilities":
            report.facilities = _facilities(filing, question)

        if question.assurance:
            report.assurance[question.id] = _assurance(filing, question.id)

    _fill_extras(report, filing)
    run_checks(report)
    return report


def _check_year_matches(report, filing):
    """FY 2025-26 must end in 2026.  If the file's own periods disagree, say so instead of silently trusting it."""
    expected_end_year = int(report.fy[:4]) + 1
    if filing.current_end.year != expected_end_year:
        report.warnings.append(
            f"The file's current reporting year ends on {filing.current_end}, which does not match FY {report.fy}. "
            "Check that the right filing was used."
        )


# ------------------------------------------------------------------------------------------------ rows
def _metric(filing, key, label, years=("current", "previous"), dims=(), sources=None):
    source = (sources or mapping.SOURCES).get(key)
    metric = Metric(key, label)
    if source is None:
        metric.current = Cell(note=NO_FIELD)
        return metric
    metric.current = read_cell(filing, source, "current", dims)
    if "previous" in years:
        metric.previous = read_cell(filing, source, "previous", dims)
    return metric


def read_cell(filing, source, year, dims=()):
    """Read one value (one cell of a SEBI table) from the filing."""
    tags = source.modern if filing.family == "modern" else source.legacy
    if not tags:
        return Cell(note=NO_FIELD)
    if source.kind in ("yes_no", "text"):
        return _read_text(filing, source, tags[0], year, dims)
    if source.kind == "percent":
        return _read_percent(filing, tags[0], year)
    return _read_number(filing, source, tags, year, dims)


def _read_number(filing, source, tags, year, dims):
    parts = []        # one entry for every tag that has a usable number
    said = ""         # e.g. "NA": the filing has the tag but no number in it
    for tag in tags:
        facts = filing.facts_named(tag, year, dims=dims)           # the plain fact (the total), if the filing has one
        numbers = _numbers(facts)
        if not numbers and source.add_all_rows:
            # No plain total: add up the row-labelled facts instead.  (Never both: when a filing gives a total AND
            # its breakdown rows, adding everything would count the same energy twice.)
            facts = filing.facts_named(tag, year, dims=None)
            numbers = _numbers(facts)
        if not numbers:
            if facts:
                said = facts[0].text
            continue
        total = sum(n for n, _ in numbers)
        raw = numbers[0][1].text if len(numbers) == 1 else f"{total:g}"
        parts.append((tag, total, numbers[0][1].unit, raw))

    if not parts:
        return Cell(note=f"The filing says '{said}'." if said else NOT_FOUND)

    legacy_text = ""
    if source.unit_text_tag:  # older filings: unit written as text in a separate tag (look in the current year too)
        legacy_text = clean_text(filing.text_of(source.unit_text_tag, year) or filing.text_of(source.unit_text_tag, "current")) or ""

    converted = [convert(source.kind, number, unit_id, legacy_text) for _, number, unit_id, _ in parts]
    value = sum(c[0] for c in converted)
    unit = converted[0][1]
    notes = [c[3] for c in converted if c[3]]
    warnings = []
    for c in converted:
        warnings += [w for w in c[4] if w not in warnings]
    as_filed = " + ".join(f"{raw} {unit_id or legacy_text or '(no unit)'}" for _, _, unit_id, raw in parts)

    if len(tags) > 1:  # we added several reported numbers together
        status = Status.CALCULATED
        notes.insert(0, source.how or "Sum of " + ", ".join(t for t, _, _, _ in parts))
        if len(parts) < len(tags):
            notes.append(f"Built from {len(parts)} of {len(tags)} parts (the filing has no figure for the others).")
    else:
        status = converted[0][2]
    if source.fixed_warning:
        warnings.append(source.fixed_warning)
    return Cell(value, unit, status, as_filed, " ".join(notes), warnings)


def _numbers(facts):
    """[(number, fact), ...] for the facts that really hold a number."""
    pairs = [(clean_number(f.text), f) for f in facts]
    return [(n, f) for n, f in pairs if n is not None]


def _read_text(filing, source, tag, year, dims):
    if year != "current":
        return Cell()  # yes/no and text questions are asked for the current year only
    facts = filing.facts_named(tag, "current", dims)
    text = clean_text(facts[0].text) if facts else None
    if text is None:
        return Cell(note=NOT_FOUND)
    if source.kind == "yes_no":
        answer, understood = clean_yes_no(text)
        cell = Cell(answer, "", Status.REPORTED, text)
        if not understood:
            cell.warnings.append(f"Unexpected answer '{text}' (expected Yes or No).")
        return cell
    return Cell(text, "", Status.REPORTED, text)


def _read_percent(filing, tag, year):
    facts = filing.facts_named(tag, year)
    number = clean_number(facts[0].text) if facts else None
    if number is None:
        return Cell(note=NOT_FOUND)
    if 0 <= number <= 1:  # XBRL stores percentages as fractions: 0.11 means 11 %
        return Cell(number * 100, "%", Status.CONVERTED, f"{facts[0].text} (as a fraction)", f"Filed as the fraction {facts[0].text}; shown as a percentage.")
    return Cell(number, "%", Status.REPORTED, facts[0].text)


# ------------------------------------------------------------------------------------------------ list tables
def _list_table(filing, question):
    columns = mapping.LIST_COLUMNS[question.id]
    tags = {tag for column in columns if column for tag in column}
    row_labels = set()
    for tag in tags:
        row_labels |= set(filing.row_labels(tag, "current"))

    rows = []
    for number, dims in enumerate(sorted(row_labels, key=natural_order), start=1):
        row = []
        for column in columns:
            if column is None:
                row.append(str(number))
            elif not column:
                row.append("Not in the structured filing")
            else:
                pieces = []
                for tag in column:
                    facts = filing.facts_named(tag, "current", dims)
                    if facts and clean_text(facts[0].text):
                        pieces.append(_tidy(facts[0].text))
                row.append("; ".join(pieces) if pieces else "Not reported")
        rows.append(row)

    note = ""
    if not rows:
        note = "The structured filing lists no rows for this table (this can mean none apply, or nothing was reported)."
    return ListTable(question.id, list(question.columns), rows, note)   # (the question's own remark is shown separately)


def _tidy(text):
    """Show true/false as Yes/No inside list tables; leave everything else as filed."""
    answer, understood = clean_yes_no(text)
    return answer if understood and text.strip().lower() in ("true", "false", "yes", "no", "y", "n") else clean_text(text)


# ------------------------------------------------------------------------------------------------ facilities in water-stressed areas
def _facilities(filing, question):
    facilities = []
    for dims in filing.row_labels(mapping.FACILITY_NAME_TAG, "current"):
        name = _first_text(filing, mapping.FACILITY_NAME_TAG, dims) or "(name not given)"
        nature = _first_text(filing, mapping.FACILITY_NATURE_TAG, dims) or "(not given)"
        metrics = {}
        for row in question.rows:
            if not row.header:
                metrics[row.key] = _metric(filing, row.key, row.label, dims=dims, sources=mapping.FACILITY_SOURCES)
        facilities.append(Facility(name, nature, metrics))
    return facilities


def _first_text(filing, tag, dims):
    facts = filing.facts_named(tag, "current", dims)
    return clean_text(facts[0].text) if facts else None


# ------------------------------------------------------------------------------------------------ extras and assurance
def _fill_extras(report, filing):
    for key, (label, source) in mapping.EXTRAS.items():
        metric = Metric(key, label, read_cell(filing, source, "current"), read_cell(filing, source, "previous"))
        if metric.current.status != Status.NOT_REPORTED or metric.previous.status != Status.NOT_REPORTED:
            report.extras[key] = metric  # only keep extras the filing really has


def _assurance(filing, question_id):
    topic = mapping.ASSURANCE_TOPICS.get(question_id)
    if topic is None:
        return Assurance()
    names = filing.tag_names()
    answer_tags = [n for n in names
                   if "Independent" in n and topic in n
                   and not any(bad in n for bad in ("NameOf", "TextBlock", "SubType", "IsAssuredBy", "AssurerHas"))]
    agency_tags = [n for n in names if n.startswith("NameOfTheExternalAgency") and topic in n]

    if question_id == "L1":
        # Energy appears twice in SEBI's form (Essential 1 and Leadership 1).  Some editions have one tag for each,
        # some only one; the Leadership one has "Leadership" in its name.
        answer_tags = [n for n in answer_tags if "Leadership" in n]
        agency_tags = [n for n in agency_tags if "ThatUndertook" in n]
    elif question_id == "E1":
        # Prefer the Essential-style tag; use the Leadership-named one only if it is the filing's single energy tag.
        answer_tags.sort(key=lambda n: "Leadership" in n)
        agency_tags.sort(key=lambda n: not n.startswith("NameOfTheExternalAgencyIf"))

    result = Assurance()
    for tag in answer_tags:
        text = clean_text(filing.text_of(tag))
        if text:
            result.carried_out = clean_yes_no(text)[0]
            break
    for tag in agency_tags:
        text = clean_text(filing.text_of(tag))
        if text:
            result.agency = text
            break
    return result
