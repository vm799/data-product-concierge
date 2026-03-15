"""
Ingredient label component for Data Product Concierge.

Renders full data product specification as detailed ingredient label with
governance metadata, technical specs, regulatory info, and action buttons.
Production-ready with zero mock data.
"""

import os
from typing import Optional

import streamlit as st

from models.data_product import DataProductSpec



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
        value_html = '<span style="color: var(--text-3); font-weight: 400;">—</span>'
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
    st.html(concierge_html)

    # Header with asset name + status badge + Collibra link
    status_class = f"dpc-status-{spec.status.lower()}" if spec.status else "dpc-status-draft"
    status_text = spec.status or "Draft"
    status_badge = f'<span class="dpc-status {status_class}">{status_text}</span>' if spec.status else ""
    _collibra_base = os.getenv("COLLIBRA_BASE_URL", "").rstrip("/")
    collibra_link = (
        f'<a href="{_collibra_base}/assets/{spec.id}" target="_blank" '
        f'style="font-size: 14px; color: var(--teal); text-decoration: none;">🔗 View in Collibra</a>'
    ) if spec.id and _collibra_base else ""

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
    st.html(header_html)

    # Build ingredient label container
    ingredient_sections = []

    # ===== SECTION: OVERVIEW =====
    overview_fields = []
    if spec.name:
        overview_fields.append(_render_ingredient_field("Name", spec.name))
    if spec.description:
        overview_fields.append(_render_ingredient_field("Description", spec.description))
    if spec.business_purpose:
        overview_fields.append(_render_ingredient_field("Business Purpose", spec.business_purpose))
    if spec.business_capability:
        overview_fields.append(_render_ingredient_field("Business Capability", spec.business_capability))
    if spec.version:
        overview_fields.append(_render_ingredient_field("Version", spec.version))
    if spec.release_notes:
        overview_fields.append(_render_ingredient_field("Release Notes", spec.release_notes))
    if spec.business_terms:
        overview_fields.append(_render_ingredient_field("Business Terms", ", ".join(spec.business_terms)))
    if overview_fields:
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
    if spec.data_domain_owner_email:
        governance_fields.append(_render_ingredient_field("Domain Owner", spec.data_domain_owner_email))
    if spec.data_custodian_email:
        governance_fields.append(_render_ingredient_field("Data Custodian", spec.data_custodian_email))
    if spec.governing_body:
        governance_fields.append(_render_ingredient_field("Governing Body", spec.governing_body))
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
    if spec.expected_release_date:
        governance_fields.append(_render_ingredient_field(
            "Expected Release",
            spec.expected_release_date.isoformat(),
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
    if spec.data_sovereignty_flag is not None:
        sov_str = "Yes" if spec.data_sovereignty_flag else "No"
        regulatory_fields.append(_render_ingredient_field("Data Sovereignty Applies", sov_str))
    if spec.data_sovereignty_details:
        regulatory_fields.append(_render_ingredient_field(
            "Sovereignty Details", spec.data_sovereignty_details
        ))
    if spec.data_licensing_flag is not None:
        lic_str = "Yes" if spec.data_licensing_flag else "No"
        regulatory_fields.append(_render_ingredient_field("Licensing Restrictions", lic_str))
    if spec.data_licensing_details:
        regulatory_fields.append(_render_ingredient_field(
            "Licensing Details", spec.data_licensing_details
        ))
    if spec.pii_flag is not None:
        pii_str = "Yes" if spec.pii_flag else "No"
        regulatory_fields.append(_render_ingredient_field("Contains PII", pii_str))
    if spec.data_subject_areas:
        regulatory_fields.append(_render_ingredient_field(
            "Data Subject Areas", ", ".join(spec.data_subject_areas)
        ))
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
    if spec.access_procedure:
        regulatory_fields.append(_render_ingredient_field(
            "Access Procedure",
            spec.access_procedure,
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
    if spec.target_systems:
        technical_fields.append(_render_ingredient_field(
            "Target Systems", ", ".join(spec.target_systems)
        ))
    if spec.target_dpro:
        technical_fields.append(_render_ingredient_field(
            "Target DPRO", spec.target_dpro, is_code=True
        ))
    if spec.critical_data_elements:
        technical_fields.append(_render_ingredient_field(
            "Critical Data Elements", ", ".join(spec.critical_data_elements)
        ))
    if spec.data_latency:
        technical_fields.append(_render_ingredient_field("Data Latency", spec.data_latency))
    if spec.data_history_from:
        technical_fields.append(_render_ingredient_field(
            "Historical Data From", spec.data_history_from.isoformat()
        ))
    if spec.data_publishing_time:
        technical_fields.append(_render_ingredient_field("Publishing Time", spec.data_publishing_time))
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
    st.html(ingredient_html)

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
    st.html(action_html)

    action = None

    # Primary actions — equal 2-col row
    col1, col2 = st.columns(2, gap="small")

    with col1:
        if st.button(
            "✉ Email the Data Owner",
            use_container_width=True,
            type="primary",
            key="action_email",
        ):
            action = "email"

    with col2:
        if st.button(
            "✂ Adapt this product",
            use_container_width=True,
            type="secondary",
            key="action_remix",
        ):
            action = "remix"

    # Secondary action — full width, clearly subordinate
    if st.button(
        "📋 View access request template",
        use_container_width=True,
        key="action_copy",
    ):
        owner_email = spec.data_owner_email or "data-owner@company.com"
        product_name = spec.name or "this data product"
        template = (
            f"To: {owner_email}\n"
            f"Subject: Access Request — {product_name}\n\n"
            f"Hi,\n\n"
            f"I would like to request access to the '{product_name}' data product "
            f"(Domain: {spec.domain or 'TBC'}, Classification: {spec.data_classification or 'TBC'}).\n\n"
            f"Intended use: [please describe your use case]\n"
            f"Team / cost centre: [your team name]\n"
            f"Required by: [date]\n\n"
            f"Thank you"
        )
        st.code(template, language=None)
        action = "copy"

    return action
