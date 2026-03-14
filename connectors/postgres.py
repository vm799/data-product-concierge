"""PostgreSQL session and data product tracking."""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

import asyncpg
import jwt

logger = logging.getLogger(__name__)


class PostgresError(Exception):
    """Raised when PostgreSQL operations fail."""
    pass


class PostgresSessionManager:
    """
    Manages data product session persistence in PostgreSQL.

    Handles:
    - Async connection pooling via asyncpg
    - Session table creation and schema management
    - Session CRUD operations with JSON spec storage
    - User identity extraction from JWT claims
    - Pending session queries
    """

    def __init__(self):
        """Initialize PostgreSQL connection with environment configuration."""
        self.database_url = os.getenv("DATABASE_URL")

        if not self.database_url:
            raise PostgresError("Missing required DATABASE_URL environment variable")

        self.pool: Optional[asyncpg.pool.Pool] = None

        logger.info(
            "PostgresSessionManager initialized",
            extra={"database_url": self._mask_url(self.database_url)}
        )

    @staticmethod
    def _mask_url(url: str) -> str:
        """Mask sensitive parts of database URL for logging."""
        if "@" in url:
            parts = url.split("@")
            return f"{parts[0][:10]}***@{parts[1]}"
        return url

    async def _get_pool(self) -> asyncpg.pool.Pool:
        """
        Get or create connection pool.

        Returns:
            asyncpg.pool.Pool: Database connection pool

        Raises:
            PostgresError: If pool creation fails
        """
        if self.pool is None:
            try:
                self.pool = await asyncpg.create_pool(
                    self.database_url,
                    min_size=2,
                    max_size=10,
                    command_timeout=30,
                )
                logger.info("PostgreSQL connection pool created")
            except asyncpg.PostgresError as e:
                logger.error(
                    f"Failed to create connection pool: {str(e)}",
                    extra={"error_type": type(e).__name__}
                )
                raise PostgresError(f"Failed to create database connection pool: {str(e)}")

        return self.pool

    async def auto_create_table(self) -> None:
        """
        Create data_product_sessions table if it does not exist.

        Raises:
            PostgresError: If table creation fails
        """
        pool = await self._get_pool()

        create_table_sql = """
        CREATE TABLE IF NOT EXISTS data_product_sessions (
            session_id UUID PRIMARY KEY,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(50) NOT NULL,
            path VARCHAR(500),
            query TEXT,
            spec_json JSONB,
            collibra_id VARCHAR(100),
            submitted_by VARCHAR(255),
            md_export TEXT,
            json_export JSONB,
            csv_export TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_status ON data_product_sessions(status);
        CREATE INDEX IF NOT EXISTS idx_created_at ON data_product_sessions(created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_collibra_id ON data_product_sessions(collibra_id);
        """

        try:
            async with pool.acquire() as conn:
                await conn.execute(create_table_sql)
            logger.info("data_product_sessions table ready")
        except asyncpg.PostgresError as e:
            logger.error(
                f"Failed to create table: {str(e)}",
                extra={"error_type": type(e).__name__}
            )
            raise PostgresError(f"Failed to create sessions table: {str(e)}")

    @staticmethod
    def _extract_user_from_jwt(jwt_token: Optional[str]) -> Optional[str]:
        """
        Extract user identity from JWT token without verification.

        Attempts to extract preferred_username or email from JWT claims.
        Does not verify signature as this is for audit trail purposes only.

        Args:
            jwt_token: JWT token string (typically from Authorization header)

        Returns:
            str: User identity (preferred_username or email), or None
        """
        if not jwt_token:
            return None

        # Remove "Bearer " prefix if present
        token = jwt_token.replace("Bearer ", "").strip()

        try:
            decoded = jwt.decode(token, options={"verify_signature": False})
            user = decoded.get("preferred_username") or decoded.get("email")
            if user:
                logger.debug(
                    "Extracted user from JWT",
                    extra={"user": user[:20] + "***" if len(user) > 20 else user}
                )
            return user
        except Exception as e:
            logger.debug(
                f"Failed to extract user from JWT: {str(e)}",
                extra={"error_type": type(e).__name__}
            )
            return None

    async def save_session(
        self,
        session_id: UUID,
        spec: dict,
        status: str,
        collibra_id: Optional[str] = None,
        submitted_by: Optional[str] = None,
        path: Optional[str] = None,
        query: Optional[str] = None,
    ) -> None:
        """
        Create new data product session record.

        Args:
            session_id: Unique session identifier
            spec: Data product specification as dictionary
            status: Session status (pending, submitted, completed, failed)
            collibra_id: Collibra asset ID if registered
            submitted_by: User email or identifier
            path: Streamlit page path
            query: Natural language query description

        Raises:
            PostgresError: If insert fails
        """
        pool = await self._get_pool()

        insert_sql = """
        INSERT INTO data_product_sessions (
            session_id, spec_json, status, collibra_id, submitted_by, path, query
        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        """

        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    insert_sql,
                    session_id,
                    json.dumps(spec),
                    status,
                    collibra_id,
                    submitted_by,
                    path,
                    query,
                )
            logger.info(
                "Session saved",
                extra={
                    "session_id": str(session_id),
                    "status": status,
                    "collibra_id": collibra_id,
                }
            )
        except asyncpg.PostgresError as e:
            logger.error(
                f"Failed to save session: {str(e)}",
                extra={
                    "session_id": str(session_id),
                    "error_type": type(e).__name__,
                }
            )
            raise PostgresError(f"Failed to save session: {str(e)}")

    async def update_session(
        self,
        session_id: UUID,
        **kwargs: Any,
    ) -> None:
        """
        Update existing session record with arbitrary fields.

        Supports updating:
        - status, collibra_id, submitted_by, path, query
        - spec_json, md_export, json_export, csv_export

        Args:
            session_id: Session to update
            **kwargs: Fields to update (status, collibra_id, etc.)

        Raises:
            PostgresError: If update fails
        """
        if not kwargs:
            return

        pool = await self._get_pool()

        # Allowed fields to prevent SQL injection
        allowed_fields = {
            "status", "collibra_id", "submitted_by", "path", "query",
            "spec_json", "md_export", "json_export", "csv_export"
        }

        # Filter and validate fields
        update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not update_fields:
            logger.warning(
                "update_session called with no valid fields",
                extra={"session_id": str(session_id), "provided_fields": list(kwargs.keys())}
            )
            return

        # Convert dict fields to JSON strings
        if "spec_json" in update_fields and isinstance(update_fields["spec_json"], dict):
            update_fields["spec_json"] = json.dumps(update_fields["spec_json"])
        if "json_export" in update_fields and isinstance(update_fields["json_export"], dict):
            update_fields["json_export"] = json.dumps(update_fields["json_export"])

        # Build dynamic SQL
        set_clauses = [f"{field} = ${i+2}" for i, field in enumerate(update_fields.keys())]
        set_clause = ", ".join(set_clauses)

        update_sql = f"""
        UPDATE data_product_sessions
        SET {set_clause}, updated_at = CURRENT_TIMESTAMP
        WHERE session_id = $1
        """

        values = [session_id] + list(update_fields.values())

        try:
            async with pool.acquire() as conn:
                await conn.execute(update_sql, *values)
            logger.info(
                "Session updated",
                extra={
                    "session_id": str(session_id),
                    "updated_fields": list(update_fields.keys()),
                }
            )
        except asyncpg.PostgresError as e:
            logger.error(
                f"Failed to update session: {str(e)}",
                extra={
                    "session_id": str(session_id),
                    "error_type": type(e).__name__,
                }
            )
            raise PostgresError(f"Failed to update session: {str(e)}")

    async def load_session(self, session_id: UUID) -> Optional[dict]:
        """
        Load session record by ID.

        Args:
            session_id: Session identifier

        Returns:
            dict: Session record with parsed JSON fields, or None if not found

        Raises:
            PostgresError: If query fails
        """
        pool = await self._get_pool()

        select_sql = """
        SELECT
            session_id, created_at, updated_at, status, path, query,
            spec_json, collibra_id, submitted_by, md_export, json_export, csv_export
        FROM data_product_sessions
        WHERE session_id = $1
        """

        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(select_sql, session_id)

            if not row:
                logger.debug(
                    "Session not found",
                    extra={"session_id": str(session_id)}
                )
                return None

            # Convert record to dict and parse JSON fields
            session_dict = dict(row)

            if session_dict.get("spec_json"):
                if isinstance(session_dict["spec_json"], str):
                    session_dict["spec_json"] = json.loads(session_dict["spec_json"])

            if session_dict.get("json_export"):
                if isinstance(session_dict["json_export"], str):
                    session_dict["json_export"] = json.loads(session_dict["json_export"])

            logger.debug(
                "Session loaded",
                extra={
                    "session_id": str(session_id),
                    "status": session_dict.get("status"),
                }
            )
            return session_dict

        except asyncpg.PostgresError as e:
            logger.error(
                f"Failed to load session: {str(e)}",
                extra={
                    "session_id": str(session_id),
                    "error_type": type(e).__name__,
                }
            )
            raise PostgresError(f"Failed to load session: {str(e)}")

    async def list_pending(self, limit: int = 100) -> list[dict]:
        """
        List all pending data product sessions.

        Args:
            limit: Maximum number of records to return

        Returns:
            list[dict]: Pending session records ordered by creation date

        Raises:
            PostgresError: If query fails
        """
        pool = await self._get_pool()

        select_sql = """
        SELECT
            session_id, created_at, updated_at, status, path, query,
            spec_json, collibra_id, submitted_by, md_export, json_export, csv_export
        FROM data_product_sessions
        WHERE status IN ('pending', 'submitted')
        ORDER BY created_at DESC
        LIMIT $1
        """

        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch(select_sql, limit)

            sessions = []
            for row in rows:
                session_dict = dict(row)

                # Parse JSON fields
                if session_dict.get("spec_json"):
                    if isinstance(session_dict["spec_json"], str):
                        session_dict["spec_json"] = json.loads(session_dict["spec_json"])

                if session_dict.get("json_export"):
                    if isinstance(session_dict["json_export"], str):
                        session_dict["json_export"] = json.loads(session_dict["json_export"])

                sessions.append(session_dict)

            logger.info(
                "Pending sessions listed",
                extra={"count": len(sessions)}
            )
            return sessions

        except asyncpg.PostgresError as e:
            logger.error(
                f"Failed to list pending sessions: {str(e)}",
                extra={"error_type": type(e).__name__}
            )
            raise PostgresError(f"Failed to list pending sessions: {str(e)}")

    async def close(self) -> None:
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("PostgreSQL connection pool closed")


# Singleton instance management
_session_manager: Optional[PostgresSessionManager] = None


async def get_session_manager() -> PostgresSessionManager:
    """
    Get or create singleton PostgresSessionManager instance.

    Returns:
        PostgresSessionManager: Singleton instance
    """
    global _session_manager
    if _session_manager is None:
        _session_manager = PostgresSessionManager()
        await _session_manager.auto_create_table()
    return _session_manager
