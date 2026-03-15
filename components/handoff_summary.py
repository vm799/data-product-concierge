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
