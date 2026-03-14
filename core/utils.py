"""Utility functions for Data Product Concierge application."""

import logging
import re
import uuid
from datetime import datetime
from typing import Any, Optional

import streamlit as st

logger = logging.getLogger(__name__)


def set_state(key: str, value: Any) -> None:
    """
    Set Streamlit session state and trigger rerun if value changed.

    Args:
        key: Session state key
        value: New value to set
    """
    if key not in st.session_state or st.session_state[key] != value:
        st.session_state[key] = value
        logger.debug(
            "Session state updated",
            extra={
                "key": key,
                "value_type": type(value).__name__,
                "request_id": get_request_id(),
            }
        )


def format_error(exc: Exception) -> str:
    """
    Map exception types to user-friendly error messages.

    Args:
        exc: Exception to format

    Returns:
        str: User-friendly error message
    """
    error_msg = str(exc)

    # Map exception types to friendly messages
    if isinstance(exc, TimeoutError):
        return "Request timed out. The operation took too long. Please try again."

    elif isinstance(exc, ConnectionError):
        return "Connection failed. Unable to reach the server. Please check your network."

    elif "401" in error_msg or "Unauthorized" in error_msg:
        return "Authentication failed. Your session may have expired. Please refresh."

    elif "403" in error_msg or "Forbidden" in error_msg:
        return "Access denied. You don't have permission to perform this action."

    elif "404" in error_msg or "Not found" in error_msg:
        return "Resource not found. It may have been deleted or the path is incorrect."

    elif "429" in error_msg or "Too many requests" in error_msg:
        return "Too many requests. Please wait a moment and try again."

    elif "500" in error_msg or "Internal server error" in error_msg:
        return "Server error. The service encountered an issue. Please try again later."

    elif "502" in error_msg or "Bad gateway" in error_msg:
        return "Gateway error. The service is temporarily unavailable. Please try again."

    elif "503" in error_msg or "Service unavailable" in error_msg:
        return "Service unavailable. Please try again later."

    elif "timeout" in error_msg.lower():
        return "Operation timed out. Please try again."

    else:
        # Generic error - truncate to reasonable length
        truncated = truncate(error_msg, 200)
        return f"An error occurred: {truncated}"


def get_request_id() -> str:
    """
    Get or create unique request ID for current page load.

    Returns:
        str: UUID string for request tracking
    """
    if "_request_id" not in st.session_state:
        st.session_state["_request_id"] = str(uuid.uuid4())
    return st.session_state["_request_id"]


def truncate(text: Optional[str], max_len: int = 100) -> str:
    """
    Truncate text to maximum length with ellipsis.

    Args:
        text: Text to truncate
        max_len: Maximum length

    Returns:
        str: Truncated text, or empty string if input is None
    """
    if text is None:
        return ""

    if len(text) <= max_len:
        return text

    return text[:max_len - 3] + "..."


def format_date(dt: Optional[datetime]) -> str:
    """
    Format datetime object for consistent display.

    Args:
        dt: DateTime object

    Returns:
        str: Formatted date string (YYYY-MM-DD HH:MM:SS), or empty string if None
    """
    if dt is None:
        return ""

    try:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        logger.warning(
            f"Failed to format date: {str(e)}",
            extra={"error_type": type(e).__name__}
        )
        return str(dt)


def pluralise(count: int, noun: str) -> str:
    """
    Return singular or plural form of noun based on count.

    Simple implementation that adds 's' for plurals.
    For irregular plurals, pass the full form directly.

    Args:
        count: Quantity
        noun: Singular noun form

    Returns:
        str: "N noun" or "N nouns"
    """
    if count == 1:
        return f"1 {noun}"

    # Simple pluralization: add 's'
    # More complex cases should pass complete forms
    if noun.endswith("y"):
        plural = noun[:-1] + "ies"
    elif noun.endswith(("s", "x", "z", "ch", "sh")):
        plural = noun + "es"
    else:
        plural = noun + "s"

    return f"{count} {plural}"


def sanitize_filename(name: str, max_length: int = 200) -> str:
    """
    Convert arbitrary string to safe filename.

    - Removes special characters except underscore, hyphen, dot
    - Limits length
    - Ensures non-empty result

    Args:
        name: Original filename or identifier
        max_length: Maximum filename length

    Returns:
        str: Safe filename
    """
    if not name:
        return "export"

    # Replace spaces with underscores
    safe_name = name.replace(" ", "_")

    # Keep only alphanumeric, underscore, hyphen, dot
    safe_name = re.sub(r"[^a-zA-Z0-9._-]", "", safe_name)

    # Remove leading/trailing dots and hyphens
    safe_name = safe_name.strip(".-")

    # Truncate to max length
    if len(safe_name) > max_length:
        safe_name = safe_name[:max_length].rstrip(".-")

    # Ensure we have a result
    if not safe_name:
        safe_name = "export"

    return safe_name


def format_json_export(data: dict) -> str:
    """
    Format dictionary as pretty-printed JSON string.

    Args:
        data: Dictionary to serialize

    Returns:
        str: Pretty-printed JSON
    """
    try:
        return json.dumps(data, indent=2, default=str)
    except Exception as e:
        logger.warning(
            f"Failed to format JSON: {str(e)}",
            extra={"error_type": type(e).__name__}
        )
        return str(data)


def format_markdown_export(title: str, content: dict, sections: Optional[list] = None) -> str:
    """
    Format specification as Markdown document.

    Args:
        title: Document title
        content: Main content dictionary
        sections: Optional list of (section_name, data) tuples

    Returns:
        str: Markdown formatted document
    """
    lines = [
        f"# {title}",
        "",
        f"Generated: {format_date(datetime.now())}",
        "",
    ]

    # Add main content sections
    if content:
        for key, value in content.items():
            if isinstance(value, dict):
                lines.append(f"## {key.title()}")
                for k, v in value.items():
                    lines.append(f"- **{k}**: {v}")
                lines.append("")
            elif isinstance(value, list):
                lines.append(f"## {key.title()}")
                for item in value:
                    lines.append(f"- {item}")
                lines.append("")
            else:
                lines.append(f"**{key.title()}**: {value}")
                lines.append("")

    # Add custom sections
    if sections:
        for section_name, data in sections:
            lines.append(f"## {section_name}")
            if isinstance(data, dict):
                for k, v in data.items():
                    lines.append(f"- **{k}**: {v}")
            elif isinstance(data, list):
                for item in data:
                    lines.append(f"- {item}")
            else:
                lines.append(str(data))
            lines.append("")

    return "\n".join(lines)


# Import json at module level for use in format_json_export
import json
