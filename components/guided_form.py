"""
Guided form component for Data Product Concierge.

Card-by-card guided form — the core experience of filling in a data product
spec one field at a time, with a live preview on the right.
"""

import json
import urllib.parse
from datetime import date, datetime

import streamlit as st

from models.data_product import DataProductSpec
from core.field_registry import (
    FIELD_REGISTRY,
    GUIDED_BUSINESS_REQUIRED,
    GUIDED_BUSINESS_OPTIONAL,
    GUIDED_TECH_FIELDS,
    GUIDED_AUTO_FIELDS,
    get_field_meta,
    FIELD_STATUS_ANSWERED,
    FIELD_STATUS_PENDING,
    FIELD_STATUS_SKIPPED,
    FIELD_STATUS_NOT_NEEDED,
    FIELD_STATUS_AUTO,
)
from components.styles import render_guidance


def _scroll_top() -> None:
    """Scroll the Streamlit main pane to the top."""
    st.components.v1.html(
        "<script>"
        "try{"
        "  var m=window.parent.document.querySelector('[data-testid=\"stMain\"] .main');"
        "  if(!m)m=window.parent.document.querySelector('.main');"
        "  if(m)m.scrollTo({top:0,behavior:'instant'});"
        "}catch(e){}"
        "</script>",
        height=0,
    )


# ---------------------------------------------------------------------------
# LIST FIELDS (textarea, split on newlines)
# ---------------------------------------------------------------------------
_LIST_FIELDS = {
    "consumer_teams",
    "tags",
    "regulatory_scope",
    "source_systems",
    "lineage_upstream",
    "lineage_downstream",
    "column_definitions",
    "related_reports",
}

# Fields that take an email text input
_EMAIL_FIELDS = {
    "data_owner_email",
    "data_steward_email",
    "certifying_officer_email",
    "incident_contact",
}

# Fields that always use text_area (even if not in _LIST_FIELDS)
_TEXTAREA_FIELDS = {
    "description",
    "business_purpose",
    "sample_query",
    "explanation",
}


# ---------------------------------------------------------------------------
# SESSION STATE INITIALISATION
# ---------------------------------------------------------------------------

def _init_session_state(spec: DataProductSpec) -> None:
    """Initialise guided form session state keys if not already set."""
    if "gf_tier" not in st.session_state:
        st.session_state["gf_tier"] = 1
        st.session_state["gf_field_idx"] = 0
        st.session_state["gf_field_status"] = {}
        st.session_state["gf_show_optional_prompt"] = False

    # Pre-populate answered status for fields already set on the spec (remix/intake seeding)
    field_status: dict = st.session_state["gf_field_status"]
    all_guided = GUIDED_BUSINESS_REQUIRED + GUIDED_BUSINESS_OPTIONAL
    for field_name in all_guided:
        if field_name in field_status:
            continue  # already tracked
        value = getattr(spec, field_name, None)
        if value is not None and value != "" and value != []:
            field_status[field_name] = FIELD_STATUS_ANSWERED

    st.session_state["gf_field_status"] = field_status


# ---------------------------------------------------------------------------
# WIDGET RENDERING
# ---------------------------------------------------------------------------

def _render_widget(field_name: str, meta: dict, current_value, valid_options: dict, widget_key: str):
    """
    Render the appropriate Streamlit input widget for a field.

    Returns the raw widget value (not yet processed for type conversion).
    """
    options_from_registry = meta.get("options", [])
    options_from_valid = valid_options.get(field_name, [])

    # Effective options: prefer valid_options override, else registry options
    effective_options = options_from_valid if options_from_valid else options_from_registry

    # --- PII flag — special radio ---
    if field_name == "pii_flag":
        radio_choices = ["Yes — contains PII", "No — no PII"]
        if current_value is True:
            default_idx = 0
        else:
            default_idx = 1
        return st.radio(
            "",
            radio_choices,
            index=default_idx,
            horizontal=True,
            key=widget_key,
        )

    # --- Selectbox fields ---
    if effective_options:
        current_str = str(current_value) if current_value is not None else None
        try:
            default_idx = effective_options.index(current_str) if current_str in effective_options else 0
        except ValueError:
            default_idx = 0
        return st.selectbox(
            "",
            effective_options,
            index=default_idx,
            key=widget_key,
        )

    # --- Date input ---
    if field_name == "last_certified_date":
        if isinstance(current_value, (date, datetime)):
            default_date = current_value if isinstance(current_value, date) else current_value.date()
        else:
            default_date = None
        return st.date_input(
            "",
            value=default_date,
            key=widget_key,
        )

    # --- Email text input ---
    if field_name in _EMAIL_FIELDS:
        return st.text_input(
            "",
            value=str(current_value) if current_value is not None else "",
            placeholder="name@company.com",
            key=widget_key,
        )

    # --- List fields (textarea, one item per line) ---
    if field_name in _LIST_FIELDS:
        if isinstance(current_value, list):
            default_text = "\n".join(str(v) for v in current_value)
        elif current_value is not None:
            default_text = str(current_value)
        else:
            default_text = ""
        return st.text_area(
            "",
            value=default_text,
            placeholder="One item per line",
            height=140,
            key=widget_key,
        )

    # --- Long text fields ---
    if field_name in _TEXTAREA_FIELDS:
        return st.text_area(
            "",
            value=str(current_value) if current_value is not None else "",
            height=120,
            key=widget_key,
        )

    # --- Default: text input ---
    return st.text_input(
        "",
        value=str(current_value) if current_value is not None else "",
        key=widget_key,
    )


