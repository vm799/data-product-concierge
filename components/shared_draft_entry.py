"""
Shared draft entry component for Data Product Concierge.

Renders a role-scoped form when a colleague arrives via a shared URL.
The colleague sees only the fields relevant to their role — no full form.
On submit, their answers are written back to the shared draft in Postgres.
"""

import streamlit as st
from typing import Optional
from models.data_product import DataProductSpec
from core.async_utils import run_async as _run
from core.field_registry import (
    COLLEAGUE_ROLES,
    VALID_ROLES,
    get_field_meta,
    FIELD_STATUS_ANSWERED,
    FIELD_STATUS_SKIPPED,
)

# Fields that use boolean (Yes/No) widget
_BOOL_FIELDS = {"pii_flag", "data_licensing_flag", "data_sovereignty_flag"}

# Fields that use date_input widget
_DATE_FIELDS = {"expected_release_date", "data_history_from"}

# Fields that use text_area (list/long text) widget
_LIST_FIELDS = {
    "business_terms",
    "target_systems",
    "critical_data_elements",
    "data_subject_areas",
}


# ============================================================================
# WIDGET HELPER
# ============================================================================


def _render_field_widget(field_name: str, meta: dict, current_value, key: str):
    """
    Render the appropriate Streamlit widget for a given field.

    Returns the raw widget value (not yet assigned to spec).
    """
    if field_name in _BOOL_FIELDS:
        # Determine current selection index
        options = ["Yes", "No"]
        if isinstance(current_value, bool):
            default_idx = 0 if current_value else 1
        else:
            default_idx = 0
        return st.radio(
            label="",
            options=options,
            index=default_idx,
            horizontal=True,
            key=key,
            label_visibility="collapsed",
        )

    if field_name in _DATE_FIELDS:
        import datetime as _dt
        default_date = None
        if isinstance(current_value, (_dt.date,)):
            default_date = current_value
        return st.date_input(
            label="",
            value=default_date,
            key=key,
            label_visibility="collapsed",
        )

    if field_name in _LIST_FIELDS:
        # Coerce stored list back to newline-delimited string for editing
        if isinstance(current_value, list):
            default_text = "\n".join(str(v) for v in current_value)
        elif isinstance(current_value, str):
            default_text = current_value
        else:
            default_text = ""
        return st.text_area(
            label="",
            value=default_text,
            placeholder="One item per line",
            height=130,
            key=key,
            label_visibility="collapsed",
        )

    # Default: single-line text input
    default_str = str(current_value) if current_value is not None else ""
    return st.text_input(
        label="",
        value=default_str,
        key=key,
        label_visibility="collapsed",
    )


# ============================================================================
# COMPLETION SCREEN
# ============================================================================


def _save_back_to_draft(spec, field_status, fields_for_role, draft_id, role):
    """Write the colleague's answers back to the shared draft in Postgres."""
    try:
        from models.draft_manager import DraftManager
        import os

        dm = DraftManager()
        if not dm.is_available:
            st.error(
                "Database not available — cannot save. "
                "Please copy your answers and send them to the spec owner."
            )
            return

        # Load the existing draft to merge
        existing = _run(dm.load(draft_id))
        if existing is None:
            st.error("Draft not found. It may have been deleted.")
            return

        # Merge: update spec_dict with answered fields
        merged_spec_dict = existing.spec_dict.copy()
        for field_name in fields_for_role:
            val = getattr(spec, field_name, None)
            if val is not None and field_status.get(field_name) == FIELD_STATUS_ANSWERED:
                if hasattr(val, "isoformat"):
                    merged_spec_dict[field_name] = val.isoformat()
                elif isinstance(val, list):
                    merged_spec_dict[field_name] = val
                elif isinstance(val, bool):
                    merged_spec_dict[field_name] = val
                else:
                    merged_spec_dict[field_name] = str(val) if val else None

        # Merge field_status into existing ui_state
        existing_ui = existing.ui_state or {}
        existing_field_status = existing_ui.get("gf_field_status") or {}
        for field_name, status in field_status.items():
            existing_field_status[field_name] = status
        existing_ui["gf_field_status"] = existing_field_status

        user_id = (
            os.getenv("USER_EMAIL")
            or os.getenv("USER_DISPLAY_NAME")
            or f"colleague:{role}"
        )

        _run(
            dm.save(
                draft_id=draft_id,
                user_id=existing.user_id,  # preserve original owner
                display_name=existing.display_name,
                spec_dict=merged_spec_dict,
                ui_state=existing_ui,
                step=existing.step,
                chapter=existing.chapter,
                path=existing.path,
                owner_role=existing.owner_role,
            )
        )

        # Log the contribution
        answered_count = len(
            [f for f in fields_for_role if field_status.get(f) == FIELD_STATUS_ANSWERED]
        )
        _run(
            dm.log_action(
                draft_id=draft_id,
                action="colleague_section_submitted",
                user_id=user_id,
                role=role,
                field_name=f"{answered_count}_fields",
            )
        )

        st.session_state["shared_submission_complete"] = True

    except Exception as e:
        st.error(f"Could not save: {str(e)}")


