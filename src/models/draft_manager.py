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
        ui_state      JSONB        NOT NULL DEFAULT '{}',
        step          VARCHAR(50),
        chapter       INTEGER DEFAULT 1,
        path          VARCHAR(50),
        status        VARCHAR(50) DEFAULT 'draft',
        invite_token  UUID         UNIQUE,
        owner_role    VARCHAR(50),
        created_at    TIMESTAMPTZ DEFAULT NOW(),
        updated_at    TIMESTAMPTZ DEFAULT NOW()
    );

Usage:
    dm = DraftManager(dsn="postgresql://...")
    draft_id = await dm.save(draft_id, user_id, display_name, spec, step, chapter, path)
    result = await dm.load(draft_id)   # Returns DraftRecord or None
    drafts = await dm.list_user_drafts(user_id, limit=10)
    await dm.delete(draft_id)
    token = await dm.create_invite_token(draft_id)
    result = await dm.get_by_invite_token(token)
    await dm.log_action(draft_id, "field_updated", user_id=uid, field_name="title")
    entries = await dm.get_audit_log(draft_id)
"""

import asyncio
import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import asyncpg
    HAS_ASYNCPG = True
except ImportError:
    HAS_ASYNCPG = False


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class ConcurrentEditError(Exception):
    """Raised when optimistic locking detects a concurrent edit."""
    pass


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
    ui_state: Dict[str, Any]   # Form navigation state
    step: str
    chapter: int
    path: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    invite_token: Optional[str] = None   # UUID string for shareable links
    owner_role: Optional[str] = None     # Role of the user who owns this draft


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
            ui_state      JSONB        NOT NULL DEFAULT '{}',
            step          VARCHAR(50)  NOT NULL DEFAULT 'search',
            chapter       INTEGER      NOT NULL DEFAULT 1,
            path          VARCHAR(50),
            status        VARCHAR(50)  NOT NULL DEFAULT 'draft',
            invite_token  UUID         UNIQUE,
            owner_role    VARCHAR(50),
            created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_drafts_user_id  ON data_product_drafts(user_id);
        CREATE INDEX IF NOT EXISTS idx_drafts_updated  ON data_product_drafts(updated_at DESC);
        CREATE TABLE IF NOT EXISTS data_product_audit_log (
            id          BIGSERIAL PRIMARY KEY,
            draft_id    UUID NOT NULL,
            user_id     VARCHAR(255),
            role        VARCHAR(50),
            action      VARCHAR(100) NOT NULL,
            field_name  VARCHAR(100),
            old_value   TEXT,
            new_value   TEXT,
            ts          TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_audit_draft_id ON data_product_audit_log(draft_id);
        CREATE INDEX IF NOT EXISTS idx_audit_ts ON data_product_audit_log(ts DESC);
    """

    UPSERT_CHECKED_SQL = """
        INSERT INTO data_product_drafts
            (draft_id, user_id, display_name, spec_json, ui_state, step, chapter, path, status, owner_role, updated_at)
        VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, $6, $7, $8, $9, $10, NOW())
        ON CONFLICT (draft_id) DO UPDATE SET
            user_id       = EXCLUDED.user_id,
            display_name  = EXCLUDED.display_name,
            spec_json     = EXCLUDED.spec_json,
            ui_state      = EXCLUDED.ui_state,
            step          = EXCLUDED.step,
            chapter       = EXCLUDED.chapter,
            path          = EXCLUDED.path,
            status        = EXCLUDED.status,
            owner_role    = EXCLUDED.owner_role,
            updated_at    = NOW()
        WHERE data_product_drafts.updated_at <= $11
        RETURNING draft_id::text, updated_at;
    """

    UPSERT_SQL = """
        INSERT INTO data_product_drafts
            (draft_id, user_id, display_name, spec_json, ui_state, step, chapter, path, status, owner_role, updated_at)
        VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, $6, $7, $8, $9, $10, NOW())
        ON CONFLICT (draft_id) DO UPDATE SET
            user_id       = EXCLUDED.user_id,
            display_name  = EXCLUDED.display_name,
            spec_json     = EXCLUDED.spec_json,
            ui_state      = EXCLUDED.ui_state,
            step          = EXCLUDED.step,
            chapter       = EXCLUDED.chapter,
            path          = EXCLUDED.path,
            status        = EXCLUDED.status,
            owner_role    = EXCLUDED.owner_role,
            updated_at    = NOW()
        RETURNING draft_id::text;
    """

    SELECT_SQL = """
        SELECT draft_id::text, user_id, display_name, spec_json,
               ui_state::text, invite_token::text, owner_role,
               step, chapter, path, status, created_at, updated_at
        FROM   data_product_drafts
        WHERE  draft_id = $1;
    """

    LIST_SQL = """
        SELECT draft_id::text, user_id, display_name, spec_json,
               ui_state::text, invite_token::text, owner_role,
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
            for _attempt in range(3):
                try:
                    self._pool = await asyncio.wait_for(
                        asyncpg.create_pool(self._dsn, min_size=1, max_size=5, command_timeout=10),
                        timeout=15,
                    )
                    async with self._pool.acquire() as conn:
                        await conn.execute(self.CREATE_TABLE_SQL)
                    break  # success
                except Exception as exc:
                    logger.warning("Pool creation attempt %d failed: %s", _attempt + 1, exc)
                    if _attempt == 2:
                        self._pool = None
                        self._available = False
                    else:
                        await asyncio.sleep(0.5)
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
        ui_state: Optional[Dict[str, Any]] = None,
        owner_role: Optional[str] = None,
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
        ui_state_json = json.dumps(ui_state or {}, default=str)

        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    self.UPSERT_SQL,
                    did, user_id, display_name, spec_json, ui_state_json,
                    step, chapter, path, status, owner_role,
                )
                return row["draft_id"] if row else did
        except Exception as exc:
            logger.error("DraftManager.save failed: %s", exc, exc_info=True)
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
            ui_state = dict(json.loads(row["ui_state"])) if row["ui_state"] else {}
            invite_token = row["invite_token"]
            owner_role = row["owner_role"]
            return DraftRecord(
                draft_id=row["draft_id"],
                user_id=row["user_id"],
                display_name=row["display_name"],
                spec_dict=self.validate_spec_json(dict(row["spec_json"]) if row["spec_json"] else {}),
                ui_state=ui_state,
                step=row["step"],
                chapter=row["chapter"],
                path=row["path"],
                status=row["status"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                invite_token=invite_token,
                owner_role=owner_role,
            )
        except Exception as exc:
            logger.error("DraftManager.load failed: %s", exc, exc_info=True)
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
                    spec_dict=self.validate_spec_json(dict(r["spec_json"]) if r["spec_json"] else {}),
                    ui_state=dict(json.loads(r["ui_state"])) if r["ui_state"] else {},
                    step=r["step"],
                    chapter=r["chapter"],
                    path=r["path"],
                    status=r["status"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                    invite_token=r["invite_token"],
                    owner_role=r["owner_role"],
                )
                for r in rows
            ]
        except Exception as exc:
            logger.error("DraftManager.list_user_drafts failed: %s", exc, exc_info=True)
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
        except Exception as exc:
            logger.error("DraftManager.delete failed: %s", exc, exc_info=True)
            return False

    async def create_invite_token(self, draft_id: str) -> Optional[str]:
        """
        Generate a UUID invite token for the draft and store it.
        Returns the token string, or None if unavailable.
        Idempotent — returns existing token if one already exists.
        """
        pool = await self._get_pool()
        if pool is None:
            return None
        try:
            did = str(uuid.UUID(draft_id))
            token = str(uuid.uuid4())
            # Use INSERT ... ON CONFLICT DO NOTHING then SELECT to get existing
            sql = """
                UPDATE data_product_drafts
                SET invite_token = COALESCE(invite_token, $2::uuid)
                WHERE draft_id = $1
                RETURNING invite_token::text;
            """
            async with pool.acquire() as conn:
                row = await conn.fetchrow(sql, did, token)
            return row["invite_token"] if row else None
        except Exception as exc:
            logger.error("DraftManager.create_invite_token failed: %s", exc, exc_info=True)
            return None

    async def get_by_invite_token(self, token: str) -> Optional[DraftRecord]:
        """Load a draft by its invite token (used for shared URLs)."""
        pool = await self._get_pool()
        if pool is None:
            return None
        try:
            tok = str(uuid.UUID(token))
        except ValueError:
            return None
        sql = """
            SELECT draft_id::text, user_id, display_name, spec_json, ui_state,
                   step, chapter, path, status, created_at, updated_at,
                   invite_token::text, owner_role
            FROM data_product_drafts
            WHERE invite_token = $1 AND status != 'deleted';
        """
        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(sql, tok)
            if not row:
                return None
            return DraftRecord(
                draft_id=row["draft_id"],
                user_id=row["user_id"],
                display_name=row["display_name"],
                spec_dict=self.validate_spec_json(dict(row["spec_json"]) if row["spec_json"] else {}),
                ui_state=dict(row["ui_state"]) if row["ui_state"] else {},
                step=row["step"],
                chapter=row["chapter"],
                path=row["path"],
                status=row["status"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                invite_token=row["invite_token"],
                owner_role=row["owner_role"],
            )
        except Exception as exc:
            logger.error("DraftManager.get_by_invite_token failed: %s", exc, exc_info=True)
            return None

    async def log_action(
        self,
        draft_id: str,
        action: str,
        user_id: Optional[str] = None,
        role: Optional[str] = None,
        field_name: Optional[str] = None,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
    ) -> None:
        """Write an audit entry. Fire-and-forget — never raises."""
        pool = await self._get_pool()
        if pool is None:
            return
        sql = """
            INSERT INTO data_product_audit_log
                (draft_id, user_id, role, action, field_name, old_value, new_value)
            VALUES ($1::uuid, $2, $3, $4, $5, $6, $7);
        """
        try:
            did = str(uuid.UUID(draft_id))
            async with pool.acquire() as conn:
                await conn.execute(sql, did, user_id, role, action,
                                   field_name,
                                   str(old_value)[:500] if old_value is not None else None,
                                   str(new_value)[:500] if new_value is not None else None)
        except Exception as exc:
            logger.error("DraftManager.log_action failed: %s", exc, exc_info=True)

    async def get_audit_log(self, draft_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Return recent audit entries for a draft, newest first."""
        pool = await self._get_pool()
        if pool is None:
            return []
        sql = """
            SELECT id, user_id, role, action, field_name, old_value, new_value, ts
            FROM data_product_audit_log
            WHERE draft_id = $1::uuid
            ORDER BY ts DESC LIMIT $2;
        """
        try:
            did = str(uuid.UUID(draft_id))
            async with pool.acquire() as conn:
                rows = await conn.fetch(sql, did, limit)
            return [dict(r) for r in rows]
        except Exception as exc:
            logger.error("DraftManager.get_audit_log failed: %s", exc, exc_info=True)
            return []

    async def save_with_audit(
        self,
        draft_id: Optional[str],
        user_id: Optional[str],
        display_name: str,
        spec_dict: Dict[str, Any],
        step: str = "search",
        chapter: int = 1,
        path: Optional[str] = None,
        status: str = "draft",
        ui_state: Optional[Dict[str, Any]] = None,
        owner_role: Optional[str] = None,
        audit_action: str = "draft_saved",
        audit_field: Optional[str] = None,
    ) -> Optional[str]:
        """Atomically save draft and log audit action in one transaction."""
        pool = await self._get_pool()
        if pool is None:
            return None

        did = str(uuid.UUID(draft_id)) if draft_id else str(uuid.uuid4())
        spec_json = json.dumps(spec_dict, default=str)
        ui_state_json = json.dumps(ui_state or {}, default=str)

        audit_sql = """
            INSERT INTO data_product_audit_log
                (draft_id, user_id, role, action, field_name)
            VALUES ($1::uuid, $2, $3, $4, $5);
        """
        try:
            async with pool.acquire() as conn:
                async with conn.transaction():
                    row = await conn.fetchrow(
                        self.UPSERT_SQL,
                        did, user_id, display_name, spec_json, ui_state_json,
                        step, chapter, path, status, owner_role,
                    )
                    await conn.execute(
                        audit_sql, did, user_id, owner_role, audit_action, audit_field
                    )
            return row["draft_id"] if row else did
        except Exception as exc:
            logger.error("save_with_audit failed for draft %s: %s", did[:8], exc, exc_info=True)
            return None

    async def save_checked(
        self,
        draft_id: str,
        user_id: Optional[str],
        display_name: str,
        spec_dict: Dict[str, Any],
        expected_updated_at: datetime,
        step: str = "search",
        chapter: int = 1,
        path: Optional[str] = None,
        status: str = "draft",
        ui_state: Optional[Dict[str, Any]] = None,
        owner_role: Optional[str] = None,
    ) -> Optional[str]:
        """
        Save with optimistic locking. Returns draft_id on success,
        raises ConcurrentEditError if another write has occurred since expected_updated_at.
        """
        pool = await self._get_pool()
        if pool is None:
            return None

        did = str(uuid.UUID(draft_id))
        spec_json = json.dumps(spec_dict, default=str)
        ui_state_json = json.dumps(ui_state or {}, default=str)

        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    self.UPSERT_CHECKED_SQL,
                    did, user_id, display_name, spec_json, ui_state_json,
                    step, chapter, path, status, owner_role,
                    expected_updated_at,
                )
            if row is None:
                raise ConcurrentEditError(
                    f"Draft {did[:8]} was modified by another user. Reload to see the latest version."
                )
            return row["draft_id"]
        except ConcurrentEditError:
            raise
        except Exception as exc:
            logger.error("save_checked failed for draft %s: %s", did[:8], exc, exc_info=True)
            return None

    @staticmethod
    def validate_spec_json(spec_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Lightly validate and clean a spec dict loaded from Postgres.
        Removes keys with None values; coerces known list fields to lists.
        Returns cleaned dict.
        """
        list_fields = {
            "source_systems", "consumer_teams", "tags", "regulatory_scope",
            "geographic_restriction", "lineage_upstream", "lineage_downstream",
            "target_systems", "critical_data_elements", "business_terms",
            "data_subject_areas", "related_reports", "column_definitions",
            "business_rules",
        }
        cleaned = {}
        for k, v in spec_dict.items():
            if v is None:
                continue
            if k in list_fields and isinstance(v, str):
                # Coerce comma-separated strings back to lists (legacy data)
                cleaned[k] = [i.strip() for i in v.split(",") if i.strip()]
            else:
                cleaned[k] = v
        return cleaned

    async def is_healthy(self) -> bool:
        """Quick health check — returns True if pool is alive."""
        pool = await self._get_pool()
        if pool is None:
            return False
        try:
            async with pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception:
            return False

    @property
    def is_available(self) -> bool:
        """True when Postgres is configured and asyncpg is installed."""
        return self._available
