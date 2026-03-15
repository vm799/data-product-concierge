"""
Production-ready multi-chapter form component for Data Product Concierge.

Handles Paths B (Remix) and C (Create) with 5 sequential chapters:
1. Identity: name, description, business_purpose, status, version
2. Classification: domain, sub_domain, data_classification, tags
3. Governance: data_owner_*, data_steward_*, certifying_officer_email, last_certified_date
4. Compliance & Technical: regulatory_scope, geographic_restriction, pii_flag,
   encryption_standard, retention_period, source_systems, update_frequency, schema_location
5. Access & Business: access_level, consumer_teams, sla_tier, business_criticality,
   cost_centre, related_reports

Full enum support with pill buttons (never dropdowns).
Email validation. Date inputs. Multi-select toggles for lists.
No mock data. Production-ready.
"""

import streamlit as st
from datetime import date as date_type
from typing import Dict, List, Tuple, Optional
from models.data_product import (
    DataProductSpec,
    StatusEnum,
    DataClassificationEnum,
    UpdateFrequencyEnum,
    AccessLevelEnum,
    SLATierEnum,
    BusinessCriticalityEnum,
    RegulatoryFrameworkEnum,
)


# Required fields per spec model
REQUIRED_FIELDS = {
    "name",
    "description",
    "business_purpose",
    "domain",
    "data_classification",
    "data_owner_email",
    "data_owner_name",
    "data_steward_email",
    "regulatory_scope",
    "update_frequency",
    "access_level",
    "sla_tier",
    "business_criticality",
    "source_systems",
    "schema_location",
}


# Chapter definitions with field names
CHAPTERS = {
    1: {
        "title": "Identity",
        "description": "Basic product information",
        "fields": ["name", "description", "business_purpose", "status", "version"],
    },
    2: {
        "title": "Classification",
        "description": "Business domain and data classification",
        "fields": ["domain", "sub_domain", "data_classification", "tags", "asset_type", "collibra_community"],
    },
    3: {
        "title": "Governance",
        "description": "Data ownership and certification",
        "fields": [
            "data_owner_name",
            "data_owner_email",
            "data_steward_name",
            "data_steward_email",
            "certifying_officer_email",
            "last_certified_date",
            "review_cycle",
            "incident_contact",
        ],
    },
    4: {
        "title": "Compliance & Technical",
        "description": "Regulatory, security, and technical details",
        "fields": [
            "regulatory_scope",
            "geographic_restriction",
            "pii_flag",
            "encryption_standard",
            "retention_period",
            "source_systems",
            "update_frequency",
            "schema_location",
            "materialization_type",
            "snowflake_role",
            "refresh_cron",
            "column_definitions",
            "sample_query",
            "lineage_upstream",
            "lineage_downstream",
        ],
    },
    5: {
        "title": "Access & Business",
        "description": "Access control and business context",
        "fields": [
            "access_level",
            "consumer_teams",
            "sla_tier",
            "business_criticality",
            "delivery_method",
            "cost_centre",
            "related_reports",
        ],
    },
}


