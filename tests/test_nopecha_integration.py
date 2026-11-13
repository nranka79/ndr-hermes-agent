"""Unit tests for the NopeCHA CAPTCHA-recognition integration.

Covers the CAPTCHA classifier (tools/browser_captcha_detection.py) and the
NopeCHA client + tool (tools/nopecha_client.py, tools/nopecha_recognition_tool.py).

All NopeCHA API calls are mocked (unittest.mock) -- per the integration's own
rules, these tests must never attempt to circumvent a live third-party CAPTCHA
system, and must not depend on live NopeCHA credit/quota (which is, as of
this writing, unreliable on free mode -- see tools/nopecha_client.py).
"""

import json
import sys
import time
from pathlib import Path
from unittest import mock

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.browser_captcha_detection import classify_page  # noqa: E402
from tools import nopecha_client as nc  # noqa: E402
from tools.nopecha_recognition_tool import nopecha_recognition  # noqa: E402


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

class _FakeResponse:
    def __init__(self, status_code=200, json_body=None, text=""):
        self.status_code = status_code
        self.is_success = 200 <= status_code < 300
        self._json_body = json_body if json_body is not None else {}
        self.text = text or json.dumps(self._json_body)

    def json(self):
        return self._json_body


@pytest.fixture(autouse=True)
def _isolated_hermes_home(tmp_path, monkeypatch):
    """Every test gets its own HERMES_HOME so the on-disk quota/stats cache
    never leaks between tests or touches the real ~/.hermes."""
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    yield


@pytest.fixture(autouse=True)
def _no_real_api_key(monkeypatch):
    """Force free mode (no key) unless a test explicitly sets one."""
    monkeypatch.delenv("NOPECHA_API_KEY", raising=False)


@pytest.fixture(autouse=True)
def _direct_egress(monkeypatch):
    """Keep the unit suite hermetic: never touch the real tunnel unless a
    test opts into router mode explicitly."""
    monkeypatch.setenv("NOPECHA_EGRESS", "direct")
    monkeypatch.delenv("NOPECHA_EGRESS_PROXY", raising=False)
    monkeypatch.delenv("AGENT_BROWSER_PROXY", raising=False)
    monkeypatch.delenv("NOPECHA_EGRESS_RETRIES", raising=False)


# ---------------------------------------------------------------------------
# 1 & 2: normal browsing / CAPTCHA detection (classify_page)
# ---------------------------------------------------------------------------

def test_classify_normal_page():
    result = classify_page(title="Example Domain", url="https://example.com", snapshot_text="Welcome.")
    assert result["classification"] == "normal"


def test_classify_captcha_by_title():
    result = classify_page(title="Just a moment...", url="https://site.com")
    assert result["classification"] == "captcha"
    assert result["confidence"] == "high"


def test_classify_captcha_by_iframe_with_no_title_match():
    frame_tree = {
        "top": {"url": "https://site.com", "name": ""},
        "children": [{"url": "https://www.google.com/recaptcha/api2/anchor?k=x", "name": "reCAPTCHA"}],
    }
    result = classify_page(title="Human Verification", url="https://site.com", frame_tree=frame_tree)
    assert result["classification"] == "captcha"
    assert result["provider_hint"] == "recaptcha"


def test_classify_access_denied_not_captcha():
    """Explicit requirement: a flat refusal must NOT be mis-classified as a CAPTCHA."""
    result = classify_page(title="403 Forbidden", url="https://site.com", snapshot_text="You do not have permission.")
    assert result["classification"] == "access_denied"


def test_classify_ambiguous_wording_is_access_denied_low_confidence_not_captcha():
    result = classify_page(title="Access to this page has been blocked", url="https://site.com")
    assert result["classification"] == "access_denied"
    assert result["confidence"] == "low"


# ---------------------------------------------------------------------------
# 3: unsupported challenge type
# ---------------------------------------------------------------------------

def test_submit_recognition_unsupported_type_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        nc.submit_recognition("funcaptcha", task="x", image_data=["data:image/png;base64,AAAA"])


def test_tool_unsupported_type_returns_structured_error():
    out = json.loads(nopecha_recognition(
        challenge_type="funcaptcha", task="x", image_data="data:image/png;base64,AAAA",
    ))
    assert out["status"] == "error"
    assert out["error"]["reason"] == "unsupported_challenge_type"


