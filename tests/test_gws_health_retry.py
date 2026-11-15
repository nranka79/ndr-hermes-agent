"""Tests for the hardened Google Health helper: token cache, retry, pagination.

Run: /opt/hermes/.venv/bin/python3 /data/hermes/tmp/test_gws_health_retry.py
"""
import io
import json
import os
import sys
import unittest
import urllib.error
from unittest import mock

sys.path.insert(0, "/opt/hermes")
from tools import gws_auth  # noqa: E402

os.environ.setdefault("HERMES_SESSION_USER_ID", "test@example.com")


class _Resp:
    def __init__(self, payload):
        self._body = json.dumps(payload).encode()

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class _Creds:
    client_id = "cid"
    client_secret = "secret"
    refresh_token = "refresh"
    scopes = ["https://www.googleapis.com/auth/googlehealth.activity_and_fitness.readonly"]


def _http_error(code, message="err", headers=None):
    return urllib.error.HTTPError(
        "https://example", code, message, headers or {},
        io.BytesIO(json.dumps({"error": {"message": message}}).encode()),
    )


class TestHealthRetry(unittest.TestCase):
    def setUp(self):
        gws_auth._HEALTH_TOKEN_CACHE.clear()
        self.creds_patch = mock.patch.object(
            gws_auth, "load_credentials", lambda service_name="google-gmail": _Creds())
        self.creds_patch.start()
        self.key = gws_auth._health_cache_key("google-gmail")

    def tearDown(self):
        self.creds_patch.stop()
        gws_auth._HEALTH_TOKEN_CACHE.clear()

    def _seed_token(self):
        gws_auth._HEALTH_TOKEN_CACHE[self.key] = ("tok", gws_auth.time.monotonic() + 1000)

    def test_token_is_cached_across_calls(self):
        with mock.patch("urllib.request.urlopen",
                        return_value=_Resp({"access_token": "tok", "expires_in": 3600})) as u:
            self.assertEqual(gws_auth.google_health_access_token("google-gmail"), "tok")
            self.assertEqual(gws_auth.google_health_access_token("google-gmail"), "tok")
        self.assertEqual(u.call_count, 1)

    def test_retry_on_503_then_success(self):
        calls = {"n": 0}

        def fake_urlopen(req, timeout=None):
            calls["n"] += 1
            if calls["n"] < 3:
                raise _http_error(503, "The service is currently unavailable.")
            return _Resp({"dataPoints": [{"name": "x"}]})

        self._seed_token()
        with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen), \
             mock.patch.object(gws_auth.time, "sleep", lambda s: None):
            out = gws_auth.google_health_request("GET", "x")
        self.assertEqual(out["dataPoints"][0]["name"], "x")
        self.assertEqual(calls["n"], 3)

    def test_400_is_not_retried(self):
        calls = {"n": 0}

        def fake_urlopen(req, timeout=None):
            calls["n"] += 1
            raise _http_error(400, "bad filter")

        self._seed_token()
        with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen), \
             mock.patch.object(gws_auth.time, "sleep", lambda s: None):
            with self.assertRaises(RuntimeError):
                gws_auth.google_health_request("GET", "x")
        self.assertEqual(calls["n"], 1)

    def test_401_re_mints_once(self):
        health_calls = {"n": 0}

        def fake_urlopen(req, timeout=None):
            url = getattr(req, "full_url", "")
            if "oauth2.googleapis.com/token" in url:
                return _Resp({"access_token": "tok2", "expires_in": 3600})
            health_calls["n"] += 1
            if health_calls["n"] == 1:
                raise _http_error(401, "Unauthenticated")
            return _Resp({"dataPoints": []})

        self._seed_token()
        with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
            out = gws_auth.google_health_request("GET", "x")
        self.assertEqual(out, {"dataPoints": []})
        self.assertEqual(health_calls["n"], 2)

    def test_paginator_sets_page_size_and_loops(self):
        seen = []

        def fake_request(method, path, service_name="google-gmail", params=None,
                         json_body=None, **kw):
            seen.append((params or {}).copy())
            if (params or {}).get("pageToken") == "p2":
                return {"dataPoints": [{"name": "b"}]}
            return {"dataPoints": [{"name": "a"}], "nextPageToken": "p2"}

        with mock.patch.object(gws_auth, "google_health_request", side_effect=fake_request):
            r = gws_auth.google_health_list_data_points("steps", page_size=None)
            self.assertEqual([p["name"] for p in r["data_points"]], ["a", "b"])
            self.assertEqual(r["pages"], 2)
            self.assertFalse(r["truncated"])
            self.assertEqual(seen[0]["pageSize"], 10000)
            seen.clear()
            gws_auth.google_health_list_data_points("sleep", page_size=None)
            self.assertEqual(seen[0]["pageSize"], 25)

    def test_rename_refuses_view_only_file(self):
        from tools import gws_ops

        class _Req:
            def get(self, **kw):
                return self

            def execute(self):
                return {"capabilities": {"canEdit": False},
                        "owners": [{"emailAddress": "owner@example.com"}]}

        class _Drive:
            def files(self):
                return _Req()

        class _Sheets:
            def spreadsheets(self):
                raise AssertionError("sheets must not be called for a view-only file")

        def fake_build(api, version, creds):
            return _Drive() if api == "drive" else _Sheets()

        with mock.patch.object(gws_ops, "_build", side_effect=fake_build):
            with self.assertRaises(gws_ops.GWSDataError):
                gws_ops.sheets_rename_tab(object(), "sid", "Sheet1", "New")

    def test_paginator_reports_truncation(self):
        def fake_request(method, path, service_name="google-gmail", params=None,
                         json_body=None, **kw):
            return {"dataPoints": [{"name": "x"}], "nextPageToken": "more"}

        with mock.patch.object(gws_auth, "google_health_request", side_effect=fake_request):
            r = gws_auth.google_health_list_data_points("steps", page_size=10, max_pages=2)
        self.assertTrue(r["truncated"])
        self.assertEqual(r["pages"], 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)