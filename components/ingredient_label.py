"""
Ingredient label component for Data Product Concierge.

Renders full data product specification as detailed ingredient label with
governance metadata, technical specs, regulatory info, and action buttons.
Production-ready with zero mock data.
"""

import math
from typing import Optional

import streamlit as st

from models.data_product import DataProductSpec


def _render_data_quality_gauge(score: Optional[float]) -> str:
    """
    Render large circular SVG gauge for data quality score.

    Args:
        score: Quality score 0-100, or None for "Not measured"

    Returns:
        SVG HTML string with gauge visualization
    """
    if score is None:
        return """
        <div class="dpc-gauge-container" style="margin: 2rem auto;">
            <svg class="dpc-gauge-svg" viewBox="0 0 200 200">
                <circle class="dpc-gauge-background" cx="100" cy="100" r="80"></circle>
            </svg>
            <div class="dpc-gauge-number" style="font-size: 48px; color: var(--text-muted);">–</div>
            <div class="dpc-gauge-label">Not measured</div>
        </div>
        """

    # Determine color class
    if score < 60:
        color_class = "score-0-59"
    elif score < 80:
        color_class = "score-60-79"
    else:
        color_class = "score-80-100"

    # SVG gauge calculation
    radius = 80
    circumference = 2 * math.pi * radius
    arc_degrees = (score / 100) * 270
    arc_radians = math.radians(arc_degrees)
    offset = circumference - (arc_radians / (2 * math.pi)) * circumference

    return f"""
    <div class="dpc-gauge-container" style="margin: 2rem auto;">
        <svg class="dpc-gauge-svg" viewBox="0 0 200 200">
            <circle class="dpc-gauge-background" cx="100" cy="100" r="80"></circle>
            <circle
                class="dpc-gauge-progress {color_class}"
                cx="100"
                cy="100"
                r="80"
                style="transform: rotate(-90deg); transform-origin: 100px 100px; stroke-dasharray: {circumference}; stroke-dashoffset: {offset};"
            ></circle>
        </svg>
        <div class="dpc-gauge-number">{int(score)}</div>
        <div class="dpc-gauge-label">Data Quality</div>
    </div>
    """


def _render_ingredient_field(label: str, value: Optional[str], is_code: bool = False) -> str:
    """
    Render a single ingredient label field row.

    Args:
        label: Field label (bold, left-aligned)
        value: Field value (right-aligned), or "Not recorded" if None
        is_code: If True, use monospace font

    Returns:
        HTML string for field row
    """
    if value is None or (isinstance(value, str) and value.strip() == ""):
        value_html = '<span style="color: var(--text-muted); font-style: italic;">Not recorded</span>'
    else:
        font_class = "text-code" if is_code else ""
        value_html = f'<span class="{font_class}">{value}</span>'

    return f"""
    <div class="dpc-ingredient-field">
        <span class="dpc-ingredient-label">{label}</span>
        <span class="dpc-ingredient-value">{value_html}</span>
    </div>
    """


def _render_ingredient_section(section_title: str, fields_html: str) -> str:
    """
    Render an ingredient label section with header and fields.

    Args:
        section_title: Section title (all caps, teal color)
        fields_html: Pre-rendered HTML of field rows

    Returns:
        HTML string for complete section
    """
    return f"""
    <div class="dpc-ingredient-section">
        <span class="dpc-ingredient-header">{section_title}</span>
        {fields_html}
    </div>
    """


