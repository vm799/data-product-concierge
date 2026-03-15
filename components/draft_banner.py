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
            "path_c": "Building — chat",
            "handoff": "Ready to submit",
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
