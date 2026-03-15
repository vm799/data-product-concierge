"""
NLQ Intake component for Data Product Concierge.

Shows a single plain-English text area before the guided form.
User describes their data product → AI extracts all possible fields via chat_turn()
→ guided form pre-populates with AI suggestions → user validates, not types from scratch.
"""

import streamlit as st
from models.data_product import DataProductSpec
from core.async_utils import run_async


def _apply_extracted_to_spec(spec: DataProductSpec, extracted: dict) -> DataProductSpec:
    """
    Merge AI-extracted field values onto the spec.
    Only sets fields that are currently blank/None — never overwrites user data.
    Returns the updated spec and the set of field names that were actually populated.
    """
    populated = set()
    for field_name, value in (extracted or {}).items():
        if not hasattr(spec, field_name):
            continue
        current = getattr(spec, field_name, None)
        # Skip if already set by user or seed
        if current is not None and current != "" and current != []:
            continue
        try:
            setattr(spec, field_name, value)
            populated.add(field_name)
        except Exception:
            pass
    return spec, populated


def render_nlq_intake(
    spec: DataProductSpec,
    valid_options: dict,
) -> tuple:
    """
    Render the NLQ intake screen: a single text area where the user describes
    their data product in plain English.

    On submit, calls concierge.chat_turn() to extract all possible fields,
    merges results onto spec, marks extracted fields in session_state for
    the "💡 AI suggestion" badge in the guided form, then reruns into the form.

    Args:
        spec: Current DataProductSpec (may be partially pre-filled by seed_new_product)
        valid_options: Collibra-backed option lists {field_name: [option, ...]}

    Returns:
        (updated_spec, submitted: bool)
        submitted=True means the user clicked "Extract fields" and the form should proceed.
    """
    # If already done this session, skip directly
    if st.session_state.get("nlq_done"):
        return spec, True

    # --- Header ---
    st.html(
        '<div style="background:rgba(0,107,115,0.06);border:1px solid rgba(0,107,115,0.2);'
        'border-radius:12px;padding:20px 24px;margin-bottom:1.5rem;">'
        '<div style="font-size:1.15rem;font-weight:700;color:#0D1B2A;margin-bottom:6px;">'
        '✨ Tell me about your data product</div>'
        '<div style="font-size:.9rem;color:#5B6A7E;line-height:1.55;">'
        'Describe it in plain English — the more detail you share, the more fields '
        'I can pre-fill for you. You\'ll review and confirm every suggestion.'
        '</div>'
        '</div>'
    )

    # Pre-fill placeholder from seed if name already extracted
    placeholder = (
        "e.g. Payments fraud detection dataset owned by the Risk Analytics team. "
        "Covers GDPR and MiFID II, updated daily from the transaction ledger. "
        "Internal use only, steward is sarah.jones@firm.com"
    )

    description = st.text_area(
        label="Data product description",
        height=160,
        placeholder=placeholder,
        label_visibility="collapsed",
        key="nlq_intake_text",
    )

    col_skip, col_submit = st.columns([1, 3])

    with col_skip:
        if st.button("Skip →", key="nlq_skip_btn", use_container_width=True):
            st.session_state["nlq_done"] = True
            st.session_state["ai_suggested_fields"] = set()
            st.rerun()

    with col_submit:
        extract_clicked = st.button(
            "Extract fields →",
            key="nlq_extract_btn",
            type="primary",
            use_container_width=True,
            disabled=not (description or "").strip(),
        )

    if extract_clicked and (description or "").strip():
        concierge = st.session_state.get("concierge")

        # Demo mode or no concierge — skip to form
        try:
            from app import _demo_active
            demo = _demo_active()
        except Exception:
            demo = False

        if concierge and not demo:
            with st.spinner("Extracting fields from your description…"):
                try:
                    result = run_async(
                        concierge.chat_turn(
                            user_message=description.strip(),
                            history=[],
                            spec=spec,
                            valid_options=valid_options or {},
                        ),
                        timeout=20,
                    )
                    extracted = result.get("extracted") or {}
                    spec, populated = _apply_extracted_to_spec(spec, extracted)
                    st.session_state["ai_suggested_fields"] = populated

                    if populated:
                        st.success(
                            f"✓ Pre-filled {len(populated)} fields from your description. "
                            f"Review each suggestion below."
                        )
                    else:
                        st.info(
                            "Couldn't extract specific fields — you can fill them in the form."
                        )
                except Exception as exc:
                    st.warning(f"AI extraction unavailable ({exc}). Proceeding to form.")
                    st.session_state["ai_suggested_fields"] = set()
        else:
            st.session_state["ai_suggested_fields"] = set()

        st.session_state["nlq_done"] = True
        st.rerun()

    return spec, False
