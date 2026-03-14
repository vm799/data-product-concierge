import streamlit as st


def inject_styles():
    """
    Injects the complete Data Product Concierge design system CSS.

    Philosophy: "Refined authority." Bloomberg Terminal meets Figma.
    Data-dense but never cluttered. Dark navy anchors trust.
    Electric teal signals intelligence.
    """
    css = """
    <style>
    /* ============================================================================
       GOOGLE FONTS IMPORT
       ============================================================================ */
    @import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Sora:wght@100;200;300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

    /* ============================================================================
       CSS CUSTOM PROPERTIES (Design Tokens)
       ============================================================================ */
    :root {
        --navy: #0D1B2A;
        --navy-mid: #1B2D42;
        --teal: #00C2CB;
        --teal-light: rgba(0, 194, 203, 0.12);
        --gold: #F5A623;
        --emerald: #00C48C;
        --crimson: #E8384D;
        --surface: #F0F4F8;
        --white: #FFFFFF;
        --text-primary: #0D1B2A;
        --text-secondary: #5B6A7E;
        --text-muted: #8C9BAA;
        --border: rgba(13, 27, 42, 0.10);
        --radius-sm: 8px;
        --radius-md: 16px;
        --radius-lg: 24px;
        --shadow-card: 0 2px 16px rgba(13, 27, 42, 0.08), 0 0 0 1px rgba(13, 27, 42, 0.04);
        --shadow-elevated: 0 8px 32px rgba(13, 27, 42, 0.16);
    }

    /* ============================================================================
       GLOBAL STYLES & RESET
       ============================================================================ */
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }

    html, body {
        font-family: 'Sora', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        font-size: 18px;
        color: var(--text-primary);
        background-color: var(--white);
        line-height: 1.6;
    }

    body {
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }

    /* ============================================================================
       TYPOGRAPHY
       ============================================================================ */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Instrument Serif', serif;
        font-weight: 400;
        line-height: 1.3;
        margin-bottom: 1rem;
        color: var(--text-primary);
    }

    h1 {
        font-size: 48px;
        letter-spacing: -0.02em;
        margin-bottom: 1.5rem;
    }

    h2 {
        font-size: 36px;
        letter-spacing: -0.015em;
        margin-bottom: 1.25rem;
    }

    h3 {
        font-size: 28px;
        letter-spacing: -0.01em;
        margin-bottom: 1rem;
    }

    h4 {
        font-size: 24px;
        margin-bottom: 0.875rem;
    }

    h5 {
        font-size: 20px;
        margin-bottom: 0.75rem;
    }

    h6 {
        font-size: 18px;
        margin-bottom: 0.65rem;
    }

    p {
        font-size: 18px;
        color: var(--text-secondary);
        margin-bottom: 1rem;
        font-weight: 400;
    }

    .text-muted {
        color: var(--text-muted);
        font-size: 16px;
    }

    .text-small {
        font-size: 16px;
    }

    .text-code {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 16px;
        color: var(--text-primary);
    }

    code, pre {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 16px;
        background-color: var(--surface);
        padding: 2px 6px;
        border-radius: 4px;
    }

    pre {
        padding: 16px;
        overflow-x: auto;
        margin-bottom: 1rem;
    }

    /* ============================================================================
       LAYOUT: MAIN CONTAINER
       ============================================================================ */
    .main .block-container {
        max-width: 880px;
        margin: 0 auto;
        padding: 2rem 1.5rem;
    }

    /* Remove sidebar styling */
    [data-testid="stSidebar"] {
        display: none;
    }

    /* ============================================================================
       HIDE STREAMLIT CHROME
       ============================================================================ */
    #MainMenu {
        visibility: hidden;
    }

    .stDeployButton {
        display: none;
    }

    footer {
        visibility: hidden;
    }

    header {
        visibility: hidden;
    }

    .viewerBadge_container__1QSob {
        display: none;
    }

    /* ============================================================================
       STREAMLIT SPINNER STYLING
       ============================================================================ */
    .stSpinner > div {
        border-top-color: var(--teal) !important;
    }

    /* ============================================================================
       COMPONENT: CARDS (.dpc-card)
       ============================================================================ */
    .dpc-card {
        background-color: var(--white);
        border-radius: var(--radius-md);
        box-shadow: var(--shadow-card);
        padding: 28px 32px;
        border-left: 4px solid var(--teal);
        transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
        display: block;
        animation: fadeSlideUp 0.4s ease forwards;
    }

    .dpc-card:nth-child(1) { animation-delay: 0s; }
    .dpc-card:nth-child(2) { animation-delay: 0.1s; }
    .dpc-card:nth-child(3) { animation-delay: 0.2s; }
    .dpc-card:nth-child(4) { animation-delay: 0.3s; }
    .dpc-card:nth-child(5) { animation-delay: 0.4s; }
    .dpc-card:nth-child(n+6) { animation-delay: 0.5s; }

    .dpc-card:hover {
        transform: translateY(-3px);
        box-shadow: var(--shadow-elevated);
    }

    /* ============================================================================
       COMPONENT: PRIMARY BUTTONS
       ============================================================================ */
    .stButton > button {
        background-color: var(--navy) !important;
        color: var(--white) !important;
        border-radius: var(--radius-sm) !important;
        padding: 16px 32px !important;
        font-size: 18px !important;
        font-weight: 600 !important;
        width: 100% !important;
        min-height: 60px !important;
        border: none !important;
        transition: all 0.2s ease !important;
        font-family: 'Sora', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
        letter-spacing: 0 !important;
    }

    .stButton > button:hover {
        background-color: var(--teal) !important;
        transform: scale(1.01) !important;
    }

    .stButton > button:active {
        background-color: var(--teal) !important;
        transform: scale(0.99) !important;
    }

    /* ============================================================================
       COMPONENT: PILL BUTTONS (.dpc-pill)
       ============================================================================ */
    .dpc-pill {
        border: 2px solid var(--navy);
        background-color: transparent;
        border-radius: 100px;
        padding: 12px 24px;
        font-size: 16px;
        color: var(--navy);
        cursor: pointer;
        transition: all 0.2s ease;
        font-weight: 500;
        font-family: 'Sora', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        display: inline-block;
        user-select: none;
    }

    .dpc-pill:hover {
        background-color: var(--navy);
        color: var(--white);
    }

    .dpc-pill.active {
        background-color: var(--navy);
        color: var(--white);
    }

    /* ============================================================================
       COMPONENT: CONCIERGE SPEECH BUBBLE (.dpc-concierge)
       ============================================================================ */
    .dpc-concierge {
        background-color: var(--teal-light);
        border-left: 4px solid var(--teal);
        border-radius: 0 var(--radius-md) var(--radius-md) 0;
        padding: 20px 24px;
        font-size: 18px;
        font-style: italic;
        color: var(--text-primary);
        position: relative;
        margin-bottom: 1.5rem;
        line-height: 1.6;
    }

    .dpc-concierge::before {
        content: "✦ Concierge";
        display: block;
        font-size: 14px;
        font-weight: 600;
        color: var(--teal);
        font-style: normal;
        margin-bottom: 12px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* ============================================================================
       COMPONENT: INGREDIENT LABEL (.dpc-ingredient)
       ============================================================================ */
    .dpc-ingredient {
        border: 3px solid var(--navy);
        border-radius: var(--radius-md);
        padding: 32px;
        background-color: var(--white);
    }

    .dpc-ingredient-section {
        margin-bottom: 2rem;
    }

    .dpc-ingredient-section:last-child {
        margin-bottom: 0;
    }

    .dpc-ingredient-header {
        font-size: 13px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--teal);
        margin-bottom: 16px;
        display: block;
    }

    .dpc-ingredient-field {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 0;
        border-bottom: 1px dashed var(--border);
    }

    .dpc-ingredient-field:last-child {
        border-bottom: none;
    }

    .dpc-ingredient-label {
        font-size: 16px;
        font-weight: 700;
        color: var(--text-primary);
    }

    .dpc-ingredient-value {
        font-size: 16px;
        color: var(--text-secondary);
        font-family: 'IBM Plex Mono', monospace;
        word-break: break-word;
        text-align: right;
        max-width: 50%;
    }

    /* ============================================================================
       COMPONENT: CHAPTER PROGRESS BAR (.dpc-progress)
       ============================================================================ */
    .dpc-progress {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin: 2rem 0;
        position: relative;
    }

    .dpc-progress::before {
        content: '';
        position: absolute;
        top: 20px;
        left: 20px;
        right: 20px;
        height: 2px;
        background-color: var(--border);
        z-index: 0;
    }

    .dpc-progress-step {
        display: flex;
        flex-direction: column;
        align-items: center;
        position: relative;
        z-index: 1;
        flex: 1;
    }

    .dpc-progress-step:last-child {
        flex: 0;
    }

    .dpc-progress-circle {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        border: 2px solid var(--navy);
        background-color: var(--white);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
        font-weight: 600;
        color: var(--navy);
        margin-bottom: 12px;
        transition: all 0.3s ease;
    }

    .dpc-progress-step.active .dpc-progress-circle {
        background-color: var(--navy);
        color: var(--white);
        box-shadow: 0 0 0 3px var(--teal-light), 0 0 12px rgba(0, 194, 203, 0.4);
    }

    .dpc-progress-step.complete .dpc-progress-circle {
        background-color: var(--teal);
        border-color: var(--teal);
        color: var(--white);
    }

    .dpc-progress-step.complete .dpc-progress-circle::after {
        content: '✓';
        font-size: 18px;
    }

    .dpc-progress-label {
        font-size: 13px;
        font-weight: 600;
        color: var(--text-secondary);
        text-align: center;
        max-width: 100px;
    }

    /* ============================================================================
       COMPONENT: DATA QUALITY GAUGE (.dpc-gauge)
       ============================================================================ */
    .dpc-gauge-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 2rem 0;
        position: relative;
        width: 200px;
        height: 200px;
        margin-left: auto;
        margin-right: auto;
    }

    .dpc-gauge-svg {
        width: 100%;
        height: 100%;
        filter: drop-shadow(var(--shadow-card));
    }

    .dpc-gauge-background {
        fill: none;
        stroke: var(--border);
        stroke-width: 8;
    }

    .dpc-gauge-progress {
        fill: none;
        stroke-width: 8;
        stroke-linecap: round;
        transition: stroke-dashoffset 1.2s cubic-bezier(0.25, 0.46, 0.45, 0.94);
    }

    .dpc-gauge-progress.score-0-59 {
        stroke: var(--crimson);
    }

    .dpc-gauge-progress.score-60-79 {
        stroke: var(--gold);
    }

    .dpc-gauge-progress.score-80-100 {
        stroke: var(--emerald);
    }

    .dpc-gauge-number {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        font-size: 48px;
        font-weight: 700;
        color: var(--text-primary);
        font-family: 'IBM Plex Mono', monospace;
    }

    .dpc-gauge-label {
        position: absolute;
        bottom: 10px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 14px;
        color: var(--text-muted);
        font-weight: 500;
    }

    /* ============================================================================
       COMPONENT: DOMAIN BADGES (.dpc-badge)
       ============================================================================ */
    .dpc-badge {
        display: inline-block;
        border-radius: 100px;
        padding: 8px 16px;
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--white);
        margin-right: 8px;
        margin-bottom: 8px;
    }

    .dpc-badge.color-1 { background-color: var(--navy); }
    .dpc-badge.color-2 { background-color: var(--teal); }
    .dpc-badge.color-3 { background-color: var(--emerald); }
    .dpc-badge.color-4 { background-color: var(--gold); color: var(--text-primary); }
    .dpc-badge.color-5 { background-color: var(--crimson); }

    /* ============================================================================
       COMPONENT: STATUS BADGES (.dpc-status-*)
       ============================================================================ */
    .dpc-status {
        display: inline-block;
        border-radius: var(--radius-sm);
        padding: 6px 12px;
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    .dpc-status-draft {
        background-color: rgba(245, 166, 35, 0.15);
        color: var(--gold);
        border: 1px solid rgba(245, 166, 35, 0.3);
    }

    .dpc-status-candidate {
        background-color: rgba(0, 194, 203, 0.15);
        color: var(--teal);
        border: 1px solid rgba(0, 194, 203, 0.3);
    }

    .dpc-status-approved {
        background-color: rgba(0, 196, 140, 0.15);
        color: var(--emerald);
        border: 1px solid rgba(0, 196, 140, 0.3);
    }

    .dpc-status-deprecated {
        background-color: rgba(232, 56, 77, 0.15);
        color: var(--crimson);
        border: 1px solid rgba(232, 56, 77, 0.3);
    }

    /* ============================================================================
       COMPONENT: HERO SEARCH (.dpc-hero)
       ============================================================================ */
    .dpc-hero {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
        width: 100%;
        text-align: center;
        padding: 2rem 1.5rem;
    }

    .dpc-hero-heading {
        font-family: 'Instrument Serif', serif;
        font-size: 56px;
        font-weight: 400;
        letter-spacing: -0.02em;
        color: var(--text-primary);
        margin-bottom: 1rem;
    }

    .dpc-hero-subheading {
        font-size: 22px;
        color: var(--text-secondary);
        margin-bottom: 2.5rem;
        max-width: 600px;
    }

    .dpc-hero-search-container {
        width: 100%;
        max-width: 600px;
        position: relative;
    }

    .dpc-hero-search-input {
        width: 100%;
        font-size: 24px;
        padding: 20px 24px;
        border: 2px solid var(--border);
        border-radius: var(--radius-md);
        font-family: 'Sora', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        color: var(--text-primary);
        transition: all 0.2s ease;
    }

    .dpc-hero-search-input:focus {
        outline: none;
        border-color: var(--teal);
        box-shadow: 0 0 0 3px rgba(0, 194, 203, 0.1);
    }

    /* ============================================================================
       COMPONENT: DOWNLOAD BUTTONS (.dpc-download)
       ============================================================================ */
    .dpc-download {
        width: 100%;
        padding: 16px 24px;
        border: 1px solid var(--border);
        background-color: transparent;
        border-radius: var(--radius-sm);
        font-size: 18px;
        color: var(--text-primary);
        cursor: pointer;
        transition: all 0.2s ease;
        font-weight: 500;
        font-family: 'Sora', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }

    .dpc-download:hover {
        border-color: var(--teal);
        background-color: var(--teal-light);
    }

    /* ============================================================================
       COMPONENT: COMPLETION ANIMATION (.dpc-complete)
       ============================================================================ */
    .dpc-complete {
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 2rem auto;
    }

    .dpc-complete-checkmark {
        width: 80px;
        height: 80px;
        border-radius: 50%;
        background-color: var(--emerald);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 48px;
        color: var(--white);
        animation: checkPop 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55);
    }

    /* ============================================================================
       STREAMLIT TEXT INPUTS
       ============================================================================ */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stNumberInput > div > div > input {
        font-family: 'Sora', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
        font-size: 18px !important;
        padding: 16px 18px !important;
        border: 2px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--text-primary) !important;
        transition: all 0.2s ease !important;
        background-color: var(--white) !important;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stNumberInput > div > div > input:focus {
        outline: none !important;
        border-color: var(--teal) !important;
        box-shadow: 0 0 0 3px rgba(0, 194, 203, 0.1) !important;
    }

    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder {
        color: var(--text-muted) !important;
    }

    /* ============================================================================
       STREAMLIT SELECTBOX
       ============================================================================ */
    .stSelectbox > div > div > select {
        font-family: 'Sora', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
        font-size: 18px !important;
        padding: 16px 18px !important;
        border: 2px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--text-primary) !important;
        background-color: var(--white) !important;
        transition: all 0.2s ease !important;
    }

    .stSelectbox > div > div > select:focus {
        outline: none !important;
        border-color: var(--teal) !important;
        box-shadow: 0 0 0 3px rgba(0, 194, 203, 0.1) !important;
    }

    /* ============================================================================
       STREAMLIT MULTISELECT
       ============================================================================ */
    .stMultiSelect [data-baseweb="tag"] {
        background-color: var(--navy) !important;
        color: var(--white) !important;
        border-radius: var(--radius-sm) !important;
    }

    .stMultiSelect [data-baseweb="tag"] span {
        color: var(--white) !important;
    }

    /* ============================================================================
       STREAMLIT CHECKBOX & RADIO
       ============================================================================ */
    .stCheckbox > label > div:first-child {
        width: 20px !important;
        height: 20px !important;
        border-radius: 4px !important;
        border: 2px solid var(--border) !important;
    }

    .stCheckbox > label > div:first-child > input:checked ~ div {
        background-color: var(--teal) !important;
        border-color: var(--teal) !important;
    }

    .stRadio > label > div:first-child {
        width: 20px !important;
        height: 20px !important;
    }

    .stRadio > label > div:first-child > input:checked ~ div {
        background-color: var(--teal) !important;
        border-color: var(--teal) !important;
    }

    /* ============================================================================
       STREAMLIT SLIDER
       ============================================================================ */
    .stSlider > div > div > div > div {
        color: var(--teal) !important;
    }

    [data-baseweb="slider"] [data-testid="stThumbValue"] {
        background-color: var(--teal) !important;
    }

    /* ============================================================================
       STREAMLIT EXPANDER
       ============================================================================ */
    .streamlit-expanderHeader {
        background-color: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-md) !important;
        padding: 16px 20px !important;
    }

    .streamlit-expanderHeader p {
        font-size: 18px !important;
        font-weight: 600 !important;
        color: var(--text-primary) !important;
    }

    /* ============================================================================
       STREAMLIT METRIC
       ============================================================================ */
    [data-testid="metric-container"] {
        background-color: var(--white) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-md) !important;
        padding: 20px 24px !important;
    }

    [data-testid="metric-container"] > div > label {
        font-size: 16px !important;
        color: var(--text-secondary) !important;
        font-weight: 500 !important;
    }

    [data-testid="metric-container"] > div > div {
        font-size: 32px !important;
        color: var(--text-primary) !important;
        font-weight: 700 !important;
        font-family: 'IBM Plex Mono', monospace !important;
    }

    /* ============================================================================
       STREAMLIT DATAFRAME / TABLE
       ============================================================================ */
    [data-testid="dataframe"] {
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-md) !important;
        font-family: 'IBM Plex Mono', monospace !important;
    }

    [data-testid="dataframe"] thead {
        background-color: var(--surface) !important;
    }

    [data-testid="dataframe"] thead th {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        border-bottom: 2px solid var(--border) !important;
        padding: 12px 16px !important;
    }

    [data-testid="dataframe"] tbody td {
        color: var(--text-secondary) !important;
        padding: 12px 16px !important;
        border-bottom: 1px solid var(--border) !important;
        font-size: 16px !important;
    }

    [data-testid="dataframe"] tbody tr:hover {
        background-color: var(--teal-light) !important;
    }

    /* ============================================================================
       STREAMLIT TABS
       ============================================================================ */
    [data-baseweb="tab-list"] {
        border-bottom: 2px solid var(--border) !important;
    }

    [data-baseweb="tab"] {
        color: var(--text-secondary) !important;
        font-size: 18px !important;
        font-weight: 500 !important;
        padding: 12px 24px !important;
        border-bottom: 2px solid transparent !important;
        margin-bottom: -2px !important;
        transition: all 0.2s ease !important;
    }

    [data-baseweb="tab"][aria-selected="true"] {
        color: var(--teal) !important;
        border-bottom-color: var(--teal) !important;
    }

    [data-baseweb="tab"]:hover {
        color: var(--text-primary) !important;
    }

    /* ============================================================================
       STREAMLIT SUCCESS / WARNING / ERROR / INFO
       ============================================================================ */
    [data-testid="stSuccess"] {
        background-color: rgba(0, 196, 140, 0.12) !important;
        border-left: 4px solid var(--emerald) !important;
        border-radius: var(--radius-md) !important;
        padding: 16px 20px !important;
        color: var(--emerald) !important;
    }

    [data-testid="stWarning"] {
        background-color: rgba(245, 166, 35, 0.12) !important;
        border-left: 4px solid var(--gold) !important;
        border-radius: var(--radius-md) !important;
        padding: 16px 20px !important;
        color: var(--gold) !important;
    }

    [data-testid="stError"] {
        background-color: rgba(232, 56, 77, 0.12) !important;
        border-left: 4px solid var(--crimson) !important;
        border-radius: var(--radius-md) !important;
        padding: 16px 20px !important;
        color: var(--crimson) !important;
    }

    [data-testid="stInfo"] {
        background-color: rgba(0, 194, 203, 0.12) !important;
        border-left: 4px solid var(--teal) !important;
        border-radius: var(--radius-md) !important;
        padding: 16px 20px !important;
        color: var(--teal) !important;
    }

    /* ============================================================================
       STREAMLIT DIVIDER
       ============================================================================ */
    hr {
        border: none;
        height: 1px;
        background-color: var(--border);
        margin: 2rem 0;
    }

    /* ============================================================================
       STREAMLIT CAPTION
       ============================================================================ */
    .stCaption {
        font-size: 14px !important;
        color: var(--text-muted) !important;
        font-weight: 400 !important;
    }

    /* ============================================================================
       STREAMLIT WRITE / MARKDOWN
       ============================================================================ */
    [data-testid="stMarkdownContainer"] a {
        color: var(--teal);
        text-decoration: none;
        font-weight: 500;
        transition: all 0.2s ease;
    }

    [data-testid="stMarkdownContainer"] a:hover {
        color: var(--navy);
        text-decoration: underline;
    }

    [data-testid="stMarkdownContainer"] blockquote {
        border-left: 4px solid var(--teal);
        padding-left: 16px;
        margin-left: 0;
        color: var(--text-secondary);
        font-style: italic;
    }

    [data-testid="stMarkdownContainer"] ul,
    [data-testid="stMarkdownContainer"] ol {
        margin-left: 1.5rem;
        margin-bottom: 1rem;
    }

    [data-testid="stMarkdownContainer"] li {
        margin-bottom: 0.5rem;
        color: var(--text-secondary);
    }

    /* ============================================================================
       STREAMLIT FILE UPLOADER
       ============================================================================ */
    [data-testid="stFileUploader"] {
        border: 2px dashed var(--border) !important;
        border-radius: var(--radius-md) !important;
        padding: 32px 24px !important;
        background-color: var(--surface) !important;
    }

    [data-testid="stFileUploader"] button {
        background-color: var(--navy) !important;
        color: var(--white) !important;
        border-radius: var(--radius-sm) !important;
        padding: 12px 24px !important;
        border: none !important;
    }

    /* ============================================================================
       STREAMLIT COLOR PICKER
       ============================================================================ */
    [data-testid="stColorPicker"] input {
        border: 2px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
    }

    /* ============================================================================
       ANIMATIONS (@keyframes)
       ============================================================================ */
    @keyframes fadeSlideUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes checkPop {
        0% {
            transform: scale(0);
        }
        50% {
            transform: scale(1.2);
        }
        100% {
            transform: scale(1);
        }
    }

    @keyframes ringFill {
        from {
            stroke-dashoffset: var(--stroke-dash);
        }
        to {
            stroke-dashoffset: 0;
        }
    }

    @keyframes pulseGlow {
        0%, 100% {
            box-shadow: 0 0 20px rgba(0, 194, 203, 0.4);
        }
        50% {
            box-shadow: 0 0 40px rgba(0, 194, 203, 0.8);
        }
    }

    /* ============================================================================
       UTILITY CLASSES
       ============================================================================ */
    .dpc-flex {
        display: flex;
    }

    .dpc-flex-between {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .dpc-flex-center {
        display: flex;
        justify-content: center;
        align-items: center;
    }

    .dpc-flex-col {
        display: flex;
        flex-direction: column;
    }

    .dpc-grid {
        display: grid;
    }

    .dpc-grid-2 {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 1.5rem;
    }

    .dpc-grid-3 {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1.5rem;
    }

    .dpc-gap-1 {
        gap: 0.5rem;
    }

    .dpc-gap-2 {
        gap: 1rem;
    }

    .dpc-gap-3 {
        gap: 1.5rem;
    }

    .dpc-gap-4 {
        gap: 2rem;
    }

    .dpc-mt-1 { margin-top: 0.5rem; }
    .dpc-mt-2 { margin-top: 1rem; }
    .dpc-mt-3 { margin-top: 1.5rem; }
    .dpc-mt-4 { margin-top: 2rem; }

    .dpc-mb-1 { margin-bottom: 0.5rem; }
    .dpc-mb-2 { margin-bottom: 1rem; }
    .dpc-mb-3 { margin-bottom: 1.5rem; }
    .dpc-mb-4 { margin-bottom: 2rem; }

    .dpc-px-1 { padding-left: 0.5rem; padding-right: 0.5rem; }
    .dpc-px-2 { padding-left: 1rem; padding-right: 1rem; }
    .dpc-px-3 { padding-left: 1.5rem; padding-right: 1.5rem; }
    .dpc-px-4 { padding-left: 2rem; padding-right: 2rem; }

    .dpc-py-1 { padding-top: 0.5rem; padding-bottom: 0.5rem; }
    .dpc-py-2 { padding-top: 1rem; padding-bottom: 1rem; }
    .dpc-py-3 { padding-top: 1.5rem; padding-bottom: 1.5rem; }
    .dpc-py-4 { padding-top: 2rem; padding-bottom: 2rem; }

    .dpc-text-center {
        text-align: center;
    }

    .dpc-text-right {
        text-align: right;
    }

    .dpc-text-left {
        text-align: left;
    }

    .dpc-truncate {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .dpc-line-clamp-2 {
        overflow: hidden;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
    }

    .dpc-line-clamp-3 {
        overflow: hidden;
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
    }

    /* ============================================================================
       RESPONSIVE DESIGN
       ============================================================================ */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 1.5rem 1rem;
        }

        h1 {
            font-size: 36px;
        }

        h2 {
            font-size: 28px;
        }

        h3 {
            font-size: 24px;
        }

        .dpc-hero-heading {
            font-size: 42px;
        }

        .dpc-hero-subheading {
            font-size: 18px;
        }

        .dpc-hero-search-input {
            font-size: 18px;
        }

        .dpc-grid-2 {
            grid-template-columns: 1fr;
        }

        .dpc-grid-3 {
            grid-template-columns: repeat(2, 1fr);
        }

        .dpc-card {
            padding: 20px 24px;
        }

        .stButton > button {
            min-height: 50px;
            font-size: 16px;
            padding: 14px 28px;
        }

        .dpc-ingredient {
            padding: 24px;
        }

        .dpc-progress {
            flex-wrap: wrap;
        }

        .dpc-progress-step {
            min-width: 80px;
        }
    }

    @media (max-width: 480px) {
        .main .block-container {
            padding: 1rem 0.75rem;
        }

        h1 {
            font-size: 28px;
        }

        h2 {
            font-size: 24px;
        }

        h3 {
            font-size: 20px;
        }

        .dpc-hero-heading {
            font-size: 32px;
        }

        .dpc-hero-subheading {
            font-size: 16px;
            margin-bottom: 1.5rem;
        }

        .dpc-hero {
            min-height: auto;
            padding: 1rem;
        }

        .dpc-card {
            padding: 16px 20px;
            border-left-width: 3px;
        }

        .dpc-ingredient {
            padding: 16px;
        }

        .dpc-ingredient-value {
            max-width: 100%;
            text-align: right;
        }

        .dpc-grid-3 {
            grid-template-columns: 1fr;
        }

        .stButton > button {
            min-height: 48px;
            font-size: 16px;
            padding: 12px 24px;
        }

        .dpc-badge {
            font-size: 12px;
            padding: 6px 12px;
        }
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
