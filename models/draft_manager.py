"""
Draft persistence manager for Data Product Concierge.

Enables auto-save and session resume for in-progress data product specs.
Each draft is identified by a UUID and optionally associated with a user.

Database table (auto-created if not exists):
    CREATE TABLE data_product_drafts (
        draft_id      UUID PRIMARY KEY,
        user_id       VARCHAR(255),
        display_name  VARCHAR(500),
        spec_json     JSONB,
        step          VARCHAR(50),
        chapter       INTEGER DEFAULT 1,
        path          VARCHAR(50),
        status        VARCHAR(50) DEFAULT 'draft',
        created_at    TIMESTAMPTZ DEFAULT NOW(),
        updated_at    TIMESTAMPTZ DEFAULT NOW()
    );

Usage:
    dm = DraftManager(dsn="postgresql://...")
    draft_id = await dm.save(draft_id, user_id, display_name, spec, step, chapter, path)
    result = await dm.load(draft_id)   # Returns DraftRecord or None
    drafts = await dm.list_user_drafts(user_id, limit=10)
    await dm.delete(draft_id)
"""

import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    import asyncpg
    HAS_ASYNCPG = True
except ImportError:
    HAS_ASYNCPG = False


# ---------------------------------------------------------------------------
# Data class for a loaded draft record
# ---------------------------------------------------------------------------

@dataclass
class DraftRecord:
    """A persisted draft loaded from Postgres."""
    draft_id: str
    user_id: Optional[str]
    display_name: str
    spec_dict: Dict[str, Any]  # Raw dict — caller reconstructs DataProductSpec
    step: str
    chapter: int
    path: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# DraftManager
# ---------------------------------------------------------------------------

