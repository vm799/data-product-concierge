"""
Draft banner component for Data Product Concierge.

Shows recent drafts on the search page and provides a resume flow.
"""

from typing import List, Optional
import streamlit as st


def render_recent_drafts(drafts: list, on_resume_key: str = "resume_draft_id") -> Optional[str]:
    """
    Render a 'Recent drafts' panel on the search page.

    Args:
        drafts: List of DraftRecord objects (from DraftManager.list_user_drafts)
        on_resume_key: session_state key to write the chosen draft_id to

    Returns:
        draft_id to resume, or None if no selection made.
    """
    if not drafts:
        return None

    st.markdown(
        '<div style="margin-top:2rem;">'
        '<p style="color:var(--text-secondary);font-size:.85rem;font-weight:600;'
        'text-transform:uppercase;letter-spacing:.06em;margin-bottom:.75rem;">📂 Resume a draft</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    selected_id = None
    for draft in drafts[:5]:
        name = draft.display_name or "Untitled draft"
        step_label = {
            "path_b": "Remixing — Ch " + str(draft.chapter),
            "path_c": "Building",
            "handoff": "Ready to submit",
            "shared_form": "Colleague filling",
        }.get(draft.step, draft.step.replace("_", " ").title())

        completion_pct = ""
        try:
            from models.data_product import DataProductSpec
            spec = DataProductSpec(**draft.spec_dict)
            completion_pct = f" · {spec.completion_percentage():.0f}% complete"
        except Exception:
            pass

        updated = draft.updated_at.strftime("%d %b %H:%M") if draft.updated_at else ""

        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(
                f'<div style="background:white;border:1px solid var(--border);border-radius:10px;'
                f'padding:.6rem 1rem;margin-bottom:.4rem;">'
                f'<div style="font-weight:600;color:var(--text-primary);font-size:.9rem;">{name}</div>'
                f'<div style="color:var(--text-muted);font-size:.78rem;margin-top:.2rem;">'
                f'{step_label}{completion_pct} · saved {updated}'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with col2:
            if st.button("Resume →", key=f"resume_{draft.draft_id}", use_container_width=True, type="primary"):
                selected_id = draft.draft_id

    return selected_id


def render_autosave_indicator(last_saved_ts: Optional[str] = None) -> None:
    """
    Render a small 'auto-saved' indicator in the sidebar.

    Args:
        last_saved_ts: Human-readable timestamp string, or None if not yet saved.
    """
    if last_saved_ts:
        st.markdown(
            f'<p style="color:#4DD9C0;font-size:.7rem;margin:.2rem 0;">💾 Saved {last_saved_ts}</p>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<p style="color:rgba(255,255,255,.3);font-size:.7rem;margin:.2rem 0;">💾 Auto-save enabled</p>',
            unsafe_allow_html=True,
        )


def render_share_panel(
    draft_id: Optional[str],
    field_status: Optional[dict] = None,
    spec_name: str = "",
) -> None:
    """
    Render a 'Share with team' expandable panel.

    Shows per-role shareable links with copy buttons.
    Indicates which roles have already contributed (green chip).

    Args:
        draft_id: The current draft ID (from session_state.draft_id)
        field_status: gf_field_status dict (to show contribution status)
        spec_name: Product name for the URL label
    """
    if not draft_id:
        st.caption("Save your draft first to get a shareable link.")
        return

    # Role definitions
    roles = [
        {
            "key": "tech",
            "label": "Data Engineer",
            "icon": "⚡",
            "description": "Target systems, DPRO, Critical Data Elements",
            "fields": ["target_systems", "target_dpro", "critical_data_elements"],
        },
        {
            "key": "owner",
            "label": "Data Owner",
            "icon": "🔒",
            "description": "Access procedure, licensing, governing body",
            "fields": ["access_procedure", "data_licensing_flag", "governing_body"],
        },
        {
            "key": "steward",
            "label": "Data Steward",
            "icon": "👥",
            "description": "Domain owner, custodian, release date",
            "fields": ["data_domain_owner_email", "data_custodian_email", "expected_release_date"],
        },
        {
            "key": "compliance",
            "label": "Compliance Officer",
            "icon": "📊",
            "description": "Business terms, latency, history, publishing",
            "fields": ["business_terms", "data_latency", "data_history_from"],
        },
    ]

    # Compute invite token (async) — try to get/create from DraftManager
    invite_token = draft_id  # fallback: use draft_id directly as token
    try:
        from models.draft_manager import DraftManager
        import asyncio

        def _run(coro):
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            return loop.run_until_complete(coro)

        dm = DraftManager()
        if dm.is_available:
            tok = _run(dm.create_invite_token(draft_id))
            if tok:
                invite_token = tok
    except Exception:
        pass

    base_url = __import__("os").getenv("APP_BASE_URL", "http://localhost:8501")
    FIELD_STATUS_ANSWERED = "answered"

    for role in roles:
        role_fields_answered = sum(
            1 for f in role["fields"]
            if (field_status or {}).get(f) == FIELD_STATUS_ANSWERED
        )
        total_role_fields = len(role["fields"])
        is_complete = role_fields_answered == total_role_fields

        # Status chip
        if is_complete:
            chip = (
                '<span style="background:rgba(0,196,140,0.12);color:#006B73;'
                'border:1px solid rgba(0,196,140,0.3);border-radius:100px;'
                'padding:1px 8px;font-size:.68rem;font-weight:700;">✓ Done</span>'
            )
        elif role_fields_answered > 0:
            chip = (
                f'<span style="background:rgba(245,166,35,0.12);color:#a66d00;'
                f'border:1px solid rgba(245,166,35,0.3);border-radius:100px;'
                f'padding:1px 8px;font-size:.68rem;font-weight:700;">'
                f'{role_fields_answered}/{total_role_fields}</span>'
            )
        else:
            chip = (
                '<span style="background:rgba(13,27,42,0.05);color:#8C9BAA;'
                'border:1px solid rgba(13,27,42,0.1);border-radius:100px;'
                'padding:1px 8px;font-size:.68rem;font-weight:600;">Not started</span>'
            )

        share_url = f"{base_url}?draft_id={invite_token}&role={role['key']}"

        st.markdown(
            f'<div style="display:flex;align-items:center;justify-content:space-between;'
            f'padding:8px 0;border-bottom:1px solid rgba(13,27,42,0.07);">'
            f'<div>'
            f'<span style="font-size:.82rem;font-weight:600;color:#0D1B2A;">'
            f'{role["icon"]} {role["label"]}</span> {chip}'
            f'<div style="font-size:.72rem;color:#8C9BAA;margin-top:2px;">{role["description"]}</div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        # Use st.code for the URL so it's easily copyable
        st.code(share_url, language=None)
