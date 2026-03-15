import re
import streamlit as st
from models.data_product import DataProductSpec, AssetResult, DataClassificationEnum, RegulatoryFrameworkEnum
from uuid import uuid4
from typing import Optional

_STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "for", "with", "from", "to",
    "in", "on", "at", "by", "is", "are", "was", "were", "be", "been",
    "have", "has", "had", "do", "does", "did", "will", "would", "can",
    "could", "i", "we", "you", "they", "it", "this", "that", "which",
    "what", "how", "need", "want", "looking", "data", "product", "try",
    "trying", "work", "build", "create", "make",
}

_FALLBACK_DOMAINS = [
    "Finance",
    "Risk",
    "Compliance",
    "Investment Management",
    "Operations",
    "Technology",
    "Market Data",
    "Client Data",
    "Reference Data",
    "Reporting",
]

_REG_OPTIONS = ["GDPR", "MiFID II", "SFDR", "EU Taxonomy", "AIFMD", "BCBS 239", "TCFD", "None"]

_DEMO_RESULTS = [
    AssetResult(
        id=uuid4(),
        name="ESG Fund Holdings Daily",
        domain="Investment Management",
        data_classification=DataClassificationEnum.CONFIDENTIAL,
        regulatory_scope=[RegulatoryFrameworkEnum.SFDR, RegulatoryFrameworkEnum.EU_TAXONOMY],
        relevance_score=92.0,
    ),
    AssetResult(
        id=uuid4(),
        name="Client PII Master",
        domain="Compliance",
        data_classification=DataClassificationEnum.RESTRICTED,
        regulatory_scope=[RegulatoryFrameworkEnum.GDPR],
        relevance_score=87.0,
    ),
    AssetResult(
        id=uuid4(),
        name="FX Spot Rates",
        domain="Market Data",
        data_classification=DataClassificationEnum.INTERNAL,
        regulatory_scope=[RegulatoryFrameworkEnum.MIFID_II],
        relevance_score=78.0,
    ),
]


def _extract_keywords(text: str, max_terms: int = 5) -> list:
    words = re.sub(r"[^\w\s]", "", text.lower()).split()
    terms = [w for w in words if w not in _STOPWORDS and len(w) > 2]
    seen = set()
    unique = []
    for t in terms:
        if t not in seen:
            seen.add(t)
            unique.append(t)
        if len(unique) >= max_terms:
            break
    return unique


def render_use_case_intake(
    spec: DataProductSpec,
    collibra_client,
    demo_mode: bool = False,
    valid_domains: list = None,
) -> tuple:
    """
    Render the use-case intake hero screen.

    Returns:
        (updated_spec, search_results, action)
        action: "search_submitted" | "idle"
        search_results: list of AssetResult (may be empty)
    """
    domains = valid_domains if valid_domains else _FALLBACK_DOMAINS

    # Step chip
    st.markdown(
        '<div style="display:inline-block; background:var(--teal-light,rgba(0,194,203,0.12)); '
        'color:var(--teal,#00C2CB); border:1px solid var(--teal,#00C2CB); border-radius:999px; '
        'padding:4px 14px; font-size:0.75rem; font-weight:600; letter-spacing:0.04em; '
        'margin-bottom:16px;">Step 1 — Discover</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<h2 style="color:#0D1B2A; font-weight:700; margin-top:0; margin-bottom:4px;">'
        'Describe the data</h2>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="color:#5B6A7E; margin-top:0; margin-bottom:28px;">'
        'Search governed data products in your catalogue, then reuse, adapt, or build a new spec.</p>',
        unsafe_allow_html=True,
    )

    # Q1: Free-text textarea
    q1_val = st.session_state.get("intake_q1", spec.business_purpose or "")
    q1 = st.text_area(
        "What data are you trying to work with?",
        value=q1_val,
        max_chars=500,
        height=120,
        placeholder="e.g. ESG fund holdings with issuer-level emissions, for SFDR reporting",
        key="intake_q1_widget",
    )
    st.session_state["intake_q1"] = q1

    # Q2: Domain selectbox
    domain_options = ["— select —"] + domains
    saved_domain = st.session_state.get("intake_domain", spec.domain or "")
    if saved_domain and saved_domain in domains:
        domain_index = domain_options.index(saved_domain)
    else:
        domain_index = 0

    selected_domain = st.selectbox(
        "Which business area does this belong to?",
        options=domain_options,
        index=domain_index,
        key="intake_domain_widget",
    )
    if selected_domain == "— select —":
        selected_domain = ""
    st.session_state["intake_domain"] = selected_domain

    # Q3: Regulatory requirements — native pill multi-select (single-click, built-in affordance)
    reg_framework_options = ["GDPR", "MiFID II", "SFDR", "EU Taxonomy", "AIFMD", "BCBS 239", "TCFD"]
    selected_regs_raw = st.pills(
        "Any regulatory requirements?",
        options=reg_framework_options,
        selection_mode="multi",
        default=st.session_state.get("intake_regs", []),
        key="intake_regs_pills",
    )
    selected_regs = list(selected_regs_raw) if selected_regs_raw else []
    st.session_state["intake_regs"] = selected_regs

    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)

    # Submit button
    submitted = st.button(
        "Search the catalogue",
        type="primary",
        use_container_width=False,
        key="intake_submit",
    )

    if not submitted:
        return (spec, [], "idle")

    if len(q1.strip()) < 10:
        st.error("Please describe the data you need — at least a few words to search the catalogue.")
        return (spec, [], "idle")

    # Seed spec fields
    spec.business_purpose = q1.strip()
    if selected_domain:
        spec.domain = selected_domain
    if selected_regs:
        reg_map = {
            "GDPR": RegulatoryFrameworkEnum.GDPR,
            "MiFID II": RegulatoryFrameworkEnum.MIFID_II,
            "SFDR": RegulatoryFrameworkEnum.SFDR,
            "EU Taxonomy": RegulatoryFrameworkEnum.EU_TAXONOMY,
            "AIFMD": RegulatoryFrameworkEnum.AIFMD,
            "BCBS 239": RegulatoryFrameworkEnum.BCBS_239,
            "TCFD": RegulatoryFrameworkEnum.TCFD,
        }
        spec.regulatory_scope = [
            reg_map[r].value for r in selected_regs if r in reg_map
        ]
    else:
        spec.regulatory_scope = None

    # Keyword extraction and search
    search_results = []
    if demo_mode:
        search_results = list(_DEMO_RESULTS)
    else:
        terms = _extract_keywords(q1) if q1.strip() else []
        if terms and collibra_client is not None:
            try:
                search_results = collibra_client.search_assets(terms) or []
            except Exception as exc:
                import warnings
                warnings.warn(f"Collibra search failed: {exc}", stacklevel=2)
                search_results = []

    return (spec, search_results, "search_submitted")
