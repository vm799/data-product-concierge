"""Collibra-specific authentication and API helpers."""

import logging
import os
from typing import Optional

import httpx

from .apim_auth import APIMAuthError, APIMTokenManager, SessionExpiredError

logger = logging.getLogger(__name__)


class CollibraAuthError(Exception):
    """Raised when Collibra API operations fail."""
    pass


class CollibraAuthenticator:
    """
    Thin wrapper around APIMTokenManager for Collibra-scoped API calls.

    Handles:
    - Collibra base URL construction
    - APIM gateway header preparation
    - 401 retry logic with session expiration
    - Async HTTP helpers for Collibra REST API
    """

    def __init__(self):
        """Initialize authenticator with environment configuration."""
        self.apim_base_url = os.getenv("APIM_BASE_URL")
        self.collibra_instance_url = os.getenv("COLLIBRA_INSTANCE_URL")

        if not self.apim_base_url:
            raise CollibraAuthError("Missing required APIM_BASE_URL environment variable")

        # Remove trailing slashes for consistent URL construction
        self.apim_base_url = self.apim_base_url.rstrip("/")

        self.token_manager = APIMTokenManager.get_instance()

        logger.info(
            "CollibraAuthenticator initialized",
            extra={
                "apim_base_url": self.apim_base_url,
                "collibra_instance_url": self.collibra_instance_url or "Not configured",
            }
        )

    def get_collibra_base_url(self) -> str:
        """
        Get the base URL for Collibra API calls.

        Returns:
            str: Base URL for Collibra 2.0 REST API
        """
        return f"{self.apim_base_url}/collibra/rest/2.0"

    def get_collibra_headers(self) -> dict:
        """
        Get HTTP headers for Collibra API requests.

        Returns:
            dict: Headers with APIM authentication and Collibra settings

        Raises:
            SessionExpiredError: If authentication session has expired
            APIMAuthError: If token fetch fails
        """
        return self.token_manager.get_auth_headers()

    async def collibra_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict] = None,
        params: Optional[dict] = None,
        timeout: float = 30.0,
    ) -> dict:
        """
        Make an authenticated HTTP request to Collibra API with 401 retry logic.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            endpoint: API endpoint path (e.g., "/assets" or "/assets/123")
            data: Request body for POST/PUT/PATCH
            params: Query parameters
            timeout: Request timeout in seconds

        Returns:
            dict: Parsed JSON response

        Raises:
            SessionExpiredError: If authentication has expired
            CollibraAuthError: If API request fails
            httpx.HTTPError: For network-level errors
        """
        url = f"{self.get_collibra_base_url()}{endpoint}"
        headers = self.get_collibra_headers()
        retry_count = 0
        max_retries = 1

        while retry_count <= max_retries:
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    request_kwargs = {
                        "headers": headers,
                        "params": params or {},
                    }

                    if data:
                        request_kwargs["json"] = data

                    logger.debug(
                        f"Making Collibra {method} request",
                        extra={
                            "url": url,
                            "method": method,
                            "retry_count": retry_count,
                            "request_id": headers.get("X-Request-ID"),
                        }
                    )

                    response = await client.request(method, url, **request_kwargs)

                    # Handle 401 with retry
                    if response.status_code == 401:
                        if retry_count < max_retries:
                            retry_count += 1
                            logger.info(
                                "Received 401 from Collibra, retrying with fresh token",
                                extra={
                                    "url": url,
                                    "request_id": headers.get("X-Request-ID"),
                                    "retry_attempt": retry_count,
                                }
                            )
                            # Clear token and refresh headers
                            self.token_manager._clear_token_cache()
                            headers = self.get_collibra_headers()
                            continue
                        else:
                            logger.error(
                                "Received 401 from Collibra after retry",
                                extra={
                                    "url": url,
                                    "request_id": headers.get("X-Request-ID"),
                                }
                            )
                            raise SessionExpiredError(
                                "Collibra authentication failed. Session may have expired."
                            )

                    # Handle other HTTP errors
                    if response.status_code >= 400:
                        error_detail = response.text if response.text else "No details"
                        logger.error(
                            f"Collibra API error {response.status_code}",
                            extra={
                                "url": url,
                                "status_code": response.status_code,
                                "error_detail": error_detail[:200],
                                "request_id": headers.get("X-Request-ID"),
                            }
                        )
                        raise CollibraAuthError(
                            f"Collibra API returned {response.status_code}: {error_detail[:100]}"
                        )

                    result = response.json()
                    logger.info(
                        f"Collibra {method} request succeeded",
                        extra={
                            "url": url,
                            "status_code": response.status_code,
                            "request_id": headers.get("X-Request-ID"),
                        }
                    )
                    return result

            except httpx.TimeoutError as e:
                logger.error(
                    f"Collibra request timeout",
                    extra={
                        "url": url,
                        "timeout": timeout,
                        "request_id": headers.get("X-Request-ID"),
                    }
                )
                raise CollibraAuthError(f"Collibra request timed out after {timeout}s: {str(e)}")

            except httpx.HTTPError as e:
                logger.error(
                    f"Collibra request failed: {str(e)}",
                    extra={
                        "url": url,
                        "error_type": type(e).__name__,
                        "request_id": headers.get("X-Request-ID"),
                    }
                )
                raise CollibraAuthError(f"Collibra request failed: {str(e)}")

        # Should not reach here due to exceptions, but for safety
        raise CollibraAuthError("Collibra request failed: max retries exceeded")
