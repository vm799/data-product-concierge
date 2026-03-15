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
import urllib.parse
from datetime import date
from typing import Optional
from models.data_product import DataProductSpec



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

    # Preview (open by default so users can copy)
    with st.expander("Copy email body (for browser-based email clients)", expanded=False):
        st.code(body, language=None)

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


def render_colleague_handoff(spec: DataProductSpec, handoff_data: dict) -> None:
    """
    Render the colleague handoff section for tech fields.

    Shows pending tech fields, a downloadable partial spec JSON,
    and a pre-composed mailto link.

    Args:
        spec: The current DataProductSpec (partial — business fields only)
        handoff_data: Dict from guided_form._generate_colleague_handoff()
    """
    from components.styles import render_guidance

    render_guidance(
        "The business specification is complete. The following technical fields are best "
        "completed by your data engineering team. Generate a handoff package below.",
        label="Colleague Handoff",
    )

    pending_fields = handoff_data.get("pending_fields", [])
    skipped_fields = handoff_data.get("skipped_fields", [])
    spec_json = handoff_data.get("spec_partial_json", "{}")
    mailto_subject = handoff_data.get("mailto_subject", "Data Product Spec — Tech Fields Needed")
    mailto_body = handoff_data.get("mailto_body", "")

    # Download partial spec
    col1, col2 = st.columns(2)
    with col1:
        product_name = spec.name.replace(" ", "_") if spec.name else "data_product"
        st.download_button(
            label="⬇ Download partial spec (.json)",
            data=spec_json,
            file_name=f"{product_name}_partial_spec.json",
            mime="application/json",
            use_container_width=True,
        )
        st.caption("Attach this to the handoff email")

    with col2:
        if mailto_body:
            encoded_subject = urllib.parse.quote(mailto_subject)
            encoded_body = urllib.parse.quote(mailto_body)
            mailto_url = f"mailto:?subject={encoded_subject}&body={encoded_body}"
            st.link_button(
                "📧 Open handoff email",
                url=mailto_url,
                use_container_width=True,
            )
            st.caption("Opens your default email client")

    # Pending fields list
    if pending_fields:
        st.markdown("#### Technical fields for your colleague")
        fields_html = '<div class="dpc-handoff-card">'
        for meta in pending_fields:
            label = meta.get("label", "")
            question = meta.get("question", "")
            can_na = meta.get("can_be_na", True)
            na_note = " *(optional)*" if can_na else ""
            fields_html += (
                f'<div style="padding:10px 0;border-bottom:1px solid rgba(13,27,42,0.08);">'
                f'<div style="font-size:.8rem;font-weight:700;color:var(--text-1);'
                f'text-transform:uppercase;letter-spacing:.06em;">{label}{na_note}</div>'
                f'<div style="font-size:.85rem;color:var(--text-2);margin-top:3px;">{question}</div>'
                f'</div>'
            )
        fields_html += "</div>"
        st.markdown(fields_html, unsafe_allow_html=True)

    if skipped_fields:
        with st.expander(f"{len(skipped_fields)} skipped field(s) — also needs attention"):
            for meta in skipped_fields:
                st.markdown(f"- **{meta.get('label', '')}**: {meta.get('question', '')}")


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
    completion_pct = spec.completion_percentage()

    # Completion bar (replaces circular gauge — cleaner, no overlap)
    bar_color = "#00C48C" if completion_pct >= 80 else "#F5A623" if completion_pct >= 50 else "#E8384D"
    st.markdown(
        f'<div style="margin:1.5rem 0 1rem;">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">'
        f'<span style="font-size:.75rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--text-secondary);">Spec completion</span>'
        f'<span style="font-size:1.1rem;font-weight:700;color:{bar_color};">{int(completion_pct)}%</span>'
        f'</div>'
        f'<div style="background:rgba(13,27,42,0.08);border-radius:100px;height:8px;">'
        f'<div style="background:{bar_color};width:{completion_pct}%;height:100%;border-radius:100px;transition:width .4s ease;"></div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

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

    st.markdown(
        '<div style="margin:1.5rem 0;padding:16px 20px;background:rgba(0,194,203,0.06);'
        'border-left:3px solid #00C2CB;border-radius:0 8px 8px 0;">'
        '<p style="font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;'
        'color:#006B73;margin:0 0 8px;">What happens next</p>'
        '<p style="font-size:.85rem;color:#5B6A7E;margin:4px 0;">1. Download the spec and share with your data engineering team to complete the technical fields.</p>'
        '<p style="font-size:.85rem;color:#5B6A7E;margin:4px 0;">2. The data owner reviews and confirms governance details.</p>'
        '<p style="font-size:.85rem;color:#5B6A7E;margin:4px 0;">3. Once complete, submit for registration in Collibra.</p>'
        '</div>',
        unsafe_allow_html=True,
    )
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

    # SECTION D: Action buttons with pre-flight guardrails
    st.markdown("### Next Steps")

    action_result = None

    missing_required = spec.required_missing()
    assignments_sent = st.session_state.get("assignments", [])

    # ── Guardrail 1: required fields incomplete ──────────────────────────────
    if missing_required:
        field_list = ", ".join(f"`{f}`" for f in missing_required[:6])
        overflow = f" and {len(missing_required) - 6} more" if len(missing_required) > 6 else ""
        st.error(
            f"**{len(missing_required)} required field{'s' if len(missing_required) > 1 else ''} still missing** — "
            f"complete these before submitting:\n\n"
            f"{field_list}{overflow}\n\n"
            f"Go back and fill them in, or hand off to the tech team to complete."
        )

    # ── Guardrail 2: no team notified ────────────────────────────────────────
    elif not assignments_sent:
        st.warning(
            "**⚠ No team member has been notified yet.**\n\n"
            "Use **Assign & Notify Team** above to send the assignment email before submitting. "
            "Without notification, the submission will sit unactioned — "
            "no engineer will know to build it in Snowflake, and no owner will know to approve it."
        )
        # Allow override, but make it clearly secondary — not the obvious choice
        with st.expander("Submit anyway (not recommended)", expanded=False):
            st.caption(
                "Only do this if you've already notified the team through another channel "
                "(e.g. Slack, Teams, or direct email not tracked here)."
            )
            if st.button(
                "Confirm — submit without notification",
                use_container_width=True,
                key="submit_force_unnotified",
            ):
                action_result = "submit"

    # ── All checks passed ─────────────────────────────────────────────────────
    else:
        last = assignments_sent[-1]
        st.success(
            f"✓ **{last['role']}** notified — {last['email']} at {last['ts']}. "
            f"Ready to submit."
        )

    # ── Buttons row (submit disabled if checks fail) ──────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        submit_blocked = bool(missing_required)
        if st.button(
            "✅ Submit for Technical Review",
            use_container_width=True,
            type="primary",
            disabled=submit_blocked,
            key="submit_for_review_btn",
        ):
            action_result = "submit"

    with col2:
        if st.button(
            "← Go back and edit",
            use_container_width=True,
            key="go_back_edit_btn",
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
        "Start a new spec",
        use_container_width=True,
        type="primary",
    ):
        return True

    return False
