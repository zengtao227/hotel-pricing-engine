from __future__ import annotations

import pytest

import app.tabs.approval as approval


class _StopCalled(Exception):
    pass


class _FakeSt:
    def __init__(self) -> None:
        self.session_state: dict[str, str] = {}
        self.errors: list[str] = []
        self.text_inputs: list[dict[str, object]] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def stop(self) -> None:
        raise _StopCalled

    def text_input(self, label: str, value: str, key: str, disabled: bool) -> str:
        self.text_inputs.append({"label": label, "value": value, "key": key, "disabled": disabled})
        return "manual_actor"


def test_actor_for_audit_fails_closed_when_strict_actor_has_no_trusted_header(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_st = _FakeSt()
    monkeypatch.setattr(approval, "st", fake_st)
    monkeypatch.setattr(approval, "_trusted_actor", lambda: None)
    monkeypatch.setattr(approval, "strict_actor_enabled", lambda: True)

    with pytest.raises(_StopCalled):
        approval._actor_for_audit("en")

    assert fake_st.errors
    assert fake_st.text_inputs == []


def test_actor_for_audit_allows_manual_actor_when_not_strict(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_st = _FakeSt()
    monkeypatch.setattr(approval, "st", fake_st)
    monkeypatch.setattr(approval, "_trusted_actor", lambda: None)
    monkeypatch.setattr(approval, "strict_actor_enabled", lambda: False)

    assert approval._actor_for_audit("en") == "manual_actor"
    assert fake_st.text_inputs[0]["disabled"] is False


def test_actor_for_audit_uses_trusted_actor_and_disables_input(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_st = _FakeSt()
    monkeypatch.setattr(approval, "st", fake_st)
    monkeypatch.setattr(approval, "_trusted_actor", lambda: "alice")
    monkeypatch.setattr(approval, "strict_actor_enabled", lambda: True)

    assert approval._actor_for_audit("en") == "alice"
    assert fake_st.text_inputs[0]["disabled"] is True
