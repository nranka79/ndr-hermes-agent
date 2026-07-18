"""Tests for the Telegram vault-direct authorization check in authz_mixin.py.

Background: ``_is_user_authorized`` used to resolve Telegram identity via the
shared ``find_user_by_identity()`` helper, which falls back to scanning the
raw ``users.json`` file whenever ``vault.resolve()`` doesn't return a
user_id -- and it does that identically whether vault genuinely has no
record for the identity, or vault is simply unreachable. Since users.json is
writable by the same OS user that runs write_file/execute_code/terminal, a
raw file edit (bypassing manage_user's permissions.manage_users gate
entirely) could resolve as "vault has no record, fall back to file, found
it, authorized."

The fix checks ``tools.gws_vault_client.resolve()`` directly inside
``_is_user_authorized`` and branches on its three real outcomes:

  1. vault resolves the identity           -> authorized (subject to the
     vault-native App Access toggle).
  2. vault reached fine, cleanly not found -> NOT authorized via this check,
     and users.json is never consulted -- falls through to the env-allowlist
     checks below, same as the long-standing "not registered at all" path.
  3. vault raises (unreachable/crash-loop) -> falls back to the pre-existing
     file-registry check, unchanged, so a vault outage can't lock out real
     employees.

Directly monkeypatches functions on the real ``tools.gws_vault_client`` /
``tools._user_registry`` modules (rather than swapping sys.modules entries)
so behavior is correct regardless of whether those modules were already
imported elsewhere in the test session.
"""

from unittest.mock import MagicMock

import pytest

import tools.gws_vault_client as vault_module
import tools._user_registry as registry_module
from gateway.config import Platform
from gateway.session import SessionSource


def _make_runner():
    """Build a bare GatewayRunner with no allowlists/adapters configured."""
    from gateway.run import GatewayRunner

    runner = object.__new__(GatewayRunner)
    runner.config = None
    runner.adapters = {}
    runner.pairing_store = MagicMock()
    runner.pairing_store.is_approved.return_value = False
    return runner


def _source(user_id: str = "1234567890") -> SessionSource:
    return SessionSource(
        platform=Platform.TELEGRAM,
        user_id=user_id,
        chat_id="chat-1",
        user_name="tester",
        chat_type="dm",
    )


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch):
    for key in (
        "TELEGRAM_ALLOWED_USERS",
        "TELEGRAM_GROUP_ALLOWED_USERS",
        "TELEGRAM_GROUP_ALLOWED_CHATS",
        "TELEGRAM_ALLOW_ALL_USERS",
        "GATEWAY_ALLOWED_USERS",
        "GATEWAY_ALLOW_ALL_USERS",
    ):
        monkeypatch.delenv(key, raising=False)


class TestVaultResolvesIdentity:
    """Case 1: vault.resolve() returns a user_id -- authoritative."""

    def test_authorized_when_vault_has_identity(self, monkeypatch):
        runner = _make_runner()
        resolve_mock = MagicMock(return_value="testuser-1234567890")
        monkeypatch.setattr(vault_module, "resolve", resolve_mock)
        monkeypatch.setattr(vault_module, "get_identity", MagicMock(return_value={"permissions": {}}))

        assert runner._is_user_authorized(_source()) is True
        resolve_mock.assert_called_once_with("telegram", "1234567890")

    def test_denied_when_app_access_toggle_is_false(self, monkeypatch):
        runner = _make_runner()
        monkeypatch.setattr(vault_module, "resolve", MagicMock(return_value="testuser-1234567890"))
        monkeypatch.setattr(
            vault_module,
            "get_identity",
            MagicMock(return_value={"permissions": {"apps": {"telegram": False}}}),
        )

        assert runner._is_user_authorized(_source()) is False

    def test_authorized_when_app_access_toggle_missing(self, monkeypatch):
        """Fail-open: absent apps.telegram key must not block existing users."""
        runner = _make_runner()
        monkeypatch.setattr(vault_module, "resolve", MagicMock(return_value="testuser-1234567890"))
        monkeypatch.setattr(
            vault_module, "get_identity", MagicMock(return_value={"permissions": {"apps": {}}})
        )

        assert runner._is_user_authorized(_source()) is True

    def test_authorized_when_get_identity_fails(self, monkeypatch):
        """A transient get_identity failure after a successful resolve must
        not deny a user vault already confirmed exists."""
        runner = _make_runner()
        monkeypatch.setattr(vault_module, "resolve", MagicMock(return_value="testuser-1234567890"))
        monkeypatch.setattr(
            vault_module, "get_identity", MagicMock(side_effect=RuntimeError("transient"))
        )

        assert runner._is_user_authorized(_source()) is True


class TestVaultCleanNotFound:
    """Case 2: the actual security fix. A raw users.json injection (never
    registered through manage_user/vault) must NOT grant access, even
    though the file itself would resolve the identity."""

    def test_fake_users_json_entry_alone_does_not_authorize(self, monkeypatch):
        runner = _make_runner()
        monkeypatch.setattr(vault_module, "resolve", MagicMock(return_value=None))

        # Simulate a raw file injection: find_user_by_identity WOULD find
        # this if it were consulted. It must not be consulted at all.
        find_mock = MagicMock(
            return_value=("fake@attacker.com", {"permissions": {"manage_users": True}})
        )
        monkeypatch.setattr(registry_module, "find_user_by_identity", find_mock)

        assert runner._is_user_authorized(_source(user_id="999999999")) is False
        find_mock.assert_not_called()

    def test_falls_through_to_env_allowlist_when_not_in_vault(self, monkeypatch):
        """A user authorized purely via TELEGRAM_ALLOWED_USERS (never
        touched manage_user/vault) must still work -- case 2 must fall
        through, not hard-deny."""
        runner = _make_runner()
        monkeypatch.setattr(vault_module, "resolve", MagicMock(return_value=None))
        monkeypatch.setenv("TELEGRAM_ALLOWED_USERS", "555,1234567890")

        assert runner._is_user_authorized(_source(user_id="1234567890")) is True

    def test_denied_by_default_when_not_in_vault_or_allowlist(self, monkeypatch):
        runner = _make_runner()
        monkeypatch.setattr(vault_module, "resolve", MagicMock(return_value=None))

        assert runner._is_user_authorized(_source(user_id="999999999")) is False


class TestVaultUnreachable:
    """Case 3: vault raises -- fall back to the pre-existing file-registry
    check, unchanged, so an infra blip doesn't lock out real employees."""

    def test_falls_back_to_file_registry_on_vault_error(self, monkeypatch):
        runner = _make_runner()
        monkeypatch.setattr(
            vault_module, "resolve", MagicMock(side_effect=RuntimeError("vault socket unreachable"))
        )
        find_mock = MagicMock(return_value=("testuser@example.com", {"permissions": {}}))
        monkeypatch.setattr(registry_module, "find_user_by_identity", find_mock)

        assert runner._is_user_authorized(_source()) is True
        find_mock.assert_called_once_with("telegram", "1234567890")

    def test_file_registry_app_access_toggle_still_honored_on_outage(self, monkeypatch):
        runner = _make_runner()
        monkeypatch.setattr(vault_module, "resolve", MagicMock(side_effect=RuntimeError("down")))
        monkeypatch.setattr(
            registry_module,
            "find_user_by_identity",
            MagicMock(
                return_value=("testuser@example.com", {"permissions": {"apps": {"telegram": False}}})
            ),
        )

        assert runner._is_user_authorized(_source()) is False

    def test_falls_through_to_allowlist_when_vault_down_and_not_in_file(self, monkeypatch):
        runner = _make_runner()
        monkeypatch.setattr(vault_module, "resolve", MagicMock(side_effect=RuntimeError("down")))
        monkeypatch.setattr(
            registry_module, "find_user_by_identity", MagicMock(return_value=(None, None))
        )
        monkeypatch.setenv("TELEGRAM_ALLOWED_USERS", "1234567890")

        assert runner._is_user_authorized(_source()) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
