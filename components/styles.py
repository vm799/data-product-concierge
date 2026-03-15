import streamlit as st

# Design token constants — use these in Python code instead of hardcoded hex values
_TEAL    = "#00C2CB"
_TEAL_D  = "#006B73"
_TEAL_DD = "#005960"
_NAVY    = "#0D1B2A"
_EMERALD = "#00C48C"
_GOLD    = "#F5A623"
_CRIMSON = "#E8384D"
_SURFACE = "#F5F7FA"
_TEXT_1  = "#0D1B2A"
_TEXT_2  = "#5B6A7E"
_TEXT_3  = "#8C9BAA"


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
        --teal-d: #006B73;
        --teal-dd: #005960;
        --teal-light: rgba(0, 194, 203, 0.12);
        --gold: #F5A623;
        --emerald: #00C48C;
        --crimson: #E8384D;
        --surface: #F5F7FA;
        --white: #FFFFFF;
        --text-primary: #0D1B2A;
        --text-secondary: #5B6A7E;
        --text-muted: #8C9BAA;
        --text-1: #0D1B2A;
        --text-2: #5B6A7E;
        --text-3: #8C9BAA;
        --border: rgba(13, 27, 42, 0.10);
        --radius-sm: 6px;
        --radius-md: 12px;
        --radius-lg: 20px;
        --shadow-sm: 0 1px 4px rgba(13,27,42,0.06);
        --shadow-md: 0 4px 16px rgba(13,27,42,0.10);
        --shadow-lg: 0 12px 40px rgba(13,27,42,0.16);
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
       LAYOUT: MAIN CONTAINER (3/4 width — sidebar takes the rest)
       ============================================================================ */
    .main .block-container {
        max-width: 860px;
        margin: 0 auto;
        padding: 2rem 2rem;
    }

    /* ============================================================================
       SIDEBAR — dark navy, full height
       ============================================================================ */
    [data-testid="stSidebar"] {
        background-color: #0D1B2A !important;
        border-right: 1px solid rgba(0,194,203,0.15) !important;
        min-width: 280px !important;
        max-width: 300px !important;
    }

    [data-testid="stSidebar"] * {
        color: rgba(255,255,255,0.85) !important;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4 {
        color: #FFFFFF !important;
        font-family: 'Sora', sans-serif !important;
    }

    [data-testid="stSidebar"] .stMarkdown p {
        color: rgba(255,255,255,0.7) !important;
        font-size: 13px !important;
    }

    [data-testid="stSidebar"] hr {
        border-color: rgba(0,194,203,0.2) !important;
        margin: 12px 0 !important;
    }

    /* Sidebar buttons — teal outline */
    [data-testid="stSidebar"] .stButton > button {
        background-color: transparent !important;
        color: rgba(255,255,255,0.8) !important;
        border: 1px solid rgba(0,194,203,0.35) !important;
        border-radius: 6px !important;
        padding: 8px 12px !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        min-height: 36px !important;
        text-transform: none !important;
        letter-spacing: 0 !important;
        box-shadow: none !important;
        width: 100% !important;
    }

    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: rgba(0,194,203,0.12) !important;
        color: #00C2CB !important;
        border-color: #00C2CB !important;
        transform: none !important;
        box-shadow: none !important;
    }

    /* Active chapter button in sidebar */
    [data-testid="stSidebar"] .stButton > button[disabled],
    [data-testid="stSidebar"] .stButton > button:disabled {
        background-color: rgba(0,194,203,0.18) !important;
        color: #00C2CB !important;
        border-color: #00C2CB !important;
        opacity: 1 !important;
    }

    /* Sidebar progress bar */
    [data-testid="stSidebar"] .stProgress > div > div {
        background-color: #00C2CB !important;
    }
    [data-testid="stSidebar"] .stProgress > div {
        background-color: rgba(255,255,255,0.1) !important;
    }

    /* Sidebar expander */
    [data-testid="stSidebar"] [data-testid="stExpander"] {
        border: 1px solid rgba(0,194,203,0.2) !important;
        border-radius: 8px !important;
        background: rgba(0,194,203,0.05) !important;
    }

    [data-testid="stSidebar"] [data-testid="stExpander"] summary {
        color: rgba(255,255,255,0.9) !important;
        font-size: 13px !important;
        font-weight: 600 !important;
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
       COMPONENT: BUTTONS — three-tier interaction design hierarchy
       Tier 1 primary  = teal filled CTA (one per screen)
       Tier 2 secondary = ghost teal outline (supporting action)
       Tier 3 default   = neutral chip (chooseable options, toggles)
       ============================================================================ */

    /* TIER 3: Default (no type) — neutral selectable chip
       Used for: regulatory pills, domain options, "Build your own", any toggle */
    .stButton button,
    .stButton > button {
        background-color: #FFFFFF !important;
        color: var(--text-primary) !important;
        border: 1.5px solid rgba(13,27,42,0.15) !important;
        border-radius: var(--radius-sm) !important;
        padding: 10px 20px !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        cursor: pointer !important;
        transition: all 0.15s ease !important;
        font-family: 'Sora', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
        letter-spacing: 0.02em !important;
        text-transform: none !important;
        box-shadow: none !important;
        min-height: 40px !important;
    }

    .stButton button p,
    .stButton > button p {
        color: var(--text-primary) !important;
        font-weight: 500 !important;
    }

    .stButton button:hover,
    .stButton > button:hover {
        background-color: rgba(0,194,203,0.06) !important;
        border-color: var(--teal) !important;
        color: var(--teal-d) !important;
        transform: none !important;
        box-shadow: none !important;
    }

    .stButton button:hover p,
    .stButton > button:hover p {
        color: var(--teal-d) !important;
    }

    .stButton button:active,
    .stButton > button:active {
        background-color: rgba(0,194,203,0.12) !important;
        border-color: var(--teal-d) !important;
        transform: none !important;
        box-shadow: none !important;
    }

    /* ============================================================================
       PRIMARY CTA BUTTONS — dark teal, decisively different from pill/accent teal
       ============================================================================ */
    [data-testid="baseButton-primary"],
    button[data-testid="baseButton-primary"] {
        background-color: #006B73 !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: 600 !important;
        letter-spacing: 0.01em !important;
        box-shadow: 0 2px 10px rgba(0, 107, 115, 0.35) !important;
        transition: background-color 0.15s ease, box-shadow 0.15s ease !important;
    }

    [data-testid="baseButton-primary"] p,
    button[data-testid="baseButton-primary"] p {
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }

    [data-testid="baseButton-primary"]:hover,
    button[data-testid="baseButton-primary"]:hover {
        background-color: #005960 !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 18px rgba(0, 107, 115, 0.50) !important;
    }

    [data-testid="baseButton-primary"]:hover p,
    button[data-testid="baseButton-primary"]:hover p {
        color: #FFFFFF !important;
    }

    /* Disabled primary buttons — clearly not clickable */
    [data-testid="baseButton-primary"]:disabled,
    button[data-testid="baseButton-primary"]:disabled {
        background-color: rgba(0, 107, 115, 0.30) !important;
        color: rgba(255, 255, 255, 0.5) !important;
        box-shadow: none !important;
        cursor: not-allowed !important;
    }

    /* ============================================================================
       SECONDARY BUTTONS — ghost style (teal outline, transparent bg)
       Higher specificity (.stButton + attribute) beats the broad .stButton button rule above.
       ============================================================================ */
    .stButton button[data-testid="baseButton-secondary"],
    .stButton > button[data-testid="baseButton-secondary"],
    [data-testid="baseButton-secondary"],
    [data-testid="stBaseButton-secondary"] {
        background: transparent !important;
        color: var(--teal-d) !important;
        border: 1.5px solid rgba(0,194,203,0.45) !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
        min-height: 44px !important;
        border-radius: var(--radius-md) !important;
        transition: all 0.15s ease !important;
    }
    /* Also override the button p rule for secondary */
    .stButton button[data-testid="baseButton-secondary"] p,
    .stButton > button[data-testid="baseButton-secondary"] p {
        color: var(--teal-d) !important;
    }
    .stButton button[data-testid="baseButton-secondary"]:hover,
    .stButton > button[data-testid="baseButton-secondary"]:hover,
    [data-testid="baseButton-secondary"]:hover,
    [data-testid="stBaseButton-secondary"]:hover {
        background: rgba(0,194,203,0.06) !important;
        border-color: var(--teal) !important;
        color: var(--teal) !important;
    }
    .stButton button[data-testid="baseButton-secondary"]:hover p,
    .stButton > button[data-testid="baseButton-secondary"]:hover p {
        color: var(--teal) !important;
    }

    /* ============================================================================
       COMPONENT: FORM OPTION PILLS (.dpc-pill) — teal, distinct from navy CTAs
       ============================================================================ */
    .dpc-pill {
        border: 2px solid var(--teal) !important;
        background-color: var(--teal-light) !important;
        border-radius: 100px !important;
        padding: 10px 20px !important;
        font-size: 14px !important;
        color: var(--teal) !important;
        cursor: pointer !important;
        transition: all 0.18s ease !important;
        font-weight: 600 !important;
        font-family: 'Sora', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
        display: inline-block !important;
        user-select: none !important;
        letter-spacing: 0.02em !important;
    }

    .dpc-pill:hover {
        background-color: var(--teal) !important;
        color: #FFFFFF !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(0,194,203,0.30) !important;
    }

    .dpc-pill.active {
        background-color: var(--teal) !important;
        color: #FFFFFF !important;
        border-color: var(--teal) !important;
        box-shadow: 0 2px 8px rgba(0,194,203,0.30) !important;
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
        font-style: normal;
        color: var(--text-primary);
        position: relative;
        margin-bottom: 1.5rem;
        line-height: 1.6;
    }

    .dpc-concierge p {
        font-style: normal !important;
        color: var(--text-2, #5B6A7E);
        font-size: 0.9rem;
        line-height: 1.6;
    }

    .dpc-concierge::before {
        content: "GUIDANCE";
        display: inline-block;
        font-size: 0.65rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--teal-d);
        background: rgba(0,194,203,0.08);
        border: 1px solid rgba(0,194,203,0.25);
        border-radius: 100px;
        padding: 2px 8px;
        margin-bottom: 10px;
        font-style: normal;
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

    /* Streamlit uses BaseWeb div-based custom dropdowns — protect their text */
    div[data-baseweb="select"] *,
    div[data-baseweb="select"] input,
    div[data-baseweb="select"] [data-testid="stWidgetLabel"] {
        color: var(--text-primary) !important;
    }

    /* Prevent BaseWeb select dropdown from being clipped at viewport bottom */
    div[data-baseweb="select"] {
        position: relative;
        z-index: 10;
    }

    /* Popover/dropdown portal — ensure it appears above other content */
    div[data-baseweb="popover"],
    div[data-baseweb="menu"] {
        z-index: 9999 !important;
        max-height: 280px !important;
        overflow-y: auto !important;
    }

    /* Dropdown option list — rendered in a portal, ensure dark text on white */
    div[data-baseweb="popover"] li,
    div[data-baseweb="popover"] [role="option"],
    div[data-baseweb="menu"] li,
    div[data-baseweb="menu"] [role="option"],
    div[data-baseweb="menu"] * {
        color: var(--text-primary) !important;
        background-color: var(--white);
    }
    div[data-baseweb="menu"] [role="option"]:hover,
    div[data-baseweb="popover"] [role="option"]:hover {
        background-color: var(--teal-light) !important;
        color: var(--teal-d) !important;
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
       STREAMLIT PILLS (st.pills — Streamlit 1.40+)
       Unselected: white chip, subtle border, dark text
       Selected: teal filled, white text — clear affordance
       ============================================================================ */
    [data-testid="stPills"] button {
        background: var(--white) !important;
        color: var(--text-primary) !important;
        border: 1.5px solid rgba(13,27,42,0.18) !important;
        border-radius: 100px !important;
        padding: 6px 16px !important;
        font-size: 0.83rem !important;
        font-weight: 500 !important;
        transition: all 0.15s ease !important;
        box-shadow: none !important;
        text-transform: none !important;
        letter-spacing: 0 !important;
    }

    [data-testid="stPills"] button:hover {
        background: rgba(0,194,203,0.08) !important;
        border-color: var(--teal) !important;
        color: var(--teal-d) !important;
    }

    [data-testid="stPills"] button[aria-pressed="true"],
    [data-testid="stPills"] button[aria-selected="true"] {
        background: var(--teal-d) !important;
        color: #fff !important;
        border-color: var(--teal-d) !important;
        font-weight: 600 !important;
    }

    [data-testid="stPills"] button[aria-pressed="true"]:hover,
    [data-testid="stPills"] button[aria-selected="true"]:hover {
        background: var(--teal-dd) !important;
        border-color: var(--teal-dd) !important;
        color: #fff !important;
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
        font-style: normal;
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

    /* ============================================================================
       FOCUS STATES & KEYBOARD ACCESSIBILITY
       ============================================================================ */

    /* Remove default browser outline; replace with teal ring */
    .stTextInput input:focus,
    .stTextArea textarea:focus,
    .stSelectbox select:focus,
    .stDateInput input:focus {
        outline: none !important;
        border-color: var(--teal) !important;
        box-shadow: 0 0 0 3px rgba(0, 194, 203, 0.20) !important;
        transition: box-shadow 0.15s ease, border-color 0.15s ease !important;
    }

    /* Pill buttons — keyboard focus ring */
    button:focus-visible {
        outline: 2px solid var(--teal) !important;
        outline-offset: 2px !important;
    }

    /* Input label glow when field is focused (parent highlight) */
    .stTextInput:focus-within label,
    .stTextArea:focus-within label {
        color: var(--teal) !important;
        transition: color 0.15s ease !important;
    }

    /* ============================================================================
       FIELD ANIMATION & TRANSITIONS
       ============================================================================ */

    /* Smooth appear for suggestions, cards, new content */
    .dpc-card,
    .dpc-concierge {
        animation: dpc-fadein 0.25s ease both !important;
    }

    @keyframes dpc-fadein {
        from { opacity: 0; transform: translateY(4px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    /* Spec panel field rows — subtle hover highlight */
    .dpc-spec-row:hover {
        background: rgba(0, 194, 203, 0.04) !important;
        border-radius: 4px !important;
    }

    /* Progress bar — smooth fill transition */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, var(--teal), #4DD9C0) !important;
        transition: width 0.4s ease !important;
        border-radius: 4px !important;
    }

    /* ============================================================================
       PILL BUTTON IMPROVEMENTS
       ============================================================================ */

    /* Selected pill state — teal fill with dark text */
    button[data-pill-selected="true"],
    .dpc-pill-selected {
        background-color: var(--teal) !important;
        color: #0D1B2A !important;
        border-color: var(--teal) !important;
        font-weight: 700 !important;
    }

    /* Pill hover state */
    .dpc-pill-btn:hover,
    div[data-testid="column"] .stButton > button:hover {
        border-color: var(--teal) !important;
        color: var(--teal) !important;
        transition: all 0.12s ease !important;
    }

    /* ============================================================================
       SMART SUGGESTION BANNERS
       ============================================================================ */

    .dpc-suggestion {
        background: rgba(245, 166, 35, 0.08) !important;
        border-left: 3px solid #F5A623 !important;
        border-radius: 0 8px 8px 0 !important;
        padding: .6rem .9rem !important;
        margin: .5rem 0 !important;
        animation: dpc-fadein 0.2s ease both !important;
    }

    /* ============================================================================
       CHAT INPUT UX
       ============================================================================ */

    /* Chat input container — teal focus ring */
    [data-testid="stChatInput"] textarea:focus {
        border-color: var(--teal) !important;
        box-shadow: 0 0 0 3px rgba(0, 194, 203, 0.15) !important;
    }

    /* ============================================================================
       CHAT MESSAGE VISUAL HIERARCHY
       ============================================================================ */

    /* Base: all chat messages get consistent padding + radius */
    [data-testid="stChatMessage"] {
        border-radius: 10px !important;
        padding: 10px 14px !important;
        margin-bottom: 6px !important;
        border-left: 3px solid transparent !important;
        transition: background 0.15s ease !important;
    }

    /* Agent / assistant messages — teal left stripe + very light teal wash */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
        background: rgba(0, 194, 203, 0.07) !important;
        border-left-color: rgba(0, 194, 203, 0.6) !important;
    }

    /* User messages — navy-grey tint, right-aligned feel via a darker stripe */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        background: rgba(13, 27, 42, 0.04) !important;
        border-left-color: rgba(13, 27, 42, 0.12) !important;
    }

    /* Fallback for browsers without :has() — use odd/even position */
    /* (Conversations start with assistant, so odd = agent, even = user in normal flow) */
    @supports not selector(:has(a)) {
        [data-testid="stChatMessage"]:nth-child(odd) {
            background: rgba(0, 194, 203, 0.07) !important;
            border-left: 3px solid rgba(0, 194, 203, 0.5) !important;
        }
        [data-testid="stChatMessage"]:nth-child(even) {
            background: rgba(13, 27, 42, 0.04) !important;
            border-left: 3px solid rgba(13, 27, 42, 0.12) !important;
        }
    }

    /* "📋 Concierge asks" badge — already injected inline, just ensure it stands out */
    [data-testid="stChatMessage"] em {
        color: var(--text-secondary) !important;
    }

    /* Chat input — teal focus ring */
    [data-testid="stChatInput"] textarea {
        border-radius: 10px !important;
    }

    /* ============================================================================
       MOBILE RESPONSIVE LAYOUT
       ============================================================================ */

    @media (max-width: 768px) {
        /* Stack the two-column chat + spec layout */
        .dpc-chat-col,
        .dpc-spec-col {
            width: 100% !important;
            flex: none !important;
        }

        /* Reduce card padding on mobile */
        .dpc-card {
            padding: 1rem !important;
            margin-bottom: .75rem !important;
        }

        /* Make progress bar steps wrap gracefully */
        div.prog-nav > div[data-testid="columns"] {
            flex-wrap: wrap !important;
            gap: .5rem !important;
        }

        /* Sidebar: auto-collapse on mobile */
        section[data-testid="stSidebar"] {
            min-width: 0 !important;
        }

        /* Full-width buttons on mobile */
        .stButton > button {
            width: 100% !important;
        }

        /* Hero headline — smaller on mobile */
        h1 {
            font-size: 1.8rem !important;
        }
    }

    @media (max-width: 480px) {
        /* Very small screens — simplify pill grids to 2 columns */
        div[data-testid="column"]:nth-child(3) {
            display: none !important;
        }
    }

    /* ============================================================================
       SIDEBAR DEMO MODE BADGE
       ============================================================================ */

    /* Demo mode toggle — gold tint when active */
    [data-testid="stSidebar"] .stToggle[data-value="true"] label {
        color: #F5A623 !important;
    }

    /* Sidebar toggle — teal when on, muted when off */
    [data-testid="stSidebar"] [data-testid="stToggle"] label {
        color: rgba(255,255,255,0.75) !important;
        font-size: .8rem !important;
    }

    [data-testid="stSidebar"] [data-testid="stToggle"] [data-testid="stMarkdownContainer"] p {
        color: rgba(255,255,255,0.75) !important;
        font-size: .8rem !important;
    }

    /* ============================================================================
       SCROLLBAR STYLING
       ============================================================================ */

    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(13, 27, 42, 0.15);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(0, 194, 203, 0.4);
    }

    /* ============================================================================
       AUTO-FOCUS HELPER — chat input refocus after bot response
       ============================================================================ */

    /* This class is added via JS after each bot message */
    .dpc-refocus-target {
        scroll-margin-top: 80px;
    }

    /* ── Guidance panel (replaces italic concierge bubble for field help) ── */
    .dpc-guidance {
        background: var(--surface);
        border-left: 3px solid var(--teal);
        border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
        padding: 12px 16px;
        margin-bottom: 1.5rem;
    }
    .dpc-guidance p {
        font-style: normal !important;
        color: var(--text-2);
        font-size: 0.875rem;
        line-height: 1.6;
        margin: 4px 0 0;
    }

    /* ── Label chip (replaces "✦ Concierge" prefix) ── */
    .dpc-label-chip {
        display: inline-block;
        font-size: 0.65rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--teal-d);
        background: rgba(0,194,203,0.08);
        border: 1px solid rgba(0,194,203,0.25);
        border-radius: 100px;
        padding: 2px 8px;
        margin-bottom: 6px;
    }

    /* ── Muted button wrapper (Tier 3 — skip/cancel/minor) ── */
    .dpc-btn-muted button,
    .dpc-btn-muted [data-testid^="stBaseButton"] {
        background: transparent !important;
        color: var(--text-3) !important;
        border: 1px solid rgba(13,27,42,0.12) !important;
        font-weight: 400 !important;
        font-size: 0.8rem !important;
        min-height: 36px !important;
        border-radius: var(--radius-sm) !important;
        box-shadow: none !important;
        transition: all 0.15s ease !important;
    }
    .dpc-btn-muted button:hover {
        color: var(--text-2) !important;
        border-color: rgba(13,27,42,0.25) !important;
    }

    /* ── Download button wrapper ── */
    .dpc-download button,
    .dpc-download [data-testid^="stBaseButton"] {
        background: var(--surface) !important;
        color: var(--teal-d) !important;
        border: 1px solid rgba(0,194,203,0.3) !important;
        font-weight: 500 !important;
        font-size: 0.8rem !important;
        border-radius: var(--radius-sm) !important;
        box-shadow: none !important;
        transition: all 0.15s ease !important;
    }
    .dpc-download button:hover {
        background: rgba(0,194,203,0.06) !important;
        border-color: var(--teal) !important;
    }

    /* ── Field label typography ── */
    .dpc-field-label {
        font-size: 1.05rem;
        font-weight: 600;
        color: var(--text-1);
        margin-bottom: 4px;
        display: block;
        font-style: normal !important;
    }
    .dpc-field-question {
        font-size: 0.875rem;
        color: var(--text-2);
        margin-bottom: 12px;
        line-height: 1.5;
        font-style: normal !important;
    }
    .dpc-field-explanation {
        font-size: 0.78rem;
        color: var(--text-3);
        margin-top: 8px;
        line-height: 1.5;
        font-style: normal !important;
    }
    .dpc-required-dot {
        display: inline-block;
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: var(--teal);
        margin-left: 4px;
        vertical-align: middle;
    }

    /* ── Dot stepper (chapter / field progress) ── */
    .dpc-stepper {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0;
        margin: 0 0 2rem;
        padding: 0.5rem 0;
    }
    .dpc-step {
        display: flex;
        flex-direction: column;
        align-items: center;
        cursor: pointer;
        position: relative;
    }
    .dpc-step-connector {
        width: 36px;
        height: 1px;
        background: rgba(13,27,42,0.12);
        margin: 0 4px;
        align-self: center;
        margin-bottom: 14px;
    }
    .dpc-step-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        transition: all 0.2s ease;
        cursor: pointer;
    }
    .dpc-step-dot--done {
        background: var(--emerald);
    }
    .dpc-step-dot--active {
        background: var(--teal);
        box-shadow: 0 0 0 4px rgba(0,194,203,0.2);
    }
    .dpc-step-dot--future {
        background: rgba(13,27,42,0.15);
    }
    .dpc-step-label {
        font-size: 0.6rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-top: 6px;
        white-space: nowrap;
        font-style: normal !important;
    }
    .dpc-step--done .dpc-step-label   { color: var(--emerald); }
    .dpc-step--active .dpc-step-label { color: var(--teal-d); }
    .dpc-step--future .dpc-step-label { color: var(--text-3); }

    /* ── Field card ── */
    .dpc-field-card {
        background: #fff;
        border: 1px solid rgba(13,27,42,0.08);
        border-radius: var(--radius-lg);
        padding: 2rem 2.5rem;
        box-shadow: var(--shadow-sm);
        margin-bottom: 1.5rem;
        min-height: 320px;
    }

    /* ── Live spec preview panel ── */
    .dpc-spec-preview {
        background: var(--surface);
        border-radius: var(--radius-md);
        padding: 1.25rem 1.5rem;
        min-height: 300px;
        position: sticky;
        top: 1rem;
        align-self: flex-start;
        max-height: calc(100vh - 120px);
        overflow-y: auto;
        overflow-x: hidden;
    }

    /* Sticky column wrapper — enables sticky on Streamlit column containers */
    [data-testid="column"]:has(.dpc-spec-preview) {
        position: sticky;
        top: 1rem;
        align-self: flex-start;
    }
    .dpc-spec-preview-title {
        font-size: 0.65rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--text-3);
        margin-bottom: 1rem;
        font-style: normal !important;
    }
    .dpc-spec-row {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        padding: 6px 0;
        border-bottom: 1px solid rgba(13,27,42,0.05);
        gap: 12px;
    }
    .dpc-spec-row-label {
        font-size: 0.75rem;
        color: var(--text-3);
        font-weight: 500;
        white-space: nowrap;
        flex-shrink: 0;
        font-style: normal !important;
    }
    .dpc-spec-row-value {
        font-size: 0.8rem;
        color: var(--text-1);
        font-weight: 500;
        text-align: right;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        max-width: 60%;
    }
    .dpc-spec-row--answered .dpc-spec-row-label { color: var(--teal-d); }
    .dpc-spec-row--skipped  .dpc-spec-row-label { color: var(--gold); }
    .dpc-spec-row--pending  .dpc-spec-row-label { color: var(--text-3); }
    .dpc-spec-row--auto     .dpc-spec-row-label { color: var(--emerald); }

    /* ── Colleague handoff card ── */
    .dpc-handoff-card {
        background: linear-gradient(135deg, rgba(0,194,203,0.04) 0%, rgba(0,107,115,0.06) 100%);
        border: 1px solid rgba(0,194,203,0.2);
        border-radius: var(--radius-lg);
        padding: 2rem;
        margin-top: 1.5rem;
    }

    /* ── No italic anywhere ── */
    .dpc-card p,
    .dpc-card span,
    .dpc-card div,
    .stMarkdown em,
    .stMarkdown i {
        font-style: normal !important;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def inject_chat_autofocus() -> None:
    """
    Inject JS to auto-focus the Streamlit chat input after bot responds.
    Call this at the end of the conversation render loop.
    """
    import streamlit as st
    st.components.v1.html(
        "<script>"
        "try {"
        "  var inp = window.parent.document.querySelector('[data-testid=\"stChatInputTextArea\"]');"
        "  if (inp) { inp.focus(); }"
        "} catch(e) {}"
        "</script>",
        height=0,
    )


def inject_keyboard_submit() -> None:
    """
    Inject JS so Cmd+Enter (Mac) / Ctrl+Enter (Win) submits the active form.
    Call this at the top of pages with primary action buttons.
    """
    import streamlit as st
    st.components.v1.html(
        "<script>"
        "try {"
        "  document.addEventListener('keydown', function(e) {"
        "    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {"
        "      var btns = window.parent.document.querySelectorAll('[data-testid=\"baseButton-primary\"]');"
        "      if (btns.length > 0) { btns[btns.length-1].click(); }"
        "    }"
        "  }, {once: true});"
        "} catch(e) {}"
        "</script>",
        height=0,
    )


def render_guidance(text: str, label: str = "Guidance") -> None:
    """Render a styled guidance panel — no italic, clean enterprise style."""
    import streamlit as st
    # Sanitise: strip any markdown italic markers that might have leaked in
    clean = text.replace("*", "").replace("_", " ").strip() if text else ""
    st.markdown(
        f'<div class="dpc-guidance">'
        f'<span class="dpc-label-chip">{label}</span>'
        f'<p>{clean}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )
