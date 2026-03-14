"""
Hero search screen component for Data Product Concierge.

Renders full viewport-height search interface with logo, tagline, concierge welcome,
and large search input field. Production-ready with zero mock data.
"""

import streamlit as st


def render_hero():
    """
    Render full viewport-height hero search screen.

    Returns:
        tuple: (query: str, submitted: bool)
            - query: Search query string from input field
            - submitted: True if "Find Data Products" button was clicked
    """

    html = """
    <div class="dpc-hero">
        <div style="max-width: 700px; width: 100%;">

            <!-- Logo / App Title -->
            <h1 class="dpc-hero-heading">Data Product Concierge</h1>

            <!-- Tagline -->
            <p class="dpc-hero-subheading">
                Find, reuse, or create governed data products
            </p>

            <!-- Concierge Welcome Message -->
            <div class="dpc-concierge" style="text-align: left; max-width: 100%; margin-left: 0; margin-right: 0; margin-bottom: 2rem;">
                Welcome! I'm your Data Product Concierge. Tell me what data you're looking for — describe it in your own words, and I'll find the best match in our catalogue.
            </div>

        </div>
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)

    # Search input - full width with custom styling
    query = st.text_input(
        label="",
        placeholder="Describe the data you need — e.g. ESG emissions for Paris-aligned European funds",
        key="search_query",
    )

    # Submit button - full width
    col1, col2, col3 = st.columns([0.2, 0.6, 0.2])
    with col2:
        submitted = st.button(
            "Find Data Products →",
            use_container_width=True,
            key="search_submit",
        )

    return query, submitted
