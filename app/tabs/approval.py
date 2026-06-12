from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import sys

import pandas as pd
import streamlit as st

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.i18n import t
from src.approval_workflow import (
    accept_price_changes,
    alabel,
    approval_signature,
    audit_log_bytes,
    build_approval_table,
    decision_log_rows,
    disabled_columns,
    editor_column_config,
    from_editor_display,
    render_approval_cards,
    reset_log_row,
    simulate_push,
    styled_preview,
    table_decision_events,
    to_editor_display,
    undo_last_push,
    update_manual_flags,
    card_label,
)
from src.audit_log_store import append_audit_log, load_audit_log, load_approval_draft, save_approval_draft
from src.channel_pricing_ui import render_channel_price_preview
from src.security_controls import default_actor_from_headers, strict_actor_enabled, trusted_remote_actor


_ACTOR_INPUT_LABELS: dict[str, str] = {
    "zh": "操作人（记录到审计日志）",
    "en": "Operator (recorded in audit log)",
    "de": "Bearbeiter (im Audit-Log erfasst)",
    "fr": "Opérateur (enregistré dans le journal d'audit)",
}

_BOUNDS_BLOCKED: dict[str, tuple[str, str]] = {
    "zh": ("价格边界拦截", "条记录的批准价超出房型价格上下限，未推送。"),
    "en": ("Bounds violation blocked", "rows blocked — approved price outside configured floor/ceiling."),
    "de": ("Preisgrenze blockiert", "Zeilen blockiert — genehmigter Preis außerhalb konfigurierter Grenzen."),
    "fr": ("Limite de prix dépassée", "lignes bloquées — prix validé hors des limites configurées."),
}

_UNDO_LABELS: dict[str, tuple[str, str, str]] = {
    "zh": ("撤销推送", "已撤销", "没有可撤销的推送记录。"),
    "en": ("Undo Push", "Undone", "No pushed rows to undo."),
    "de": ("Veröffentlichung zurücksetzen", "Rückgängig gemacht", "Keine veröffentlichten Zeilen zum Zurücksetzen."),
    "fr": ("Annuler la publication", "Annulé", "Aucune ligne publiée à annuler."),
}

_STRICT_ACTOR_ERRORS: dict[str, str] = {
    "zh": "已启用 HOTEL_STRICT_ACTOR=1，但没有可信的 X-Remote-User。请同时启用 HOTEL_TRUST_REMOTE_USER=1，并确保反向代理先清除客户端伪造头再注入认证用户名。",
    "en": "HOTEL_STRICT_ACTOR=1 is enabled, but no trusted X-Remote-User is available. Enable HOTEL_TRUST_REMOTE_USER=1 behind a proxy that strips client-supplied headers before injecting the authenticated user.",
    "de": "HOTEL_STRICT_ACTOR=1 ist aktiviert, aber kein vertrauenswürdiger X-Remote-User ist verfügbar. Aktivieren Sie HOTEL_TRUST_REMOTE_USER=1 hinter einem Proxy, der clientseitige Header entfernt und danach den authentifizierten Benutzer setzt.",
    "fr": "HOTEL_STRICT_ACTOR=1 est activé, mais aucun X-Remote-User fiable n'est disponible. Activez HOTEL_TRUST_REMOTE_USER=1 derrière un proxy qui supprime les en-têtes client avant d'injecter l'utilisateur authentifié.",
}


def _context_headers() -> dict[str, object]:
    try:
        return dict(st.context.headers)
    except Exception:
        return {}


def _default_actor() -> str:
    return default_actor_from_headers(_context_headers())


def _trusted_actor() -> str | None:
    return trusted_remote_actor(_context_headers())


def _actor_for_audit(lang: str) -> str:
    trusted_actor: str | None = _trusted_actor()
    if strict_actor_enabled() and trusted_actor is None:
        st.error(_STRICT_ACTOR_ERRORS.get(lang, _STRICT_ACTOR_ERRORS["en"]))
        st.stop()

    header_actor: str = trusted_actor or "demo_user"
    actor_value: str = st.text_input(
        _ACTOR_INPUT_LABELS.get(lang, _ACTOR_INPUT_LABELS["en"]),
        value=st.session_state.get("audit_actor", header_actor),
        key="audit_actor",
        disabled=trusted_actor is not None,
    )
    return trusted_actor or (actor_value or "").strip() or header_actor


def _approval_draft_key(signature: str, actor: str) -> str:
    actor_hash = sha256(actor.encode("utf-8")).hexdigest()[:16]
    return f"{signature}:{actor_hash}"


