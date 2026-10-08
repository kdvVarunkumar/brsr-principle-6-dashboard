"""Turn what the user typed ("Reliance", "Tata Steel", "TATASTEEL") into one NSE symbol.

NSE's own search box calls  /api/smart-search/eqEtf?q=<text>  and gets a list of matches. That list is messy:
it mixes equities with bonds and ETFs, and one company can appear under several share series.
`pick_company` (a pure function, easy to test) applies our rules; `resolve_company` adds the network call + a cache.
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path

from brsr_p6.core.errors import AmbiguousCompany, UnknownCompany

SEARCH_URL = "https://www.nseindia.com/api/smart-search/eqEtf"


@dataclass(frozen=True)
class Company:
    symbol: str
    name: str


def normalise_name(text: str) -> str:
    """'Tata Steel Limited' -> 'tata steel' so company names can be compared fairly."""
    text = re.sub(r"[^a-z0-9& ]+", " ", (text or "").lower())
    words = [w for w in text.split() if w not in ("limited", "ltd")]
    return " ".join(words)


def pick_company(query: str, candidates: list) -> Company:
    """Apply our matching rules to NSE's search results.

    1. Keep only equities (drop bonds, ETFs...).
    2. A symbol that equals the text typed wins ("reliance" -> RELIANCE).
    3. Otherwise a company whose name equals the text typed wins ("tata steel" -> Tata Steel Limited);
       if the same company has several share series, prefer the normal 'EQ' series.
    4. Otherwise a single remaining equity is accepted; several -> AmbiguousCompany (we list them).
    """
    equities = [c for c in candidates if str(c.get("segment", "")).lower() == "in equity"]
    if not equities:
        raise UnknownCompany(
            f"No NSE-listed company matches '{query}'. Check the spelling, or try the NSE symbol (for example TATASTEEL)."
        )

    typed_symbol = query.strip().upper()
    by_symbol = [c for c in equities if str(c.get("symbol", "")).upper() == typed_symbol]
    if len(by_symbol) == 1:
        return _to_company(by_symbol[0])

    typed_name = normalise_name(query)
    by_name = [c for c in equities if normalise_name(c.get("companyName", "")) == typed_name]
    if len(by_name) > 1:
        main_series = [c for c in by_name if c.get("series") == "EQ"]
        by_name = main_series or by_name
    if len(by_name) == 1:
        return _to_company(by_name[0])

    pool = by_name or equities
    if len(pool) == 1:
        return _to_company(pool[0])

    listing = "; ".join(f"{c['companyName']} ({c['symbol']})" for c in pool[:10])
    raise AmbiguousCompany(
        f"'{query}' matches several companies: {listing}. Run again with the exact NSE symbol, for example --company {pool[0]['symbol']}.",
        candidates=[_to_company(c) for c in pool[:10]],
    )


def resolve_company(query: str, client, cache_path: Path | None = None) -> Company:
    """Find the company for `query`. Search results are cached so repeating a query makes no network call."""
    query = (query or "").strip()
    if len(query) < 2:
        raise UnknownCompany("Please give at least 2 characters of the company name or NSE symbol.")

    key = normalise_name(query) or query.lower()
    cache = _load_json(cache_path)
    if key in cache:
        candidates = cache[key]
    else:
        found = client.get_json(SEARCH_URL, params={"q": query})
        candidates = [
            {k: c.get(k) for k in ("companyName", "symbol", "series", "segment")}
            for c in (found if isinstance(found, list) else [])
        ]
        if cache_path is not None:
            cache[key] = candidates
            _save_json(cache_path, cache)
    return pick_company(query, candidates)


def _to_company(candidate: dict) -> Company:
    return Company(symbol=candidate["symbol"], name=candidate["companyName"])


def _load_json(path):
    if path is not None and path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            return {}  # a damaged cache file is simply ignored
    return {}


def _save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1), encoding="utf-8")
