"""The only place in the project that talks to NSE over the internet.

Being polite to NSE (an explicit rule of the assignment) is enforced here, in one place:
  * a minimum pause between ANY two requests (default 3 seconds),
  * a few retries only for temporary problems (timeouts, NSE server errors), with growing pauses,
  * NO retry when NSE says 403/429 ("go away / too many requests"): we stop and tell the user,
  * files are written only after we check they look like the right kind of file.
"""

import time
from pathlib import Path

import requests

from brsr_p6.errors import FileNotAvailable, NSEUnavailable

HOME_URL = "https://www.nseindia.com/"
BRSR_PAGE_URL = "https://www.nseindia.com/companies-listing/corporate-filings-bussiness-sustainabilitiy-reports"

# NSE serves its pages and data to browsers; we identify ourselves as an ordinary browser.
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


class NseClient:
    def __init__(
        self,
        min_interval: float = 3.0,
        timeout: float = 60.0,
        max_retries: int = 2,
        retry_backoff: float = 4.0,
        session=None,
        sleep=time.sleep,
        clock=time.monotonic,
    ):
        self.min_interval = min_interval
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self.session = session or requests.Session()  # a Session remembers cookies between requests
        self.session.headers.update(BROWSER_HEADERS)
        # `sleep` and `clock` are parameters so tests can replace them with instant fakes.
        self._sleep = sleep
        self._clock = clock
        self._last_request_at = None
        self._warmed_up = False
        self.request_count = 0  # how many requests we really sent (handy to prove caching works)

    # ------------------------------------------------------------------ politeness
    def _wait_turn(self):
        """Pause if the previous request was less than `min_interval` seconds ago."""
        if self._last_request_at is not None:
            wait = self.min_interval - (self._clock() - self._last_request_at)
            if wait > 0:
                self._sleep(wait)

    def _request(self, url, params=None, headers=None):
        """One polite GET with retries for temporary problems. Returns the response (HTTP 200) or raises."""
        problem = "unknown problem"
        for attempt in range(self.max_retries + 1):
            self._wait_turn()
            try:
                self.request_count += 1
                response = self.session.get(url, params=params, headers=headers, timeout=self.timeout)
            except (requests.Timeout, requests.ConnectionError) as exc:
                problem = f"{type(exc).__name__}"
            else:
                if response.status_code == 200:
                    self._last_request_at = self._clock()
                    return response
                if response.status_code in (403, 429):
                    raise NSEUnavailable(
                        f"NSE refused the request (HTTP {response.status_code}). It is probably limiting automated "
                        "access. Wait a few minutes and try again. Companies you have already downloaded keep working "
                        "from the copy saved on disk."
                    )
                if response.status_code in (404, 410):
                    raise FileNotAvailable(f"NSE has nothing at {url} (HTTP {response.status_code}).")
                if response.status_code < 500:
                    raise NSEUnavailable(f"NSE answered HTTP {response.status_code} for {url}.")
                problem = f"HTTP {response.status_code}"  # a 5xx = NSE-side problem, worth a retry
            self._last_request_at = self._clock()
            if attempt < self.max_retries:
                self._sleep(self.retry_backoff * (2 ** attempt))
        raise NSEUnavailable(
            f"Could not get {url} from NSE after {self.max_retries + 1} tries ({problem}). "
            "Check your internet connection or try again later."
        )

    # ------------------------------------------------------------------ public methods
    def warm_up(self):
        """Visit the NSE home page once so NSE gives us its cookies (its API refuses cookie-less callers)."""
        if not self._warmed_up:
            self._request(HOME_URL)
            self._warmed_up = True

    def get_json(self, url, params=None):
        """Call an NSE data API and return the parsed JSON."""
        self.warm_up()
        response = self._request(
            url,
            params=params,
            headers={"Accept": "application/json, text/plain, */*", "Referer": BRSR_PAGE_URL},
        )
        try:
            return response.json()
        except ValueError:
            raise NSEUnavailable(
                "NSE did not return data in the expected (JSON) format. It may be showing a block page; try again later."
            )

    def download(self, url, dest: Path, kind: str) -> int:
        """Download a file (kind is 'xml' or 'pdf') to `dest`. Returns the size in bytes."""
        content = self._request(url).content
        if not _looks_like(kind, content):
            raise NSEUnavailable(
                f"NSE returned something that is not a valid {kind.upper()} file for {url} "
                "(possibly a block page). Nothing was saved."
            )
        dest.parent.mkdir(parents=True, exist_ok=True)
        # Write to a temporary name first, then rename: a crash never leaves a half-written file behind.
        partial = dest.with_name(dest.name + ".part")
        partial.write_bytes(content)
        partial.replace(dest)
        return len(content)


def _looks_like(kind: str, content: bytes) -> bool:
    """Cheap check on the first bytes, so an HTML 'access denied' page is never saved as a filing."""
    head = content[:200].lstrip(b"\xef\xbb\xbf \r\n\t")  # ignore a byte-order mark / leading blanks
    if kind == "pdf":
        return head.startswith(b"%PDF")
    return head.startswith(b"<?xml") or head.startswith(b"<xbrl")
