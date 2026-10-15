"""Tests for brsr_p6/api: the Dashboard JSON, the /api/ addresses and the file serving (uses the committed Tata Steel filings)."""

import json
from http import HTTPStatus

from brsr_p6.api.dashboard_json import available_filings, dashboard_to_dict
from brsr_p6.api.server import answer, app_file, respond
from brsr_p6.workflows.pipeline import load_saved_report


def test_available_filings_lists_the_saved_years():
    assert "2023-24" in available_filings()["TATASTEEL"]


def test_available_filings_of_a_missing_folder_is_empty(tmp_path):
    assert available_filings(tmp_path / "nothing") == {}


def test_the_dashboard_json_has_the_facts_the_sentences_and_the_cards_and_can_be_written_as_json():
    data = dashboard_to_dict(load_saved_report("TATASTEEL", "2023-24"))
    json.dumps(data)                                                  # nothing in it may be a non-JSON object
    assert data["symbol"] == "TATASTEEL" and data["fy"] == "2023-24" and data["previous_fy"] == "2022-23"
    dash = data["dashboard"]
    assert dash["glance"]["story"] and len(dash["glance"]["tiles"]) >= 5
    card = dash["topics"][0]["cards"][0]
    assert {"title", "big", "unit", "chip_text", "trend", "alerts", "trace"} <= set(card)


def test_dashboard_address_answers_with_the_dashboard():
    status, body = answer("/api/dashboard?symbol=tatasteel&fy=2023-24")
    assert status == HTTPStatus.OK and body["symbol"] == "TATASTEEL"


def test_dashboard_address_explains_a_missing_or_bad_request():
    assert answer("/api/dashboard?symbol=TATASTEEL")[0] == HTTPStatus.BAD_REQUEST
    assert answer("/api/dashboard?symbol=TATASTEEL&fy=abc")[0] == HTTPStatus.BAD_REQUEST
    status, body = answer("/api/dashboard?symbol=NOSUCH&fy=2023-24")
    assert status == HTTPStatus.NOT_FOUND and "flow.py download" in body["error"]


def test_unknown_address_is_404():
    assert answer("/api/nope")[0] == HTTPStatus.NOT_FOUND


# ------------------------------------------------------------------------------------------------ the built React app
def test_files_of_the_built_app_are_served_and_nothing_outside_the_folder_can_be_reached(tmp_path):
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<p>app</p>", encoding="utf-8")
    (dist / "assets" / "a.js").write_text("//js", encoding="utf-8")
    (tmp_path / "secret.txt").write_text("no", encoding="utf-8")
    assert app_file("/", dist) == (dist / "index.html").resolve()
    assert app_file("/assets/a.js", dist) == (dist / "assets" / "a.js").resolve()
    for bad in ("/missing.js", "/../secret.txt", "/%2e%2e/secret.txt", "/assets"):
        assert app_file(bad, dist) is None


def test_respond_serves_the_app_json_and_a_clear_message_when_the_app_is_not_built(tmp_path):
    (tmp_path / "index.html").write_text("<p>app</p>", encoding="utf-8")
    status, kind, body = respond("/", tmp_path, tmp_path)
    assert status == HTTPStatus.OK and kind.startswith("text/html") and body == b"<p>app</p>"
    status, kind, body = respond("/api/filings", tmp_path, tmp_path)
    assert status == HTTPStatus.OK and kind.startswith("application/json") and json.loads(body) == {}
    status, _, body = respond("/", tmp_path, tmp_path / "not_built")
    assert status == HTTPStatus.NOT_FOUND and b"npm run build" in body


# ------------------------------------------------------------------------------------------------ the chat runtime
def test_port_in_use_sees_a_listening_port_and_a_free_one():
    import socket

    from brsr_p6.api.assistant import port_in_use

    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        assert port_in_use(listener.getsockname()[1])
    free = socket.socket()
    free.bind(("127.0.0.1", 0))
    port = free.getsockname()[1]
    free.close()
    assert not port_in_use(port)


def test_the_runtime_is_not_started_without_its_setup_and_says_what_is_missing(tmp_path):
    from brsr_p6.api.assistant import start_runtime

    process, message = start_runtime(tmp_path)
    assert process is None and "npm install" in message
    (tmp_path / "node_modules").mkdir()
    process, message = start_runtime(tmp_path)
    assert process is None and ".env" in message
