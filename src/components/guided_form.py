"""
Guided form component for Data Product Concierge.

Card-by-card guided form — the core experience of filling in a data product
spec one field at a time, with a live preview on the right.
"""

import json
import urllib.parse
from datetime import date, datetime
from typing import Optional

import streamlit as st

from models.data_product import DataProductSpec
from core.field_registry import (
    FIELD_REGISTRY,
    GUIDED_BUSINESS_REQUIRED,
    GUIDED_BUSINESS_OPTIONAL,
    GUIDED_TECH_FIELDS,
    GUIDED_AUTO_FIELDS,
    GUIDED_PANEL_ACCESS_LICENSING,
    GUIDED_PANEL_EXTENDED_OWNERSHIP,
    GUIDED_PANEL_DATA_DETAIL,
    GUIDED_PANEL_TECH_DEPTH,
    get_field_meta,
    FIELD_STATUS_ANSWERED,
    FIELD_STATUS_PENDING,
    FIELD_STATUS_SKIPPED,
    FIELD_STATUS_NOT_NEEDED,
    FIELD_STATUS_AUTO,
)
from components.styles import render_guidance


# ============================================================================
# AI HELPERS
# ============================================================================


def _get_field_explanation(field_name: str, meta: dict, spec) -> str:
    """
    Return field explanation — AI-generated in live mode (cached per domain+classification),
    static registry text in demo mode or when concierge unavailable.
    """
    static = meta.get("explanation", "")
    concierge = st.session_state.get("concierge")
    if not concierge:
        return static
    try:
        from app import _demo_active
        if _demo_active():
            return static
    except Exception:
        return static

    domain = getattr(spec, "domain", "") or ""
    cls = getattr(spec, "data_classification", "") or ""
    cache_key = f"field_expl_{field_name}_{domain[:10]}_{cls[:10]}"
    if cache_key in st.session_state:
        return st.session_state[cache_key]

    from core.async_utils import run_async
    context = (
        f"Domain: {domain or 'unknown'}. "
        f"Classification: {cls or 'unknown'}. "
        f"{meta.get('question', '')}"
    )
    try:
        result = run_async(concierge.explain_field(field_name, context), timeout=8)
        st.session_state[cache_key] = result or static
    except Exception:
        st.session_state[cache_key] = static
    return st.session_state[cache_key]


def _maybe_normalise(field_name: str, raw_value, meta: dict, valid_options: dict) -> tuple:
    """
    If in live mode and field has option constraints, fuzzy-match user input to canonical enum.

    Returns:
        (normalised_value, needs_disambig: bool, disambig_msg: str)
    """
    opts = (valid_options or {}).get(field_name, []) or meta.get("options", [])
    concierge = st.session_state.get("concierge")
    raw_str = str(raw_value).strip() if raw_value is not None else ""
    if not opts or not concierge or not raw_str:
        return raw_value, False, ""
    try:
        from app import _demo_active
        if _demo_active():
            return raw_value, False, ""
    except Exception:
        return raw_value, False, ""

    from core.async_utils import run_async
    try:
        r = run_async(
            concierge.validate_and_normalise(field_name, raw_str, opts),
            timeout=8,
        )
        if r.confidence >= 0.7 and r.matched:
            st.toast(f"✓ Matched: {r.matched}", icon="✓")
            return r.matched, False, ""
        elif r.confidence >= 0.4 and r.matched:
            return raw_value, True, f'Did you mean "{r.matched}"? ({r.message})'
        else:
            if r.message:
                st.caption(f"⚠ {r.message}")
            return raw_value, False, ""
    except Exception:
        return raw_value, False, ""


_IMPACT_TRIGGER_FIELDS = {
    "data_classification",
    "pii_flag",
    "regulatory_scope",
    "data_sovereignty_flag",
}


# ---------------------------------------------------------------------------
# CONTEXTUAL INJECTION RULES
# Mapping: (field_name, trigger_value) → fields to inject immediately after
# trigger_value=None means: inject regardless of the answered value
# ---------------------------------------------------------------------------

_CONTEXTUAL_INJECTIONS = {
    # pii_flag=Yes → inject data_subject_areas right after
    ("pii_flag", "Yes — contains PII"): ["data_subject_areas"],
    # access_level=Request-based → inject access_procedure right after
    ("access_level", "Request-based"): ["access_procedure"],
    # data_classification=Confidential or Restricted → inject data_sovereignty_flag
    ("data_classification", "Confidential"): ["data_sovereignty_flag"],
    ("data_classification", "Restricted"): ["data_sovereignty_flag"],
}