# ---------------------------------------------------------------------------
# VALUE ASSIGNMENT
# ---------------------------------------------------------------------------

def _assign_value(spec: DataProductSpec, field_name: str, raw_value) -> DataProductSpec:
    """
    Assign widget raw_value to spec field with correct type conversion.

    Returns updated spec (copy via dict update).
    """
    spec_dict = spec.dict()

    if field_name == "pii_flag":
        spec_dict[field_name] = raw_value == "Yes — contains PII"

    elif field_name == "last_certified_date":
        spec_dict[field_name] = raw_value  # already a date object from st.date_input

    elif field_name in _LIST_FIELDS:
        if isinstance(raw_value, str):
            items = [line.strip() for line in raw_value.splitlines() if line.strip()]
            spec_dict[field_name] = items if items else None
        else:
            spec_dict[field_name] = raw_value

    else:
        # Plain string — store or None if empty
        str_val = str(raw_value).strip() if raw_value is not None else ""
        spec_dict[field_name] = str_val if str_val else None

    try:
        return DataProductSpec(**spec_dict)
    except Exception:
        # If validation fails (e.g. enum mismatch), return original spec unchanged
        return spec


# ---------------------------------------------------------------------------
# COLLEAGUE HANDOFF GENERATION
# ---------------------------------------------------------------------------

def _generate_colleague_handoff(spec: DataProductSpec, field_status: dict) -> dict:
    """
    Build the colleague handoff payload for forwarding tech fields to engineering.
    """
    pending_fields = [get_field_meta(f) | {"field_name": f} for f in GUIDED_TECH_FIELDS]
    skipped_fields = [
        f for f in (GUIDED_BUSINESS_REQUIRED + GUIDED_BUSINESS_OPTIONAL)
        if field_status.get(f) == FIELD_STATUS_SKIPPED
    ]

    product_name = spec.name or "Unnamed Data Product"

    # Compose mailto body
    body_lines = [
        f"Hi,",
        f"",
        f"I've completed the business specification for the data product below and need your help filling in the technical fields in Collibra.",
        f"",
        f"Data Product: {product_name}",
        f"",
        f"--- TECHNICAL FIELDS NEEDED ---",
        f"",
    ]
    for field_name in GUIDED_TECH_FIELDS:
        meta = get_field_meta(field_name)
        body_lines.append(f"Field: {meta.get('label', field_name)}")
        body_lines.append(f"Question: {meta.get('question', '')}")
        body_lines.append(f"Answer: [PLEASE COMPLETE]")
        body_lines.append(f"")

    if skipped_fields:
        body_lines.append("--- SKIPPED BUSINESS FIELDS (may also need your input) ---")
        body_lines.append("")
        for f in skipped_fields:
            meta = get_field_meta(f)
            body_lines.append(f"  - {meta.get('label', f)}")
        body_lines.append("")

    body_lines.append("The partial spec JSON is available via the Data Product Concierge tool.")
    body_lines.append("")
    body_lines.append("Thanks,")

    mailto_body = "\n".join(body_lines)

    subject = f"Data Product Spec — Tech Fields Needed: {product_name}"

    return {
        "spec_partial_json": spec.json(),
        "pending_fields": pending_fields,
        "mailto_subject": subject,
        "mailto_body": urllib.parse.quote(mailto_body),
        "skipped_fields": skipped_fields,
    }


# ---------------------------------------------------------------------------
# SPEC PREVIEW (right panel)
# ---------------------------------------------------------------------------