# ---------------------------------------------------------------------------
# 4: NopeCHA API unavailable (transient network failure)
# ---------------------------------------------------------------------------

def test_network_unavailable_raises_network_error_after_bounded_retries():
    calls = {"n": 0}

    def _boom(*a, **k):
        calls["n"] += 1
        raise httpx.ConnectError("no route to host")

    with mock.patch("tools.nopecha_client._http_request", side_effect=_boom), \
         mock.patch("tools.nopecha_client.time.sleep"):
        with pytest.raises(nc.NopeCHAError) as exc_info:
            nc.get_status()
    assert exc_info.value.reason == "network_error"
    assert calls["n"] == 2  # bounded retry, not unbounded


# ---------------------------------------------------------------------------
# 5: invalid/malformed API response
# ---------------------------------------------------------------------------

def test_submit_with_missing_data_field_raises_unknown_error():
    resp = _FakeResponse(status_code=200, json_body={})  # 200 OK but no "data"
    with mock.patch("tools.nopecha_client._http_request", return_value=resp):
        with pytest.raises(nc.NopeCHAError) as exc_info:
            nc.submit_recognition("recaptcha", task="x", grid="4x4", image_data=["data:image/png;base64,AAAA"])
    assert exc_info.value.reason == "unknown_error"


# ---------------------------------------------------------------------------
# 6: free quota exhausted -- pre-flight check blocks before a doomed submit
# ---------------------------------------------------------------------------

def test_preflight_blocks_submit_when_cached_credit_is_zero():
    status_resp = _FakeResponse(status_code=200, json_body={
        "plan": "Free", "status": "Active", "credit": 0, "quota": 100, "duration": 82800,
    })
    calls = []

    def _fake_request(client, method, url, **kwargs):
        calls.append((method, url))
        return status_resp

    with mock.patch("tools.nopecha_client._http_request", side_effect=_fake_request):
        with pytest.raises(nc.NopeCHAError) as exc_info:
            nc.submit_recognition("recaptcha", task="x", grid="4x4", image_data=["data:image/png;base64,AAAA"])

    assert exc_info.value.reason == "insufficient_credit"
    # Only the /v1/status GET happened -- the doomed POST to /v1/recognition/* never fired.
    assert len(calls) == 1
    assert calls[0][0] == "GET"
    assert "/v1/status" in calls[0][1]


def test_preflight_does_not_block_when_quota_check_itself_is_transient_error():
    """A flaky quota check must not mask a request that might still succeed."""
    rate_limited = _FakeResponse(status_code=429, json_body={"error": 11, "message": "Rate limit reached"})
    submit_ok = _FakeResponse(status_code=200, json_body={"data": "job123"})
    responses = [rate_limited, submit_ok]

    def _fake_request(client, method, url, **kwargs):
        return responses.pop(0)

    with mock.patch("tools.nopecha_client._http_request", side_effect=_fake_request):
        job_id = nc.submit_recognition("recaptcha", task="x", grid="4x4", image_data=["data:image/png;base64,AAAA"])
    assert job_id == "job123"


# ---------------------------------------------------------------------------
# 7 / IP ineligible -- the real failure mode hit during Phase 0/2 testing
# ---------------------------------------------------------------------------

def test_ip_ineligible_error_surfaces_through_the_tool():
    banned_resp = _FakeResponse(status_code=403, json_body={"error": 12, "message": "Banned IP"})
    with mock.patch("tools.nopecha_client._http_request", return_value=banned_resp):
        out = json.loads(nopecha_recognition(
            challenge_type="recaptcha", task="Select all squares with vehicles.", grid="4x4",
            image_data="data:image/png;base64,AAAA",
        ))
    assert out["status"] == "error"
    assert out["error"]["reason"] == "ip_ineligible"
    assert out["error"]["code"] == 12


# ---------------------------------------------------------------------------
# job_incomplete retry-then-success (poll_recognition)
# ---------------------------------------------------------------------------

