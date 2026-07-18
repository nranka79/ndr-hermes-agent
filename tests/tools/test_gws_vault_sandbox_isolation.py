"""End-to-end regression tests: the execute_code sandbox must never receive
GWS_VAULT_SOCKET (2026-07-18 vault impersonation fix), and gws_fetch_token
must be wired into the sandbox's allowed tools / generated stubs.

These run a REAL sandboxed subprocess (same harness as
tests/tools/test_code_execution.py's TestExecuteCode), not a mock -- the
property under test is about the actual child process environment, which a
mocked dispatcher wouldn't exercise.
"""

import json
import os

import pytest

os.environ["TERMINAL_ENV"] = "local"


@pytest.fixture(autouse=True)
def _force_local_terminal(monkeypatch):
    monkeypatch.setenv("TERMINAL_ENV", "local")


class TestSandboxAllowedToolsAndStubs:
    def test_gws_fetch_token_in_sandbox_allowed_tools(self):
        from tools.code_execution_tool import SANDBOX_ALLOWED_TOOLS
        assert "gws_fetch_token" in SANDBOX_ALLOWED_TOOLS

    def test_gws_fetch_token_stub_is_generated(self):
        from tools.code_execution_tool import generate_hermes_tools_module, SANDBOX_ALLOWED_TOOLS
        src = generate_hermes_tools_module(list(SANDBOX_ALLOWED_TOOLS))
        assert "def gws_fetch_token(" in src

    def test_gws_fetch_token_stub_omitted_when_not_enabled(self):
        from tools.code_execution_tool import generate_hermes_tools_module
        src = generate_hermes_tools_module(["terminal"])
        assert "def gws_fetch_token(" not in src


class TestSandboxEnvironmentIsolation:
    """Real subprocess execution -- confirms GWS_VAULT_SOCKET (and
    GWS_VAULT_SECRET, belt-and-suspenders) never reach the sandboxed child,
    even when they're set in the parent process."""

    def _run_real_sandbox(self, code, monkeypatch, enabled_tools=None):
        from tools.code_execution_tool import execute_code, SANDBOX_ALLOWED_TOOLS

        # Simulate the parent process legitimately having vault access
        # (as the real hermes gateway process does).
        monkeypatch.setenv("GWS_VAULT_SOCKET", "/run/gws-vault/vault.sock")
        monkeypatch.setenv("GWS_VAULT_SECRET", "definitely-not-a-real-secret")

        result = execute_code(
            code=code,
            task_id="test-vault-isolation",
            enabled_tools=enabled_tools or list(SANDBOX_ALLOWED_TOOLS),
        )
        return json.loads(result)

    def test_gws_vault_socket_absent_in_sandbox(self, monkeypatch):
        code = (
            'import os\n'
            'print("GWS_VAULT_SOCKET_PRESENT=" + str("GWS_VAULT_SOCKET" in os.environ))\n'
        )
        result = self._run_real_sandbox(code, monkeypatch)
        assert result["status"] == "success", result
        assert "GWS_VAULT_SOCKET_PRESENT=False" in result["output"]

    def test_gws_vault_secret_absent_in_sandbox(self, monkeypatch):
        """Already covered by the general secret-substring scrub, but pin it
        specifically for GWS_VAULT_SECRET since that's the credential this
        whole fix protects.

        Printed as a space-separated sentinel, not KEY=value -- the latter
        shape trips agent.redact.redact_sensitive_text's generic
        NAME_CONTAINING_SECRET=value pattern and would redact our own
        diagnostic output (a real, separate, pre-existing defense-in-depth
        feature; not a bug in this fix)."""
        code = (
            'import os\n'
            'present = "GWS_VAULT_SECRET" in os.environ\n'
            'print("sentinel-result", "present" if present else "absent")\n'
        )
        result = self._run_real_sandbox(code, monkeypatch)
        assert result["status"] == "success", result
        assert "sentinel-result absent" in result["output"]

    def test_direct_vault_client_import_fails_in_sandbox(self, monkeypatch):
        """The actual attack this closes: a sandboxed script hand-rolling a
        raw tools.gws_vault_client call (bypassing gws_auth.py's identity
        guard entirely) must fail outright, because there is no socket path
        to connect to."""
        code = (
            'from tools import gws_vault_client as vault\n'
            'try:\n'
            '    vault.resolve("email", "someone-else@draas.com")\n'
            '    print("VULNERABLE: resolve() succeeded without a socket")\n'
            'except Exception as e:\n'
            '    print("BLOCKED: " + str(e))\n'
        )
        result = self._run_real_sandbox(code, monkeypatch)
        assert result["status"] == "success", result
        assert "BLOCKED:" in result["output"]
        assert "VULNERABLE" not in result["output"]
        assert "GWS_VAULT_SOCKET" in result["output"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