class DraftManager:
    """
    Async Postgres-backed draft persistence.

    Falls back gracefully (no-op) when Postgres is not configured, so the
    app works in demo mode without any database.
    """

    CREATE_TABLE_SQL = """
        CREATE TABLE IF NOT EXISTS data_product_drafts (
            draft_id      UUID PRIMARY KEY,
            user_id       VARCHAR(255),
            display_name  VARCHAR(500) NOT NULL DEFAULT '',
            spec_json     JSONB NOT NULL DEFAULT '{}',
            step          VARCHAR(50)  NOT NULL DEFAULT 'search',
            chapter       INTEGER      NOT NULL DEFAULT 1,
            path          VARCHAR(50),
            status        VARCHAR(50)  NOT NULL DEFAULT 'draft',
            created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_drafts_user_id  ON data_product_drafts(user_id);
        CREATE INDEX IF NOT EXISTS idx_drafts_updated  ON data_product_drafts(updated_at DESC);
    """

    UPSERT_SQL = """
        INSERT INTO data_product_drafts
            (draft_id, user_id, display_name, spec_json, step, chapter, path, status, updated_at)
        VALUES ($1, $2, $3, $4::jsonb, $5, $6, $7, $8, NOW())
        ON CONFLICT (draft_id) DO UPDATE SET
            user_id       = EXCLUDED.user_id,
            display_name  = EXCLUDED.display_name,
            spec_json     = EXCLUDED.spec_json,
            step          = EXCLUDED.step,
            chapter       = EXCLUDED.chapter,
            path          = EXCLUDED.path,
            status        = EXCLUDED.status,
            updated_at    = NOW()
        RETURNING draft_id::text;
    """

    SELECT_SQL = """
        SELECT draft_id::text, user_id, display_name, spec_json,
               step, chapter, path, status, created_at, updated_at
        FROM   data_product_drafts
        WHERE  draft_id = $1;
    """

    LIST_SQL = """
        SELECT draft_id::text, user_id, display_name, spec_json,
               step, chapter, path, status, created_at, updated_at
        FROM   data_product_drafts
        WHERE  user_id = $1 AND status != 'deleted'
        ORDER  BY updated_at DESC
        LIMIT  $2;
    """

    DELETE_SQL = """
        UPDATE data_product_drafts SET status = 'deleted', updated_at = NOW()
        WHERE  draft_id = $1;
    """

    def __init__(self, dsn: Optional[str] = None) -> None:
        """
        Args:
            dsn: asyncpg DSN string. Falls back to POSTGRES_DSN env var,
                 then assembles from POSTGRES_HOST/DB/USER/PASSWORD env vars.
        """
        self._dsn = dsn or self._dsn_from_env()
        self._pool: Optional[Any] = None  # asyncpg pool
        self._available = bool(self._dsn) and HAS_ASYNCPG

    # ── DSN helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _dsn_from_env() -> Optional[str]:
        """Build DSN from environment variables."""
        explicit = os.getenv("POSTGRES_DSN")
        if explicit:
            return explicit
        host = os.getenv("POSTGRES_HOST")
        if not host:
            return None
        db   = os.getenv("POSTGRES_DB", "concierge")
        user = os.getenv("POSTGRES_USER", "postgres")
        pw   = os.getenv("POSTGRES_PASSWORD", "")
        port = os.getenv("POSTGRES_PORT", "5432")
        return f"postgresql://{user}:{pw}@{host}:{port}/{db}"

    # ── Pool management ───────────────────────────────────────────────────────

    async def _get_pool(self):
        """Return (or create) the connection pool. Returns None if unavailable."""
        if not self._available:
            return None
        if self._pool is None:
            try:
                self._pool = await asyncpg.create_pool(self._dsn, min_size=1, max_size=5)
                async with self._pool.acquire() as conn:
                    await conn.execute(self.CREATE_TABLE_SQL)
            except Exception:
                self._pool = None
                self._available = False
        return self._pool

    # ── Public API ────────────────────────────────────────────────────────────

    async def save(
        self,
        draft_id: Optional[str],
        user_id: Optional[str],
        display_name: str,
        spec_dict: Dict[str, Any],
        step: str = "search",
        chapter: int = 1,
        path: Optional[str] = None,
        status: str = "draft",
    ) -> Optional[str]:
        """
        Upsert a draft. Creates a new UUID if draft_id is None.

        Returns:
            The draft_id string, or None if Postgres is not available.
        """
        pool = await self._get_pool()
        if pool is None:
            return None

        did = str(uuid.UUID(draft_id)) if draft_id else str(uuid.uuid4())
        spec_json = json.dumps(spec_dict, default=str)

        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    self.UPSERT_SQL,
                    did, user_id, display_name, spec_json,
                    step, chapter, path, status,
                )
                return row["draft_id"] if row else did
        except Exception:
            return None

    async def load(self, draft_id: str) -> Optional[DraftRecord]:
        """
        Load a draft by ID.

        Returns:
            DraftRecord, or None if not found or Postgres unavailable.
        """
        pool = await self._get_pool()
        if pool is None:
            return None

        try:
            did = str(uuid.UUID(draft_id))
        except ValueError:
            return None

        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(self.SELECT_SQL, did)
            if not row:
                return None
            return DraftRecord(
                draft_id=row["draft_id"],
                user_id=row["user_id"],
                display_name=row["display_name"],
                spec_dict=dict(row["spec_json"]) if row["spec_json"] else {},
                step=row["step"],
                chapter=row["chapter"],
                path=row["path"],
                status=row["status"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
        except Exception:
            return None

    async def list_user_drafts(
        self, user_id: str, limit: int = 10
    ) -> List[DraftRecord]:
        """
        Return the most recent drafts for a user (excludes deleted).

        Returns:
            List of DraftRecord (may be empty).
        """
        pool = await self._get_pool()
        if pool is None:
            return []

        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch(self.LIST_SQL, user_id, limit)
            return [
                DraftRecord(
                    draft_id=r["draft_id"],
                    user_id=r["user_id"],
                    display_name=r["display_name"],
                    spec_dict=dict(r["spec_json"]) if r["spec_json"] else {},
                    step=r["step"],
                    chapter=r["chapter"],
                    path=r["path"],
                    status=r["status"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                )
                for r in rows
            ]
        except Exception:
            return []

    async def delete(self, draft_id: str) -> bool:
        """Soft-delete a draft (sets status = 'deleted'). Returns True on success."""
        pool = await self._get_pool()
        if pool is None:
            return False
        try:
            did = str(uuid.UUID(draft_id))
            async with pool.acquire() as conn:
                await conn.execute(self.DELETE_SQL, did)
            return True
        except Exception:
            return False

    @property
    def is_available(self) -> bool:
        """True when Postgres is configured and asyncpg is installed."""
        return self._available
