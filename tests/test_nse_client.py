"""Tests for brsr_p6/nse_client.py. No real network: a scripted fake session plays NSE's part."""

import pytest
import requests

from brsr_p6.errors import FileNotAvailable, NSEUnavailable
from brsr_p6.nse_client import NseClient


class FakeResponse:
    def __init__(self, status=200, content=b"", json_data=None):
        self.status_code = status
        self.content = content
        self._json = json_data

    def json(self):
        if self._json is None:
            raise ValueError("not json")
        return self._json


class FakeSession:
    """Hands out the scripted answers one by one; an Exception in the script is raised instead of returned."""

    def __init__(self, script):
        self.script = list(script)
        self.headers = {}
        self.urls = []

    def get(self, url, params=None, headers=None, timeout=None):
        self.urls.append(url)
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class FakeTime:
    """A pretend clock: sleeping just moves time forward, instantly."""

    def __init__(self):
        self.now = 0.0
        self.sleeps = []

    def clock(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


def make_client(script, **kwargs):
    fake_time = FakeTime()
    session = FakeSession(script)
    client = NseClient(session=session, sleep=fake_time.sleep, clock=fake_time.clock, **kwargs)
    return client, session, fake_time


def test_requests_are_spaced_at_least_min_interval_apart():
    # script: home page (warm-up), then the two API calls
    client, session, fake_time = make_client([FakeResponse(), FakeResponse(json_data={"a": 1}), FakeResponse(json_data={"b": 2})])
    client.get_json("https://x/1")
    client.get_json("https://x/2")
    # 3 requests happened (home, /1, /2); each of the 2 gaps must have been padded to 3 seconds
    assert len(session.urls) == 3
    assert fake_time.sleeps == [3.0, 3.0]


def test_warm_up_happens_once_only():
    client, session, _ = make_client([FakeResponse(), FakeResponse(json_data=[1]), FakeResponse(json_data=[2])])
    client.get_json("https://x/1")
    client.get_json("https://x/2")
    assert session.urls.count("https://www.nseindia.com/") == 1


@pytest.mark.parametrize("status", [403, 429])
def test_block_or_rate_limit_stops_immediately_without_retrying(status):
    client, session, _ = make_client([FakeResponse(status)])
    with pytest.raises(NSEUnavailable) as excinfo:
        client.download("https://x/file.xml", None, "xml")
    assert str(status) in str(excinfo.value)
    assert len(session.urls) == 1  # we did NOT hammer NSE with retries


def test_temporary_server_error_is_retried_with_growing_pauses(tmp_path):
    client, session, fake_time = make_client([FakeResponse(503), FakeResponse(502), FakeResponse(200, content=b"<?xml version='1.0'?><a/>")], retry_backoff=4.0)
    assert client.download("https://x/f.xml", tmp_path / "f.xml", "xml") > 0
    assert len(session.urls) == 3
    assert fake_time.sleeps[:2] == [4.0, 8.0]  # 4 s, then 8 s (the 3 s politeness gap is covered by the longer pause)


def test_gives_up_after_the_retries_with_a_clear_message():
    client, session, _ = make_client([requests.Timeout(), requests.ConnectionError(), requests.Timeout()])
    with pytest.raises(NSEUnavailable) as excinfo:
        client.download("https://x/f.xml", None, "xml")
    assert "3 tries" in str(excinfo.value)
    assert len(session.urls) == 3


def test_404_means_only_that_file_is_missing():
    client, _, _ = make_client([FakeResponse(404)])
    with pytest.raises(FileNotAvailable):
        client.download("https://x/gone.xml", None, "xml")


def test_html_block_page_is_never_saved_as_a_filing(tmp_path):
    client, _, _ = make_client([FakeResponse(200, content=b"<html><body>Access Denied</body></html>")])
    dest = tmp_path / "f.xml"
    with pytest.raises(NSEUnavailable):
        client.download("https://x/f.xml", dest, "xml")
    assert not dest.exists() and not list(tmp_path.iterdir())


def test_valid_xml_and_pdf_are_saved_without_leftover_partial_files(tmp_path):
    client, _, _ = make_client([FakeResponse(200, content=b"\xef\xbb\xbf<?xml version='1.0'?><x/>"), FakeResponse(200, content=b"%PDF-1.7 ...")])
    client.download("https://x/f.xml", tmp_path / "a" / "f.xml", "xml")
    client.download("https://x/f.pdf", tmp_path / "a" / "f.pdf", "pdf")
    assert sorted(p.name for p in (tmp_path / "a").iterdir()) == ["f.pdf", "f.xml"]


def test_non_json_answer_is_reported_clearly():
    client, _, _ = make_client([FakeResponse(), FakeResponse(200, content=b"<html>")])
    with pytest.raises(NSEUnavailable) as excinfo:
        client.get_json("https://x/api")
    assert "JSON" in str(excinfo.value)
