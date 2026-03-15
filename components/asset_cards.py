"""
Search results card component for Data Product Concierge.

Renders asset search results as cards with governance metadata, quality scores,
and intent buttons for user interaction. Production-ready with zero mock data.
"""

import math
from typing import Optional, Tuple

import streamlit as st

from models.data_product import AssetResult


def _render_data_quality_gauge(score: Optional[float]) -> str:
    """
    Render SVG circular gauge for data quality score.

    Args:
        score: Quality score 0-100, or None for "Not measured"

    Returns:
        SVG HTML string
    """
    if score is None:
        # "Not measured" state
        return """
        <div class="dpc-gauge-container">
            <svg class="dpc-gauge-svg" viewBox="0 0 200 200">
                <circle class="dpc-gauge-background" cx="100" cy="100" r="80"></circle>
            </svg>
            <div class="dpc-gauge-number" style="font-size: 32px; color: var(--text-muted);">–</div>
            <div class="dpc-gauge-label">Not measured</div>
        </div>
        """

    # Determine color class based on score range
    if score < 60:
        color_class = "score-0-59"
    elif score < 80:
        color_class = "score-60-79"
    else:
        color_class = "score-80-100"

    # Calculate circumference and stroke-dashoffset for progress ring
    radius = 80
    circumference = 2 * math.pi * radius
    # Map score 0-100 to arc 0-270 degrees (3/4 circle)
    arc_degrees = (score / 100) * 270
    arc_radians = math.radians(arc_degrees)
    offset = circumference - (arc_radians / (2 * math.pi)) * circumference

    return f"""
    <div class="dpc-gauge-container">
        <svg class="dpc-gauge-svg" viewBox="0 0 200 200">
            <!-- Background ring -->
            <circle class="dpc-gauge-background" cx="100" cy="100" r="80"></circle>
            <!-- Progress ring (starts at top, goes clockwise 3/4 around) -->
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


def _get_classification_color(classification: Optional[str]) -> str:
    """
    Map data classification to badge color code.

    Args:
        classification: Classification name (Confidential, Internal, Public, Restricted)

    Returns:
        CSS class name for badge color
    """
    if not classification:
        return "color-1"

    classification_lower = classification.lower()
    if "confidential" in classification_lower:
        return "color-5"  # crimson
    elif "internal" in classification_lower:
        return "color-4"  # gold
    elif "public" in classification_lower:
        return "color-3"  # emerald
    elif "restricted" in classification_lower:
        return "color-1"  # navy
    return "color-1"


def render_results(
    results: list[AssetResult],
    concierge_message: str,
) -> Tuple[Optional[AssetResult], Optional[str]]:
    """
    Render search results as cards with intent buttons.

    Args:
        results: List of AssetResult objects from search
        concierge_message: Message from concierge to display at top

    Returns:
        tuple: (selected_asset, action_path)
            - selected_asset: The AssetResult that user selected, or None
            - action_path: The intent path selected ('reuse', 'remix', 'create'), or None
    """

    # Show concierge message bubble
    concierge_html = f"""
    <div class="dpc-concierge">
        {concierge_message}
    </div>
    """
    st.html(concierge_html)

    selected_asset = None
    action_path = None

    # Filter out cards the user has skipped this session
    skipped_ids = st.session_state.get("skipped_ids", [])
    visible_results = [r for r in results if r.id not in skipped_ids]

    # Empty state: no search results at all
    if not results:
        st.markdown(
            '<div style="text-align:center;padding:2rem 1rem;border:1px dashed rgba(13,27,42,0.15);'
            'border-radius:12px;margin:1rem 0;">'
            '<p style="color:#5B6A7E;font-size:1rem;margin-bottom:.5rem;">No existing data products matched your search.</p>'
            '<p style="color:#8C9BAA;font-size:.85rem;">Try different terms, or build a new governed data product from scratch.</p>'
            '</div>',
            unsafe_allow_html=True,
        )

    # Render each result as a card
    for idx, result in enumerate(visible_results):
        # Determine domain badge color (rotating through 5 colors)
        domain_color = f"color-{(idx % 5) + 1}"

        # Format regulatory scope pills (max 3 shown, +N more if needed)
        regulatory_pills = ""
        if result.regulatory_scope:
            shown_frameworks = result.regulatory_scope[:3]
            for framework in shown_frameworks:
                regulatory_pills += f'<span class="dpc-badge color-2">{framework}</span> '

            if len(result.regulatory_scope) > 3:
                remainder = len(result.regulatory_scope) - 3
                regulatory_pills += f'<span class="dpc-badge color-2">+{remainder} more</span>'

        # Data quality band badge
        quality_html = ""
        if result.data_quality_score is not None:
            score = result.data_quality_score
            if score >= 80:
                band_label, band_color, band_bg = "High quality", "#00C48C", "rgba(0,196,140,0.12)"
            elif score >= 60:
                band_label, band_color, band_bg = "Medium quality", "#F5A623", "rgba(245,166,35,0.12)"
            else:
                band_label, band_color, band_bg = "Low quality", "#E8384D", "rgba(232,56,77,0.12)"
            quality_html = (
                f'<span style="display:inline-block;background:{band_bg};color:{band_color};'
                f'border:1px solid {band_color};border-radius:100px;padding:2px 10px;'
                f'font-size:.72rem;font-weight:600;">{band_label}</span>'
            )
        else:
            quality_html = (
                '<span style="display:inline-block;background:rgba(13,27,42,0.04);color:#8C9BAA;'
                'border:1px solid rgba(13,27,42,0.1);border-radius:100px;padding:2px 10px;'
                'font-size:.72rem;font-weight:600;">Quality unscored</span>'
            )

        # Relevance score inline badge
        relevance_html = ""
        if result.relevance_score and result.relevance_score > 0:
            relevance_html = (
                f'<span style="display:inline-block;background:rgba(0,194,203,0.08);color:#006B73;'
                f'border:1px solid rgba(0,194,203,0.25);border-radius:100px;padding:2px 10px;'
                f'font-size:.72rem;font-weight:600;">{int(result.relevance_score)}% match</span>'
            )

        # Get classification badge color
        classification_color = _get_classification_color(result.data_classification)

        # Build card HTML
        card_html = f"""
        <div class="dpc-card">
            <!-- Header: Name + Domain Badge + Status -->
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px;">
                <h4 style="margin: 0; font-size: 22px; font-weight: 600; color: var(--text-primary); flex: 1; word-break: break-word;">
                    {result.name}
                </h4>
                <span class="dpc-badge {domain_color}" style="margin-left: 12px; white-space: nowrap;">
                    {result.domain}
                </span>
            </div>

            <!-- Owner info -->
            <div style="font-size: 15px; color: var(--text-secondary); margin-bottom: 12px;">
                <strong>Owner:</strong> {result.owner_name or 'Unassigned'}
                {f' / {result.department}' if result.department else ''}
            </div>

            <!-- Data Classification + Quality + Relevance badges -->
            <div style="margin-bottom: 12px; display: flex; flex-wrap: wrap; gap: 6px; align-items: center;">
                <span class="dpc-badge {classification_color}">
                    {result.data_classification or 'Unclassified'}
                </span>
                {quality_html}
                {relevance_html}
            </div>

            <!-- Regulatory scope tags -->
            {f'<div style="margin-bottom: 12px;">{regulatory_pills}</div>' if regulatory_pills else ''}

            <!-- Update frequency -->
            {f'<div style="font-size: 14px; color: var(--text-secondary); margin-bottom: 12px;"><strong>Updates:</strong> {result.update_frequency}</div>' if result.update_frequency else ''}

        </div>
        """

        st.html(card_html)

        # Intent action buttons — 2-col primary row, skip as text link below
        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "✓ USE AS IS",
                key=f"reuse_{result.id}_{idx}",
                use_container_width=True,
                type="primary",
            ):
                selected_asset = result
                action_path = "reuse"

        with col2:
            if st.button(
                "✂ ADAPT THIS",
                key=f"remix_{result.id}_{idx}",
                use_container_width=True,
                type="secondary",
            ):
                selected_asset = result
                action_path = "remix"

        st.markdown('<div class="dpc-btn-muted" style="margin-top:6px;">', unsafe_allow_html=True)
        if st.button(
            "✕ Not what I need — skip",
            key=f"skip_{result.id}_{idx}",
            use_container_width=True,
        ):
            if "skipped_ids" not in st.session_state:
                st.session_state.skipped_ids = []
            st.session_state.skipped_ids.append(result.id)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.divider()

    # Empty state: user skipped all results
    if not visible_results and results:
        st.markdown(
            '<div style="text-align:center;padding:2rem 1rem;border:1px dashed rgba(13,27,42,0.15);'
            'border-radius:12px;margin:1rem 0;">'
            '<p style="color:#5B6A7E;font-size:1rem;margin-bottom:.5rem;">No results left to review.</p>'
            '<p style="color:#8C9BAA;font-size:.85rem;">You\'ve reviewed all matches. Build a new governed data product below.</p>'
            '</div>',
            unsafe_allow_html=True,
        )

    # Bottom CTA: Build your own
    create_html = """
    <div style="text-align: center; margin-top: 2rem; margin-bottom: 1rem;">
        <p style="color: var(--text-secondary); margin-bottom: 1rem;">
            None of these match? Build a new governed data product from scratch.
        </p>
    </div>
    """
    st.html(create_html)

    if st.button(
        "🏗 BUILD YOUR OWN",
        use_container_width=True,
        key="create_from_scratch",
        type="primary",
    ):
        selected_asset = None
        action_path = "create"

    return selected_asset, action_path
