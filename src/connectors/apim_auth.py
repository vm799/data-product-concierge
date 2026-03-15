"""APIM Gateway authentication and token management."""

import asyncio
import logging
import os
import time
import uuid
from datetime import datetime, timedelta
from typing import Optional

import httpx
import streamlit as st

logger = logging.getLogger(__name__)


class APIMAuthError(Exception):
    """Raised when APIM authentication fails."""
    pass


class SessionExpiredError(Exception):
    """Raised when authentication session has expired."""
    pass


class APIMTokenManager:
    """
    Manages JWT token lifecycle for APIM Gateway authentication.

    Handles:
    - Token fetching via OAuth2 client_credentials grant
    - Token caching with automatic refresh 60s before expiry
    - 401 retry logic with session expiration detection
    - Request ID tracking for audit trails
    - Streamlit session state persistence
    """

    # Class-level configuration keys
    _INSTANCE_KEY = "_apim_token_manager"
    _TOKEN_KEY = "_apim_token"
    _EXPIRY_KEY = "_apim_token_expiry"
    _REQUEST_ID_KEY = "_apim_request_id"

    def __init__(self):
        """Initialize token manager with environment configuration."""
        self.token_endpoint = os.getenv("APIM_TOKEN_ENDPOINT")
        self.client_id = os.getenv("APIM_CLIENT_ID")
        self.client_secret = os.getenv("APIM_CLIENT_SECRET")
        self.scope = os.getenv("APIM_SCOPE", "")
        self.subscription_key = os.getenv("APIM_SUBSCRIPTION_KEY")
        self.grant_type = "client_credentials"
        self._retry_count = 0

        # Validate required configuration
        if not all([self.token_endpoint, self.client_id, self.client_secret, self.subscription_key]):
            raise APIMAuthError(
                "Missing required APIM configuration: "
                "APIM_TOKEN_ENDPOINT, APIM_CLIENT_ID, APIM_CLIENT_SECRET, APIM_SUBSCRIPTION_KEY"
            )

        logger.info(
            "APIMTokenManager initialized",
            extra={
                "token_endpoint": self.token_endpoint,
                "client_id": self.client_id[:10] + "***",
                "request_id": self._get_request_id()
            }
        )

    @staticmethod
    def _get_request_id() -> str:
        """Get or create request ID for this API call sequence."""
        if APIMTokenManager._REQUEST_ID_KEY not in st.session_state:
            st.session_state[APIMTokenManager._REQUEST_ID_KEY] = str(uuid.uuid4())
        return st.session_state[APIMTokenManager._REQUEST_ID_KEY]

    @staticmethod
    def get_instance() -> "APIMTokenManager":
        """
        Get singleton instance from Streamlit session state.

        Returns:
            APIMTokenManager: Singleton instance for current session

        Raises:
            APIMAuthError: If initialization fails
        """
        if APIMTokenManager._INSTANCE_KEY not in st.session_state:
            st.session_state[APIMTokenManager._INSTANCE_KEY] = APIMTokenManager()
        return st.session_state[APIMTokenManager._INSTANCE_KEY]

    async def _fetch_token(self) -> dict:
        """
        Fetch new JWT token from APIM OAuth2 endpoint.

        Returns:
            dict: Token response containing access_token, expires_in, etc.

        Raises:
            APIMAuthError: If token fetch fails
        """
        request_id = self._get_request_id()

        payload = {
            "grant_type": self.grant_type,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        if self.scope:
            payload["scope"] = self.scope

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-APIM-Subscription-Key": self.subscription_key,
        }

        logger.info(
            "Fetching APIM token",
            extra={
                "request_id": request_id,
                "endpoint": self.token_endpoint,
                "client_id": self.client_id[:10] + "***",
            }
        )

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.token_endpoint,
                    data=payload,
                    headers=headers,
                )

                if response.status_code == 401:
                    logger.warning(
                        "APIM token endpoint returned 401 Unauthorized",
                        extra={
                            "request_id": request_id,
                            "status_code": response.status_code,
                            "client_id": self.client_id[:10] + "***",
                        }
                    )
                    raise APIMAuthError("APIM authentication failed: 401 Unauthorized")

                response.raise_for_status()

                token_data = response.json()
                logger.info(
                    "APIM token fetched successfully",
                    extra={
                        "request_id": request_id,
                        "expires_in": token_data.get("expires_in"),
                    }
                )
                return token_data

        except httpx.HTTPError as e:
            logger.error(
                f"APIM token fetch failed: {str(e)}",
                extra={
                    "request_id": request_id,
                    "error_type": type(e).__name__,
                }
            )
            raise APIMAuthError(f"Failed to fetch APIM token: {str(e)}")

    def _is_expired(self) -> bool:
        """
        Check if cached token is expired or within 60 seconds of expiry.

        Returns:
            bool: True if token should be refreshed
        """
        if self._TOKEN_KEY not in st.session_state or self._EXPIRY_KEY not in st.session_state:
            return True

        expiry_timestamp = st.session_state[self._EXPIRY_KEY]
        now = time.time()
        refresh_threshold = 60  # seconds

        is_expired = (expiry_timestamp - now) < refresh_threshold

        if is_expired:
            logger.debug(
                "Token expired or near expiry, will refresh",
                extra={
                    "request_id": self._get_request_id(),
                    "seconds_until_expiry": max(0, expiry_timestamp - now),
                }
            )

        return is_expired

    def _clear_token_cache(self) -> None:
        """Clear cached token and expiry from session state."""
        if self._TOKEN_KEY in st.session_state:
            del st.session_state[self._TOKEN_KEY]
        if self._EXPIRY_KEY in st.session_state:
            del st.session_state[self._EXPIRY_KEY]
        logger.info(
            "Token cache cleared",
            extra={"request_id": self._get_request_id()}
        )

    def get_token(self) -> str:
        """
        Get valid bearer token, refreshing if necessary.

        Implements 401 retry logic:
        - First 401: clear cache and retry once
        - Second 401: raise SessionExpiredError

        Returns:
            str: Bearer token (without "Bearer " prefix)

        Raises:
            SessionExpiredError: If authentication session has expired
            APIMAuthError: If token fetch fails for other reasons
        """
        request_id = self._get_request_id()

        if not self._is_expired():
            token = st.session_state.get(self._TOKEN_KEY)
            logger.debug(
                "Using cached token",
                extra={
                    "request_id": request_id,
                    "expires_in": st.session_state.get(self._EXPIRY_KEY, 0) - time.time(),
                }
            )
            return token

        # Need to fetch new token
        try:
            token_response = asyncio.run(self._fetch_token())
        except APIMAuthError as e:
            if "401" in str(e) and self._retry_count == 0:
                self._retry_count += 1
                self._clear_token_cache()
                logger.info(
                    "Retrying token fetch after 401",
                    extra={"request_id": request_id}
                )
                try:
                    token_response = asyncio.run(self._fetch_token())
                except APIMAuthError as retry_error:
                    raise SessionExpiredError(
                        "Authentication session expired. Please refresh your session."
                    ) from retry_error
                finally:
                    self._retry_count = 0
            else:
                raise

        access_token = token_response.get("access_token")
        expires_in = token_response.get("expires_in", 3600)

        # Cache token with expiry timestamp
        st.session_state[self._TOKEN_KEY] = access_token
        st.session_state[self._EXPIRY_KEY] = time.time() + expires_in

        logger.info(
            "Token cached",
            extra={
                "request_id": request_id,
                "expires_in": expires_in,
                "expiry_timestamp": st.session_state[self._EXPIRY_KEY],
            }
        )

        return access_token

    def get_auth_headers(self) -> dict:
        """
        Get complete HTTP headers for APIM requests.

        Returns:
            dict: Headers with Authorization bearer, subscription key, and content type

        Raises:
            SessionExpiredError: If authentication has expired
            APIMAuthError: If token fetch fails
        """
        token = self.get_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "X-APIM-Subscription-Key": self.subscription_key,
            "Content-Type": "application/json",
            "X-Request-ID": self._get_request_id(),
        }

        logger.debug(
            "Auth headers prepared",
            extra={
                "request_id": self._get_request_id(),
                "has_bearer_token": bool(token),
                "has_subscription_key": bool(self.subscription_key),
            }
        )

        return headers

    async def get_llm_headers(self) -> dict:
        """
        Return auth headers for LLM calls routed through APIM (Azure OpenAI).
        Reuses the existing APIM bearer token cache — no new auth roundtrip needed.
        """
        base = self.get_auth_headers()
        return {
            "Authorization": base["Authorization"],
            "X-APIM-Subscription-Key": base["X-APIM-Subscription-Key"],
            "api-key": base["Authorization"].removeprefix("Bearer "),
            "Content-Type": "application/json",
        }