_PANEL_KEY_TO_FIELDS = {
    "panel_access_licensing": GUIDED_PANEL_ACCESS_LICENSING,
    "panel_extended_ownership": GUIDED_PANEL_EXTENDED_OWNERSHIP,
    "panel_data_detail": GUIDED_PANEL_DATA_DETAIL,
    "panel_tech_depth": GUIDED_PANEL_TECH_DEPTH,
}


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
    "data_subject_areas",
    "business_terms",
    "target_systems",
    "critical_data_elements",
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
    "access_procedure",
    "data_licensing_details",
    "data_sovereignty_details",
    "release_notes",
}

# Date input fields beyond last_certified_date
_DATE_FIELDS = {
    "last_certified_date",
    "expected_release_date",
    "data_history_from",
}

# Boolean flag fields rendered as radio (Yes/No)
_BOOL_FLAG_FIELDS = {
    "data_licensing_flag",
    "data_sovereignty_flag",
}


# ---------------------------------------------------------------------------
# VALUE → STRING HELPER (module-level, reused by preview + amend panel)
# ---------------------------------------------------------------------------

def _val_to_str(val) -> str:
    """Convert any spec field value to a short display string."""
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


# ---------------------------------------------------------------------------
# AMEND PANEL — lists all answered fields with jump-to-edit buttons
# ---------------------------------------------------------------------------

