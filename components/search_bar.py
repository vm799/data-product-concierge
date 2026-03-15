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

    html = '<div style="background: #F0F4F8; padding: 1.25rem 1.5rem; border-radius: 12px; max-width: 640px; color: #5B6A7E; font-size: .95rem; line-height: 1.55; margin-bottom: 1.25rem;">Tell me what data you\'re looking for — describe it in your own words, and I\'ll find the best match in our catalogue.</div>'

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
