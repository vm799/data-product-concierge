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

    html = '<div style="text-align: center; padding: 2rem;"><h1 style="color: #0D1B2A; font-size: 2.5rem; margin-bottom: 1rem;">Data Product Concierge</h1><p style="color: #5B6A7E; font-size: 1.2rem; margin-bottom: 2rem;">Find, reuse, or create governed data products</p><div style="background: #F0F4F8; padding: 1.5rem; border-radius: 16px; max-width: 600px; margin: 0 auto; text-align: left;">Welcome! I\'m your Data Product Concierge. Tell me what data you\'re looking for — describe it in your own words, and I\'ll find the best match in our catalogue.</div></div>'

    st.html(html)
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
