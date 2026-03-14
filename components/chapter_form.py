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
from typing import Dict, List, Tuple
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
        "fields": ["domain", "sub_domain", "data_classification", "tags"],
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
            "cost_centre",
            "related_reports",
        ],
    },
}


def render_progress_bar(current_chapter: int, chapter_names: List[str]):
    """
    Renders a 5-circle progress bar with connecting line.

    Args:
        current_chapter: Current chapter (1-5)
        chapter_names: List of chapter titles
    """
    html = '<div class="dpc-progress">'

    for i, name in enumerate(chapter_names, 1):
        if i < current_chapter:
            status = "complete"
            icon = "✓"
        elif i == current_chapter:
            status = "active"
            icon = str(i)
        else:
            status = "inactive"
            icon = str(i)

        html += f"""
        <div class="dpc-progress-step {status}">
            <div class="dpc-progress-circle">{icon if status != 'complete' else ''}</div>
            <div class="dpc-progress-label">{name}</div>
        </div>
        """

    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def _validate_email(email: str) -> bool:
    """Simple email validation."""
    if not email:
        return False
    return "@" in email and "." in email.split("@")[1]


def _render_text_field(
    label: str,
    value: str | None,
    field_name: str,
    required: bool,
    path: str,
    explanation: str,
    is_multiline: bool = False,
) -> str | None:
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
    label: str, value: str | None, field_name: str, required: bool, path: str, explanation: str
) -> str | None:
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
    label: str, value: date_type | None, field_name: str, required: bool, path: str, explanation: str
) -> date_type | None:
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
    value: str | None,
    field_name: str,
    required: bool,
    path: str,
    valid_options: List[str],
    explanation: str,
) -> str | None:
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
            cols = st.columns(min(len(valid_options), 3))
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
        cols = st.columns(min(len(valid_options), 3))
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
    value: List[str] | None,
    field_name: str,
    required: bool,
    path: str,
    valid_options: List[str],
    explanation: str,
) -> List[str] | None:
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
            cols = st.columns(min(len(valid_options), 3))
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
        cols = st.columns(min(len(valid_options), 3))
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
    label: str, value: bool | None, field_name: str, required: bool, path: str, explanation: str
) -> bool | None:
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

        st.divider()

    # Navigation buttons
    col1, col2, col3 = st.columns([1, 2, 1])

    nav_action = None

    with col1:
        if chapter > 1:
            if st.button("← Previous chapter", use_container_width=True):
                nav_action = "prev"

    with col3:
        if chapter < 5:
            if st.button("Looks good → next chapter", use_container_width=True):
                nav_action = "next"
        else:
            if st.button("Review & Submit →", use_container_width=True):
                nav_action = "submit"

    return spec, nav_action or "stay"