def render_price_approval_publishing(
    recommendations: pd.DataFrame,
    lang: str,
    audit_log_dir: Path,
) -> None:
    st.subheader(alabel("tab", lang))
    st.write(alabel("intro", lang))

    if "approval_log" not in st.session_state:
        st.session_state.approval_log = load_audit_log(audit_log_dir)

    actor = _actor_for_audit(lang)

    signature = approval_signature(recommendations)
    draft_key = _approval_draft_key(signature, actor)
    if st.session_state.get("approval_signature") != draft_key or "approval_table" not in st.session_state:
        draft = load_approval_draft(draft_key, audit_log_dir)
        st.session_state.approval_table = draft if draft is not None else build_approval_table(recommendations)
        st.session_state.approval_signature = draft_key

    view_card = card_label("view_card", lang)
    view_table = card_label("view_table", lang)
    view_mode = st.radio(
        card_label("view_label", lang),
        options=[view_card, view_table],
        horizontal=True,
        label_visibility="collapsed",
        key="approval_view_mode",
        index=0,
    )

    if view_mode == view_card:
        render_approval_cards(recommendations, lang, actor=actor, audit_dir=audit_log_dir)
    else:
        c1, c2 = st.columns([0.35, 0.65])
        with c1:
            if st.button(alabel("bulk_accept", lang), width="stretch"):
                st.session_state.approval_table = accept_price_changes(st.session_state.approval_table)
                changed = st.session_state.approval_table[st.session_state.approval_table["action"] != "hold"]
                st.session_state.approval_log = append_audit_log(
                    decision_log_rows(changed, "bulk_accept", actor), audit_log_dir
                )
        with c2:
            if st.button(alabel("reset", lang), width="stretch"):
                row_count = len(st.session_state.approval_table)
                st.session_state.approval_table = build_approval_table(recommendations)
                st.session_state.approval_log = append_audit_log(
                    reset_log_row(actor, row_count), audit_log_dir
                )

        st.caption(alabel("editor_caption", lang))
        editor_display = to_editor_display(st.session_state.approval_table, lang)
        edited_display = st.data_editor(
            editor_display,
            width="stretch",
            hide_index=True,
            column_config=editor_column_config(lang),
            disabled=disabled_columns(lang),
            key=f"approval_editor_{signature}_{lang}",
        )

        edited_internal = from_editor_display(edited_display, lang)
        previous_table = st.session_state.approval_table.copy()
        approval_table = st.session_state.approval_table.copy()
        for column in ["selected", "approved_price", "approval_status", "review_comment"]:
            approval_table[column] = edited_internal[column].values
        st.session_state.approval_table = update_manual_flags(approval_table)
        for event, rows in table_decision_events(previous_table, st.session_state.approval_table):
            st.session_state.approval_log = append_audit_log(
                decision_log_rows(rows, event, actor), audit_log_dir
            )

    st.caption(alabel("preview_caption", lang))
    st.dataframe(styled_preview(st.session_state.approval_table, lang), width="stretch", hide_index=True)
    render_channel_price_preview(st.session_state.approval_table, lang)

    push_col, undo_col = st.columns([0.7, 0.3])
    _bl = _BOUNDS_BLOCKED.get(lang, _BOUNDS_BLOCKED["en"])
    _ul = _UNDO_LABELS.get(lang, _UNDO_LABELS["en"])

    with push_col:
        if st.button(alabel("simulate_push", lang), type="primary", width="stretch"):
            pushed_table, log_rows, bounds_violations = simulate_push(
                st.session_state.approval_table, lang, actor=actor
            )
            st.session_state.approval_table = pushed_table
            if bounds_violations > 0:
                st.warning(f"{_bl[0]}: {bounds_violations} {_bl[1]}")
            if log_rows.empty:
                st.info(alabel("no_rows", lang))
            else:
                st.session_state.approval_log = append_audit_log(log_rows, audit_log_dir)
                st.success(f"{alabel('push_success', lang)}: {len(log_rows[log_rows['event'] == 'push'])}")
    with undo_col:
        if st.button(_ul[0], width="stretch"):
            undone_table, undone_count = undo_last_push(
                st.session_state.approval_table, actor, audit_log_dir
            )
            st.session_state.approval_table = undone_table
            if undone_count:
                st.session_state.approval_log = load_audit_log(audit_log_dir)
                st.success(f"{_ul[1]}: {undone_count}")
            else:
                st.info(_ul[2])

    if st.session_state.approval_log.empty:
        st.info(alabel("audit_empty", lang))
    else:
        audit_log_column_config = {
            "current_price": st.column_config.NumberColumn(t("column_current_price", lang), format="%.2f"),
            "recommended_price": st.column_config.NumberColumn(t("column_recommended_price", lang), format="%.2f"),
            "approved_price": st.column_config.NumberColumn(t("column_approved_price", lang), format="%.0f"),
        }
        st.dataframe(
            st.session_state.approval_log,
            width="stretch",
            hide_index=True,
            column_config=audit_log_column_config,
        )
        st.download_button(
            alabel("download_audit", lang),
            data=audit_log_bytes(st.session_state.approval_log),
            file_name="price_approval_publishing_log.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    table_hash = int(pd.util.hash_pandas_object(st.session_state.approval_table).sum())
    if (
        st.session_state.get("_draft_hash") != table_hash
        or st.session_state.get("_draft_signature") != draft_key
    ):
        save_approval_draft(st.session_state.approval_table, draft_key, audit_log_dir)
        st.session_state._draft_hash = table_hash
        st.session_state._draft_signature = draft_key
