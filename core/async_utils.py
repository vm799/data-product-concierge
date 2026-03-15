"""
Async utility helpers for Data Product Concierge.

Provides a single shared run_async() that safely runs coroutines from
synchronous Streamlit render context. All async-to-sync bridges in the
app should use this instead of rolling their own event loop logic.
"""

import asyncio
import concurrent.futures
import logging
from typing import Any, Coroutine, Optional

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 15  # seconds

# Module-level executor — created once, reused across all run_async calls
_executor = concurrent.futures.ThreadPoolExecutor(max_workers=4, thread_name_prefix="async_bridge")


def run_async(coro: Coroutine, timeout: Optional[float] = _DEFAULT_TIMEOUT) -> Any:
    """
    Run an async coroutine from synchronous (Streamlit) context.

    Uses asyncio.run() when no event loop is running (standard Streamlit case).
    Falls back to thread executor when called from within an existing event loop.

    Args:
        coro: The coroutine to run.
        timeout: Max seconds to wait. None disables timeout (not recommended in UI context).

    Returns:
        The coroutine's return value.

    Raises:
        asyncio.TimeoutError: If the coroutine exceeds `timeout` seconds.
        Any exception raised by the coroutine itself.
    """
    wrapped = asyncio.wait_for(coro, timeout=timeout) if timeout is not None else coro
    try:
        asyncio.get_running_loop()
        # Already inside a running loop — use thread executor to avoid deadlock
        future = _executor.submit(asyncio.run, wrapped)
        return future.result(timeout=(timeout or 60) + 5)  # give a little extra for overhead
    except RuntimeError:
        # No running loop — standard Streamlit render thread case
        return asyncio.run(wrapped)
