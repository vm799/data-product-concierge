"""
Production-ready handoff/summary screen component for Data Product Concierge.

Renders the completion dashboard before submission with:
- Section A: Completion dashboard with circular gauge and field status
- Section B: Full markdown specification preview
- Section C: Three export options (Markdown, Collibra JSON, Snowflake CSV)
- Section D: Action buttons (Submit or Go Back)

Also includes completion/success screen with animated checkmark and reference info.

No mock data. Production-ready.
"""

import streamlit as st
import json
from datetime import date
from typing import Optional
from models.data_product import DataProductSpec


def _render_completion_gauge(percentage: float) -> str:
    """
    Generate SVG circular gauge for completion percentage.

    Args:
        percentage: Completion percentage (0-100)

    Returns:
        HTML string with SVG gauge
    """
    # SVG configuration
    cx, cy = 100, 100
    radius = 90
    circumference = 2 * 3.14159 * radius
    offset = circumference * (1 - percentage / 100)

    # Determine color based on percentage
    if percentage >= 80:
        color = "#00C48C"  # emerald
    elif percentage >= 60:
        color = "#F5A623"  # gold
    else:
        color = "#E8384D"  # crimson

    html = f"""
    <div class="dpc-gauge-container">
        <svg class="dpc-gauge-svg" viewBox="0 0 200 200">
            <circle
                class="dpc-gauge-background"
                cx="{cx}"
                cy="{cy}"
                r="{radius}"
            />
            <circle
                class="dpc-gauge-progress score-{int(percentage//20)*20}-{int((percentage//20)*20)+19}"
                cx="{cx}"
                cy="{cy}"
                r="{radius}"
                style="stroke-dasharray: {circumference}; stroke-dashoffset: {offset}; stroke: {color};"
            />
        </svg>
        <div class="dpc-gauge-number">{int(percentage)}%</div>
        <div class="dpc-gauge-label">Complete</div>
    </div>
    """
    return html