# ============================================================================
# FIELD INTERDEPENDENCY RULES
# When a field changes, these rules suggest related field values.
# Format: {trigger_field: {trigger_value: [rule_dict, ...]}}
# rule_dict keys: action, field, value/values, message
# ============================================================================
FIELD_RULES: Dict[str, Dict] = {
    "pii_flag": {
        True: [
            {"action": "add_to_list", "field": "regulatory_scope", "value": "GDPR",
             "message": "PII data must comply with GDPR — added to Regulatory Scope."},
            {"action": "suggest_text", "field": "encryption_standard", "value": "AES-256",
             "message": "PII data should be encrypted with AES-256 at minimum."},
            {"action": "suggest_text", "field": "retention_period", "value": "6 years",
             "message": "GDPR requires a defined retention period. 6 years is typical for financial PII."},
        ],
    },
    "data_classification": {
        "Confidential": [
            {"action": "suggest_text", "field": "encryption_standard", "value": "AES-256",
             "message": "Confidential data requires AES-256 encryption as a minimum standard."},
            {"action": "suggest_enum", "field": "access_level", "value": "Restricted",
             "message": "Confidential data should have Restricted or higher access level."},
        ],
        "Public": [
            {"action": "suggest_enum", "field": "access_level", "value": "Open",
             "message": "Public data can use Open access level — no approval required."},
        ],
        "Restricted": [
            {"action": "suggest_enum", "field": "access_level", "value": "Confidential",
             "message": "Restricted data typically requires Confidential access control."},
        ],
    },
    "domain": {
        "Sustainable Investing": [
            {"action": "add_to_list", "field": "regulatory_scope", "value": "SFDR",
             "message": "ESG/Sustainable Investing data typically falls under SFDR reporting requirements."},
            {"action": "add_to_list", "field": "regulatory_scope", "value": "EU Taxonomy",
             "message": "EU Taxonomy disclosure is required for sustainable investment products."},
            {"action": "add_to_list", "field": "regulatory_scope", "value": "TCFD",
             "message": "TCFD climate-related financial disclosures are standard for ESG products."},
        ],
        "Risk & Analytics": [
            {"action": "add_to_list", "field": "regulatory_scope", "value": "BCBS 239",
             "message": "Risk data aggregation is governed by BCBS 239 — required for risk products."},
            {"action": "add_to_list", "field": "regulatory_scope", "value": "MiFID II",
             "message": "MiFID II governs risk data used in trading and investment decisions."},
        ],
        "Client Data": [
            {"action": "add_to_list", "field": "regulatory_scope", "value": "GDPR",
             "message": "Client data falls under GDPR — added to regulatory scope."},
            {"action": "add_to_list", "field": "regulatory_scope", "value": "MiFID II",
             "message": "Client data used in investment services requires MiFID II compliance."},
            {"action": "suggest_bool", "field": "pii_flag", "value": True,
             "message": "Client data usually contains PII — consider flagging pii_flag as Yes."},
        ],
        "Market Data": [
            {"action": "add_to_list", "field": "regulatory_scope", "value": "MiFID II",
             "message": "Market data distribution is governed by MiFID II."},
        ],
        "Compliance": [
            {"action": "suggest_enum", "field": "data_classification", "value": "Confidential",
             "message": "Compliance data is typically Confidential by default."},
        ],
    },
    "update_frequency": {
        "Real-time": [
            {"action": "suggest_enum", "field": "sla_tier", "value": "Gold (99.9%)",
             "message": "Real-time data products require Gold SLA tier (99.9% uptime)."},
            {"action": "suggest_enum", "field": "materialization_type", "value": "Dynamic Table",
             "message": "Real-time refresh is best implemented as a Snowflake Dynamic Table."},
        ],
        "Daily": [
            {"action": "suggest_enum", "field": "materialization_type", "value": "Table",
             "message": "Daily batch refresh typically uses a standard Snowflake Table."},
        ],
    },
}


def _get_field_rules(field_name: str, new_value) -> List[Dict]:
    """Return applicable rules for a field value change. Skips dismissed rules."""
    rules = FIELD_RULES.get(field_name, {})
    if isinstance(rules, dict):
        rule_list = rules.get(new_value, [])
    else:
        rule_list = []
    dismissed = st.session_state.get("dismissed_suggestions", set())
    return [r for r in rule_list if f"{field_name}__{r['field']}" not in dismissed]


def _apply_suggestion(rule: Dict, spec: DataProductSpec) -> DataProductSpec:
    """Apply a single suggestion rule to the spec."""
    field = rule["field"]
    action = rule["action"]
    value = rule.get("value")

    current = getattr(spec, field, None)

    if action == "add_to_list":
        lst = list(current) if current else []
        if value not in lst:
            lst.append(value)
        spec = spec.model_copy(update={field: lst})
    elif action in ("suggest_text", "suggest_enum"):
        if not current:  # Only apply if field is currently empty
            spec = spec.model_copy(update={field: value})
    elif action == "suggest_bool":
        if current is None:
            spec = spec.model_copy(update={field: value})

    return spec