def _render_spec_preview(spec: DataProductSpec, field_status: dict, current_field: str) -> None:
    """
    Render the live spec preview in the right panel.
    Groups fields into labelled sections and colour-codes by status.
    """
    teal_d = "var(--teal-d, #006B73)"
    gold = "var(--gold, #F5A623)"
    text3 = "var(--text-3, #8C9BAA)"
    navy = "var(--navy, #0D1B2A)"

    def _status_color(field_name: str) -> str:
        status = field_status.get(field_name, FIELD_STATUS_PENDING)
        if field_name == current_field:
            return navy
        if status == FIELD_STATUS_ANSWERED:
            return teal_d
        if status == FIELD_STATUS_SKIPPED:
            return gold
        return text3

    def _field_value_str(field_name: str) -> str:
        val = getattr(spec, field_name, None)
        if val is None or val == "" or val == []:
            return "—"
        if isinstance(val, list):
            return ", ".join(str(v) for v in val) if val else "—"
        if isinstance(val, bool):
            return "Yes" if val else "No"
        if isinstance(val, (date, datetime)):
            return val.isoformat()
        text = str(val)
        return text[:60] + "…" if len(text) > 60 else text

    def _row(field_name: str, label: str) -> str:
        color = _status_color(field_name)
        val = _field_value_str(field_name)
        is_current = field_name == current_field
        weight = "600" if is_current else "400"
        highlight_bg = "background:rgba(0,194,203,0.08);border-radius:4px;padding:2px 4px;" if is_current else ""
        return (
            f'<div style="display:flex;justify-content:space-between;align-items:baseline;'
            f'margin-bottom:6px;{highlight_bg}">'
            f'<span style="font-size:11px;color:#8C9BAA;text-transform:uppercase;'
            f'letter-spacing:.5px;flex-shrink:0;margin-right:8px;">{label}</span>'
            f'<span style="font-size:12px;color:{color};font-weight:{weight};'
            f'text-align:right;word-break:break-word;">{val}</span>'
            f'</div>'
        )

    def _section(title: str, rows_html: str) -> str:
        return (
            f'<div style="margin-bottom:16px;">'
            f'<div style="font-size:10px;text-transform:uppercase;letter-spacing:1px;'
            f'color:#00C2CB;font-weight:600;margin-bottom:8px;padding-bottom:4px;'
            f'border-bottom:1px solid rgba(0,194,203,0.2);">{title}</div>'
            f'{rows_html}'
            f'</div>'
        )

    # Build sections
    identity_rows = (
        _row("name", "Name")
        + _row("description", "Description")
        + _row("business_purpose", "Business Purpose")
    )

    governance_rows = (
        _row("data_owner_name", "Data Owner")
        + _row("data_owner_email", "Owner Email")
        + _row("data_steward_email", "Steward Email")
    )

    classification_rows = (
        _row("domain", "Domain")
        + _row("data_classification", "Classification")
        + _row("pii_flag", "Contains PII")
        + _row("regulatory_scope", "Regulatory Scope")
    )

    access_rows = (
        _row("access_level", "Access Level")
        + _row("sla_tier", "SLA Tier")
        + _row("business_criticality", "Criticality")
        + _row("consumer_teams", "Consumer Teams")
    )

    # Auto-populated section
    today_str = date.today().isoformat()
    auto_html = (
        f'<div style="display:flex;justify-content:space-between;align-items:baseline;'
        f'margin-bottom:6px;">'
        f'<span style="font-size:11px;color:#8C9BAA;text-transform:uppercase;'
        f'letter-spacing:.5px;flex-shrink:0;margin-right:8px;">Status</span>'
        f'<span style="font-size:12px;color:#8C9BAA;">Draft</span>'
        f'</div>'
        f'<div style="display:flex;justify-content:space-between;align-items:baseline;'
        f'margin-bottom:6px;">'
        f'<span style="font-size:11px;color:#8C9BAA;text-transform:uppercase;'
        f'letter-spacing:.5px;flex-shrink:0;margin-right:8px;">Created</span>'
        f'<span style="font-size:12px;color:#8C9BAA;">{today_str}</span>'
        f'</div>'
    )

    html = (
        f'<div class="dpc-spec-preview" style="padding:16px;">'
        f'<div style="font-size:13px;font-weight:600;color:#0D1B2A;margin-bottom:16px;">'
        f'Live Preview</div>'
        + _section("Identity", identity_rows)
        + _section("Governance", governance_rows)
        + _section("Classification", classification_rows)
        + _section("Access", access_rows)
        + _section("Auto-populated", auto_html)
        + f'</div>'
    )

    st.markdown(html, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# CROSSROADS CARD (after last required field)
# ---------------------------------------------------------------------------

def _render_crossroads_card(spec: DataProductSpec, tier: int, field_idx: int) -> str:
    """
    Render the crossroads card shown after tier 1 completes.

    Returns action string or "idle".
    """
    render_guidance(
        "The business specification is complete. Technical fields are best completed by your data engineering team.",
        label="Guidance",
    )

    st.markdown(
        '<p style="font-size:16px;font-weight:600;color:#0D1B2A;margin:16px 0 8px;">'
        'Business specification complete.</p>'
        '<p style="font-size:14px;color:#5B6A7E;margin-bottom:8px;">'
        'Technical fields — schema location, source systems, Snowflake configuration — '
        'are best completed by your data engineering team.</p>',
        unsafe_allow_html=True,
    )

    col_a, col_b = st.columns([1, 1], gap="small")
    with col_a:
        if st.button(
            "Add optional business details",
            key=f"gf_crossroads_optional_{tier}_{field_idx}",
            type="secondary",
            use_container_width=True,
        ):
            st.session_state["gf_tier"] = 2
            st.session_state["gf_field_idx"] = 0
            st.session_state["gf_show_optional_prompt"] = False
            st.rerun()
    with col_b:
        if st.button(
            "Generate colleague handoff →",
            key=f"gf_crossroads_colleague_{tier}_{field_idx}",
            type="primary",
            use_container_width=True,
        ):
            return "colleague_handoff"

    return "idle"


# ---------------------------------------------------------------------------
# OPTIONAL TIER COMPLETION CARD
# ---------------------------------------------------------------------------

def _render_optional_complete_card(tier: int, field_idx: int) -> str:
    """
    Render the end-of-optional-tier prompt card.

    Returns action string or "idle".
    """
    render_guidance(
        "All optional business fields have been reviewed. You can now generate the full handoff summary.",
        label="Guidance",
    )

    st.markdown(
        '<p style="font-size:16px;font-weight:600;color:#0D1B2A;margin:16px 0 8px;">'
        'Optional details complete.</p>',
        unsafe_allow_html=True,
    )

    if st.button(
        "View full summary →",
        key=f"gf_opt_handoff_{tier}_{field_idx}",
        type="primary",
        use_container_width=True,
    ):
        return "handoff"

    st.caption("Technical fields can be delegated from the handoff summary.")

    return "idle"


# ---------------------------------------------------------------------------
# FIELD CARD RENDERING
# ---------------------------------------------------------------------------

def _render_field_card(
    spec: DataProductSpec,
    path: str,
    valid_options: dict,
    tier: int,
    field_idx: int,
    field_list: list,
    field_status: dict,
) -> tuple:
    """
    Render the field card for the current field.

    Returns (updated_spec, action).
    """
    field_name = field_list[field_idx]
    meta = get_field_meta(field_name)
    total = len(field_list)

    tier_label = "Business — Required" if tier == 1 else "Business — Optional"

    # --- Remix chip ---
    if path == "remix":
        st.markdown(
            '<span style="background:rgba(245,166,35,0.15);color:#a66d00;'
            'font-size:11px;font-weight:600;padding:3px 10px;border-radius:12px;'
            'text-transform:uppercase;letter-spacing:.5px;">'
            'Pre-filled from existing product</span>',
            unsafe_allow_html=True,
        )
        st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)

    # --- Progress header ---
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">'
        f'<span style="font-size:12px;color:#8C9BAA;">Field {field_idx + 1} of {total}</span>'
        f'<span style="background:rgba(0,194,203,0.12);color:#006B73;font-size:11px;'
        f'font-weight:600;padding:2px 10px;border-radius:10px;">{tier_label}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # --- Field label ---
    st.markdown(
        f'<div class="dpc-field-label" style="font-size:20px;font-weight:700;'
        f'color:#0D1B2A;margin-bottom:8px;">{meta.get("label", field_name)}</div>',
        unsafe_allow_html=True,
    )

    # --- Question text ---
    st.markdown(
        f'<div class="dpc-field-question" style="font-size:14px;color:#5B6A7E;'
        f'margin-bottom:16px;line-height:1.5;">{meta.get("question", "")}</div>',
        unsafe_allow_html=True,
    )

    # --- Widget ---
    current_value = getattr(spec, field_name, None)
    widget_key = f"gf_widget_{tier}_{field_name}_{field_idx}"
    raw_value = _render_widget(field_name, meta, current_value, valid_options, widget_key)

    # --- Guidance ---
    explanation = meta.get("explanation", "")
    if explanation:
        render_guidance(explanation)

    st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)

    # --- Navigation row ---
    col_back, col_skip, col_continue = st.columns([1, 1, 2], gap="small")

    action = "idle"
    updated_spec = spec

    with col_back:
        if st.button(
            "← Back to results" if field_idx == 0 and tier == 1 else "← Back",
            key=f"gf_back_{tier}_{field_name}_{field_idx}",
            type="secondary",
            use_container_width=True,
        ):
            if field_idx == 0 and tier == 1:
                action = "back"
                return updated_spec, action
            else:
                st.session_state["gf_field_idx"] = max(0, field_idx - 1)
                _scroll_top()
                action = "back"
                return updated_spec, action

    with col_skip:
        if st.button(
            "I don't know this yet",
            key=f"gf_skip_{tier}_{field_name}_{field_idx}",
            use_container_width=True,
        ):
            field_status[field_name] = FIELD_STATUS_SKIPPED
            st.session_state["gf_field_status"] = field_status
            st.session_state["gf_field_idx"] = field_idx + 1
            _scroll_top()
            action = "continue"
            return updated_spec, action

    with col_continue:
        if st.button(
            "Continue →",
            key=f"gf_continue_{tier}_{field_name}_{field_idx}",
            type="primary",
            use_container_width=True,
        ):
            # Email fields — validate format before advancing
            if field_name in _EMAIL_FIELDS and raw_value and raw_value.strip():
                import re
                if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", raw_value.strip()):
                    st.error("Please enter a valid email address (e.g. name@company.com)")
                    return updated_spec, "idle"  # Don't advance, show error

            updated_spec = _assign_value(spec, field_name, raw_value)
            field_status[field_name] = FIELD_STATUS_ANSWERED
            st.session_state["gf_field_status"] = field_status
            st.session_state["gf_field_idx"] = field_idx + 1
            _scroll_top()
            action = "continue"
            return updated_spec, action

    return updated_spec, action