def render_approval_timeline(current_stage: str = "business_review") -> None:
    """
    Render a horizontal approval workflow timeline showing the 5 governance stages.

    Args:
        current_stage: One of 'draft', 'business_review', 'tech_validation',
                       'governance_approval', 'published'
    """
    stages = [
        ("draft",               "📝", "Draft",               "Business user creating spec"),
        ("business_review",     "👤", "Business Review",     "Data owner approves governance"),
        ("tech_validation",     "🔧", "Tech Validation",     "Engineer builds in Snowflake"),
        ("governance_approval", "✅", "Governance Approval", "Data steward certifies"),
        ("published",           "🌐", "Published",           "Live in Collibra catalogue"),
    ]
    stage_ids = [s[0] for s in stages]
    try:
        current_idx = stage_ids.index(current_stage)
    except ValueError:
        current_idx = 1  # default to business_review

    # Build HTML timeline
    items_html = ""
    for i, (sid, icon, label, desc) in enumerate(stages):
        if i < current_idx:
            # Completed
            circle_bg = "#00C48C"
            circle_color = "#fff"
            circle_content = "✓"
            label_color = "#00C48C"
            connector_color = "#00C48C"
        elif i == current_idx:
            # Current
            circle_bg = "#0D1B2A"
            circle_color = "#fff"
            circle_content = icon
            label_color = "#0D1B2A"
            connector_color = "rgba(13,27,42,0.12)"
        else:
            # Future
            circle_bg = "rgba(13,27,42,0.08)"
            circle_color = "#8C9BAA"
            circle_content = str(i + 1)
            label_color = "#8C9BAA"
            connector_color = "rgba(13,27,42,0.08)"

        # Connector line (not on last item)
        connector = ""
        if i < len(stages) - 1:
            next_done = (i + 1) <= current_idx
            conn_color = "#00C48C" if next_done else "rgba(13,27,42,0.12)"
            connector = (
                f'<div style="flex:1;height:2px;background:{conn_color};'
                f'margin-top:18px;margin-left:4px;margin-right:4px;"></div>'
            )

        # Current stage gets a pulsing ring
        ring = ""
        if i == current_idx:
            ring = "box-shadow:0 0 0 4px rgba(0,194,203,0.25);"

        items_html += (
            f'<div style="display:flex;flex-direction:column;align-items:center;flex:1;min-width:0;">'
            f'  <div style="display:flex;align-items:center;width:100%;">'
            f'    <div style="display:flex;flex-direction:column;align-items:center;flex:1;">'
            f'      <div style="width:36px;height:36px;border-radius:50%;background:{circle_bg};'
            f'color:{circle_color};display:flex;align-items:center;justify-content:center;'
            f'font-size:14px;font-weight:700;flex-shrink:0;{ring}">{circle_content}</div>'
            f'      <div style="font-size:.72rem;font-weight:600;color:{label_color};'
            f'text-align:center;margin-top:.35rem;text-transform:uppercase;letter-spacing:.04em;'
            f'line-height:1.2;">{label}</div>'
            f'    </div>'
            f'    {connector}'
            f'  </div>'
            f'</div>'
        )

    st.markdown(
        f'<div style="margin:1.5rem 0;">'
        f'  <p style="color:var(--text-secondary);font-size:.75rem;font-weight:600;'
        f'  text-transform:uppercase;letter-spacing:.1em;margin-bottom:.75rem;">Approval Workflow</p>'
        f'  <div style="display:flex;align-items:flex-start;gap:0;">{items_html}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_team_assignment(spec: "DataProductSpec") -> None:
    """
    Render a team assignment panel for notifying collaborators.

    Allows selecting a role (Data Owner, Tech Team, Data Steward, Compliance),
    entering a recipient email, and composing a pre-filled assignment email.
    Tracks sent assignments in session_state.

    Args:
        spec: The current DataProductSpec.
    """
    from urllib.parse import quote
    import streamlit as st

    st.markdown(
        '<p style="color:var(--text-secondary);font-size:.75rem;font-weight:600;'
        'text-transform:uppercase;letter-spacing:.1em;margin-bottom:.75rem;">📨 Assign to Team Member</p>',
        unsafe_allow_html=True,
    )

    # Role presets — email pre-fill and body template
    role_options = ["Data Owner", "Tech Team / Data Engineer", "Data Steward", "Compliance Officer"]
    selected_role = st.radio(
        "Recipient role",
        role_options,
        horizontal=True,
        key="assign_role_radio",
        label_visibility="collapsed",
    )

    # Pre-fill recipient email based on role + spec
    default_email = ""
    body_context = ""
    if selected_role == "Data Owner":
        default_email = spec.data_owner_email or ""
        body_context = (
            f"As the nominated Data Owner for '{spec.name or 'this data product'}', "
            f"please review and confirm the governance details in the attached specification. "
            f"Key fields for your attention: Data Classification ({spec.data_classification or 'TBC'}), "
            f"Regulatory Scope ({', '.join(spec.regulatory_scope or []) or 'TBC'}), "
            f"and Retention Period ({spec.retention_period or 'TBC'})."
        )
    elif "Tech" in selected_role:
        default_email = ""
        missing_tech = [f for f in ["schema_location", "materialization_type", "snowflake_role", "column_definitions"] if not getattr(spec, f, None)]
        body_context = (
            f"Please complete the technical specification for '{spec.name or 'this data product'}'. "
            f"The following fields still need your input: {', '.join(missing_tech) if missing_tech else 'all technical fields are populated — please review and validate'}. "
            f"Schema location target: {spec.schema_location or 'TBC'}. "
            f"Source systems: {', '.join(spec.source_systems or []) or 'TBC'}."
        )
    elif selected_role == "Data Steward":
        default_email = spec.data_steward_email or ""
        body_context = (
            f"As Data Steward for '{spec.name or 'this data product'}', "
            f"please review the data quality standards, lineage documentation, and certify the specification. "
            f"Data Quality Score: {spec.data_quality_score or 'Not yet measured'}. "
            f"Upstream dependencies: {', '.join(spec.lineage_upstream or []) or 'TBC'}."
        )
    elif selected_role == "Compliance":
        default_email = spec.certifying_officer_email or ""
        body_context = (
            f"Please review '{spec.name or 'this data product'}' for regulatory compliance. "
            f"Regulatory scope: {', '.join(spec.regulatory_scope or []) or 'TBC'}. "
            f"PII flag: {'Yes' if spec.pii_flag else 'No' if spec.pii_flag is False else 'TBC'}. "
            f"Geographic restrictions: {', '.join(spec.geographic_restriction or []) or 'None'}."
        )

    recipient = st.text_input(
        "Recipient email",
        value=default_email,
        placeholder="colleague@company.com",
        key="assign_recipient_email",
    )

    # Build full email body
    product_name = spec.name or "New Data Product"
    completion = spec.completion_percentage() if hasattr(spec, "completion_percentage") else 0
    subject = f"Action Required: Data Product Specification — {product_name}"
    body = (
        f"Hi,\n\n"
        f"{body_context}\n\n"
        f"Current specification completion: {completion:.0f}%\n\n"
        f"Please review the attached specification and complete your assigned fields. "
        f"Once complete, return this to the requesting analyst or submit directly via the Data Product Concierge.\n\n"
        f"Product: {product_name}\n"
        f"Domain: {spec.domain or 'TBC'}\n"
        f"Classification: {spec.data_classification or 'TBC'}\n\n"
        f"Thank you,\nData Governance Team"
    )

    # Preview (collapsed by default)
    with st.expander("Preview email body", expanded=False):
        st.text(body)

    # Send button (opens default email client via mailto)
    if recipient and "@" in recipient:
        mailto_url = f"mailto:{quote(recipient)}?subject={quote(subject)}&body={quote(body)}"
        col1, col2 = st.columns([2, 1])
        with col1:
            st.link_button(
                f"📧 Open email to {selected_role}",
                url=mailto_url,
                use_container_width=True,
            )
        with col2:
            # Track assignment in session_state
            if st.button("✓ Mark as sent", key="mark_sent_btn", use_container_width=True):
                if "assignments" not in st.session_state:
                    st.session_state.assignments = []
                from datetime import datetime
                st.session_state.assignments.append({
                    "role": selected_role,
                    "email": recipient,
                    "ts": datetime.now().strftime("%d %b %H:%M"),
                    "product": product_name,
                })
                st.success(f"Marked as sent to {recipient}")
    else:
        st.caption("Enter a recipient email to compose the assignment email.")

    # Show previous assignments this session
    assignments = st.session_state.get("assignments", [])
    if assignments:
        st.markdown(
            '<p style="color:var(--text-muted);font-size:.78rem;margin-top:.75rem;margin-bottom:.25rem;">Sent this session:</p>',
            unsafe_allow_html=True,
        )
        for a in reversed(assignments[-5:]):
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;padding:.25rem 0;'
                f'border-bottom:1px solid var(--border);">'
                f'<span style="color:var(--text-secondary);font-size:.78rem;">✓ {a["role"]} — {a["email"]}</span>'
                f'<span style="color:var(--text-muted);font-size:.72rem;">{a["ts"]}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )


def render(
    spec: DataProductSpec, narrative: str, concierge_message: str
) -> Optional[str]:
    """
    Render the handoff/summary screen before submission.

    Args:
        spec: DataProductSpec to summarize
        narrative: Concierge narrative/summary text
        concierge_message: Message to display in concierge bubble

    Returns:
        'submit' to proceed with submission, 'edit' to go back and edit, None if no action
    """
    # SECTION A: Concierge bubble
    st.markdown(
        f'<div class="dpc-concierge">{concierge_message}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("## Handoff Summary")
    st.markdown("Review your data product specification before submission.")

    # SECTION A: Completion Dashboard
    st.markdown("### Completion Dashboard")

    # Render gauge
    completion_pct = spec.completion_percentage()
    gauge_html = _render_completion_gauge(completion_pct)
    st.html(gauge_html)

    # Field status summary
    required_missing = spec.required_missing()
    optional_missing = spec.optional_missing()

    required_count = len(spec.REQUIRED_FIELDS)
    optional_count = len(spec.OPTIONAL_FIELDS)

    required_filled = required_count - len(required_missing)
    optional_filled = optional_count - len(optional_missing)

    status_html = f"""
    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; margin: 2rem 0;">
        <div style="background-color: rgba(0, 196, 140, 0.15); padding: 20px; border-radius: 12px; border-left: 4px solid #00C48C;">
            <div style="font-size: 24px; font-weight: 700; color: #00C48C;">✅ {required_filled + optional_filled}</div>
            <div style="font-size: 14px; color: #5B6A7E;">Fields Complete</div>
        </div>
        <div style="background-color: rgba(245, 166, 35, 0.15); padding: 20px; border-radius: 12px; border-left: 4px solid #F5A623;">
            <div style="font-size: 24px; font-weight: 700; color: #F5A623;">⚠ {len(optional_missing)}</div>
            <div style="font-size: 14px; color: #5B6A7E;">Optional Missing</div>
        </div>
        <div style="background-color: rgba(232, 56, 77, 0.15); padding: 20px; border-radius: 12px; border-left: 4px solid #E8384D;">
            <div style="font-size: 24px; font-weight: 700; color: #E8384D;">❌ {len(required_missing)}</div>
            <div style="font-size: 14px; color: #5B6A7E;">Required Missing</div>
        </div>
    </div>
    """
    st.html(status_html)

    # List required missing fields with explanations
    if required_missing:
        st.warning(
            f"**{len(required_missing)} required field(s) still needed:**\n\n"
            + "\n".join([f"- **{field}**" for field in required_missing])
        )

    st.divider()

    # SECTION B: Spec Preview
    st.markdown("### Specification Preview")

    spec_markdown = spec.to_markdown()
    with st.container(border=True):
        st.markdown(spec_markdown)

    render_approval_timeline("business_review")
    st.divider()

    # SECTION C: Downloads
    st.markdown("### Export Options")

    col1, col2, col3 = st.columns(3)

    # Download 1: Markdown specification
    with col1:
        st.download_button(
            label="⬇ Download Specification (.md)",
            data=spec.to_markdown(),
            file_name=f"{spec.name.replace(' ', '_')}_spec_{date.today()}.md",
            mime="text/markdown",
            use_container_width=True,
        )
        st.caption("Professional markdown document")

    # Download 2: Collibra JSON
    with col2:
        collibra_json = spec.to_collibra_json()
        st.download_button(
            label="⬇ Download Collibra (.json)",
            data=json.dumps(collibra_json, indent=2),
            file_name=f"collibra_{spec.name.replace(' ', '_')}.json",
            mime="application/json",
            use_container_width=True,
        )
        st.caption("Bulk import into Collibra")

    # Download 3: Snowflake CSV
    with col3:
        st.download_button(
            label="⬇ Download Snowflake (.csv)",
            data=spec.to_snowflake_csv(),
            file_name=f"snowflake_{spec.name.replace(' ', '_')}.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.caption("Ingest into DATA_GOVERNANCE schema")

    st.divider()
    render_team_assignment(spec)
    st.divider()

    # SECTION D: Action buttons
    st.markdown("### Next Steps")

    col1, col2 = st.columns(2)

    action_result = None

    with col1:
        if st.button(
            "✅ Submit for Technical Review",
            use_container_width=True,
            type="primary",
        ):
            action_result = "submit"

    with col2:
        if st.button(
            "← Go back and edit",
            use_container_width=True,
        ):
            action_result = "edit"

    return action_result


def render_completion(
    spec: DataProductSpec,
    concierge_message: str,
    collibra_id: Optional[str],
    session_id: str,
) -> bool:
    """
    Render the completion/success screen after submission.

    Args:
        spec: Submitted DataProductSpec
        concierge_message: Completion message from concierge
        collibra_id: Optional Collibra asset ID if imported
        session_id: Session identifier (first 8 chars used as reference number)

    Returns:
        True if "Start a new search" button is clicked, False otherwise
    """
    # Concierge bubble
    st.markdown(
        f'<div class="dpc-concierge">{concierge_message}</div>',
        unsafe_allow_html=True,
    )

    # Large animated checkmark
    checkmark_html = """
    <div class="dpc-complete">
        <div class="dpc-complete-checkmark">✓</div>
    </div>
    """
    st.html(checkmark_html)

    st.markdown("## Submission Complete", help="Your data product has been successfully submitted")

    # Reference information
    reference_number = session_id[:8].upper()

    info_html = f"""
    <div style="background-color: #F0F4F8; padding: 20px; border-radius: 16px; border-left: 4px solid #00C2CB; margin: 2rem 0;">
        <div style="font-size: 18px; color: #5B6A7E; margin-bottom: 8px;">Reference Number</div>
        <div style="font-size: 32px; font-weight: 700; font-family: 'IBM Plex Mono', monospace; color: #0D1B2A;">{reference_number}</div>
        <div style="font-size: 14px; color: #8C9BAA; margin-top: 12px;">Keep this number for tracking and support inquiries</div>
    </div>
    """
    st.html(info_html)

    # Product summary
    st.markdown(f"**Data Product:** {spec.name}")
    if spec.description:
        st.markdown(f"**Description:** {spec.description}")
    if spec.data_owner_name:
        st.markdown(f"**Owner:** {spec.data_owner_name}")

    # Collibra asset link if available
    if collibra_id:
        st.markdown(
            f"""
        ### Collibra Asset
        Your data product has been created as a Collibra asset.

        **Asset ID:** `{collibra_id}`

        Visit your Collibra instance to view and manage the asset.
        """
        )

    st.divider()

    # Next steps
    st.markdown("### What Happens Next")

    st.markdown("""
    1. **Technical Review:** Your specification will be reviewed by the data governance team
    2. **Validation:** The data product will be validated against enterprise standards
    3. **Publication:** Upon approval, your data product becomes discoverable in the catalog
    4. **Notification:** You will receive an email confirmation at each stage
    """)

    st.divider()

    # Action button
    if st.button(
        "🔍 Start a new search",
        use_container_width=True,
        type="primary",
    ):
        return True

    return False