def _render_suggestions(active_suggestions: List[Dict], spec: DataProductSpec) -> DataProductSpec:
    """Render gold suggestion banners. Returns potentially modified spec."""
    for rule in active_suggestions:
        key = f"{rule.get('_trigger_field')}__{rule['field']}"
        st.markdown(
            f'<div style="background:rgba(245,166,35,.1);border-left:3px solid #F5A623;'
            f'padding:.5rem .75rem;margin:.5rem 0 .25rem;border-radius:0 6px 6px 0;">'
            f'<span style="color:#F5A623;font-weight:700;font-size:.8rem;">⚡ Smart suggestion</span>'
            f'<span style="color:var(--text-secondary);font-size:.82rem;margin-left:.5rem;">{rule["message"]}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("✓ Apply", key=f"apply_sugg_{key}", use_container_width=True, type="primary"):
                spec = _apply_suggestion(rule, spec)
                if "dismissed_suggestions" not in st.session_state:
                    st.session_state.dismissed_suggestions = set()
                st.session_state.dismissed_suggestions.add(key)
                st.rerun()
        with col2:
            if st.button("✕ Dismiss", key=f"dismiss_sugg_{key}", use_container_width=True):
                if "dismissed_suggestions" not in st.session_state:
                    st.session_state.dismissed_suggestions = set()
                st.session_state.dismissed_suggestions.add(key)
                st.rerun()
    return spec


def render_progress_bar(current_chapter: int, chapter_names: List[str]):
    """
    Renders a clickable 5-step progress bar.

    Completed and future steps are clickable buttons to jump chapters.
    Current step is highlighted and non-interactive.

    Args:
        current_chapter: Current chapter (1-5)
        chapter_names: List of chapter titles
    """
    st.markdown("""
    <style>
    /* Progress nav column buttons — styled as step circles */
    div.prog-nav div[data-testid="column"] .stButton > button {
        border-radius: 100px !important;
        padding: 6px 16px !important;
        min-height: 36px !important;
        font-size: 13px !important;
        font-weight: 700 !important;
        letter-spacing: 0.03em !important;
        text-transform: uppercase !important;
        width: 100% !important;
        box-shadow: none !important;
    }
    </style>
    <div class="prog-nav">
    """, unsafe_allow_html=True)

    cols = st.columns(len(chapter_names))
    for i, (col, name) in enumerate(zip(cols, chapter_names), 1):
        with col:
            if i < current_chapter:
                # Completed — teal, clickable
                st.markdown(
                    f'<div style="text-align:center;margin-bottom:4px;">'
                    f'<span style="display:inline-block;width:28px;height:28px;border-radius:50%;'
                    f'background:#00C48C;color:#fff;font-weight:700;font-size:13px;line-height:28px;text-align:center;">✓</span>'
                    f'</div>'
                    f'<div style="text-align:center;font-size:11px;color:#00C48C;font-weight:600;letter-spacing:0.04em;text-transform:uppercase;">{name}</div>',
                    unsafe_allow_html=True,
                )
                if st.button(f"← Back", key=f"chap_nav_{i}", use_container_width=True, help=f"Go back to {name}"):
                    st.session_state.chapter = i
                    st.rerun()
            elif i == current_chapter:
                # Active — navy, non-clickable
                st.markdown(
                    f'<div style="text-align:center;margin-bottom:4px;">'
                    f'<span style="display:inline-block;width:28px;height:28px;border-radius:50%;'
                    f'background:#0D1B2A;color:#fff;font-weight:700;font-size:13px;line-height:28px;text-align:center;'
                    f'box-shadow:0 0 0 3px rgba(0,194,203,0.4);">{i}</span>'
                    f'</div>'
                    f'<div style="text-align:center;font-size:11px;color:#0D1B2A;font-weight:700;letter-spacing:0.04em;text-transform:uppercase;">{name}</div>',
                    unsafe_allow_html=True,
                )
            else:
                # Future — grey, clickable (allow skipping forward in remix)
                st.markdown(
                    f'<div style="text-align:center;margin-bottom:4px;">'
                    f'<span style="display:inline-block;width:28px;height:28px;border-radius:50%;'
                    f'background:#CBD5E0;color:#5B6A7E;font-weight:700;font-size:13px;line-height:28px;text-align:center;">{i}</span>'
                    f'</div>'
                    f'<div style="text-align:center;font-size:11px;color:#8C9BAA;font-weight:600;letter-spacing:0.04em;text-transform:uppercase;">{name}</div>',
                    unsafe_allow_html=True,
                )
                if st.button(f"→ {name}", key=f"chap_nav_{i}", use_container_width=True, help=f"Skip to {name}"):
                    st.session_state.chapter = i
                    st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<hr style='margin:16px 0 8px;border-color:rgba(13,27,42,0.08);'>", unsafe_allow_html=True)


def _validate_email(email: str) -> bool:
    """Simple email validation."""
    if not email:
        return False
    return "@" in email and "." in email.split("@")[1]


def _render_text_field(
    label: str,
    value: Optional[str],
    field_name: str,
    required: bool,
    path: str,
    explanation: str,
    is_multiline: bool = False,
) -> Optional[str]:
    """Render a text input field (single or multi-line)."""
    display_label = f"{label} {'*' if required else '(Optional)'}"

    if path == "remix":
        # Read-only mode with Change button
        current_value = value or "(Not set)"
        col1, col2 = st.columns([4, 1])
        with col1:
            st.text(f"**Current:** {current_value}")
        with col2:
            if st.button(f"Change ✏", key=f"btn_change_{field_name}"):
                st.session_state[f"editing_{field_name}"] = True

        if st.session_state.get(f"editing_{field_name}", False):
            if is_multiline:
                new_value = st.text_area(
                    display_label, value=value or "", key=f"input_{field_name}"
                )
            else:
                new_value = st.text_input(
                    display_label, value=value or "", key=f"input_{field_name}"
                )
            if st.button(f"Save", key=f"btn_save_{field_name}"):
                st.session_state[f"editing_{field_name}"] = False
                return new_value
            return value
    else:
        # Create mode: direct input
        if is_multiline:
            return st.text_area(display_label, value=value or "", key=f"input_{field_name}")
        else:
            return st.text_input(
                display_label, value=value or "", key=f"input_{field_name}"
            )

    # Show explanation below field
    if explanation:
        st.caption(explanation)

    return value


def _render_email_field(
    label: str, value: Optional[str], field_name: str, required: bool, path: str, explanation: str
) -> Optional[str]:
    """Render an email input field with validation."""
    display_label = f"{label} {'*' if required else '(Optional)'}"

    if path == "remix":
        current_value = value or "(Not set)"
        col1, col2 = st.columns([4, 1])
        with col1:
            st.text(f"**Current:** {current_value}")
        with col2:
            if st.button(f"Change ✏", key=f"btn_change_{field_name}"):
                st.session_state[f"editing_{field_name}"] = True

        if st.session_state.get(f"editing_{field_name}", False):
            new_value = st.text_input(
                display_label,
                value=value or "",
                key=f"input_{field_name}",
                placeholder="user@company.com",
            )
            if st.button(f"Save", key=f"btn_save_{field_name}"):
                if new_value and not _validate_email(new_value):
                    st.error("Invalid email format")
                    return value
                st.session_state[f"editing_{field_name}"] = False
                return new_value
            return value
    else:
        new_value = st.text_input(
            display_label,
            value=value or "",
            key=f"input_{field_name}",
            placeholder="user@company.com",
        )
        if new_value and not _validate_email(new_value):
            st.error("Invalid email format")
        return new_value if _validate_email(new_value) else value

    if explanation:
        st.caption(explanation)

    return value


def _render_date_field(
    label: str, value: Optional[date_type], field_name: str, required: bool, path: str, explanation: str
) -> Optional[date_type]:
    """Render a date input field."""
    display_label = f"{label} {'*' if required else '(Optional)'}"

    if path == "remix":
        current_value = value.isoformat() if value else "(Not set)"
        col1, col2 = st.columns([4, 1])
        with col1:
            st.text(f"**Current:** {current_value}")
        with col2:
            if st.button(f"Change ✏", key=f"btn_change_{field_name}"):
                st.session_state[f"editing_{field_name}"] = True

        if st.session_state.get(f"editing_{field_name}", False):
            new_value = st.date_input(display_label, value=value, key=f"input_{field_name}")
            if st.button(f"Save", key=f"btn_save_{field_name}"):
                st.session_state[f"editing_{field_name}"] = False
                return new_value
            return value
    else:
        return st.date_input(display_label, value=value, key=f"input_{field_name}")

    if explanation:
        st.caption(explanation)

    return value


def _render_enum_field(
    label: str,
    value: Optional[str],
    field_name: str,
    required: bool,
    path: str,
    valid_options: List[str],
    explanation: str,
) -> Optional[str]:
    """Render enum field as pill buttons (never dropdown)."""
    display_label = f"{label} {'*' if required else '(Optional)'}"

    if path == "remix":
        current_value = value or "(Not set)"
        col1, col2 = st.columns([4, 1])
        with col1:
            st.text(f"**Current:** {current_value}")
        with col2:
            if st.button(f"Change ✏", key=f"btn_change_{field_name}"):
                st.session_state[f"editing_{field_name}"] = True

        if st.session_state.get(f"editing_{field_name}", False):
            st.write(display_label)
            cols = st.columns(max(1, min(len(valid_options), 3)))
            selected = None
            for i, option in enumerate(valid_options):
                with cols[i % 3]:
                    is_active = option == value
                    btn_class = "dpc-pill active" if is_active else "dpc-pill"
                    if st.button(option, key=f"pill_{field_name}_{i}"):
                        selected = option
            if selected:
                st.session_state[f"editing_{field_name}"] = False
                return selected
            return value
    else:
        st.write(display_label)
        cols = st.columns(max(1, min(len(valid_options), 3)))
        selected = None
        for i, option in enumerate(valid_options):
            with cols[i % 3]:
                is_active = option == value
                btn_class = "dpc-pill active" if is_active else "dpc-pill"
                if st.button(option, key=f"pill_{field_name}_{i}"):
                    selected = option
        if explanation:
            st.caption(explanation)
        return selected if selected is not None else value

    if explanation:
        st.caption(explanation)

    return value


def _render_multi_select_field(
    label: str,
    value: Optional[List[str]],
    field_name: str,
    required: bool,
    path: str,
    valid_options: List[str],
    explanation: str,
) -> Optional[List[str]]:
    """Render multi-select field as pill toggles."""
    display_label = f"{label} {'*' if required else '(Optional)'}"
    current_value = value or []

    if path == "remix":
        if current_value:
            st.text(f"**Current:** {', '.join(current_value)}")
        else:
            st.text("**Current:** (Not set)")

        if st.button(f"Change ✏", key=f"btn_change_{field_name}"):
            st.session_state[f"editing_{field_name}"] = True

        if st.session_state.get(f"editing_{field_name}", False):
            st.write(display_label)
            cols = st.columns(max(1, min(len(valid_options), 3)))
            selected = list(current_value)
            for i, option in enumerate(valid_options):
                with cols[i % 3]:
                    is_selected = option in selected
                    if st.button(
                        option,
                        key=f"pill_{field_name}_{i}",
                        help=f"Toggle {option}",
                    ):
                        if is_selected:
                            selected.remove(option)
                        else:
                            selected.append(option)
            if st.button(f"Save", key=f"btn_save_{field_name}"):
                st.session_state[f"editing_{field_name}"] = False
                return selected
            return current_value
    else:
        st.write(display_label)
        cols = st.columns(max(1, min(len(valid_options), 3)))
        selected = list(current_value)
        for i, option in enumerate(valid_options):
            with cols[i % 3]:
                is_selected = option in selected
                if st.button(
                    option,
                    key=f"pill_{field_name}_{i}",
                    help=f"Toggle {option}",
                ):
                    if is_selected:
                        selected.remove(option)
                    else:
                        selected.append(option)
        if explanation:
            st.caption(explanation)
        return selected if selected else None

    if explanation:
        st.caption(explanation)

    return current_value if current_value else None


def _render_bool_field(
    label: str, value: Optional[bool], field_name: str, required: bool, path: str, explanation: str
) -> Optional[bool]:
    """Render boolean field as Yes/No pill buttons."""
    display_label = f"{label} {'*' if required else '(Optional)'}"

    if path == "remix":
        current_value = "Yes" if value else ("No" if value is False else "(Not set)")
        col1, col2 = st.columns([4, 1])
        with col1:
            st.text(f"**Current:** {current_value}")
        with col2:
            if st.button(f"Change ✏", key=f"btn_change_{field_name}"):
                st.session_state[f"editing_{field_name}"] = True

        if st.session_state.get(f"editing_{field_name}", False):
            st.write(display_label)
            col1, col2 = st.columns(2)
            selected = None
            with col1:
                if st.button("Yes", key=f"pill_{field_name}_yes"):
                    selected = True
            with col2:
                if st.button("No", key=f"pill_{field_name}_no"):
                    selected = False
            if selected is not None:
                st.session_state[f"editing_{field_name}"] = False
                return selected
            return value
    else:
        st.write(display_label)
        col1, col2 = st.columns(2)
        selected = None
        with col1:
            if st.button("Yes", key=f"pill_{field_name}_yes"):
                selected = True
        with col2:
            if st.button("No", key=f"pill_{field_name}_no"):
                selected = False
        if explanation:
            st.caption(explanation)
        return selected if selected is not None else value

    if explanation:
        st.caption(explanation)

    return value


def render_chapter(
    chapter: int,
    spec: DataProductSpec,
    path: str,
    concierge_message: str,
    field_explanations: Dict[str, str],
    valid_options: Dict[str, List[str]],
) -> Tuple[DataProductSpec, str]:
    """
    Render a single chapter of the multi-chapter form.

    Args:
        chapter: Chapter number (1-5)
        spec: Current DataProductSpec
        path: 'remix' or 'create'
        concierge_message: Message to display in concierge bubble
        field_explanations: Dict mapping field names to explanations
        valid_options: Dict mapping field names to lists of valid enum values

    Returns:
        Tuple of (updated_spec, nav_action) where nav_action is 'prev', 'next', or 'submit'
    """
    chapter_data = CHAPTERS[chapter]

    # Scroll to top + focus first field when entering a new chapter
    if st.session_state.pop("_chapter_just_changed", False):
        st.components.v1.html(
            "<script>"
            "try{"
            "  var m=window.parent.document.querySelector('section[data-testid=\"stMain\"] .main')||"
            "         window.parent.document.querySelector('.main');"
            "  if(m) m.scrollTo({top:0,behavior:'smooth'});"
            "  setTimeout(function(){"
            "    var inp=window.parent.document.querySelector("
            "      'input:not([type=checkbox]):not([type=hidden]),textarea');"
            "    if(inp){inp.focus();inp.select();}"
            "  },350);"
            "}catch(e){}"
            "</script>",
            height=0,
        )

    # Snapshot spec at chapter entry to detect field changes for rule triggers
    snapshot_key = f"_chapter_{chapter}_snapshot"
    if snapshot_key not in st.session_state:
        st.session_state[snapshot_key] = spec.model_dump()

    # Show concierge bubble
    st.markdown(
        f'<div class="dpc-concierge">{concierge_message}</div>',
        unsafe_allow_html=True,
    )

    # Show progress bar
    chapter_names = [CHAPTERS[i]["title"] for i in range(1, 6)]
    render_progress_bar(chapter, chapter_names)

    # Chapter heading
    st.markdown(f"## Chapter {chapter}: {chapter_data['title']}")
    st.markdown(f"_{chapter_data['description']}_")

    st.divider()

    # Render fields for this chapter
    for field_name in chapter_data["fields"]:
        current_value = getattr(spec, field_name, None)
        required = field_name in REQUIRED_FIELDS
        explanation = field_explanations.get(field_name, "")

        if field_name == "name":
            spec.name = (
                _render_text_field(
                    "Data Product Name",
                    current_value,
                    field_name,
                    required,
                    path,
                    explanation,
                )
                or spec.name
            )

        elif field_name == "description":
            spec.description = (
                _render_text_field(
                    "Description",
                    current_value,
                    field_name,
                    required,
                    path,
                    explanation,
                    is_multiline=True,
                )
                or spec.description
            )

        elif field_name == "business_purpose":
            spec.business_purpose = (
                _render_text_field(
                    "Business Purpose",
                    current_value,
                    field_name,
                    required,
                    path,
                    explanation,
                    is_multiline=True,
                )
                or spec.business_purpose
            )

        elif field_name == "status":
            options = [e.value for e in StatusEnum]
            spec.status = _render_enum_field(
                "Status",
                current_value,
                field_name,
                required,
                path,
                options,
                explanation,
            )

        elif field_name == "version":
            spec.version = _render_text_field(
                "Version (e.g., 1.0.0)",
                current_value,
                field_name,
                required,
                path,
                explanation,
            )

        elif field_name == "domain":
            spec.domain = _render_text_field(
                "Domain",
                current_value,
                field_name,
                required,
                path,
                explanation,
            )

        elif field_name == "sub_domain":
            spec.sub_domain = _render_text_field(
                "Sub-Domain",
                current_value,
                field_name,
                required,
                path,
                explanation,
            )

        elif field_name == "data_classification":
            options = [e.value for e in DataClassificationEnum]
            spec.data_classification = _render_enum_field(
                "Data Classification",
                current_value,
                field_name,
                required,
                path,
                options,
                explanation,
            )

        elif field_name == "tags":
            spec.tags = _render_multi_select_field(
                "Tags",
                current_value,
                field_name,
                required,
                path,
                valid_options.get("tags", []),
                explanation,
            )

        elif field_name == "data_owner_name":
            spec.data_owner_name = _render_text_field(
                "Data Owner Name",
                current_value,
                field_name,
                required,
                path,
                explanation,
            )

        elif field_name == "data_owner_email":
            spec.data_owner_email = _render_email_field(
                "Data Owner Email",
                current_value,
                field_name,
                required,
                path,
                explanation,
            )

        elif field_name == "data_steward_name":
            spec.data_steward_name = _render_text_field(
                "Data Steward Name",
                current_value,
                field_name,
                required,
                path,
                explanation,
            )

        elif field_name == "data_steward_email":
            spec.data_steward_email = _render_email_field(
                "Data Steward Email",
                current_value,
                field_name,
                required,
                path,
                explanation,
            )

        elif field_name == "certifying_officer_email":
            spec.certifying_officer_email = _render_email_field(
                "Certifying Officer Email",
                current_value,
                field_name,
                required,
                path,
                explanation,
            )

        elif field_name == "last_certified_date":
            spec.last_certified_date = _render_date_field(
                "Last Certified Date",
                current_value,
                field_name,
                required,
                path,
                explanation,
            )

        elif field_name == "regulatory_scope":
            options = [e.value for e in RegulatoryFrameworkEnum]
            spec.regulatory_scope = _render_multi_select_field(
                "Regulatory Scope",
                current_value,
                field_name,
                required,
                path,
                options,
                explanation,
            )

        elif field_name == "geographic_restriction":
            spec.geographic_restriction = _render_multi_select_field(
                "Geographic Restrictions",
                current_value,
                field_name,
                required,
                path,
                valid_options.get("geographic_restriction", []),
                explanation,
            )

        elif field_name == "pii_flag":
            spec.pii_flag = _render_bool_field(
                "Contains PII",
                current_value,
                field_name,
                required,
                path,
                explanation,
            )

        elif field_name == "encryption_standard":
            spec.encryption_standard = _render_text_field(
                "Encryption Standard",
                current_value,
                field_name,
                required,
                path,
                explanation,
            )

        elif field_name == "retention_period":
            spec.retention_period = _render_text_field(
                "Retention Period",
                current_value,
                field_name,
                required,
                path,
                explanation,
            )

        elif field_name == "source_systems":
            spec.source_systems = _render_multi_select_field(
                "Source Systems",
                current_value,
                field_name,
                required,
                path,
                valid_options.get("source_systems", []),
                explanation,
            )

        elif field_name == "update_frequency":
            options = [e.value for e in UpdateFrequencyEnum]
            spec.update_frequency = _render_enum_field(
                "Update Frequency",
                current_value,
                field_name,
                required,
                path,
                options,
                explanation,
            )

        elif field_name == "schema_location":
            spec.schema_location = _render_text_field(
                "Schema Location",
                current_value,
                field_name,
                required,
                path,
                explanation,
            )

        elif field_name == "access_level":
            options = [e.value for e in AccessLevelEnum]
            spec.access_level = _render_enum_field(
                "Access Level",
                current_value,
                field_name,
                required,
                path,
                options,
                explanation,
            )

        elif field_name == "consumer_teams":
            spec.consumer_teams = _render_multi_select_field(
                "Consumer Teams",
                current_value,
                field_name,
                required,
                path,
                valid_options.get("consumer_teams", []),
                explanation,
            )

        elif field_name == "sla_tier":
            options = [e.value for e in SLATierEnum]
            spec.sla_tier = _render_enum_field(
                "SLA Tier",
                current_value,
                field_name,
                required,
                path,
                options,
                explanation,
            )

        elif field_name == "business_criticality":
            options = [e.value for e in BusinessCriticalityEnum]
            spec.business_criticality = _render_enum_field(
                "Business Criticality",
                current_value,
                field_name,
                required,
                path,
                options,
                explanation,
            )

        elif field_name == "cost_centre":
            spec.cost_centre = _render_text_field(
                "Cost Centre",
                current_value,
                field_name,
                required,
                path,
                explanation,
            )

        elif field_name == "related_reports":
            spec.related_reports = _render_multi_select_field(
                "Related Reports",
                current_value,
                field_name,
                required,
                path,
                valid_options.get("related_reports", []),
                explanation,
            )

        # ── Collibra registration fields ──────────────────────────────────────
        elif field_name == "asset_type":
            options = ["Data Product", "Data Set", "Report", "API", "Stream", "ML Model"]
            spec.asset_type = _render_enum_field(
                "Asset Type (Collibra)",
                current_value,
                field_name,
                required,
                path,
                options,
                explanation,
            )

        elif field_name == "collibra_community":
            spec.collibra_community = _render_text_field(
                "Collibra Community",
                current_value,
                field_name,
                required,
                path,
                explanation,
            )

        # ── Governance cadence fields ─────────────────────────────────────────
        elif field_name == "review_cycle":
            options = ["Annual", "Semi-Annual", "Quarterly", "Monthly"]
            spec.review_cycle = _render_enum_field(
                "Review / Recertification Cycle",
                current_value,
                field_name,
                required,
                path,
                options,
                explanation,
            )

        elif field_name == "incident_contact":
            spec.incident_contact = _render_email_field(
                "Incident / On-Call Contact Email",
                current_value,
                field_name,
                required,
                path,
                explanation,
            )

        # ── Snowflake build fields ────────────────────────────────────────────
        elif field_name == "materialization_type":
            options = ["Table", "View", "Materialized View", "Dynamic Table", "External Table"]
            spec.materialization_type = _render_enum_field(
                "Snowflake Materialization Type",
                current_value,
                field_name,
                required,
                path,
                options,
                explanation,
            )

        elif field_name == "snowflake_role":
            spec.snowflake_role = _render_text_field(
                "Snowflake Role (SELECT grant)",
                current_value,
                field_name,
                required,
                path,
                explanation,
            )

        elif field_name == "refresh_cron":
            spec.refresh_cron = _render_text_field(
                "Refresh Schedule (cron expression)",
                current_value,
                field_name,
                required,
                path,
                explanation,
            )

        elif field_name == "column_definitions":
            # column_definitions is List[str] — render as a single multiline textarea
            raw = "\n".join(current_value) if current_value else ""
            new_raw = _render_text_field(
                "Column Definitions (one column per line, e.g. ISSUER_ID VARCHAR NOT NULL)",
                raw or None,
                field_name,
                required,
                path,
                explanation,
                is_multiline=True,
            )
            if new_raw:
                spec.column_definitions = [line.strip() for line in new_raw.split("\n") if line.strip()]

        elif field_name == "sample_query":
            spec.sample_query = _render_text_field(
                "Sample Query",
                current_value,
                field_name,
                required,
                path,
                explanation,
                is_multiline=True,
            )

        elif field_name == "lineage_upstream":
            raw = "\n".join(current_value) if current_value else ""
            new_raw = _render_text_field(
                "Upstream Dependencies (one per line)",
                raw or None,
                field_name,
                required,
                path,
                explanation,
                is_multiline=True,
            )
            if new_raw:
                spec.lineage_upstream = [line.strip() for line in new_raw.split("\n") if line.strip()]

        elif field_name == "lineage_downstream":
            raw = "\n".join(current_value) if current_value else ""
            new_raw = _render_text_field(
                "Downstream Consumers (one per line)",
                raw or None,
                field_name,
                required,
                path,
                explanation,
                is_multiline=True,
            )
            if new_raw:
                spec.lineage_downstream = [line.strip() for line in new_raw.split("\n") if line.strip()]

        # ── Access & delivery ─────────────────────────────────────────────────
        elif field_name == "delivery_method":
            options = ["SQL Table", "SQL View", "REST API", "Kafka Topic", "File Export (S3/ADLS)", "GraphQL API"]
            spec.delivery_method = _render_enum_field(
                "Delivery Method",
                current_value,
                field_name,
                required,
                path,
                options,
                explanation,
            )

        st.divider()

    # ── Field interdependency suggestions ────────────────────────────────────
    prev_snap = st.session_state.get(f"_chapter_{chapter}_snapshot", {})
    active_suggestions = []
    for field_name in chapter_data["fields"]:
        new_val = getattr(spec, field_name, None)
        old_val = prev_snap.get(field_name)
        if new_val != old_val and new_val is not None:
            rules = _get_field_rules(field_name, new_val)
            for r in rules:
                active_suggestions.append({**r, "_trigger_field": field_name})
    if active_suggestions:
        st.markdown("---")
        spec = _render_suggestions(active_suggestions, spec)
    # Update snapshot after rendering
    st.session_state[f"_chapter_{chapter}_snapshot"] = spec.model_dump()

    # Navigation buttons
    st.markdown('<div style="margin-top:1.5rem;"></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])

    nav_action = None

    with col1:
        if chapter > 1:
            if st.button(
                "← Previous",
                use_container_width=True,
                key=f"ch_{chapter}_prev",
            ):
                nav_action = "prev"

    with col2:
        # Chapter position indicator — centred, no interaction
        fields_here = CHAPTERS[chapter]["fields"]
        required_here = [f for f in fields_here if f in REQUIRED_FIELDS]
        filled_here = [
            f for f in required_here
            if getattr(spec, f, None) not in (None, "", [])
        ]
        all_done = len(filled_here) == len(required_here) if required_here else True
        dot = "✓" if all_done else f"{len(filled_here)}/{len(required_here)}"
        color = "#00C48C" if all_done else "#F5A623"
        st.markdown(
            f'<div style="text-align:center;padding:.4rem 0;">'
            f'<span style="font-size:.7rem;color:var(--text-muted);text-transform:uppercase;'
            f'letter-spacing:.1em;">Chapter {chapter} of 5</span><br>'
            f'<span style="font-size:.8rem;font-weight:600;color:{color};">'
            f'{dot} required fields</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col3:
        if chapter < 5:
            if st.button(
                "Looks good → next",
                use_container_width=True,
                type="primary",
                key=f"ch_{chapter}_next",
            ):
                nav_action = "next"
        else:
            if st.button(
                "Review & Submit →",
                use_container_width=True,
                type="primary",
                key=f"ch_{chapter}_submit",
            ):
                nav_action = "submit"

    return spec, nav_action or "stay"
