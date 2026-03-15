"""
Governance Maturity Dashboard component for Data Product Concierge.

Renders an open vertical list of optional enhancement panels shown after
required fields are complete. Each panel always shows its field labels so
users immediately know what they're signing up for. One click per panel
enters the flow — no extra confirmation step.
"""

import math
from typing import Optional

import streamlit as st

from core.field_registry import (
    GUIDED_PANEL_ACCESS_LICENSING,
    GUIDED_PANEL_EXTENDED_OWNERSHIP,
    GUIDED_PANEL_DATA_DETAIL,
    GUIDED_PANEL_TECH_DEPTH,
    FIELD_STATUS_ANSWERED,
    get_field_meta,
)
from models.data_product import DataProductSpec


# ---------------------------------------------------------------------------
# PANEL DEFINITIONS
# ---------------------------------------------------------------------------

_PANELS = [
    {
        "key": "panel_access_licensing",
        "icon": "🔒",
        "title": "Access & Licensing",
        "description": "How people request access, any licensing or sovereignty restrictions, and which governance body oversees this product.",
        "fields": GUIDED_PANEL_ACCESS_LICENSING,
        "est_minutes": 3,
        "level": "L0",
        "level_color": "#E8384D",
        "level_bg": "rgba(232,56,77,0.10)",
        "why": "Required to reach L0 certification — the baseline standard for all governed data products.",
    },
    {
        "key": "panel_extended_ownership",
        "icon": "👥",
        "title": "Extended Ownership",
        "description": "Domain owner above the product, technical custodian, expected go-live date, and linked business capability.",
        "fields": GUIDED_PANEL_EXTENDED_OWNERSHIP,
        "est_minutes": 3,
        "level": "L1",
        "level_color": "#F5A623",
        "level_bg": "rgba(245,166,35,0.10)",
        "why": "Makes escalation paths clear and connects the product to the firm's capability map.",
    },
    {
        "key": "panel_data_detail",
        "icon": "📊",
        "title": "Data Detail",
        "description": "Business glossary links, release notes, data latency, history depth, and daily publishing schedule.",
        "fields": GUIDED_PANEL_DATA_DETAIL,
        "est_minutes": 4,
        "level": "L1–L2",
        "level_color": "#00C2CB",
        "level_bg": "rgba(0,194,203,0.10)",
        "why": "Helps consumers know exactly when data arrives and how far back history goes — essential for models and reports.",
    },
    {
        "key": "panel_tech_depth",
        "icon": "⚡",
        "title": "Tech Depth",
        "description": "Target downstream systems, the Collibra DPRO mapping, and Critical Data Element designations.",
        "fields": GUIDED_PANEL_TECH_DEPTH,
        "est_minutes": 3,
        "level": "L2",
        "level_color": "#006B73",
        "level_bg": "rgba(0,107,115,0.10)",
        "why": "Required for BCBS 239 compliance and full Collibra lineage reconciliation.",
    },
]


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _panel_completion(panel_fields: list, field_status: dict) -> tuple:
    """Return (answered_count, total_count) for a panel."""
    answered = sum(
        1 for f in panel_fields
        if field_status.get(f) == FIELD_STATUS_ANSWERED
    )
    return answered, len(panel_fields)


def _mini_ring(answered: int, total: int, color: str) -> str:
    """Return a 28×28 SVG completion ring as an inline HTML string."""
    pct = (answered / total) if total > 0 else 0.0
    r = 11
    circ = 2 * math.pi * r
    offset = circ - pct * 0.75 * circ
    ring_color = "#00C48C" if (answered == total and total > 0) else color
    return (
        f'<svg width="28" height="28" viewBox="0 0 28 28" style="vertical-align:middle;flex-shrink:0;">'
        f'<circle cx="14" cy="14" r="{r}" fill="none" stroke="rgba(13,27,42,0.10)" stroke-width="3"/>'
        f'<circle cx="14" cy="14" r="{r}" fill="none" stroke="{ring_color}" stroke-width="3"'
        f' stroke-linecap="round"'
        f' stroke-dasharray="{circ:.1f}" stroke-dashoffset="{offset:.1f}"'
        f' style="transform:rotate(135deg);transform-origin:14px 14px;"/>'
        f'</svg>'
    )


