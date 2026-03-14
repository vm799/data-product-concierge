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
    st.markdown(concierge_html, unsafe_allow_html=True)

    selected_asset = None
    action_path = None

    # Render each result as a card
    for idx, result in enumerate(results):
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

        # Data quality score progress bar
        quality_html = ""
        if result.data_quality_score is not None:
            score = result.data_quality_score
            if score < 60:
                quality_color = "#E8384D"  # crimson
                quality_label = f"{int(score)} / 100"
            elif score < 80:
                quality_color = "#F5A623"  # gold
                quality_label = f"{int(score)} / 100"
            else:
                quality_color = "#00C48C"  # emerald
                quality_label = f"{int(score)} / 100"

            quality_html = f"""
            <div style="margin-top: 12px; margin-bottom: 12px;">
                <div style="font-size: 13px; font-weight: 600; color: var(--text-primary); margin-bottom: 6px;">
                    Data Quality Score
                </div>
                <div style="background-color: var(--border); border-radius: 4px; height: 8px; overflow: hidden;">
                    <div style="background-color: {quality_color}; height: 100%; width: {score}%; transition: width 0.3s ease;"></div>
                </div>
                <div style="font-size: 12px; color: var(--text-muted); margin-top: 4px; text-align: right;">
                    {quality_label}
                </div>
            </div>
            """
        else:
            quality_html = """
            <div style="margin-top: 12px; margin-bottom: 12px;">
                <div style="font-size: 13px; font-weight: 600; color: var(--text-primary); margin-bottom: 6px;">
                    Data Quality Score
                </div>
                <div style="color: var(--text-muted); font-size: 12px;">Not measured</div>
            </div>
            """

        # Relevance score progress bar (always teal)
        relevance_html = ""
        if result.relevance_score is not None:
            relevance_score = result.relevance_score
            relevance_html = f"""
            <div style="margin-top: 12px; margin-bottom: 16px;">
                <div style="font-size: 13px; font-weight: 600; color: var(--text-primary); margin-bottom: 6px;">
                    Relevance
                </div>
                <div style="background-color: var(--border); border-radius: 4px; height: 8px; overflow: hidden;">
                    <div style="background-color: var(--teal); height: 100%; width: {relevance_score}%; transition: width 0.3s ease;"></div>
                </div>
                <div style="font-size: 12px; color: var(--text-muted); margin-top: 4px; text-align: right;">
                    {int(relevance_score)}% match
                </div>
            </div>
            """

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

            <!-- Data Classification -->
            <div style="margin-bottom: 12px;">
                <span class="dpc-badge {classification_color}">
                    {result.data_classification or 'Unclassified'}
                </span>
            </div>

            <!-- Regulatory scope tags -->
            {f'<div style="margin-bottom: 12px;">{regulatory_pills}</div>' if regulatory_pills else ''}

            <!-- Update frequency -->
            {f'<div style="font-size: 14px; color: var(--text-secondary); margin-bottom: 12px;"><strong>Updates:</strong> {result.update_frequency}</div>' if result.update_frequency else ''}

            <!-- Data Quality Score -->
            {quality_html}

            <!-- Relevance Score -->
            {relevance_html}

            <!-- Intent Buttons (horizontal row) -->
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; margin-top: 16px;">
                <div>
                    <button class="dpc-pill" style="width: 100%; padding: 10px 12px; font-size: 14px;" id="btn-reuse-{idx}">
                        ✓ Use as-is
                    </button>
                </div>
                <div>
                    <button class="dpc-pill" style="width: 100%; padding: 10px 12px; font-size: 14px;" id="btn-remix-{idx}">
                        ✂ Remix
                    </button>
                </div>
                <div>
                    <button class="dpc-pill" style="width: 100%; padding: 10px 12px; font-size: 14px;" id="btn-skip-{idx}">
                        Skip
                    </button>
                </div>
            </div>
        </div>
        """

        st.markdown(card_html, unsafe_allow_html=True)

        # Create three columns for intent buttons (Streamlit-backed)
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button(
                "✓ This is it — use as-is",
                key=f"reuse_{result.id}_{idx}",
                use_container_width=True,
            ):
                selected_asset = result
                action_path = "reuse"
                st.rerun()

        with col2:
            if st.button(
                "✂ Use this as a starting point",
                key=f"remix_{result.id}_{idx}",
                use_container_width=True,
            ):
                selected_asset = result
                action_path = "remix"
                st.rerun()

        with col3:
            if st.button(
                "Skip",
                key=f"skip_{result.id}_{idx}",
                use_container_width=True,
            ):
                pass  # No action on skip

        st.divider()

    # Bottom CTA: Create from scratch
    create_html = """
    <div style="text-align: center; margin-top: 2rem; margin-bottom: 1rem;">
        <p style="color: var(--text-secondary); margin-bottom: 1rem;">
            None of these match? Create your own governed data product.
        </p>
    </div>
    """
    st.markdown(create_html, unsafe_allow_html=True)

    if st.button(
        "➕ None of these — create from scratch",
        use_container_width=True,
        key="create_from_scratch",
    ):
        selected_asset = None
        action_path = "create"
        st.rerun()

    return selected_asset, action_path