def render(
    spec: DataProductSpec,
    concierge_message: str,
) -> Optional[str]:
    """
    Render full ingredient-label view of a data product (Path A: Reuse).

    Args:
        spec: DataProductSpec with all governance and technical metadata
        concierge_message: Message from concierge to display at top

    Returns:
        str: Action selected by user ('email', 'copy', 'remix'), or None if no action taken
    """

    # Concierge bubble
    concierge_html = f"""
    <div class="dpc-concierge">
        {concierge_message}
    </div>
    """
    st.markdown(concierge_html, unsafe_allow_html=True)

    # Header with asset name + status badge + Collibra link
    status_class = f"dpc-status-{spec.status.lower()}" if spec.status else "dpc-status-draft"
    status_text = spec.status or "Draft"
    status_badge = f'<span class="dpc-status {status_class}">{status_text}</span>' if spec.status else ""
    collibra_link = f'<a href="https://collibra.example.com/assets/{spec.id}" target="_blank" style="font-size: 14px; color: var(--teal); text-decoration: none;">🔗 View in Collibra</a>' if spec.id else ""

    header_html = f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; flex-wrap: wrap;">
        <div>
            <h2 style="margin: 0; font-size: 36px; color: var(--text-primary);">
                {spec.name}
            </h2>
        </div>
        <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
            {status_badge}
            {collibra_link}
        </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

    # Build ingredient label container
    ingredient_sections = []

    # ===== SECTION: OVERVIEW =====
    overview_fields = []
    overview_fields.append(_render_ingredient_field("Name", spec.name))
    overview_fields.append(_render_ingredient_field("Description", spec.description))
    overview_fields.append(_render_ingredient_field("Business Purpose", spec.business_purpose))
    if spec.version:
        overview_fields.append(_render_ingredient_field("Version", spec.version))
    ingredient_sections.append(_render_ingredient_section(
        "OVERVIEW",
        "".join(overview_fields),
    ))

    # ===== SECTION: CLASSIFICATION =====
    classification_fields = []
    if spec.domain:
        classification_fields.append(_render_ingredient_field("Domain", spec.domain))
    if spec.sub_domain:
        classification_fields.append(_render_ingredient_field("Sub-Domain", spec.sub_domain))
    if spec.data_classification:
        classification_fields.append(_render_ingredient_field(
            "Data Classification",
            spec.data_classification,
        ))
    if spec.tags:
        tags_str = ", ".join(spec.tags)
        classification_fields.append(_render_ingredient_field("Tags", tags_str))
    if classification_fields:
        ingredient_sections.append(_render_ingredient_section(
            "CLASSIFICATION",
            "".join(classification_fields),
        ))

    # ===== SECTION: GOVERNANCE =====
    governance_fields = []
    if spec.data_owner_name:
        owner_str = spec.data_owner_name
        if spec.data_owner_email:
            owner_str += f" ({spec.data_owner_email})"
        governance_fields.append(_render_ingredient_field("Data Owner", owner_str))
    if spec.data_steward_name:
        steward_str = spec.data_steward_name
        if spec.data_steward_email:
            steward_str += f" ({spec.data_steward_email})"
        governance_fields.append(_render_ingredient_field("Data Steward", steward_str))
    if spec.certifying_officer_email:
        governance_fields.append(_render_ingredient_field(
            "Certifying Officer",
            spec.certifying_officer_email,
        ))
    if spec.last_certified_date:
        governance_fields.append(_render_ingredient_field(
            "Certification Date",
            spec.last_certified_date.isoformat(),
        ))
    if governance_fields:
        ingredient_sections.append(_render_ingredient_section(
            "GOVERNANCE",
            "".join(governance_fields),
        ))

    # ===== SECTION: REGULATORY & COMPLIANCE =====
    regulatory_fields = []
    if spec.regulatory_scope:
        scope_str = ", ".join(spec.regulatory_scope)
        regulatory_fields.append(_render_ingredient_field("Regulatory Scope", scope_str))
    if spec.geographic_restriction:
        geo_str = ", ".join(spec.geographic_restriction)
        regulatory_fields.append(_render_ingredient_field("Geographic Restrictions", geo_str))
    if spec.pii_flag is not None:
        pii_str = "Yes" if spec.pii_flag else "No"
        regulatory_fields.append(_render_ingredient_field("Contains PII", pii_str))
    if spec.encryption_standard:
        regulatory_fields.append(_render_ingredient_field(
            "Encryption Standard",
            spec.encryption_standard,
        ))
    if spec.retention_period:
        regulatory_fields.append(_render_ingredient_field(
            "Retention Period",
            spec.retention_period,
        ))
    if regulatory_fields:
        ingredient_sections.append(_render_ingredient_section(
            "REGULATORY & COMPLIANCE",
            "".join(regulatory_fields),
        ))

    # ===== SECTION: TECHNICAL =====
    technical_fields = []
    if spec.source_systems:
        sources_str = ", ".join(spec.source_systems)
        technical_fields.append(_render_ingredient_field("Source Systems", sources_str))
    if spec.update_frequency:
        technical_fields.append(_render_ingredient_field(
            "Update Frequency",
            spec.update_frequency,
        ))
    if spec.schema_location:
        technical_fields.append(_render_ingredient_field(
            "Schema Location",
            spec.schema_location,
            is_code=True,
        ))
    if spec.sample_query:
        # For sample query, use code block instead of inline
        technical_fields.append(_render_ingredient_field(
            "Sample Query",
            spec.sample_query[:100] + ("..." if len(spec.sample_query) > 100 else ""),
            is_code=True,
        ))
    if spec.lineage_upstream:
        upstream_str = ", ".join(spec.lineage_upstream)
        technical_fields.append(_render_ingredient_field("Upstream Dependencies", upstream_str))
    if spec.lineage_downstream:
        downstream_str = ", ".join(spec.lineage_downstream)
        technical_fields.append(_render_ingredient_field("Downstream Consumers", downstream_str))
    if technical_fields:
        ingredient_sections.append(_render_ingredient_section(
            "TECHNICAL",
            "".join(technical_fields),
        ))

    # ===== SECTION: ACCESS & CONSUMERS =====
    access_fields = []
    if spec.access_level:
        access_fields.append(_render_ingredient_field("Access Level", spec.access_level))
    if spec.consumer_teams:
        teams_str = ", ".join(spec.consumer_teams)
        access_fields.append(_render_ingredient_field("Consumer Teams", teams_str))
    if spec.sla_tier:
        access_fields.append(_render_ingredient_field("SLA Tier", spec.sla_tier))
    if access_fields:
        ingredient_sections.append(_render_ingredient_section(
            "ACCESS & CONSUMERS",
            "".join(access_fields),
        ))

    # ===== SECTION: BUSINESS =====
    business_fields = []
    if spec.business_criticality:
        business_fields.append(_render_ingredient_field(
            "Business Criticality",
            spec.business_criticality,
        ))
    if spec.cost_centre:
        business_fields.append(_render_ingredient_field("Cost Centre", spec.cost_centre))
    if spec.related_reports:
        reports_str = ", ".join(spec.related_reports)
        business_fields.append(_render_ingredient_field("Related Reports", reports_str))
    if business_fields:
        ingredient_sections.append(_render_ingredient_section(
            "BUSINESS",
            "".join(business_fields),
        ))

    # Render ingredient label container
    ingredient_html = f"""
    <div class="dpc-ingredient">
        {''.join(ingredient_sections)}
    </div>
    """
    st.markdown(ingredient_html, unsafe_allow_html=True)

    # Data quality gauge
    if spec.data_quality_score is not None:
        st.markdown(
            _render_data_quality_gauge(spec.data_quality_score),
            unsafe_allow_html=True,
        )

    # Full sample query in expander (if exists)
    if spec.sample_query:
        with st.expander("📋 View full sample query"):
            st.code(spec.sample_query, language="sql")

    # Action buttons section
    st.divider()

    action_html = """
    <div style="text-align: center; margin: 2rem 0 1rem;">
        <h4 style="color: var(--text-primary); font-size: 18px; margin-bottom: 1rem;">
            What would you like to do?
        </h4>
    </div>
    """
    st.markdown(action_html, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    action = None

    with col1:
        if st.button(
            "✉ Email the Data Owner",
            use_container_width=True,
            key="action_email",
        ):
            action = "email"

    with col2:
        if st.button(
            "📋 Copy access request template",
            use_container_width=True,
            key="action_copy",
        ):
            action = "copy"

    with col3:
        if st.button(
            "✂ Actually, I need to adapt this",
            use_container_width=True,
            key="action_remix",
        ):
            action = "remix"

    return action