# ---------------------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------------------

def render_maturity_dashboard(
    spec: DataProductSpec,
    field_status: dict,
) -> Optional[str]:
    """
    Render the governance maturity open-list dashboard.

    All panels are always visible with their field labels shown as scannable
    chips — no accordion, no extra click to see what's inside.
    One click on a panel button enters that panel's field flow.

    Args:
        spec: Current DataProductSpec
        field_status: Dict of field_name → FIELD_STATUS_* from session state

    Returns:
        Panel key string, "fill_all", "summary", or None if no action taken.
    """

    # ── Overall progress ────────────────────────────────────────────────────
    all_panel_fields = (
        GUIDED_PANEL_ACCESS_LICENSING
        + GUIDED_PANEL_EXTENDED_OWNERSHIP
        + GUIDED_PANEL_DATA_DETAIL
        + GUIDED_PANEL_TECH_DEPTH
    )
    total_answered = sum(
        1 for f in all_panel_fields
        if field_status.get(f) == FIELD_STATUS_ANSWERED
    )
    total_fields = len(all_panel_fields)
    overall_pct = int(total_answered / total_fields * 100) if total_fields else 0

    # ── Header ──────────────────────────────────────────────────────────────
    st.markdown(
        '<div style="display:inline-flex;align-items:center;gap:8px;'
        'background:rgba(0,196,140,0.10);border:1px solid rgba(0,196,140,0.28);'
        'border-radius:100px;padding:4px 14px;margin-bottom:12px;">'
        '<span style="color:#00C48C;font-size:15px;">✓</span>'
        '<span style="color:#006B73;font-size:.8rem;font-weight:600;">'
        'Required fields complete</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<p style="font-size:1rem;font-weight:600;color:#0D1B2A;margin:0 0 4px;">'
        'Enhance your specification</p>'
        '<p style="font-size:.85rem;color:#5B6A7E;margin:0 0 16px;">'
        'These optional sections deepen governance metadata. '
        'Pick any section — each takes 3–5 minutes.</p>',
        unsafe_allow_html=True,
    )

    # Progress bar
    bar_color = "#00C48C" if overall_pct >= 80 else "#00C2CB" if overall_pct >= 30 else "#8C9BAA"
    st.markdown(
        f'<div style="display:flex;justify-content:space-between;'
        f'align-items:center;margin-bottom:6px;">'
        f'<span style="font-size:.7rem;color:#8C9BAA;text-transform:uppercase;'
        f'letter-spacing:.08em;font-weight:600;">Enhancement progress</span>'
        f'<span style="font-size:.8rem;font-weight:700;color:{bar_color};">'
        f'{total_answered}/{total_fields} fields</span>'
        f'</div>'
        f'<div style="background:rgba(13,27,42,0.08);border-radius:100px;'
        f'height:4px;margin-bottom:20px;">'
        f'<div style="background:{bar_color};width:{overall_pct}%;height:100%;'
        f'border-radius:100px;transition:width .4s ease;"></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Top action row: Fill all + Summary ──────────────────────────────────
    remaining = total_fields - total_answered
    col_all, col_summary = st.columns(2, gap="small")
    action = None

    with col_all:
        fill_label = (
            "✓ All sections complete" if remaining == 0
            else f"Fill all sections ({remaining} remaining)"
        )
        if st.button(
            fill_label,
            key="maturity_fill_all",
            type="primary" if remaining > 0 else "secondary",
            use_container_width=True,
            disabled=(remaining == 0),
        ):
            action = "fill_all"

    with col_summary:
        if st.button(
            "View summary →",
            key="maturity_view_summary",
            type="secondary",
            use_container_width=True,
        ):
            action = "summary"

    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

    # ── Panel list ──────────────────────────────────────────────────────────
    for panel in _PANELS:
        answered, total = _panel_completion(panel["fields"], field_status)
        is_done = (answered == total and total > 0)
        in_progress = (0 < answered < total)

        # Status chip
        if is_done:
            status_chip = (
                '<span style="background:rgba(0,196,140,0.12);color:#00C48C;'
                'border:1px solid rgba(0,196,140,0.3);border-radius:100px;'
                'padding:2px 9px;font-size:.68rem;font-weight:700;">'
                '✓ Complete</span>'
            )
        elif in_progress:
            status_chip = (
                f'<span style="background:rgba(245,166,35,0.10);color:#a66d00;'
                f'border:1px solid rgba(245,166,35,0.3);border-radius:100px;'
                f'padding:2px 9px;font-size:.68rem;font-weight:700;">'
                f'{answered}/{total} done</span>'
            )
        else:
            status_chip = (
                f'<span style="background:{panel["level_bg"]};color:{panel["level_color"]};'
                f'border:1px solid {panel["level_color"]}33;border-radius:100px;'
                f'padding:2px 9px;font-size:.68rem;font-weight:700;">'
                f'{panel["level"]}</span>'
            )

        # Field labels as chips
        field_chips = ""
        for f in panel["fields"]:
            label = get_field_meta(f).get("label", f)
            filled = field_status.get(f) == FIELD_STATUS_ANSWERED
            chip_bg = "rgba(0,196,140,0.10)" if filled else "rgba(13,27,42,0.04)"
            chip_color = "#006B73" if filled else "#8C9BAA"
            chip_border = "rgba(0,196,140,0.25)" if filled else "rgba(13,27,42,0.10)"
            checkmark = "✓ " if filled else ""
            field_chips += (
                f'<span style="display:inline-block;background:{chip_bg};'
                f'color:{chip_color};border:1px solid {chip_border};'
                f'border-radius:6px;padding:2px 8px;font-size:.72rem;'
                f'font-weight:500;margin:2px 3px 2px 0;">'
                f'{checkmark}{label}</span>'
            )

        ring_svg = _mini_ring(answered, total, panel["level_color"])

        panel_html = (
            f'<div style="background:#fff;border:1px solid rgba(13,27,42,0.09);'
            f'border-radius:12px;padding:16px 18px 12px;'
            f'box-shadow:0 1px 3px rgba(13,27,42,0.05);">'
            # Header row
            f'<div style="display:flex;align-items:center;gap:8px;'
            f'flex-wrap:wrap;margin-bottom:6px;">'
            f'{ring_svg}'
            f'<span style="font-size:.95rem;font-weight:700;color:#0D1B2A;">'
            f'{panel["icon"]} {panel["title"]}</span>'
            f'{status_chip}'
            f'<span style="margin-left:auto;font-size:.72rem;color:#8C9BAA;">'
            f'~{panel["est_minutes"]} min</span>'
            f'</div>'
            # Description
            f'<div style="font-size:.8rem;color:#5B6A7E;margin-bottom:8px;'
            f'line-height:1.5;">{panel["description"]}</div>'
            # Field chips
            f'<div style="margin-bottom:4px;">{field_chips}</div>'
            # Why this matters
            f'<div style="font-size:.72rem;color:#8C9BAA;margin-top:6px;'
            f'font-style:italic;">{panel["why"]}</div>'
            f'</div>'
        )

        st.html(panel_html)

        # Single button — full width, flush below card, no gap
        if is_done:
            btn_label = "✓ Review answers"
            btn_type = "secondary"
        elif in_progress:
            btn_label = f"Continue ({total - answered} remaining) →"
            btn_type = "primary"
        else:
            btn_label = f"Fill {panel['title']} ({total} fields) →"
            btn_type = "primary"

        if st.button(
            btn_label,
            key=f"maturity_{panel['key']}",
            type=btn_type,
            use_container_width=True,
        ):
            action = panel["key"]

        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    return action