def _render_amend_panel(
    field_list: list,
    field_status: dict,
    spec: DataProductSpec,
    path: str,
    original_spec: Optional[DataProductSpec],
) -> Optional[int]:
    """
    Render a collapsible 'Review answers' panel in the right column.

    Shows every answered/skipped field with its current value and an Edit button.
    In remix mode, highlights fields that differ from the original.
    Returns the field_idx to jump to if Edit was clicked, else None.
    """
    answered = [
        (i, f) for i, f in enumerate(field_list)
        if field_status.get(f) in (FIELD_STATUS_ANSWERED, FIELD_STATUS_SKIPPED)
    ]
    if not answered:
        return None

    changed_count = 0
    if path == "remix" and original_spec is not None:
        for _, f in answered:
            orig = _val_to_str(getattr(original_spec, f, None))
            curr = _val_to_str(getattr(spec, f, None))
            if orig != curr:
                changed_count += 1

    label = f"Review answers · {len(answered)} filled"
    if changed_count:
        label += f" · {changed_count} changed"

    with st.expander(label, expanded=False):
        jump_to = None
        for i, (field_idx, field_name) in enumerate(answered):
            meta = get_field_meta(field_name)
            display_label = meta.get("label", field_name)
            status = field_status.get(field_name)
            curr_str = _val_to_str(getattr(spec, field_name, None))

            # Diff for remix
            is_changed = False
            orig_str = None
            if path == "remix" and original_spec is not None:
                orig_str = _val_to_str(getattr(original_spec, field_name, None))
                is_changed = orig_str != curr_str

            if status == FIELD_STATUS_SKIPPED:
                val_color = "#F5A623"
                val_display = "— skipped"
            elif is_changed:
                val_color = "#00C48C"
                val_display = curr_str
            else:
                val_color = "#006B73"
                val_display = curr_str

            col_lbl, col_val, col_btn = st.columns([2, 3, 1], gap="small")
            with col_lbl:
                st.markdown(
                    f'<div style="font-size:.78rem;color:#5B6A7E;padding:4px 0;">{display_label}</div>',
                    unsafe_allow_html=True,
                )
            with col_val:
                orig_html = ""
                if is_changed and orig_str and orig_str != "—":
                    orig_html = (
                        f'<span style="color:#8C9BAA;text-decoration:line-through;'
                        f'font-size:.72rem;margin-right:4px;">{orig_str}</span>'
                    )
                st.markdown(
                    f'<div style="font-size:.78rem;padding:4px 0;">'
                    f'{orig_html}<span style="color:{val_color};">{val_display}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with col_btn:
                if st.button("Edit", key=f"amend_{field_name}_{field_idx}_{i}", use_container_width=True):
                    jump_to = field_idx

        return jump_to

    return None


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
        st.session_state["gf_dynamic_field_list"] = list(GUIDED_BUSINESS_REQUIRED)
        st.session_state["gf_active_panel"] = None  # panel key or None

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

    # --- Generic boolean flag fields (Yes/No radio) ---
    if field_name in _BOOL_FLAG_FIELDS:
        label_yes = "Yes"
        label_no = "No"
        if current_value is True:
            default_idx = 0
        else:
            default_idx = 1
        return st.radio(
            "",
            [label_yes, label_no],
            index=default_idx,
            horizontal=True,
            key=widget_key,
        )

    # --- Selectbox fields ---
    if effective_options:
        current_str = str(current_value) if current_value is not None else None
        if current_str and current_str in effective_options:
            display_options = effective_options
            default_idx = effective_options.index(current_str)
        else:
            display_options = ["— Select —"] + effective_options
            default_idx = 0
        return st.selectbox("", display_options, index=default_idx, key=widget_key)

    # --- Date input ---
    if field_name in _DATE_FIELDS:
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

    elif field_name in _BOOL_FLAG_FIELDS:
        spec_dict[field_name] = raw_value == "Yes"

    elif field_name in _DATE_FIELDS:
        spec_dict[field_name] = raw_value  # already a date object from st.date_input

    elif field_name in _LIST_FIELDS:
        if isinstance(raw_value, str):
            items = [line.strip() for line in raw_value.splitlines() if line.strip()]
            spec_dict[field_name] = items if items else None
        else:
            spec_dict[field_name] = raw_value

    elif raw_value == "— Select —":
        spec_dict[field_name] = None

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

def _render_spec_preview(
    spec: DataProductSpec,
    field_status: dict,
    current_field: str,
    path: str = "create",
    original_spec: Optional[DataProductSpec] = None,
) -> None:
    """
    Render the live spec preview in the right panel.
    In remix mode, shows changed fields with strikethrough original → new value.
    """
    teal_d = "#006B73"
    gold = "#F5A623"
    text3 = "#8C9BAA"
    navy = "#0D1B2A"
    emerald = "#00C48C"

    is_remix = (path == "remix" and original_spec is not None)

    def _status_color(field_name: str) -> str:
        status = field_status.get(field_name, FIELD_STATUS_PENDING)
        if field_name == current_field:
            return navy
        if is_remix:
            orig = _val_to_str(getattr(original_spec, field_name, None))
            curr = _val_to_str(getattr(spec, field_name, None))
            if status == FIELD_STATUS_ANSWERED and orig != curr:
                return emerald  # changed field
        if status == FIELD_STATUS_ANSWERED:
            return teal_d
        if status == FIELD_STATUS_SKIPPED:
            return gold
        return text3

    def _row(field_name: str, label: str) -> str:
        curr_str = _val_to_str(getattr(spec, field_name, None))
        is_current = field_name == current_field
        weight = "600" if is_current else "400"
        highlight_bg = "background:rgba(0,194,203,0.08);border-radius:4px;padding:2px 4px;" if is_current else ""
        color = _status_color(field_name)

        # Diff annotation for remix
        diff_prefix = ""
        if is_remix:
            orig_str = _val_to_str(getattr(original_spec, field_name, None))
            if orig_str != curr_str and orig_str != "—" and curr_str != "—":
                diff_prefix = (
                    f'<span style="color:#8C9BAA;text-decoration:line-through;'
                    f'font-size:10px;margin-right:3px;">{orig_str}</span>'
                    f'<span style="color:#8C9BAA;font-size:10px;margin-right:3px;">→</span>'
                )
            elif orig_str == "—" and curr_str != "—":
                diff_prefix = '<span style="color:#00C48C;font-size:10px;margin-right:3px;">+</span>'

        return (
            f'<div style="display:flex;justify-content:space-between;align-items:baseline;'
            f'margin-bottom:6px;{highlight_bg}">'
            f'<span style="font-size:11px;color:#8C9BAA;text-transform:uppercase;'
            f'letter-spacing:.5px;flex-shrink:0;margin-right:8px;">{label}</span>'
            f'<span style="font-size:12px;color:{color};font-weight:{weight};'
            f'text-align:right;word-break:break-word;">{diff_prefix}{curr_str}</span>'
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

    # Changes counter badge for remix
    changes_badge = ""
    if is_remix:
        all_preview_fields = [
            "name", "description", "business_purpose",
            "data_owner_name", "data_owner_email", "data_steward_email",
            "domain", "data_classification", "pii_flag", "regulatory_scope",
            "access_level", "sla_tier", "business_criticality", "consumer_teams",
        ]
        n_changed = sum(
            1 for f in all_preview_fields
            if _val_to_str(getattr(original_spec, f, None)) != _val_to_str(getattr(spec, f, None))
            and field_status.get(f) == FIELD_STATUS_ANSWERED
        )
        if n_changed:
            changes_badge = (
                f'<span style="display:inline-block;background:rgba(0,196,140,0.12);'
                f'color:#006B73;border:1px solid rgba(0,196,140,0.3);border-radius:100px;'
                f'padding:2px 10px;font-size:.7rem;font-weight:600;margin-bottom:12px;">'
                f'✎ {n_changed} field{"s" if n_changed != 1 else ""} changed</span>'
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

    today_str = date.today().isoformat()
    auto_html = (
        f'<div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px;">'
        f'<span style="font-size:11px;color:#8C9BAA;text-transform:uppercase;letter-spacing:.5px;flex-shrink:0;margin-right:8px;">Status</span>'
        f'<span style="font-size:12px;color:#8C9BAA;">Draft</span>'
        f'</div>'
        f'<div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px;">'
        f'<span style="font-size:11px;color:#8C9BAA;text-transform:uppercase;letter-spacing:.5px;flex-shrink:0;margin-right:8px;">Created</span>'
        f'<span style="font-size:12px;color:#8C9BAA;">{today_str}</span>'
        f'</div>'
    )

    preview_label = "Changes" if is_remix else "Live Preview"
    html = (
        f'<div class="dpc-spec-preview" style="padding:16px;">'
        f'<div style="font-size:13px;font-weight:600;color:#0D1B2A;margin-bottom:10px;">'
        f'{preview_label}</div>'
        f'{changes_badge}'
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
    tier_label_override: str = None,
) -> tuple:
    """
    Render the field card for the current field.

    Returns (updated_spec, action).
    """
    field_name = field_list[field_idx]
    meta = get_field_meta(field_name)
    total = len(field_list)

    tier_label = tier_label_override if tier_label_override else ("Business — Required" if tier == 1 else "Business — Optional")

    # --- Remix banner ---
    if path == "remix":
        _orig = st.session_state.get("original_spec")
        _orig_name = (_orig.name if _orig and _orig.name else "existing product")
        _prefilled = sum(
            1 for f in field_list
            if field_status.get(f) == FIELD_STATUS_ANSWERED
        )
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;'
            f'background:rgba(245,166,35,0.08);border:1px solid rgba(245,166,35,0.25);'
            f'border-radius:8px;padding:8px 12px;">'
            f'<span style="font-size:1rem;">✂</span>'
            f'<div>'
            f'<div style="font-size:.78rem;font-weight:700;color:#a66d00;">Adapting: {_orig_name}</div>'
            f'<div style="font-size:.72rem;color:#8C9BAA;margin-top:1px;">'
            f'{_prefilled} fields pre-filled — review and amend any below</div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # --- Progress header ---
    pct = int((field_idx / max(total, 1)) * 100)
    bar_color = "#00C48C" if pct >= 80 else "#00C2CB"
    st.markdown(
        f'<div style="margin-bottom:14px;">'
        f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">'
        f'<span style="font-size:12px;color:#8C9BAA;">Field {field_idx + 1} of {total}</span>'
        f'<span style="background:rgba(0,194,203,0.12);color:#006B73;font-size:11px;'
        f'font-weight:600;padding:2px 10px;border-radius:10px;">{tier_label}</span>'
        f'</div>'
        f'<div style="background:rgba(13,27,42,0.08);border-radius:100px;height:3px;">'
        f'<div style="background:{bar_color};width:{pct}%;height:100%;border-radius:100px;transition:width .3s ease;"></div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # --- AI suggestion badge ---
    _ai_suggested = st.session_state.get("ai_suggested_fields", set())
    if field_name in _ai_suggested:
        st.html(
            '<div style="display:inline-flex;align-items:center;gap:4px;'
            'background:rgba(0,107,115,0.08);border:1px solid rgba(0,107,115,0.2);'
            'border-radius:100px;padding:2px 10px;font-size:.72rem;color:#006B73;'
            'font-weight:600;margin-bottom:.6rem;">💡 AI suggestion — review and confirm</div>'
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

    # --- Guidance ---
    explanation = _get_field_explanation(field_name, meta, spec)
    if explanation:
        render_guidance(explanation)

    # --- Remix governance impact banner ---
    _impact_key = f"impact_msg_{field_name}"
    if _impact_key in st.session_state:
        st.html(
            f'<div style="background:rgba(245,166,35,0.1);border-left:3px solid #F5A623;'
            f'border-radius:0 8px 8px 0;padding:10px 14px;margin-bottom:.8rem;'
            f'font-size:.85rem;color:#5B6A7E;">⚡ {st.session_state[_impact_key]}</div>'
        )

    # --- Widget ---
    current_value = getattr(spec, field_name, None)
    widget_key = f"gf_widget_{tier}_{field_name}_{field_idx}"
    raw_value = _render_widget(field_name, meta, current_value, valid_options, widget_key)

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
            "Skip for now",
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
                if not re.match(r"^[\w.%+\-]+@[\w.\-]+\.[a-zA-Z]{2,}$", raw_value.strip()):
                    st.error("Please enter a valid email address (e.g. name@company.com)")
                    return updated_spec, "idle"  # Don't advance, show error

            # Normalise free-text input against Collibra options
            normalised_value, needs_disambig, disambig_msg = _maybe_normalise(
                field_name, raw_value, meta, valid_options
            )
            if needs_disambig:
                st.warning(disambig_msg)
                # Store pending disambiguation — user must confirm on next render
                st.session_state[f"disambig_{field_name}"] = {
                    "raw": raw_value,
                    "matched": disambig_msg,
                }
                return updated_spec, "idle"
            raw_value = normalised_value

            updated_spec = _assign_value(spec, field_name, raw_value)
            field_status[field_name] = FIELD_STATUS_ANSWERED
            st.session_state["gf_field_status"] = field_status

            # --- Contextual injection: inject extra fields after this one ---
            if tier == 1:
                dynamic_list = st.session_state.get("gf_dynamic_field_list", list(GUIDED_BUSINESS_REQUIRED))
                for (trigger_field, trigger_val), inject_fields in _CONTEXTUAL_INJECTIONS.items():
                    if trigger_field == field_name and str(raw_value) == trigger_val:
                        insert_pos = field_idx + 1
                        for extra_field in reversed(inject_fields):
                            if extra_field not in dynamic_list:
                                dynamic_list.insert(insert_pos, extra_field)
                st.session_state["gf_dynamic_field_list"] = dynamic_list

            # Remix governance impact analysis
            if path == "remix" and field_name in _IMPACT_TRIGGER_FIELDS:
                _original_spec = st.session_state.get("original_spec")
                if _original_spec:
                    _orig_val = _val_to_str(getattr(_original_spec, field_name, None))
                    _new_val = _val_to_str(getattr(updated_spec, field_name, None))
                    if _orig_val != _new_val:
                        _concierge = st.session_state.get("concierge")
                        _demo = False
                        try:
                            from app import _demo_active
                            _demo = _demo_active()
                        except Exception:
                            pass
                        if _concierge and not _demo:
                            from core.async_utils import run_async
                            try:
                                _impact = run_async(
                                    _concierge.explain_field_impact(
                                        field_name,
                                        _orig_val,
                                        _new_val,
                                        {
                                            "domain": getattr(updated_spec, "domain", None),
                                            "data_classification": getattr(updated_spec, "data_classification", None),
                                            "pii_flag": getattr(updated_spec, "pii_flag", None),
                                            "regulatory_scope": getattr(updated_spec, "regulatory_scope", None),
                                        },
                                    ),
                                    timeout=8,
                                )
                                if _impact and _impact.strip():
                                    st.session_state[f"impact_msg_{field_name}"] = _impact
                            except Exception:
                                pass

            # Clear AI suggestion badge once user confirms this field
            _ai_suggested = st.session_state.get("ai_suggested_fields", set())
            _ai_suggested.discard(field_name)
            st.session_state["ai_suggested_fields"] = _ai_suggested

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

    from components.maturity_dashboard import render_maturity_dashboard
    from components.maturity_dashboard import _PANELS as _MD_PANELS

    # Initialise session state
    _init_session_state(spec)

    tier: int = st.session_state.get("gf_tier", 1)
    field_idx: int = st.session_state.get("gf_field_idx", 0)
    field_status: dict = st.session_state.get("gf_field_status", {})
    active_panel: Optional[str] = st.session_state.get("gf_active_panel", None)

    # Determine current field list
    if tier == 1:
        field_list = st.session_state.get("gf_dynamic_field_list", list(GUIDED_BUSINESS_REQUIRED))
    elif active_panel and active_panel in _PANEL_KEY_TO_FIELDS:
        field_list = _PANEL_KEY_TO_FIELDS[active_panel]
    else:
        field_list = GUIDED_BUSINESS_OPTIONAL

    total = len(field_list)

    # Determine current_field for preview highlighting
    if field_idx < total:
        current_field = field_list[field_idx]
    else:
        current_field = ""

    # Retrieve original spec for remix diff
    original_spec: Optional[DataProductSpec] = st.session_state.get("original_spec")

    # Split-pane layout
    left_col, right_col = st.columns([3, 2], gap="large")

    with right_col:
        _render_spec_preview(spec, field_status, current_field, path=path, original_spec=original_spec)
        # Amend panel — jump to any previous answer
        if field_idx < total:  # Only show during active form, not on dashboard
            jump_idx = _render_amend_panel(field_list, field_status, spec, path, original_spec)
            if jump_idx is not None:
                st.session_state["gf_field_idx"] = jump_idx
                _scroll_top()
                st.rerun()

    with left_col:
        # --- Tier 1 complete: show maturity dashboard ---
        if tier == 1 and field_idx >= total and active_panel is None:
            dashboard_action = render_maturity_dashboard(spec, field_status)
            if dashboard_action == "summary":
                return spec, "handoff"
            elif dashboard_action == "fill_all":
                # Queue all panels in order, start first
                all_keys = [p["key"] for p in _MD_PANELS]
                st.session_state["gf_panel_queue"] = all_keys[1:]  # remainder after first
                st.session_state["gf_active_panel"] = all_keys[0]
                st.session_state["gf_field_idx"] = 0
                st.rerun()
            elif dashboard_action is not None and dashboard_action in _PANEL_KEY_TO_FIELDS:
                st.session_state["gf_panel_queue"] = []  # single panel only
                st.session_state["gf_active_panel"] = dashboard_action
                st.session_state["gf_field_idx"] = 0
                st.rerun()
            return spec, "idle"

        # --- Panel complete: advance queue or return to dashboard ---
        if active_panel and field_idx >= total:
            # Find the panel title for the toast
            panel_title = active_panel.replace("panel_", "").replace("_", " ").title()
            st.toast(f"✓ {panel_title} complete", icon="✅")
            panel_queue = st.session_state.get("gf_panel_queue", [])
            if panel_queue:
                # Auto-advance to next queued panel
                next_panel = panel_queue[0]
                st.session_state["gf_panel_queue"] = panel_queue[1:]
                st.session_state["gf_active_panel"] = next_panel
                st.session_state["gf_field_idx"] = 0
            else:
                st.session_state["gf_active_panel"] = None
                st.session_state["gf_field_idx"] = total  # keep tier 1 "complete" state
            st.rerun()

        # --- Tier 2 complete (old optional flow, kept for backward compat): ---
        if tier == 2 and field_idx >= total and active_panel is None:
            action = _render_optional_complete_card(tier, field_idx)
            return spec, action

        # --- Normal field card ---
        tier_label_override = None
        if active_panel:
            panel_meta = next((p for p in _MD_PANELS if p["key"] == active_panel), None)
            if panel_meta:
                tier_label_override = f"Enhancement · {panel_meta['title']}"

        updated_spec, action = _render_field_card(
            spec=spec,
            path=path,
            valid_options=valid_options,
            tier=tier,
            field_idx=field_idx,
            field_list=field_list,
            field_status=field_status,
            tier_label_override=tier_label_override,
        )

        # If we just advanced past tier 1 last field, flip to dashboard on next render
        new_field_idx: int = st.session_state.get("gf_field_idx", 0)
        if tier == 1 and new_field_idx >= total and action in ("continue",):
            st.session_state["gf_show_optional_prompt"] = True

        return updated_spec, action