def test_poll_retries_on_job_incomplete_then_succeeds():
    incomplete = _FakeResponse(status_code=409, json_body={"error": 14, "message": "Job is incomplete"})
    done = _FakeResponse(status_code=200, json_body={"data": [True, False]})
    responses = [incomplete, incomplete, done]

    def _fake_request(client, method, url, **kwargs):
        return responses.pop(0)

    with mock.patch("tools.nopecha_client._http_request", side_effect=_fake_request), \
         mock.patch("tools.nopecha_client.time.sleep"):
        result = nc.poll_recognition("recaptcha", "job123", poll_interval=0.01, max_wait=5.0)
    assert result == [True, False]


# ---------------------------------------------------------------------------
# 8: multiple Hermes sessions sharing one public IP -- quota cache dedup
# ---------------------------------------------------------------------------

def test_quota_cache_shared_across_concurrent_callers_only_hits_network_once():
    status_resp = _FakeResponse(status_code=200, json_body={
        "plan": "Free", "status": "Active", "credit": 50, "quota": 100, "duration": 82800,
    })
    calls = {"n": 0}

    def _fake_request(*a, **k):
        calls["n"] += 1
        return status_resp

    with mock.patch("tools.nopecha_client._http_request", side_effect=_fake_request):
        first = nc.get_status_cached()   # "session 1"
        second = nc.get_status_cached()  # "session 2", same process tick, same IP/key bucket
    assert first["credit"] == 50
    assert second["credit"] == 50
    assert calls["n"] == 1  # second call served from the shared on-disk cache


# ---------------------------------------------------------------------------
# 9: successful completion of an authorized verification workflow (mocked
#    mirror of the real recaptcha round trip proven live in Phase 1)
# ---------------------------------------------------------------------------

def test_tool_success_path_end_to_end_mocked():
    submit_resp = _FakeResponse(status_code=200, json_body={"data": "job_abc"})
    status_resp = _FakeResponse(status_code=200, json_body={
        "plan": "Free", "status": "Active", "credit": 99, "quota": 100, "duration": 82800,
    })
    poll_resp = _FakeResponse(status_code=200, json_body={"data": [False, False, True, False]})
    responses = [status_resp, submit_resp, poll_resp]

    def _fake_request(client, method, url, **kwargs):
        return responses.pop(0)

    with mock.patch("tools.nopecha_client._http_request", side_effect=_fake_request):
        out = json.loads(nopecha_recognition(
            challenge_type="recaptcha",
            task="Select all squares with vehicles.",
            grid="4x4",
            image_data="data:image/png;base64,AAAA",
            task_id="test-session",
        ))

    assert out["status"] == "success"
    assert out["provider"] == "nopecha"
    assert out["request_id"] == "job_abc"
    assert out["result"] == [False, False, True, False]

    stats = nc.get_call_stats()
    assert stats["success_count"] == 1
    assert stats["by_type"]["recaptcha"]["success_count"] == 1


# ---------------------------------------------------------------------------
# Missing/invalid input -- the "decline rather than guess" path (the
# implementation-level counterpart of "human intervention required": the
# tool must not attempt a best-effort guess when it structurally can't proceed)
# ---------------------------------------------------------------------------

def test_tool_missing_image_input_is_invalid_request_not_a_guess():
    out = json.loads(nopecha_recognition(challenge_type="recaptcha", task="x"))
    assert out["status"] == "error"
    assert out["error"]["reason"] == "invalid_request"


def test_tool_rejects_both_image_path_and_image_data():
    out = json.loads(nopecha_recognition(
        challenge_type="recaptcha", task="x",
        image_path="some/path.png", image_data="data:image/png;base64,AAAA",
    ))
    assert out["status"] == "error"
    assert out["error"]["reason"] == "invalid_request"


# ---------------------------------------------------------------------------
# Egress routing: router mode, per-job sessions, and the bounded retry
# ---------------------------------------------------------------------------

class _FakeHttpxClient:
    """Minimal stand-in for httpx.Client used by the _client seam."""

    def __init__(self, response):
        self.response = response

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def request(self, method, url, **kwargs):
        return self.response


def test_resolve_egress_router_uses_unique_socks5h_sessions(monkeypatch):
    monkeypatch.setenv("NOPECHA_EGRESS", "router")
    monkeypatch.setenv("NOPECHA_EGRESS_PROXY", "socks5://hermes-utilities:1000")

    first = nc.resolve_egress()
    second = nc.resolve_egress()

    assert first.mode == second.mode == "router"
    assert first.is_router is True
    assert first.proxy_url.startswith("socks5h://nopecha-")
    assert "@hermes-utilities:1000" in first.proxy_url
    assert first.session_id != second.session_id

    retry = nc.resolve_egress(force_residential=True)
    assert retry.session_id.startswith("res-")
    assert retry.proxy_url.startswith("socks5h://res-")


