"""A fake NSE for the loader tests: company search + filing list + files, all from memory.  Shared by test_trend_loader and test_summary_loader."""

import re

from xbrl_samples import both_years, build_xbrl

from brsr_p6.core.errors import FileNotAvailable
from brsr_p6.download.company_lookup import SEARCH_URL

XML = "https://nsearchives.nseindia.com/corporate/xbrl/"
SEARCH_ANSWER = [{"companyName": "Test Company Limited", "symbol": "TESTCO", "series": "EQ", "segment": "in equity"}]


def xbrl_for(fy_start, boundary="Standalone basis"):
    """A small but real filing whose reporting periods match `fy_start` (the helper's own dates are fixed to FY 2023-24)."""
    text = build_xbrl(both_years("TotalEnergyConsumedFromRenewableAndNonRenewableSources", 100 + fy_start % 100, 90, "Gigajoule")
                      + f'<in-capmkt:ReportingBoundary contextRef="DCYMain">{boundary}</in-capmkt:ReportingBoundary>\n')
    shift = {"2023-04-01": f"{fy_start}-04-01", "2024-03-31": f"{fy_start + 1}-03-31",
             "2022-04-01": f"{fy_start - 1}-04-01", "2023-03-31": f"{fy_start}-03-31"}
    return re.sub("|".join(shift), lambda m: shift[m.group(0)], text).encode("utf-8")


def row(fy_from):
    return {"symbol": "TESTCO", "companyName": "Test Company Limited", "fyFrom": fy_from, "fyTo": fy_from + 1,
            "submissionDate": "24-Jun-2025", "revisionDate": "-", "xbrlFile": f"{XML}f{fy_from}.xml", "attachmentFile": "null"}


class FakeNse:
    """Answers the company search and the filing list from memory and writes the given file contents."""

    def __init__(self, years, files=None, gone=(), search=SEARCH_ANSWER):
        self.listing = {"data": [row(y) for y in years]}
        self.files = files or {}
        self.gone, self.search = set(gone), search
        self.api_calls, self.downloads = [], []

    request_count = 0

    def get_json(self, url, params=None):
        self.api_calls.append(url)
        return {"data": []} if url == SEARCH_URL and not self.search else (self.search if url == SEARCH_URL else self.listing)

    def download(self, url, dest, kind):
        self.downloads.append(url)
        name = url.rsplit("/", 1)[-1]
        if name in self.gone:
            raise FileNotAvailable("gone")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(self.files.get(name, xbrl_for(int(name[1:5]))))
        return 10
