"""Tests for brsr_p6/company_lookup.py (search results below are shaped like real NSE answers)."""

import pytest

from brsr_p6.company_lookup import Company, normalise_name, pick_company, resolve_company
from brsr_p6.errors import AmbiguousCompany, UnknownCompany


def eq(name, symbol, series="EQ"):
    return {"companyName": name, "symbol": symbol, "series": series, "segment": "in equity"}


TATA_STEEL_RESULTS = [
    eq("Tata Steel Limited", "TATASTEEL"),
    eq("Tata Steel Bsl Limited", "TATASTLBSL"),
    eq("Tata Steel Limited", "TATASTLPP", series="BE"),  # partly-paid shares of the same company
    eq("Tata Steel Long Products Limited", "TATASTLLP", series="BE"),
]

HDFC_RESULTS = [
    eq("HDFC Bank Limited", "HDFCBANK"),
    {"companyName": "HDFC Bank Limited", "symbol": "765HDFC34", "series": None, "segment": "in bonds"},
    {"companyName": "HDFC Bank Limited", "symbol": "771HDFCB33", "series": None, "segment": "in bonds"},
]


def test_normalise_name_drops_limited_and_punctuation():
    assert normalise_name("Tata Steel Limited") == "tata steel"
    assert normalise_name("Reliance Industries Ltd.") == "reliance industries"


def test_company_name_match_prefers_the_main_eq_series():
    assert pick_company("Tata Steel", TATA_STEEL_RESULTS) == Company("TATASTEEL", "Tata Steel Limited")


def test_bonds_are_ignored():
    assert pick_company("hdfc bank", HDFC_RESULTS).symbol == "HDFCBANK"


def test_typed_symbol_wins():
    results = [eq("Reliance Industries Limited", "RELIANCE"), eq("Reliance Power Limited", "RPOWER"), eq("Reliance Infrastructure Limited", "RELINFRA")]
    assert pick_company("reliance", results).symbol == "RELIANCE"


def test_typed_symbol_is_case_insensitive():
    assert pick_company("tatasteel", TATA_STEEL_RESULTS).symbol == "TATASTEEL"


def test_single_equity_result_is_accepted():
    assert pick_company("infosy", [eq("Infosys Limited", "INFY")]).symbol == "INFY"


def test_several_different_companies_is_ambiguous_and_lists_candidates():
    results = [eq("Tata Power Company Limited", "TATAPOWER"), eq("Tata Motors Limited", "TATAMOTORS")]
    with pytest.raises(AmbiguousCompany) as excinfo:
        pick_company("tata", results)
    assert "TATAPOWER" in str(excinfo.value) and "TATAMOTORS" in str(excinfo.value)
    assert len(excinfo.value.candidates) == 2


def test_no_equity_results_is_unknown_company():
    only_bonds = [{"companyName": "X", "symbol": "1", "series": None, "segment": "in bonds"}]
    with pytest.raises(UnknownCompany):
        pick_company("xyz", only_bonds)
    with pytest.raises(UnknownCompany):
        pick_company("xyz", [])


class FakeSearchClient:
    def __init__(self, answer):
        self.answer = answer
        self.calls = 0

    def get_json(self, url, params=None):
        self.calls += 1
        return self.answer


def test_resolve_company_caches_search_results(tmp_path):
    client = FakeSearchClient(TATA_STEEL_RESULTS)
    cache = tmp_path / "company_search.json"

    first = resolve_company("Tata Steel", client, cache_path=cache)
    second = resolve_company("tata  STEEL", client, cache_path=cache)  # same company, different spelling/case

    assert first == second == Company("TATASTEEL", "Tata Steel Limited")
    assert client.calls == 1  # the second lookup came from the cache


def test_resolve_company_rejects_too_short_text():
    with pytest.raises(UnknownCompany):
        resolve_company("a", FakeSearchClient([]))