def test_auto_egress_is_direct_without_a_proxy(monkeypatch):
    monkeypatch.setenv("NOPECHA_EGRESS", "auto")
    egress = nc.resolve_egress()
    assert egress.mode == "direct"
    assert egress.is_router is False


def test_max_egress_attempts_default_and_clamped(monkeypatch):
    monkeypatch.delenv("NOPECHA_EGRESS_RETRIES", raising=False)
    assert nc.max_egress_attempts() == 2

    monkeypatch.setenv("NOPECHA_EGRESS_RETRIES", "0")
    assert nc.max_egress_attempts() == 1

    monkeypatch.setenv("NOPECHA_EGRESS_RETRIES", "9")
    assert nc.max_egress_attempts() == 3


def test_router_mode_skips_free_quota_preflight(monkeypatch):
    monkeypatch.setenv("NOPECHA_EGRESS_PROXY", "socks5://hermes-utilities:1000")
    seen = []

    def _fake_client(egress, timeout):
        seen.append((egress, timeout))
        return _FakeHttpxClient(_FakeResponse(status_code=200, json_body={"data": "job_router"}))

    with mock.patch("tools.nopecha_client._client", side_effect=_fake_client):
        job_id = nc.submit_recognition(
            "recaptcha", task="x", grid="4x4",
            image_data=["data:image/png;base64,AAAA"],
            egress=nc.resolve_egress(mode="router"),
        )

    assert job_id == "job_router"
    assert len(seen) == 1  # POST only -- no /v1/status preflight
    assert seen[0][0].is_router is True


def test_submit_and_poll_reuse_one_egress(monkeypatch):
    monkeypatch.setenv("NOPECHA_EGRESS_PROXY", "socks5://hermes-utilities:1000")
    egresses = []
    responses = [
        _FakeResponse(status_code=200, json_body={"data": "job_shared"}),
        _FakeResponse(status_code=200, json_body={"data": [True, False]}),
    ]

    def _fake_client(egress, timeout):
        egresses.append(egress)
        return _FakeHttpxClient(responses.pop(0))

    egress = nc.resolve_egress(mode="router")
    with mock.patch("tools.nopecha_client._client", side_effect=_fake_client):
        job_id = nc.submit_recognition(
            "recaptcha", task="x", image_data=["data:image/png;base64,AAAA"], egress=egress,
        )
        result = nc.poll_recognition("recaptcha", job_id, egress=egress)

    assert job_id == "job_shared"
    assert result == [True, False]
    assert len(egresses) == 2
    assert egresses[0] == egresses[1]
    assert egresses[0].session_id.startswith("nopecha-")


def test_retry_on_ip_ineligible_uses_forced_residential_session(monkeypatch):
    monkeypatch.setenv("NOPECHA_EGRESS", "router")
    monkeypatch.setenv("NOPECHA_EGRESS_PROXY", "socks5://hermes-utilities:1000")
    monkeypatch.setenv("NOPECHA_EGRESS_RETRIES", "1")

    egresses = []
    responses = [
        _FakeResponse(status_code=403, json_body={"error": 12, "message": "Banned IP"}),
        _FakeResponse(status_code=200, json_body={"data": "job_retry"}),
        _FakeResponse(status_code=200, json_body={"data": [False, True]}),
    ]

    def _fake_client(egress, timeout):
        egresses.append(egress)
        return _FakeHttpxClient(responses.pop(0))

    with mock.patch("tools.nopecha_client._client", side_effect=_fake_client):
        out = json.loads(nopecha_recognition(
            challenge_type="recaptcha",
            task="Select all squares with vehicles.",
            grid="4x4",
            image_data="data:image/png;base64,AAAA",
            task_id="test-retry",
        ))

    assert out["status"] == "success"
    assert out["request_id"] == "job_retry"
    assert len(egresses) == 3  # failed attempt, retry submit, retry poll
    assert egresses[0].session_id.startswith("nopecha-")
    assert all(e.session_id.startswith("res-") for e in egresses[1:])
    assert egresses[1] == egresses[2]
