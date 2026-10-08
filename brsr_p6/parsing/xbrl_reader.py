"""Read a BRSR filing (the .xml file downloaded from NSE) into plain Python objects.

An XBRL file is a long list of "facts" (one value each).  Every fact points to a "context" that says
WHICH YEAR it belongs to and (for table rows) which row label it carries.  This module:
  1. cleans the file and parses it,
  2. works out which year is the current and which the previous financial year (from the DATES in the contexts),
  3. gives back simple Fact objects you can look up by tag name.
"""

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from brsr_p6.core.errors import UnparseableFiling

_XBRLI = "{http://www.xbrl.org/2003/instance}"
_LINKBASE = "{http://www.xbrl.org/2003/linkbase}"   # the schemaRef element lives here; it is not a fact

# Characters that XML forbids.  A few filings contain some (Word soft-hyphens) inside long text answers.
_ILLEGAL_CHARACTERS = re.compile(rb"[\x00-\x08\x0b\x0c\x0e-\x1f]")

# The edition of SEBI's form is part of a namespace in the file, e.g. .../xbrl/2024-04-30/in-capmkt
_RELEASE = re.compile(rb'xmlns:in-capmkt="[^"]*/xbrl/(\d{4}-\d{2}-\d{2})/in-capmkt"')

# Editions released before this date use the older layout of tag names (checked on real filings).
FIRST_MODERN_RELEASE = date(2024, 4, 30)


@dataclass
class Fact:
    name: str     # tag name, e.g. "TotalScope1Emissions"
    text: str     # the value as text, e.g. "64"
    unit: str     # unit id as filed, e.g. "Gigajoule" ("" if none)
    end: date     # the day the period ends (for single-day "instant" facts: that day)
    dims: tuple   # extra row labels, e.g. ("SpecificInitiativesAxis=SpecificInitiativesDomain1",); () if none


class XbrlFiling:
    def __init__(self, path, release, current_end, previous_end, facts, warnings):
        self.path = path
        self.release = release                       # date of the form edition
        self.family = "legacy" if release < FIRST_MODERN_RELEASE else "modern"
        self.current_end = current_end               # last day of the current financial year
        self.previous_end = previous_end             # last day of the previous financial year
        self.facts = facts
        self.warnings = warnings                     # problems found while reading (shown to the user)
        # Tags are looked up ignoring upper/lower case, because NSE's own spelling is inconsistent
        # (e.g. "WithOutTreatment" in one tag and "WithoutTreatment" in the next).
        self._by_name = {}
        for fact in facts:
            self._by_name.setdefault(fact.name.lower(), []).append(fact)
        self._names = sorted({fact.name for fact in facts})

    def year_end(self, year):
        return self.current_end if year == "current" else self.previous_end

    def facts_named(self, name, year="current", dims=()):
        """Facts with this tag in the given year ("current" or "previous").
        dims=()      -> only plain facts (no extra row labels);   dims=None -> any;   dims=(...) -> exactly those labels."""
        wanted_end = self.year_end(year)
        found = []
        for fact in self._by_name.get(name.lower(), []):
            if fact.end != wanted_end:
                continue
            if dims is None or fact.dims == tuple(dims):
                found.append(fact)
        return found

    def text_of(self, name, year="current"):
        """The text of a plain fact, or None if the filing has none."""
        facts = self.facts_named(name, year)
        return facts[0].text if facts else None

    def row_labels(self, name, year="current"):
        """The distinct row labels (dims) used by a tag in a year, in natural order (...1, ...2, ...10)."""
        labels = {fact.dims for fact in self.facts_named(name, year, dims=None) if fact.dims}
        return sorted(labels, key=natural_order)

    def tag_names(self):
        return list(self._names)


def read_filing(path):
    """Read one filing file.  Raises UnparseableFiling (with a clear message) if it cannot be read at all."""
    path = Path(path)
    raw = path.read_bytes()
    cleaned, removed = _ILLEGAL_CHARACTERS.subn(b"", raw)  # strip forbidden characters (in memory only)
    warnings = []
    if removed:
        warnings.append(f"The file contained {removed} characters that XML forbids (inside free-text answers); they were removed before reading.")

    release = _find_release(cleaned, path)
    try:
        root = ET.fromstring(cleaned)
    except ET.ParseError as problem:
        line, column = problem.position
        raise UnparseableFiling(
            f"{path.name} is not valid XML (line {line}, column {column}: {problem}). "
            "The file on NSE appears to be damaged, so no figures can be read from it."
        )

    contexts = _read_contexts(root)
    current_end, previous_end = _find_years(contexts, path)
    facts = _read_facts(root, contexts)
    return XbrlFiling(path, release, current_end, previous_end, facts, warnings)


# ---------------------------------------------------------------------------------------------- helpers
def _find_release(cleaned, path):
    match = _RELEASE.search(cleaned[:20000])
    if not match:
        raise UnparseableFiling(
            f"{path.name} does not look like a SEBI BRSR XBRL filing (no 'in-capmkt' taxonomy found), so it cannot be used."
        )
    return date.fromisoformat(match.group(1).decode())


def _local(tag):
    return tag.rsplit("}", 1)[-1]


def _read_contexts(root):
    """context id -> (end date, dims).  A context says which period a fact is about and which row label it carries."""
    contexts = {}
    for context in root.findall(_XBRLI + "context"):
        end = context.find(f"{_XBRLI}period/{_XBRLI}endDate")
        if end is None:
            end = context.find(f"{_XBRLI}period/{_XBRLI}instant")  # a single-day period
        if end is None or not end.text:
            continue
        dims = []
        for element in context.iter():
            if _local(element.tag) in ("explicitMember", "typedMember"):
                axis = (element.get("dimension") or "").split(":")[-1]
                member = (element.text or "").strip() or "".join((child.text or "").strip() for child in element)
                dims.append(f"{axis}={member.split(':')[-1]}")
        contexts[context.get("id")] = (date.fromisoformat(end.text.strip()), tuple(sorted(dims)))
    return contexts


def _find_years(contexts, path):
    """Current year = the latest period end among plain contexts; previous year = one year earlier."""
    plain_ends = sorted({end for end, dims in contexts.values() if not dims}, reverse=True)
    if not plain_ends:
        raise UnparseableFiling(f"{path.name} has no reporting period, so no year can be assigned to its figures.")
    current_end = plain_ends[0]
    try:
        previous_end = current_end.replace(year=current_end.year - 1)
    except ValueError:  # 29 February
        previous_end = current_end.replace(year=current_end.year - 1, day=28)
    return current_end, previous_end


def _read_facts(root, contexts):
    facts = []
    for element in root:
        if element.tag.startswith(_XBRLI) or element.tag.startswith(_LINKBASE):
            continue  # structure elements (context, unit, schemaRef...), not facts
        context = contexts.get(element.get("contextRef"))
        if context is None:
            continue
        text = " ".join("".join(element.itertext()).split())
        facts.append(Fact(_local(element.tag), text, element.get("unitRef") or "", context[0], context[1]))
    return facts


def natural_order(dims):
    """Sort key so that 'Axis=Member2' comes before 'Axis=Member10'."""
    numbers = re.findall(r"\d+", "|".join(dims))
    return [int(n) for n in numbers] + [0]