def _render_completion_screen(
    spec, role, role_label, draft_id, field_status, fields_for_role
):
    """Show confirmation and write answers back to Postgres."""
    answered_count = sum(
        1 for f in fields_for_role if field_status.get(f) == FIELD_STATUS_ANSWERED
    )

    st.html(
        f'<div style="text-align:center;padding:2rem;background:rgba(0,196,140,0.08);'
        f'border:1px solid rgba(0,196,140,0.25);border-radius:12px;margin-bottom:1.5rem;">'
        f'<div style="font-size:2rem;margin-bottom:.5rem;">✓</div>'
        f'<div style="font-size:1.1rem;font-weight:700;color:#0D1B2A;margin-bottom:.4rem;">'
        f"{role_label} section complete</div>"
        f'<div style="font-size:.9rem;color:#5B6A7E;">'
        f"{answered_count} of {len(fields_for_role)} fields answered</div>"
        f"</div>"
    )

    # Field summary — answered fields only
    answered_fields = [
        f for f in fields_for_role if field_status.get(f) == FIELD_STATUS_ANSWERED
    ]
    if answered_fields:
        st.html(
            '<div style="font-size:.85rem;font-weight:600;color:#5B6A7E;'
            'text-transform:uppercase;letter-spacing:.06em;margin-bottom:.6rem;">'
            "Your answers</div>"
        )
        for field_name in answered_fields:
            meta = get_field_meta(field_name)
            label = meta.get("label", field_name.replace("_", " ").title())
            val = getattr(spec, field_name, None)

            # Format value for display
            if isinstance(val, list):
                display_val = ", ".join(str(v) for v in val) if val else "—"
            elif hasattr(val, "isoformat"):
                display_val = val.isoformat()
            elif isinstance(val, bool):
                display_val = "Yes" if val else "No"
            elif val:
                display_val = str(val)
            else:
                display_val = "—"

            st.html(
                f'<div style="background:#F7F9FB;border:1px solid #E4EAF0;border-radius:8px;'
                f'padding:10px 14px;margin-bottom:.5rem;">'
                f'<div style="font-size:.8rem;font-weight:600;color:#5B6A7E;margin-bottom:2px;">'
                f"{label}</div>"
                f'<div style="font-size:.9rem;color:#0D1B2A;">{display_val}</div>'
                f"</div>"
            )

    # Submit button
    already_submitted = st.session_state.get("shared_submission_complete", False)

    if already_submitted:
        st.success("Your answers have been saved. The spec owner will be notified.")
    else:
        if st.button(
            "Submit my answers",
            type="primary",
            use_container_width=True,
            key="shared_submit_btn",
        ):
            _save_back_to_draft(spec, field_status, fields_for_role, draft_id, role)
            if st.session_state.get("shared_submission_complete"):
                st.success(
                    "Your answers have been saved. The spec owner will be notified."
                )
                try:
                    st.query_params.clear()
                except Exception:
                    pass
                st.rerun()


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================