# ---------------------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------------------

def render_guided_form(
    spec: DataProductSpec,
    path: str,
    valid_options: dict = None,
) -> tuple:
    """
    Render the card-by-card guided form.

    Args:
        spec: The current DataProductSpec being built.
        path: "remix" | "create"
        valid_options: Optional dict of {field_name: [option, ...]} overrides.

    Returns:
        (updated_spec, action)
        action: "continue" | "handoff" | "colleague_handoff" | "back" | "idle"
    """
    if valid_options is None:
        valid_options = {}

    # Initialise session state
    _init_session_state(spec)

    tier: int = st.session_state.get("gf_tier", 1)
    field_idx: int = st.session_state.get("gf_field_idx", 0)
    field_status: dict = st.session_state.get("gf_field_status", {})
    show_optional_prompt: bool = st.session_state.get("gf_show_optional_prompt", False)

    # Determine current field list
    if tier == 1:
        field_list = GUIDED_BUSINESS_REQUIRED
    else:
        field_list = GUIDED_BUSINESS_OPTIONAL

    total = len(field_list)

    # Determine current_field for preview highlighting
    if field_idx < total:
        current_field = field_list[field_idx]
    else:
        current_field = ""

    # Split-pane layout
    left_col, right_col = st.columns([3, 2], gap="large")

    with right_col:
        _render_spec_preview(spec, field_status, current_field)

    with left_col:
        # --- Tier 1 complete: show crossroads card ---
        if tier == 1 and field_idx >= total:
            action = _render_crossroads_card(spec, tier, field_idx)
            return spec, action

        # --- Tier 2 complete: show handoff prompt ---
        if tier == 2 and field_idx >= total:
            action = _render_optional_complete_card(tier, field_idx)
            return spec, action

        # --- Normal field card ---
        updated_spec, action = _render_field_card(
            spec=spec,
            path=path,
            valid_options=valid_options,
            tier=tier,
            field_idx=field_idx,
            field_list=field_list,
            field_status=field_status,
        )

        # If we just advanced past tier 1 last field, flip to crossroads on next render
        # (field_idx was already incremented inside _render_field_card)
        new_field_idx: int = st.session_state.get("gf_field_idx", 0)
        if tier == 1 and new_field_idx >= total and action in ("continue",):
            st.session_state["gf_show_optional_prompt"] = True

        return updated_spec, action
