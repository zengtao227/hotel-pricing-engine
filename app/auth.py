from __future__ import annotations

import os
import secrets
import threading
import time
from collections.abc import Mapping

import streamlit as st

from src.security_controls import client_key_from_request, env_flag, is_loopback_ip


_AUTH_FAILURES: dict[str, tuple[int, float]] = {}
_AUTH_LOCK = threading.Lock()
_AUTH_MAX_ATTEMPTS = 5
_AUTH_LOCKOUT_SECONDS = 60.0


def unauthenticated_access_allowed(
    ip_address: object | None,
    environ: Mapping[str, str] | None = None,
) -> bool:
    if env_flag("HOTEL_ALLOW_UNAUTHENTICATED", environ):
        return True
    return env_flag("HOTEL_ALLOW_LOCAL_UNAUTHENTICATED", environ) and is_loopback_ip(ip_address)


def _request_ip() -> object | None:
    try:
        return st.context.ip_address
    except Exception:
        return None


def _request_headers() -> dict[str, object]:
    try:
        return dict(st.context.headers)
    except Exception:
        return {}


def client_key() -> str:
    return client_key_from_request(_request_ip(), _request_headers())


def auth_locked_remaining(key: str) -> int:
    with _AUTH_LOCK:
        failures, locked_until = _AUTH_FAILURES.get(key, (0, 0.0))
        remaining = locked_until - time.time()
    return max(0, int(remaining) + 1) if remaining > 0 else 0


def record_auth_failure(key: str) -> int:
    """Register one failed attempt; returns attempts left before lockout."""
    with _AUTH_LOCK:
        failures, _ = _AUTH_FAILURES.get(key, (0, 0.0))
        failures += 1
        locked_until = time.time() + _AUTH_LOCKOUT_SECONDS if failures >= _AUTH_MAX_ATTEMPTS else 0.0
        if failures >= _AUTH_MAX_ATTEMPTS:
            failures = 0
        _AUTH_FAILURES[key] = (failures, locked_until)
    return _AUTH_MAX_ATTEMPTS - failures if not locked_until else 0


def clear_auth_failures(key: str) -> None:
    with _AUTH_LOCK:
        _AUTH_FAILURES.pop(key, None)


def require_auth() -> None:
    """Password gate controlled by HOTEL_APP_PASSWORD.

    Public requests fail closed unless HOTEL_APP_PASSWORD is set or
    HOTEL_ALLOW_UNAUTHENTICATED=1 is explicitly used. Local development without
    a password also requires HOTEL_ALLOW_LOCAL_UNAUTHENTICATED=1 because a
    reverse proxy can make public requests appear as 127.0.0.1 to Streamlit.
    """
    password: str = os.environ.get("HOTEL_APP_PASSWORD", "")
    if not password:
        if unauthenticated_access_allowed(_request_ip()):
            return
        st.error("HOTEL_APP_PASSWORD is required for access.")
        st.stop()
    if st.session_state.get("_authenticated"):
        return

    _, center, _ = st.columns([1, 1.2, 1])
    with center:
        st.markdown(
            '<div style="text-align:center; padding: 2.5rem 0 0.5rem;">'
            '<div style="font-size:2.6rem;">🏨</div>'
            '<h2 style="margin:0.2rem 0 0.1rem;">Hotel Pricing Engine</h2>'
            '<p style="color:#64748B; margin:0 0 1rem;">请输入访问密码 · Please enter the access password</p>'
            "</div>",
            unsafe_allow_html=True,
        )
        current_client: str = client_key()
        wait: int = auth_locked_remaining(current_client)
        if wait:
            st.error(f"Too many failed attempts. Try again in {wait}s.")
            st.stop()

        with st.form("login_form"):
            entered: str = st.text_input("Password", type="password", key="_auth_input")
            submitted: bool = st.form_submit_button("Login", type="primary", width="stretch")
        if submitted:
            if secrets.compare_digest(entered.encode(), password.encode()):
                clear_auth_failures(current_client)
                st.session_state._authenticated = True
                st.rerun()
            attempts_left: int = record_auth_failure(current_client)
            if attempts_left:
                st.error(f"Incorrect password. {attempts_left} attempt(s) remaining before lockout.")
            else:
                st.error(f"Too many failed attempts. Locked for {int(_AUTH_LOCKOUT_SECONDS)} seconds.")
    st.stop()
