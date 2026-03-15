"""
Snowflake DDL Preview component for Data Product Concierge.

Renders an auto-generated CREATE statement, GRANT, and optional Task
from a DataProductSpec. Shown in the handoff/review screen.
"""

from typing import Optional

import streamlit as st

from models.data_product import DataProductSpec


def render_snowflake_preview(spec: DataProductSpec) -> None:
    """
    Render a Snowflake DDL preview panel.

    Shows:
      - Generated CREATE TABLE/VIEW/DYNAMIC TABLE statement
      - GRANT SELECT statement
      - Missing fields that prevent complete DDL
      - Download button for the DDL file

    Args:
        spec: The DataProductSpec to generate DDL from.
    """
    ddl = spec.to_snowflake_ddl()

    # Completeness check for DDL-critical fields
    ddl_fields = {
        "Schema Location": spec.schema_location,
        "Materialization Type": spec.materialization_type,
        "Snowflake Role": spec.snowflake_role,
        "Column Definitions": spec.column_definitions,
    }
    missing_ddl = [k for k, v in ddl_fields.items() if not v]
    complete = len(missing_ddl) == 0

    # Header
    completeness_color = "#00C48C" if complete else "#F5A623"
    completeness_label = "DDL Ready" if complete else f"{len(missing_ddl)} field(s) needed"
    completeness_icon = "✅" if complete else "⚠"

    st.markdown(
        f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:.75rem;">'
        f'<h4 style="margin:0;color:var(--text-primary);">🏔 Snowflake DDL Preview</h4>'
        f'<span style="font-size:.8rem;font-weight:600;color:{completeness_color};">'
        f'{completeness_icon} {completeness_label}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Missing field warnings
    if missing_ddl:
        missing_str = " · ".join(missing_ddl)
        st.markdown(
            f'<div style="background:rgba(245,166,35,.08);border:1px solid rgba(245,166,35,.3);'
            f'border-radius:8px;padding:.6rem .9rem;margin-bottom:.75rem;">'
            f'<span style="color:#F5A623;font-size:.8rem;font-weight:600;">Missing for complete DDL: </span>'
            f'<span style="color:var(--text-secondary);font-size:.8rem;">{missing_str}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # DDL code block
    st.code(ddl, language="sql")

    # Download button
    col1, col2 = st.columns([1, 1])
    with col1:
        object_name = (spec.schema_location or "data_product").replace(".", "_").lower()
        st.download_button(
            label="⬇ Download DDL (.sql)",
            data=ddl,
            file_name=f"{object_name}_ddl.sql",
            mime="text/plain",
            use_container_width=True,
        )
    with col2:
        # Show what type of object will be created
        mat_type = spec.materialization_type or "Table (default)"
        st.markdown(
            f'<div style="text-align:center;padding:.4rem;">'
            f'<span style="font-size:.75rem;color:var(--text-muted);">Object type</span><br>'
            f'<span style="font-size:.9rem;font-weight:600;color:var(--text-primary);">{mat_type}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