def render_shared_draft_entry(
    spec: DataProductSpec,
    role: str,
    product_name: str,
    draft_id: str,
) -> None:
    """
    Render the role-scoped form for a colleague filling their section.

    Args:
        spec: Current DataProductSpec loaded from the shared draft
        role: "tech" | "owner" | "steward" | "compliance"
        product_name: Display name of the data product
        draft_id: The shared draft ID to write answers back to
    """
    # 1. Normalise role
    if role not in VALID_ROLES:
        role = "tech"

    # 2. Resolve role metadata
    role_meta = COLLEAGUE_ROLES[role]
    icon = role_meta.get("icon", "📋")
    role_label = role_meta.get("label", role.title())
    description = role_meta.get("description", "")
    fields_for_role = role_meta["fields"]

    # 2. Show welcome header
    st.html(
        f'<div style="background:rgba(0,107,115,0.06);border:1px solid rgba(0,107,115,0.2);'
        f"border-radius:12px;padding:20px 24px;margin-bottom:1.5rem;\">"
        f'<div style="font-size:1.1rem;font-weight:700;color:#0D1B2A;margin-bottom:6px;">'
        f"{icon} {role_label} — {product_name}</div>"
        f'<div style="font-size:.9rem;color:#5B6A7E;line-height:1.55;">{description}</div>'
        f"</div>"
    )

    # 3. Track field position in session state
    if "shared_field_idx" not in st.session_state:
        st.session_state["shared_field_idx"] = 0
    if "shared_field_status" not in st.session_state:
        st.session_state["shared_field_status"] = {}
    if "shared_spec" not in st.session_state:
        st.session_state["shared_spec"] = spec

    field_idx = st.session_state["shared_field_idx"]
    field_status = st.session_state["shared_field_status"]
    working_spec = st.session_state["shared_spec"]
    total = len(fields_for_role)

    # 4. All fields done — show completion screen
    if field_idx >= total:
        _render_completion_screen(
            working_spec, role, role_label, draft_id, field_status, fields_for_role
        )
        return

    # 5. Render current field card
    field_name = fields_for_role[field_idx]
    meta = get_field_meta(field_name)
    label = meta.get("label", field_name.replace("_", " ").title())
    question = meta.get("question", f"Please provide the {label}.")
    current_value = getattr(working_spec, field_name, None)

    # Progress header
    progress_pct = field_idx / total
    st.html(
        f'<div style="display:flex;align-items:center;justify-content:space-between;'
        f'margin-bottom:.5rem;">'
        f'<div style="font-size:.8rem;color:#5B6A7E;font-weight:500;">'
        f"Field {field_idx + 1} of {total}</div>"
        f'<div style="font-size:.8rem;color:#5B6A7E;">'
        f'{role_label}</div>'
        f"</div>"
        f'<div style="height:4px;background:#E4EAF0;border-radius:2px;margin-bottom:1.4rem;">'
        f'<div style="height:4px;background:#006B73;border-radius:2px;'
        f'width:{progress_pct * 100:.1f}%;transition:width .3s ease;"></div>'
        f"</div>"
    )

    # Field label and question
    st.html(
        f'<div style="font-size:1.1rem;font-weight:700;color:#0D1B2A;margin-bottom:.35rem;">'
        f"{label}</div>"
        f'<div style="font-size:.88rem;color:#5B6A7E;margin-bottom:.9rem;line-height:1.55;">'
        f"{question}</div>"
    )

    # Widget
    widget_key = f"shared_widget_{field_name}_{field_idx}"
    raw_value = _render_field_widget(field_name, meta, current_value, widget_key)

    st.write("")  # spacer

    # Navigation buttons: [Back | Skip | Continue]
    col_back, col_skip, col_cont = st.columns([1, 1, 2])

    with col_back:
        back_disabled = field_idx == 0
        if st.button(
            "← Back",
            key=f"shared_back_{field_idx}",
            disabled=back_disabled,
            use_container_width=True,
        ):
            st.session_state["shared_field_idx"] = max(0, field_idx - 1)
            st.rerun()

    with col_skip:
        if st.button(
            "Skip",
            key=f"shared_skip_{field_idx}",
            use_container_width=True,
        ):
            field_status[field_name] = FIELD_STATUS_SKIPPED
            st.session_state["shared_field_status"] = field_status
            st.session_state["shared_field_idx"] = field_idx + 1
            st.rerun()

    with col_cont:
        if st.button(
            "Continue →",
            key=f"shared_continue_{field_idx}",
            type="primary",
            use_container_width=True,
        ):
            # Coerce raw_value to the right type and assign to spec
            coerced = _coerce_value(field_name, raw_value)
            _validation_error = None
            try:
                setattr(working_spec, field_name, coerced)
            except Exception as exc:
                _validation_error = str(exc)

            if _validation_error:
                st.error(f"Invalid value: {_validation_error}")
            else:
                field_status[field_name] = FIELD_STATUS_ANSWERED
                st.session_state["shared_spec"] = working_spec
                st.session_state["shared_field_status"] = field_status
                st.session_state["shared_field_idx"] = field_idx + 1
                st.rerun()


# ============================================================================
# VALUE COERCION HELPER
# ============================================================================


def _coerce_value(field_name: str, raw_value):
    """
    Coerce the raw widget return value to the type expected by DataProductSpec.

    - Boolean fields: "Yes" → True, "No" → False
    - List fields: newline-delimited string → list[str]
    - Date fields: already a date object from st.date_input
    - Default: return as-is (str)
    """
    if field_name in _BOOL_FIELDS:
        return raw_value == "Yes"

    if field_name in _LIST_FIELDS:
        if isinstance(raw_value, str):
            lines = [line.strip() for line in raw_value.splitlines() if line.strip()]
            return lines
        return raw_value if isinstance(raw_value, list) else []

    # Date fields are already date objects from st.date_input — pass through
    if field_name in _DATE_FIELDS:
        return raw_value

    return raw_value
