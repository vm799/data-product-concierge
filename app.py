"""
Data Product Concierge — Main Application Orchestrator.

Supports two modes:
  - LIVE MODE:    Full APIM/Collibra/LLM integration (set APIM_BASE_URL in env)
  - DEMO MODE:    Complete UI walkthrough with sample spec data (no APIs needed)

Demo mode activates automatically when APIM_BASE_URL is not configured.
In live mode, a sidebar toggle lets you flip demo data on/off instantly.
"""

import streamlit as st
import asyncio
import logging
import os
import uuid
from datetime import date, datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)

# Set page config as the first Streamlit command
st.set_page_config(
    page_title="Data Product Concierge",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# Bridge Streamlit Cloud secrets → os.environ (silent if no secrets file)
# ---------------------------------------------------------------------------
import pathlib as _pathlib

_SECRETS_LOADED: bool = False   # True if secrets.toml was found and loaded
_SECRETS_PATHS = [
    _pathlib.Path.home() / ".streamlit" / "secrets.toml",
    _pathlib.Path(__file__).parent / ".streamlit" / "secrets.toml",
]


def _load_streamlit_secrets_to_env() -> bool:
    """
    Load secrets into os.environ. Returns True if a secrets file was found.
    Checks file existence BEFORE touching st.secrets so Streamlit never
    renders the 'No secrets found' error to the main page.
    """
    if not any(p.exists() for p in _SECRETS_PATHS):
        return False
    try:
        for key in st.secrets:
            if isinstance(st.secrets[key], str) and key not in os.environ:
                os.environ[key] = st.secrets[key]
        return True
    except Exception:
        return False


_SECRETS_LOADED = _load_streamlit_secrets_to_env()


# ---------------------------------------------------------------------------
# Mode detection
# ---------------------------------------------------------------------------
LIVE_CAPABLE = bool(os.getenv("APIM_BASE_URL"))  # Can we connect to live APIs?
# Legacy alias used by sidebar (read-only — do not use in handlers; use _demo_active())
PREVIEW_MODE = not LIVE_CAPABLE


def _demo_active() -> bool:
    """True when using sample/mock data — demo toggle or no live APIs configured."""
    if not LIVE_CAPABLE:
        return True
    return st.session_state.get("demo_mode", False)


# ---------------------------------------------------------------------------
# Audit helper — in-session log, max 200 entries
# ---------------------------------------------------------------------------
def _audit(action: str, detail: str = "") -> None:
    """Append a structured entry to the in-session audit log."""
    if "audit_log" not in st.session_state:
        st.session_state.audit_log = []
    user = os.getenv("USER_DISPLAY_NAME") or os.getenv("USER_ROLE", "analyst")
    session_id = st.session_state.get("session_id", "—")
    st.session_state.audit_log.append({
        "ts": datetime.now().strftime("%H:%M:%S"),
        "user": user,
        "action": action,
        "detail": str(detail)[:120],
        "session": session_id[:8],
    })
    st.session_state.audit_log = st.session_state.audit_log[-200:]


# ---------------------------------------------------------------------------
# Scroll-to-top helper
# ---------------------------------------------------------------------------
def _scroll_top() -> None:
    """Inject JS to scroll the Streamlit main pane to the top on step change."""
    st.components.v1.html(
        "<script>"
        "try{"
        "  var m = window.parent.document.querySelector('section[data-testid=\"stMain\"] .main');"
        "  if(!m) m = window.parent.document.querySelector('.main');"
        "  if(m) m.scrollTo({top:0,behavior:'instant'});"
        "}catch(e){}"
        "</script>",
        height=0,
    )


# ---------------------------------------------------------------------------
# Imports — conditional to avoid import errors when deps aren't configured
# ---------------------------------------------------------------------------
from models.data_product import DataProductSpec, AssetResult
from components.styles import inject_styles
from components import search_bar, asset_cards, ingredient_label, chapter_form, handoff_summary, conversation_create

try:
    from components.use_case_intake import render_use_case_intake
    _HAS_INTAKE = True
except ImportError:
    _HAS_INTAKE = False

try:
    from components.guided_form import render_guided_form
    _HAS_GUIDED_FORM = True
except ImportError:
    _HAS_GUIDED_FORM = False

# Optional components — available once agents have written them
try:
    from components.snowflake_preview import render_snowflake_preview
    _HAS_SNOWFLAKE_PREVIEW = True
except ImportError:
    _HAS_SNOWFLAKE_PREVIEW = False

try:
    from models.draft_manager import DraftManager
    from components.draft_banner import render_recent_drafts, render_autosave_indicator
    _HAS_DRAFT_MANAGER = True
except ImportError:
    _HAS_DRAFT_MANAGER = False

try:
    from components.styles import inject_chat_autofocus, inject_keyboard_submit
    _HAS_UX_HELPERS = True
except ImportError:
    _HAS_UX_HELPERS = False

if LIVE_CAPABLE:
    from connectors.apim_auth import (
        APIMTokenManager, APIMAuthError, SessionExpiredError, get_or_create_token_manager,
    )
    from connectors.collibra_auth import CollibraAuthenticator
    from connectors.postgres import PostgresSessionManager
    from core.collibra_client import CollibraClient
    from agents.concierge import DataProductConcierge
from core.utils import set_state, format_error


# ---------------------------------------------------------------------------
# Form state reset helper
# ---------------------------------------------------------------------------
def _reset_form_state() -> None:
    """Clear all guided-form navigation state. Call when entering a new path."""
    for key in [
        "gf_tier", "gf_field_idx", "gf_field_status", "gf_dynamic_field_list",
        "gf_active_panel", "gf_panel_queue", "gf_colleague_handoff",
        "shared_field_idx", "shared_field_status", "shared_spec",
        "shared_submission_complete", "shared_draft_loaded",
    ]:
        st.session_state.pop(key, None)


# ---------------------------------------------------------------------------
# Draft manager singleton
# ---------------------------------------------------------------------------
_draft_manager_instance = None

def _get_draft_manager():
    """Return a DraftManager instance, or None if unavailable."""
    global _draft_manager_instance
    if not _HAS_DRAFT_MANAGER:
        return None
    if _draft_manager_instance is None:
        _draft_manager_instance = DraftManager()
    return _draft_manager_instance


def _autosave_draft(role: str = None) -> None:
    """
    Persist the current spec + form navigation state to Postgres.
    Silently no-ops if draft manager is unavailable or in demo mode.
    """
    dm = _get_draft_manager()
    if dm is None or not dm.is_available or _demo_active():
        return
    spec = st.session_state.get("spec")
    if spec is None:
        return
    try:
        user_id = os.getenv("USER_EMAIL") or os.getenv("USER_DISPLAY_NAME") or "anonymous"
        display_name = spec.name or "Untitled draft"

        # Capture form navigation state so resume restores exact position
        ui_state = {
            "gf_tier": st.session_state.get("gf_tier"),
            "gf_field_idx": st.session_state.get("gf_field_idx"),
            "gf_field_status": st.session_state.get("gf_field_status"),
            "gf_dynamic_field_list": st.session_state.get("gf_dynamic_field_list"),
            "gf_active_panel": st.session_state.get("gf_active_panel"),
            "gf_panel_queue": st.session_state.get("gf_panel_queue"),
        }
        # Serialize original_spec if present (for remix diff baseline)
        orig = st.session_state.get("original_spec")
        if orig is not None:
            try:
                ui_state["original_spec_dict"] = orig.dict()
            except Exception:
                pass

        _existing_draft_id = st.session_state.get("draft_id")
        _expected_updated_at = st.session_state.get("draft_updated_at")
        _save_kwargs = dict(
            user_id=user_id,
            display_name=display_name,
            spec_dict=spec.dict(),
            ui_state=ui_state,
            step=st.session_state.get("step", "search"),
            chapter=st.session_state.get("chapter", 1),
            path=st.session_state.get("path"),
            owner_role=role,
        )
        try:
            from models.draft_manager import ConcurrentEditError
            if _existing_draft_id and _expected_updated_at:
                # Existing draft — use optimistic locking
                draft_id = run_async(dm.save_checked(
                    draft_id=_existing_draft_id,
                    expected_updated_at=_expected_updated_at,
                    **_save_kwargs,
                ))
            else:
                # New draft — plain save
                draft_id = run_async(dm.save(
                    draft_id=_existing_draft_id,
                    **_save_kwargs,
                ))
        except ConcurrentEditError:
            st.warning(
                "⚠ This draft was updated by another collaborator. "
                "Reload the page to see the latest version before saving."
            )
            logger.warning("Concurrent edit detected on draft %s", _existing_draft_id)
            draft_id = None
        except asyncio.TimeoutError:
            logger.error("run_async call failed: autosave dm.save timed out", exc_info=True)
            draft_id = None
        except Exception as _exc:
            logger.error("run_async call failed: %s", _exc, exc_info=True)
            draft_id = None
        if draft_id:
            st.session_state.draft_id = draft_id
            st.session_state.last_saved_ts = datetime.now().strftime("%H:%M:%S")
            st.session_state.draft_updated_at = datetime.now()  # track for optimistic locking
            # Write audit entry
            try:
                run_async(dm.log_action(
                    draft_id=draft_id,
                    action="autosave",
                    user_id=user_id,
                    role=role or st.session_state.get("path", "business"),
                ))
            except asyncio.TimeoutError:
                logger.error("run_async call failed: autosave dm.log_action timed out", exc_info=True)
            except Exception as _exc:
                logger.error("run_async call failed: %s", _exc, exc_info=True)
    except Exception:
        pass  # Never crash on autosave failure


# ---------------------------------------------------------------------------
# Async helper
# ---------------------------------------------------------------------------
from core.async_utils import run_async as _core_run_async

def run_async(coro, timeout=15):
    """Thin wrapper — delegates to core.async_utils.run_async."""
    return _core_run_async(coro, timeout=timeout)


# ---------------------------------------------------------------------------
# Live Collibra option loader (parallel fetch, cached in session_state)
# ---------------------------------------------------------------------------
async def _load_live_valid_options_async(collibra_client, selected_id=None) -> dict:
    """Fetch all Collibra-fed option lists in parallel. Never raises — returns [] on error."""
    tasks = [
        collibra_client.get_source_systems(),
        collibra_client.get_consumer_teams(),
        collibra_client.get_domains(),
        collibra_client.get_valid_options("tags"),
        collibra_client.get_valid_options("geographic_restriction"),
    ]
    if selected_id:
        tasks.append(collibra_client.get_related_reports(str(selected_id)))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    def safe_names(r):
        if isinstance(r, Exception):
            return []
        return [o.name if hasattr(o, "name") else str(o) for o in (r or [])]

    opts = {
        "source_systems": safe_names(results[0]),
        "consumer_teams": safe_names(results[1]),
        "domain": safe_names(results[2]),
        "tags": safe_names(results[3]),
        "geographic_restriction": safe_names(results[4]),
    }
    if selected_id and len(results) > 5:
        raw = results[5]
        opts["related_reports"] = (
            [r.name for r in raw] if not isinstance(raw, Exception) else []
        )
    return opts


def _load_live_valid_options() -> dict:
    """Sync wrapper — call once then cache in st.session_state.live_valid_options."""
    selected = st.session_state.get("selected")
    selected_id = selected.id if selected else None
    try:
        result = run_async(
            _load_live_valid_options_async(st.session_state.collibra_client, selected_id)
        )
    except asyncio.TimeoutError:
        st.error("Request timed out. Please try again.")
        result = None
    except Exception as _exc:
        logger.error("run_async call failed: %s", _exc, exc_info=True)
        result = None
    return result


# ---------------------------------------------------------------------------
# Demo-mode sample data (used ONLY when _demo_active() is True)
# ---------------------------------------------------------------------------
def _demo_sample_results() -> list:
    return [
        AssetResult(
            id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            name="ESG Scope 1 Emissions EU",
            domain="Sustainable Investing",
            domain_id="d001e2f3-a4b5-6c7d-8e9f-123456789abc",
            owner_name="Sarah Chen",
            owner_email="sarah.chen@firm.com",
            department="ESG Data & Analytics",
            data_classification="Internal",
            regulatory_scope=["GDPR", "SFDR", "EU Taxonomy"],
            update_frequency="Monthly",
            data_quality_score=87.5,
            relevance_score=0.94,
        ),
        AssetResult(
            id="b2c3d4e5-f6a7-8901-bcde-f12345678901",
            name="Carbon Footprint Portfolio Analytics",
            domain="Risk & Analytics",
            domain_id="d002f3a4-b5c6-7d8e-9f12-3456789abcde",
            owner_name="James Morgan",
            owner_email="james.morgan@firm.com",
            department="Quantitative Research",
            data_classification="Confidential",
            regulatory_scope=["MiFID II", "TCFD"],
            update_frequency="Weekly",
            data_quality_score=72.0,
            relevance_score=0.81,
        ),
        AssetResult(
            id="c3d4e5f6-a7b8-9012-cdef-123456789012",
            name="EU Sustainable Fund Reference Data",
            domain="Reference Data",
            domain_id="d003a4b5-c6d7-8e9f-1234-567890abcdef",
            owner_name="Amara Osei",
            owner_email="amara.osei@firm.com",
            department="Data Operations",
            data_classification="Internal",
            regulatory_scope=["GDPR", "AIFMD"],
            update_frequency="Daily",
            data_quality_score=None,
            relevance_score=0.67,
        ),
    ]


def _demo_sample_spec() -> DataProductSpec:
    return DataProductSpec(
        id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        name="ESG Scope 1 Emissions EU",
        description="Scope 1 direct greenhouse gas emissions data for European fund holdings, aggregated monthly from verified corporate disclosures.",
        business_purpose="Support Paris-aligned fund reporting and SFDR Article 8/9 compliance for European equity portfolios.",
        status="Candidate",
        version="2.1.0",
        domain="Sustainable Investing",
        sub_domain="Climate & Carbon",
        data_classification="Internal",
        tags=["ESG", "emissions", "carbon", "scope-1", "EU", "Paris Agreement"],
        data_owner_email="sarah.chen@firm.com",
        data_owner_name="Sarah Chen",
        data_steward_email="marco.silva@firm.com",
        data_steward_name="Marco Silva",
        certifying_officer_email="karen.liu@firm.com",
        last_certified_date=date.today(),
        regulatory_scope=["GDPR", "SFDR", "EU Taxonomy", "TCFD"],
        geographic_restriction=["EU", "UK", "Switzerland"],
        pii_flag=False,
        encryption_standard="AES-256",
        retention_period="7 years",
        source_systems=["Bloomberg ESG", "MSCI ESG Ratings", "Corporate Filings DB"],
        update_frequency="Monthly",
        schema_location="ANALYTICS_DB.ESG.SCOPE1_EMISSIONS_EU",
        sample_query="SELECT issuer, emission_tonnes, reporting_date FROM ANALYTICS_DB.ESG.SCOPE1_EMISSIONS_EU WHERE reporting_date >= '2025-01-01'",
        lineage_upstream=["Bloomberg Raw Feed", "MSCI ESG Extract", "Corporate Filing Parser"],
        lineage_downstream=["Paris Alignment Dashboard", "SFDR Reporting Engine", "Fund Factsheets"],
        access_level="Request-based",
        consumer_teams=["Portfolio Management", "ESG Research", "Client Reporting", "Compliance"],
        sla_tier="Gold (99.9%)",
        business_criticality="Mission-critical",
        cost_centre="CC-4521-ESG",
        related_reports=["SFDR PAI Report", "TCFD Climate Disclosure", "Monthly ESG Scorecard"],
        data_quality_score=87.5,
    )


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
def initialize_session_state():
    defaults = {
        "step": "search" if LIVE_CAPABLE else "search",
        "token_manager": None,
        "query": "",
        "intent": None,
        "results": [],
        "selected": None,
        "path": None,
        "spec": None,
        "chapter": 1,
        "concierge_msg": "",
        "session_id": str(uuid.uuid4()),
        "errors": [],
        "collibra_client": None,
        "concierge": None,
        "postgres": None,
        "demo_mode": not LIVE_CAPABLE,  # True = show sample data; togglable in sidebar
        "audit_log": [],
        "_prev_step": None,
        "draft_id": None,
        "last_saved_ts": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ---------------------------------------------------------------------------
# Step handlers
# ---------------------------------------------------------------------------
def handle_auth():
    try:
        token_manager = get_or_create_token_manager()
        collibra_auth = CollibraAuthenticator(token_manager)
        st.session_state.token_manager = token_manager
        st.session_state.collibra_client = CollibraClient(collibra_auth)
        st.session_state.concierge = DataProductConcierge()
        st.session_state.postgres = PostgresSessionManager()
        _audit("auth", "authentication successful")
        st.session_state.step = "search"
        st.rerun()
    except Exception as e:
        _audit("auth_failed", format_error(e))
        st.error("**Authentication Failed**")
        st.markdown(f"Unable to connect to data services. {format_error(e)}")
        st.info("Contact IT Support: dataplatform-support@company.com")
        if st.button("Retry Authentication"):
            st.rerun()


def handle_search():
    # ── Draft resume (live mode only) ─────────────────────────────────────────
    if not _demo_active() and _HAS_DRAFT_MANAGER:
        dm = _get_draft_manager()
        if dm and dm.is_available:
            user_id = os.getenv("USER_EMAIL") or os.getenv("USER_DISPLAY_NAME") or "anonymous"
            try:
                drafts = run_async(dm.list_user_drafts(user_id, limit=5))
            except asyncio.TimeoutError:
                st.error("Request timed out. Please try again.")
                drafts = None
            except Exception as _exc:
                logger.error("run_async call failed: %s", _exc, exc_info=True)
                drafts = None
            if drafts:
                resumed_id = render_recent_drafts(drafts)
                if resumed_id:
                    try:
                        record = run_async(dm.load(resumed_id))
                    except asyncio.TimeoutError:
                        st.error("Request timed out. Please try again.")
                        record = None
                    except Exception as _exc:
                        logger.error("run_async call failed: %s", _exc, exc_info=True)
                        record = None
                    if record:
                        try:
                            st.session_state.spec = DataProductSpec(**record.spec_dict)
                        except Exception as exc:
                            logger.warning("Spec deserialization failed, starting fresh: %s", exc)
                            st.session_state.spec = DataProductSpec(name="", description="", business_purpose="")
                            st.warning("Some saved fields could not be restored. Please review your draft.")
                        st.session_state.step = record.step
                        st.session_state.chapter = record.chapter
                        st.session_state.path = record.path
                        st.session_state.draft_id = record.draft_id
                        st.session_state.draft_updated_at = record.updated_at  # for optimistic locking
                        # Restore form navigation state from ui_state
                        if hasattr(record, 'ui_state') and record.ui_state:
                            ui = record.ui_state
                            if ui.get("gf_tier") is not None:
                                st.session_state["gf_tier"] = ui["gf_tier"]
                            if ui.get("gf_field_idx") is not None:
                                st.session_state["gf_field_idx"] = ui["gf_field_idx"]
                            if ui.get("gf_field_status") is not None:
                                st.session_state["gf_field_status"] = ui["gf_field_status"]
                            if ui.get("gf_dynamic_field_list") is not None:
                                st.session_state["gf_dynamic_field_list"] = ui["gf_dynamic_field_list"]
                            if ui.get("gf_active_panel") is not None:
                                st.session_state["gf_active_panel"] = ui["gf_active_panel"]
                            if ui.get("gf_panel_queue") is not None:
                                st.session_state["gf_panel_queue"] = ui["gf_panel_queue"]
                            # Restore original_spec for remix diff
                            try:
                                _orig_dict = ui.get("original_spec_dict")
                                if _orig_dict:
                                    from models.data_product import DataProductSpec as _DPS
                                    st.session_state["original_spec"] = _DPS(**_orig_dict)
                            except Exception as exc:
                                logger.warning("original_spec deserialization failed: %s", exc)
                                # don't set original_spec — diff view will just show no changes
                        _audit("draft_resumed", f"resumed draft {record.draft_id[:8]}")
                        st.rerun()

    # Welcome heading — always shown on the search/home page
    st.markdown(
        '<h1 style="font-size:2.2rem;font-weight:700;color:#0D1B2A;margin-bottom:.25rem;line-height:1.2;">'
        'Welcome to your <span style="color:#006B73;">Data Product Concierge</span></h1>'
        '<p style="font-size:1rem;color:#5B6A7E;margin-top:0;margin-bottom:1.75rem;">'
        'Find governed data products, or register a new one in minutes.</p>',
        unsafe_allow_html=True,
    )

    if _HAS_INTAKE:
        working_spec = st.session_state.get("spec") or DataProductSpec(name="", description="", business_purpose="")

        valid_domains = None
        if not _demo_active() and st.session_state.get("collibra_client"):
            try:
                domains = run_async(st.session_state.collibra_client.get_domains())
                valid_domains = [d.name for d in domains] if domains else None
            except asyncio.TimeoutError:
                st.error("Request timed out. Please try again.")
                domains = None
            except Exception:
                pass

        seeded_spec, intake_results, action = render_use_case_intake(
            working_spec,
            st.session_state.get("collibra_client"),
            _demo_active(),
            valid_domains,
        )

        if action == "search_submitted":
            st.session_state.spec = seeded_spec
            st.session_state.results = intake_results
            st.session_state.concierge_msg = (
                f"Found {len(intake_results)} data product(s) in the catalogue matching your requirements."
            )
            _audit("search", f"intake → {len(intake_results)} results")
            st.session_state.step = "results"
            st.rerun()
    else:
        query, submitted = search_bar.render_hero()

        if _demo_active():
            st.html(
                '<div class="dpc-concierge" style="margin-top:1rem;">'
                '<strong style="color:var(--teal);font-style:normal;">Demo Mode</strong><br>'
                'Showing sample data — no live APIs connected.'
                '</div>'
            )

        if submitted and query:
            st.session_state.query = query
            if _demo_active():
                st.session_state.results = _demo_sample_results()
                st.session_state.concierge_msg = (
                    f'Found 3 results matching "{query}". The top match looks like a strong fit.'
                )
                _audit("search", f'demo query: "{query}"')
            else:
                try:
                    intent = run_async(st.session_state.concierge.interpret_query(query))
                except asyncio.TimeoutError:
                    st.error("Request timed out. Please try again.")
                    intent = None
                except Exception as _exc:
                    logger.error("run_async call failed: %s", _exc, exc_info=True)
                    intent = None
                try:
                    results = run_async(st.session_state.collibra_client.search_assets(intent.search_terms if intent else []))
                except asyncio.TimeoutError:
                    st.error("Request timed out. Please try again.")
                    results = None
                except Exception as _exc:
                    logger.error("run_async call failed: %s", _exc, exc_info=True)
                    results = None
                try:
                    narration = run_async(st.session_state.concierge.narrate_results(results, query))
                except asyncio.TimeoutError:
                    st.error("Request timed out. Please try again.")
                    narration = None
                except Exception as _exc:
                    logger.error("run_async call failed: %s", _exc, exc_info=True)
                    narration = None
                st.session_state.intent = intent
                st.session_state.results = results
                st.session_state.concierge_msg = narration
                _audit("search", f'live query: "{query}" → {len(results or [])} results')
            st.session_state.step = "results"
            st.rerun()


def handle_results():
    col_back, _ = st.columns([1, 5])
    with col_back:
        if st.button("← Refine search", key="results_back_btn", type="secondary"):
            st.session_state.step = "search"
            st.rerun()

    selected, path = asset_cards.render_results(
        st.session_state.results, st.session_state.concierge_msg
    )

    if selected and path:
        st.session_state.selected = selected
        st.session_state.path = path
        if path == "reuse":
            if _demo_active():
                st.session_state.spec = _demo_sample_spec()
            else:
                try:
                    st.session_state.spec = run_async(
                        st.session_state.collibra_client.get_asset_detail(selected.id)
                    )
                except asyncio.TimeoutError:
                    st.error("Request timed out. Please try again.")
                    st.session_state.spec = None
                except Exception as _exc:
                    logger.error("run_async call failed: %s", _exc, exc_info=True)
                    st.session_state.spec = None
            _audit("path_chosen", f"reuse: {selected.name}")
            _reset_form_state()
            st.session_state.step = "path_a"
        elif path == "remix":
            if _demo_active():
                _loaded = _demo_sample_spec()
            else:
                try:
                    _loaded = run_async(
                        st.session_state.collibra_client.get_asset_detail(selected.id)
                    )
                except asyncio.TimeoutError:
                    st.error("Request timed out. Please try again.")
                    _loaded = None
                except Exception as _exc:
                    logger.error("run_async call failed: %s", _exc, exc_info=True)
                    _loaded = None
            st.session_state.spec = _loaded
            # Snapshot the original so the form can show diffs
            st.session_state.original_spec = DataProductSpec(**_loaded.dict()) if _loaded else None
            _audit("path_chosen", f"remix: {selected.name}")
            st.session_state.step = "path_b"
            st.session_state.chapter = 1
        elif path == "create":
            st.session_state.spec = DataProductSpec(name="", description="", business_purpose="")
            _audit("path_chosen", f"create from asset: {selected.name}")
            _reset_form_state()
            st.session_state.step = "path_c"
            st.session_state.chapter = 1
        st.rerun()

    # Handle "create from scratch" (no selected asset)
    if path == "create" and not selected:
        if not _demo_active() and st.session_state.get("intent"):
            with st.spinner("Drafting a starting point from your search…"):
                try:
                    seed = run_async(
                        st.session_state.concierge.seed_new_product(
                            st.session_state.query, st.session_state.intent
                        )
                    )
                except asyncio.TimeoutError:
                    st.error("Request timed out. Please try again.")
                    seed = None
                except Exception as _exc:
                    logger.error("run_async call failed: %s", _exc, exc_info=True)
                    seed = None
            seed = seed or {}
            spec = DataProductSpec(
                name=seed.get("name", ""),
                description=seed.get("description", ""),
                business_purpose=seed.get("business_purpose", ""),
            )
            if seed.get("domain"):
                d = spec.dict()
                d["domain"] = seed["domain"]
                spec = DataProductSpec(**d)
            if seed.get("regulatory_scope"):
                d = spec.dict()
                d["regulatory_scope"] = seed["regulatory_scope"]
                spec = DataProductSpec(**d)
            st.session_state.concierge_seeded = True
        else:
            spec = DataProductSpec(name="", description="", business_purpose="")
            st.session_state.concierge_seeded = False
        _audit("path_chosen", "create from scratch")
        st.session_state.spec = spec
        st.session_state.path = "create"
        _reset_form_state()
        st.session_state.step = "path_c"
        st.session_state.chapter = 1
        st.rerun()


def handle_reuse():
    if _demo_active():
        concierge_msg = (
            "This looks like an excellent match for what you described. "
            "All the governance and compliance details are shown below — you can email "
            "the data owner directly to request access, or if you need to adapt it, "
            "switch to the remix path."
        )
    else:
        try:
            _recommend = run_async(
                st.session_state.concierge.recommend_path(st.session_state.selected, st.session_state.query)
            )
            concierge_msg = _recommend.message if _recommend else ""
        except asyncio.TimeoutError:
            st.error("Request timed out. Please try again.")
            concierge_msg = ""
        except Exception as _exc:
            logger.error("run_async call failed: %s", _exc, exc_info=True)
            concierge_msg = ""

    action = ingredient_label.render(st.session_state.spec, concierge_msg)

    if action == "remix":
        _audit("action", "switched from reuse to remix")
        st.session_state.step = "path_b"
        st.session_state.chapter = 1
        st.rerun()
    elif action == "email":
        owner_email = st.session_state.spec.data_owner_email or ""
        product_name = st.session_state.spec.name or "Data Product"
        _audit("action", f"email owner: {owner_email}")
        mailto = f"mailto:{owner_email}?subject=Access%20Request%3A%20{product_name}&body=Hi%2C%0A%0AI%20would%20like%20to%20request%20access%20to%20{product_name}.%0A%0AThank%20you."
        st.html(f'<a href="{mailto}" target="_blank">Email client opened</a>')


def _get_chapter_name(chapter: int) -> str:
    return {1: "Identity", 2: "Classification", 3: "Governance", 4: "Compliance & Technical", 5: "Access & Business"}.get(chapter, "")


def _demo_field_explanations() -> dict:
    """Static field explanations for demo mode."""
    return {
        "name": "The official name as it will appear in Collibra and all downstream reporting.",
        "description": "A plain-language summary so business users can quickly understand what this data product contains.",
        "business_purpose": "Explains why this data product exists — essential for prioritisation and funding decisions.",
        "status": "The lifecycle stage — Draft products aren't visible to consumers yet.",
        "version": "Semantic versioning helps consumers know when breaking changes occur.",
        "domain": "The business domain determines which governance policies and stewardship teams apply.",
        "sub_domain": "Narrows the classification for more precise data discovery.",
        "data_classification": "Drives encryption, access controls, and audit requirements — Confidential data has the strictest rules.",
        "tags": "Searchable keywords that help others discover this product in the catalogue.",
        "data_owner_email": "The accountable person — compliance will contact them for audit queries.",
        "data_owner_name": "Display name shown on the data product card in Collibra.",
        "data_steward_email": "The day-to-day contact for data quality issues and access requests.",
        "data_steward_name": "Display name for the steward.",
        "certifying_officer_email": "Senior person who certifies the data meets quality and compliance standards.",
        "last_certified_date": "When the data was last formally certified — recertification may be required annually.",
        "regulatory_scope": "Which regulations govern how this data can be used — critical for MiFID II and SFDR reporting.",
        "geographic_restriction": "Where this data is legally permitted to be processed or stored.",
        "pii_flag": "Flags whether this data contains personally identifiable information — triggers GDPR obligations.",
        "encryption_standard": "The encryption applied at rest and in transit — required for Confidential data.",
        "retention_period": "How long this data must be kept — driven by regulatory requirements.",
        "source_systems": "The upstream systems feeding this product — essential for lineage and impact analysis.",
        "update_frequency": "How often the data refreshes — consumers need this to plan their reporting cycles.",
        "schema_location": "The Snowflake table or S3 path where the data lives.",
        "access_level": "Determines whether consumers can self-serve or need approval.",
        "consumer_teams": "Business teams approved to use this data — helps the owner understand their audience.",
        "sla_tier": "The uptime guarantee — Gold means 99.9% availability.",
        "business_criticality": "How critical this data is to operations — Mission-critical gets priority incident response.",
        "cost_centre": "For internal chargeback and budgeting.",
        "related_reports": "Downstream reports and dashboards that depend on this data product.",
        # Collibra registration
        "asset_type": "Collibra requires an asset type to correctly classify this in the catalogue. 'Data Product' is the most common choice for governed analytical outputs.",
        "collibra_community": "The Collibra community is the top-level grouping above domain. Without it, the Collibra API cannot create the asset. Ask your Collibra admin if unsure.",
        # Snowflake build
        "materialization_type": "How this data product is physically built in Snowflake. Tables offer best query performance; Dynamic Tables auto-refresh on schedule; Views have no storage cost.",
        "snowflake_role": "The Snowflake RBAC role that will be granted SELECT on this object. e.g. ROLE_ESG_READ, ROLE_RISK_ANALYST. Align with your security team's naming convention.",
        "column_definitions": "The DDL-level column schema. Providing this lets the tech team generate the CREATE TABLE/VIEW statement directly. One column definition per line.",
        "refresh_cron": "For Dynamic Tables or Snowflake Tasks, the cron schedule in '0 6 * * 1-5' format (UTC). Leave blank for static tables or Views.",
        "sample_query": "A representative SQL query showing how a consumer would access this data. Helps consumers validate the access pattern and the tech team test the implementation.",
        "lineage_upstream": "The source systems or upstream data products that feed this one. Essential for impact analysis when a source changes.",
        "lineage_downstream": "Reports, dashboards, or downstream data products that depend on this one. Used for change impact notifications.",
        # Operational
        "delivery_method": "How consumers will physically access the data — a SQL table is the most common for Snowflake; REST API for real-time; Kafka for streaming.",
        "review_cycle": "How often this data product's governance, quality, and ownership should be reviewed. Annual is minimum for regulatory data; Quarterly for mission-critical.",
        "incident_contact": "The on-call or team inbox to contact when this data product has a production incident. Can be an individual or a distribution list.",
    }


def _demo_valid_options() -> dict:
    """Static valid options for demo mode."""
    return {
        "status": ["Draft", "Candidate", "Approved", "Deprecated"],
        "data_classification": ["Confidential", "Internal", "Public", "Restricted"],
        "update_frequency": ["Real-time", "Hourly", "Daily", "Weekly", "Monthly", "Ad-hoc"],
        "access_level": ["Open", "Request-based", "Restricted", "Confidential"],
        "sla_tier": ["Gold (99.9%)", "Silver (99.5%)", "Bronze (99%)", "None"],
        "business_criticality": ["Mission-critical", "High", "Medium", "Low"],
        "encryption_standard": ["AES-256", "TLS-1.3", "AES-128", "None"],
        "regulatory_scope": ["GDPR", "MiFID II", "AIFMD", "BCBS 239", "Solvency II", "SFDR", "EU Taxonomy", "TCFD", "DORA"],
        "geographic_restriction": ["EU", "UK", "US", "APAC", "Switzerland", "Global"],
        "domain": ["Sustainable Investing", "Risk & Analytics", "Reference Data", "Client Data", "Market Data", "Operations"],
        "sub_domain": ["Climate & Carbon", "Biodiversity", "Social Impact", "Governance Metrics"],
        "source_systems": ["Bloomberg", "MSCI", "Refinitiv", "FactSet", "Internal DWH", "Corporate Filings DB"],
        "consumer_teams": ["Portfolio Management", "ESG Research", "Client Reporting", "Compliance", "Risk", "Operations"],
        "asset_type": ["Data Product", "Data Set", "Report", "API", "Stream", "ML Model"],
        "materialization_type": ["Table", "View", "Materialized View", "Dynamic Table", "External Table"],
        "delivery_method": ["SQL Table", "SQL View", "REST API", "Kafka Topic", "File Export (S3/ADLS)", "GraphQL API"],
        "review_cycle": ["Annual", "Semi-Annual", "Quarterly", "Monthly"],
    }


def _handle_guided_form(path_label: str):
    """Shared handler for guided card-by-card form (path_b remix + path_c create)."""
    if _demo_active():
        valid_options = _demo_valid_options()
    else:
        if "live_valid_options" not in st.session_state:
            with st.spinner("Loading your organisation's data from Collibra…"):
                st.session_state.live_valid_options = _load_live_valid_options()
        valid_options = st.session_state.live_valid_options

    updated_spec, action = render_guided_form(
        st.session_state.spec,
        path_label,
        valid_options,
    )

    if updated_spec and updated_spec is not st.session_state.spec:
        st.session_state.spec = updated_spec
        _autosave_draft()
    elif action not in ("idle", None):
        # Autosave on navigation (skips, panel transitions) even if spec unchanged
        _autosave_draft()

    if action == "handoff":
        _audit("guided_form_complete", f"spec submitted via guided form ({path_label})")
        st.session_state.step = "handoff"
        st.rerun()
    elif action == "colleague_handoff":
        _audit("colleague_handoff", f"handoff generated ({path_label})")
        handoff_data = st.session_state.get("gf_colleague_handoff", {})
        from components.handoff_summary import render_colleague_handoff
        render_colleague_handoff(st.session_state.spec, handoff_data)
    elif action == "back":
        st.session_state.step = "results"
        st.rerun()


def handle_chapter_form(path_label: str):
    if _HAS_GUIDED_FORM:
        _handle_guided_form(path_label)
        return

    chapter = st.session_state.chapter
    chapter_name = _get_chapter_name(chapter)

    if _demo_active():
        concierge_msg = {
            1: "Let's start with the basics — the name, description, and purpose of your data product. These are the first things people will see when they find it in the catalogue.",
            2: "Now let's classify it. The domain and data classification determine which governance policies apply and who can discover it.",
            3: "Time for governance. Clear ownership is what the compliance team looks at first — let's make sure the right people are assigned.",
            4: "Almost there! This section covers the regulatory and technical details — which regulations apply, where the data lives, and how often it updates.",
            5: "Final chapter! Let's define who can access this data, the SLA commitment, and how critical it is to the business.",
        }.get(chapter, "")
        field_explanations = _demo_field_explanations()
        valid_options = _demo_valid_options()
    else:
        try:
            concierge_msg = run_async(st.session_state.concierge.introduce_chapter(chapter, chapter_name, st.session_state.spec))
        except asyncio.TimeoutError:
            st.error("Request timed out. Please try again.")
            concierge_msg = None
        except Exception as _exc:
            logger.error("run_async call failed: %s", _exc, exc_info=True)
            concierge_msg = None

        if "live_valid_options" not in st.session_state:
            with st.spinner("Loading your organisation's data from Collibra…"):
                st.session_state.live_valid_options = _load_live_valid_options()
        valid_options = st.session_state.live_valid_options

        expl_key = f"field_expl_{chapter}"
        if expl_key not in st.session_state:
            try:
                st.session_state[expl_key] = run_async(
                    st.session_state.concierge.explain_chapter_fields(
                        chapter, chapter_name, st.session_state.spec
                    )
                )
            except asyncio.TimeoutError:
                st.error("Request timed out. Please try again.")
                st.session_state[expl_key] = None
            except Exception as _exc:
                logger.error("run_async call failed: %s", _exc, exc_info=True)
                st.session_state[expl_key] = None
        field_explanations = st.session_state[expl_key]

    updated_spec, nav_action = chapter_form.render_chapter(
        chapter, st.session_state.spec, path_label,
        concierge_msg, field_explanations, valid_options
    )

    if updated_spec:
        _audit("chapter_save", f"ch{chapter} '{chapter_name}' saved")
        st.session_state.spec = updated_spec
        _autosave_draft()

    if nav_action == "next" and chapter < 5:
        st.session_state.chapter = chapter + 1
        _scroll_top()
        st.rerun()
    elif nav_action == "prev" and chapter > 1:
        st.session_state.chapter = chapter - 1
        _scroll_top()
        st.rerun()
    elif nav_action == "submit":
        _audit("chapter_submit", f"all chapters submitted → handoff")
        st.session_state.step = "handoff"
        st.rerun()


def handle_create_conversation():
    """Handle the CREATE flow (path_c)."""
    if _HAS_GUIDED_FORM:
        _handle_guided_form("create")
        return

    if _demo_active():
        valid_options = _demo_valid_options()
    else:
        if "live_valid_options" not in st.session_state:
            with st.spinner("Loading your organisation's data from Collibra…"):
                st.session_state.live_valid_options = _load_live_valid_options()
        valid_options = st.session_state.live_valid_options

    updated_spec, is_complete = conversation_create.render_conversation(
        st.session_state.spec,
        valid_options,
        _demo_active(),
    )

    if updated_spec:
        st.session_state.spec = updated_spec
        _autosave_draft()

    if is_complete:
        _audit("conversation_complete", "spec submitted from chat flow")
        st.session_state.step = "handoff"
        st.rerun()


def handle_handoff():
    spec = st.session_state.spec

    if _demo_active():
        narrative = (
            f"**{spec.name or 'Your Data Product'}** is ready for technical review.\n\n"
            f"{'The data owner, ' + spec.data_owner_name + ', will be accountable for ongoing quality and governance.' if spec.data_owner_name else 'An owner should be assigned before approval.'}\n\n"
            f"The technical team should verify the schema at `{spec.schema_location or 'TBC'}` and confirm the "
            f"{spec.update_frequency or 'specified'} refresh schedule is achievable.\n\n"
            f"There are {len(spec.required_missing())} required fields still to complete — "
            f"these can be filled in during the technical review stage."
        )
    else:
        try:
            narrative = run_async(st.session_state.concierge.generate_handoff_narrative(spec))
        except asyncio.TimeoutError:
            st.error("Request timed out. Please try again.")
            narrative = None
        except Exception as _exc:
            logger.error("run_async call failed: %s", _exc, exc_info=True)
            narrative = None

    # DDL preview — shown when schema_location or materialization_type is set
    if _HAS_SNOWFLAKE_PREVIEW and (spec.schema_location or spec.materialization_type):
        with st.expander("🏔 Snowflake DDL Preview", expanded=bool(spec.schema_location and spec.materialization_type)):
            render_snowflake_preview(spec)

    action = handoff_summary.render(spec, narrative, st.session_state.concierge_msg)

    if action == "submit":
        if _demo_active():
            _audit("submit", f"demo submit: {spec.name}")
            st.session_state.step = "complete"
            st.rerun()
        else:
            try:
                collibra_id = run_async(st.session_state.collibra_client.create_draft_asset(spec))
            except asyncio.TimeoutError:
                st.error("Request timed out. Please try again.")
                collibra_id = None
            except Exception as _exc:
                logger.error("run_async call failed: %s", _exc, exc_info=True)
                collibra_id = None
            try:
                run_async(st.session_state.postgres.save_session(
                    st.session_state.session_id, spec.dict(), "submitted", collibra_id
                ))
            except asyncio.TimeoutError:
                st.error("Request timed out. Please try again.")
            except Exception as _exc:
                logger.error("run_async call failed: %s", _exc, exc_info=True)
            _audit("submit", f"live submit: {spec.name} → Collibra {collibra_id}")
            st.session_state.collibra_id = collibra_id
            st.session_state.step = "complete"
            st.rerun()
    elif action == "edit":
        st.session_state.step = "path_b" if st.session_state.path == "remix" else "path_c"
        st.session_state.chapter = 5
        st.rerun()


def handle_complete():
    spec = st.session_state.spec
    collibra_id = st.session_state.get("collibra_id")

    if _demo_active():
        completion_msg = (
            f"Brilliant work! {spec.name or 'Your data product'} has been submitted for technical review. "
            f"{'The owner, ' + spec.data_owner_name + ', has been notified.' if spec.data_owner_name else ''} "
            f"You'll receive an email when the review is complete."
        )
    else:
        try:
            completion_msg = run_async(st.session_state.concierge.generate_completion_message(spec))
        except asyncio.TimeoutError:
            st.error("Request timed out. Please try again.")
            completion_msg = None
        except Exception as _exc:
            logger.error("run_async call failed: %s", _exc, exc_info=True)
            completion_msg = None

    restart = handoff_summary.render_completion(
        spec, completion_msg, collibra_id, st.session_state.session_id
    )

    if restart:
        _audit("restart", "user started a new session")
        st.session_state.clear()
        st.rerun()


def _handle_shared_draft_url(draft_id: str, role: str) -> None:
    """
    Entry point when a colleague arrives via a shared URL.
    Loads the draft, sets session state, routes to role-scoped form.
    """
    # Validate role is one of the known roles
    _VALID_ROLES = {"tech", "owner", "steward", "compliance"}
    if role not in _VALID_ROLES:
        st.error(f"Unknown role '{role}'. Valid roles: {', '.join(sorted(_VALID_ROLES))}")
        return

    dm = _get_draft_manager()
    if dm is None or not dm.is_available:
        st.warning("Draft sharing requires a database connection. Running in demo mode.")
        return
    try:
        try:
            record = run_async(dm.get_by_invite_token(draft_id))
        except asyncio.TimeoutError:
            st.error("Request timed out. Please try again.")
            return
        except Exception as _exc:
            logger.error("run_async call failed: %s", _exc, exc_info=True)
            record = None
        if record is None:
            # Try loading by draft_id directly as fallback
            try:
                record = run_async(dm.load(draft_id))
            except asyncio.TimeoutError:
                st.error("Request timed out. Please try again.")
                return
            except Exception as _exc:
                logger.error("run_async call failed: %s", _exc, exc_info=True)
                record = None
        if record is None:
            st.error("This shared link has expired or the draft was not found.")
            return

        # Load spec
        try:
            st.session_state.spec = DataProductSpec(**record.spec_dict)
        except Exception as exc:
            logger.warning("Spec deserialization failed, starting fresh: %s", exc)
            st.session_state.spec = DataProductSpec(name="", description="", business_purpose="")
            st.warning("Some saved fields could not be restored. Please review your draft.")
        st.session_state.draft_id = record.draft_id
        st.session_state.draft_updated_at = record.updated_at  # for optimistic locking
        st.session_state.path = record.path or "remix"
        st.session_state.step = "shared_form"
        st.session_state.shared_role = role
        st.session_state.shared_product_name = record.display_name
        st.session_state.shared_draft_loaded = True

        # Restore field status from ui_state so colleague sees existing progress
        if record.ui_state and record.ui_state.get("gf_field_status"):
            st.session_state["gf_field_status"] = record.ui_state["gf_field_status"]

        _audit("shared_draft_opened", f"role={role} draft={record.draft_id[:8]}")
        st.rerun()
    except Exception:
        st.error(f"Could not load shared draft. Please ask the sender to reshare the link.")


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
_STEP_LABELS = {
    "auth": ("🔐", "Authenticating"),
    "search": ("🔍", "Search"),
    "results": ("📋", "Results"),
    "path_a": ("✓", "Use As-Is"),
    "path_b": ("✂", "Remixing"),
    "path_c": ("🏗", "Building"),
    "handoff": ("📤", "Handoff"),
    "complete": ("✅", "Complete"),
}

_CHAPTER_NAMES = ["Identity", "Classification", "Governance", "Compliance", "Access"]


def render_sidebar():
    step = st.session_state.get("step", "search")
    spec = st.session_state.get("spec")
    chapter = st.session_state.get("chapter", 1)
    errors = st.session_state.get("errors", [])

    with st.sidebar:
        # ── Wordmark ──────────────────────────────────────────────────────────
        st.markdown(
            '<p style="color:#4DD9C0;font-size:1.5rem;font-weight:700;letter-spacing:.04em;margin-bottom:0;line-height:1.2;">✦ Data Product</p>'
            '<p style="color:#FFFFFF;font-size:1.05rem;margin-top:2px;opacity:.65;letter-spacing:.06em;font-weight:300;">Concierge</p>',
            unsafe_allow_html=True,
        )
        st.markdown('<hr style="border-color:rgba(77,217,192,.2);margin:0.5rem 0 1rem;">', unsafe_allow_html=True)

        # ── Config warning (sidebar only, never main page) ───────────────────
        if not _SECRETS_LOADED:
            st.markdown(
                '<div style="background:rgba(232,56,77,.1);border:1px solid rgba(232,56,77,.3);'
                'border-radius:6px;padding:.4rem .6rem;margin-bottom:.5rem;">'
                '<span style="color:#E8384D;font-size:.72rem;font-weight:600;">⚠ No secrets.toml</span><br>'
                '<span style="color:rgba(255,255,255,.6);font-size:.68rem;">'
                'Add .streamlit/secrets.toml to connect live APIs.</span>'
                '</div>',
                unsafe_allow_html=True,
            )

        # ── Demo mode toggle — always visible ────────────────────────────────
        current_demo = st.session_state.get("demo_mode", not LIVE_CAPABLE)
        new_demo = st.toggle(
            "Demo mode",
            value=current_demo,
            key="_sidebar_demo_toggle",
            help="On: sample data only. Off: connects to live Collibra APIs (requires secrets.toml).",
        )
        if new_demo != current_demo:
            st.session_state.demo_mode = new_demo
            _audit("demo_toggle", f"demo mode → {'on' if new_demo else 'off'}")
            st.rerun()

        st.markdown('<div style="height:.3rem;"></div>', unsafe_allow_html=True)

        # ── Step progress ─────────────────────────────────────────────────────
        icon, label = _STEP_LABELS.get(step, ("•", step.title()))
        step_order = list(_STEP_LABELS.keys())
        completed_steps = step_order.index(step) if step in step_order else 0
        total_steps = len(step_order) - 1
        pct = int((completed_steps / total_steps) * 100)

        st.markdown(
            f'<p style="color:#4DD9C0;font-size:.7rem;text-transform:uppercase;letter-spacing:.1em;margin-bottom:.3rem;">Current Step</p>'
            f'<p style="color:#FFFFFF;font-size:1rem;font-weight:600;margin:0;">{icon} {label}</p>',
            unsafe_allow_html=True,
        )
        st.progress(pct / 100)
        st.markdown('<div style="height:.5rem;"></div>', unsafe_allow_html=True)

        # ── Spec completion ──────────────────────────────────────────────────
        if spec and step in ("path_a", "path_b", "path_c", "handoff", "complete"):
            completion = spec.completion_percentage()
            missing = spec.required_missing()

            st.markdown(
                '<p style="color:#4DD9C0;font-size:.7rem;text-transform:uppercase;letter-spacing:.1em;margin-bottom:.3rem;">Spec Completion</p>',
                unsafe_allow_html=True,
            )
            st.progress(completion / 100)
            st.markdown(
                f'<p style="color:#FFFFFF;font-size:.85rem;margin-top:.2rem;">'
                f'<span style="color:#4DD9C0;font-weight:700;">{completion:.0f}%</span>'
                f'{"  ·  " + str(len(missing)) + " required field" + ("s" if len(missing) != 1 else "") + " remaining" if missing else "  ·  All required fields complete ✓"}'
                f'</p>',
                unsafe_allow_html=True,
            )

            # Chapter indicators (path_b only)
            if step == "path_b":
                st.markdown(
                    '<p style="color:#4DD9C0;font-size:.7rem;text-transform:uppercase;letter-spacing:.1em;margin:.8rem 0 .4rem;">Chapters</p>',
                    unsafe_allow_html=True,
                )
                for i, name in enumerate(_CHAPTER_NAMES, 1):
                    if i < chapter:
                        marker, color, weight = "✓", "#4DD9C0", "600"
                    elif i == chapter:
                        marker, color, weight = "●", "#FFFFFF", "700"
                    else:
                        marker, color, weight = "○", "rgba(255,255,255,.4)", "400"
                    st.markdown(
                        f'<p style="color:{color};font-weight:{weight};font-size:.85rem;margin:.15rem 0;">'
                        f'{marker}  {i}. {name}</p>',
                        unsafe_allow_html=True,
                    )

            st.markdown('<div style="height:.5rem;"></div>', unsafe_allow_html=True)

        # ── Share with Team ───────────────────────────────────────────────────
        _draft_id = st.session_state.get("draft_id")
        if _draft_id and step in ("path_c", "handoff", "complete"):
            st.markdown('<hr style="border-color:rgba(77,217,192,.2);margin:.6rem 0;">', unsafe_allow_html=True)
            with st.expander("🔗 Share with Team", expanded=False):
                try:
                    from components.draft_banner import render_share_panel
                    _field_status = st.session_state.get("gf_field_status")
                    _spec_name = spec.name if spec else ""
                    render_share_panel(
                        draft_id=_draft_id,
                        field_status=_field_status,
                        spec_name=_spec_name,
                    )
                except Exception as _e:
                    st.caption(f"Share panel unavailable: {_e}")

        # ── RBAC / Role ───────────────────────────────────────────────────────
        st.markdown(
            '<p style="color:#4DD9C0;font-size:.7rem;text-transform:uppercase;letter-spacing:.1em;margin-bottom:.3rem;">Access</p>',
            unsafe_allow_html=True,
        )
        role = os.getenv("USER_ROLE", "Data Analyst")
        display_name = os.getenv("USER_DISPLAY_NAME", role)
        mode_label = "Demo" if _demo_active() else "Live"
        mode_color = "rgba(255,255,255,.4)" if _demo_active() else "#4DD9C0"
        st.markdown(
            f'<p style="color:#FFFFFF;font-size:.85rem;margin:.1rem 0;">👤 {display_name}</p>'
            f'<p style="color:{mode_color};font-size:.8rem;margin:.1rem 0;">⬤ {mode_label} mode</p>',
            unsafe_allow_html=True,
        )

        # ── Connections ───────────────────────────────────────────────────────
        st.markdown('<hr style="border-color:rgba(77,217,192,.2);margin:1rem 0 .5rem;">', unsafe_allow_html=True)

        with st.expander("⚙ Connections", expanded=False):
            def _conn_row(name, env_key, alt_keys=None):
                val = os.getenv(env_key) or next(
                    (os.getenv(k) for k in (alt_keys or []) if os.getenv(k)), None
                )
                dot = '<span style="color:#00C48C;">⬤</span>' if val else '<span style="color:#E8384D;">⬤</span>'
                state = "Connected" if val else "Not configured"
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;align-items:center;margin:.25rem 0;">'
                    f'<span style="color:rgba(255,255,255,.75);font-size:.8rem;">{name}</span>'
                    f'<span style="font-size:.75rem;">{dot} <span style="color:rgba(255,255,255,.5);">{state}</span></span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            st.markdown('<p style="color:#4DD9C0;font-size:.7rem;text-transform:uppercase;letter-spacing:.1em;margin:.3rem 0 .5rem;">Collibra / APIM</p>', unsafe_allow_html=True)
            _conn_row("APIM Gateway", "APIM_BASE_URL")
            _conn_row("JWT Client ID", "APIM_CLIENT_ID", ["CLIENT_ID"])
            _conn_row("JWT Secret", "APIM_CLIENT_SECRET", ["CLIENT_SECRET"])
            _conn_row("Collibra Tenant", "COLLIBRA_BASE_URL")

            st.markdown('<p style="color:#4DD9C0;font-size:.7rem;text-transform:uppercase;letter-spacing:.1em;margin:.6rem 0 .5rem;">Snowflake</p>', unsafe_allow_html=True)
            _conn_row("Account", "SNOWFLAKE_ACCOUNT")
            _conn_row("Database", "SNOWFLAKE_DATABASE")
            _conn_row("Schema", "SNOWFLAKE_SCHEMA")
            _conn_row("User", "SNOWFLAKE_USER")
            _conn_row("Warehouse", "SNOWFLAKE_WAREHOUSE")

            st.markdown('<p style="color:#4DD9C0;font-size:.7rem;text-transform:uppercase;letter-spacing:.1em;margin:.6rem 0 .5rem;">AI Provider</p>', unsafe_allow_html=True)
            llm = os.getenv("LLM_PROVIDER", "openai")
            _conn_row("OpenAI API Key", "OPENAI_API_KEY") if llm == "openai" else _conn_row("AWS Bedrock Region", "AWS_DEFAULT_REGION")
            st.markdown(f'<p style="color:rgba(255,255,255,.4);font-size:.75rem;margin:.3rem 0;">Provider: {llm.upper()}</p>', unsafe_allow_html=True)

        # ── Audit & Logging ────────────────────────────────────────────────────
        with st.expander("📋 Audit & Logging", expanded=False):
            st.markdown('<p style="color:#4DD9C0;font-size:.7rem;text-transform:uppercase;letter-spacing:.1em;margin:.3rem 0 .5rem;">Postgres / Audit Log</p>', unsafe_allow_html=True)

            def _conn_row_audit(name, env_key):
                val = os.getenv(env_key)
                dot = '<span style="color:#00C48C;">⬤</span>' if val else '<span style="color:#E8384D;">⬤</span>'
                state = "Configured" if val else "Not configured"
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;align-items:center;margin:.25rem 0;">'
                    f'<span style="color:rgba(255,255,255,.75);font-size:.8rem;">{name}</span>'
                    f'<span style="font-size:.75rem;">{dot} <span style="color:rgba(255,255,255,.5);">{state}</span></span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            _conn_row_audit("Postgres Host", "POSTGRES_HOST")
            _conn_row_audit("Postgres DB", "POSTGRES_DB")
            _conn_row_audit("Postgres User", "POSTGRES_USER")

            log_level = os.getenv("LOG_LEVEL", "INFO")
            st.markdown(
                f'<p style="color:rgba(255,255,255,.5);font-size:.75rem;margin:.5rem 0 .2rem;">Log level: <span style="color:#4DD9C0;">{log_level}</span></p>',
                unsafe_allow_html=True,
            )

            sid = st.session_state.get("session_id", "—")
            st.markdown(
                f'<p style="color:rgba(255,255,255,.4);font-size:.7rem;margin:.3rem 0;word-break:break-all;">Session: {sid[:16]}…</p>',
                unsafe_allow_html=True,
            )

            # In-session audit trail
            audit_log = st.session_state.get("audit_log", [])
            if audit_log:
                st.markdown('<p style="color:#4DD9C0;font-size:.7rem;text-transform:uppercase;letter-spacing:.1em;margin:.6rem 0 .3rem;">Session Activity</p>', unsafe_allow_html=True)
                for entry in reversed(audit_log[-8:]):
                    detail_str = f" — {entry['detail']}" if entry.get("detail") else ""
                    st.markdown(
                        f'<p style="color:rgba(255,255,255,.45);font-size:.7rem;margin:.1rem 0;">'
                        f'[{entry["ts"]}] <span style="color:rgba(255,255,255,.7);">{entry["action"]}</span>{detail_str}'
                        f'</p>',
                        unsafe_allow_html=True,
                    )

            if not _demo_active() and st.button("Clear session cache", key="sidebar_clear_cache"):
                for key in ["live_valid_options"] + [k for k in st.session_state if k.startswith("field_expl_")]:
                    st.session_state.pop(key, None)
                st.rerun()

        # ── Debug / Errors ────────────────────────────────────────────────────
        error_count = len(errors)
        with st.expander(f"🐛 Debug{' (' + str(error_count) + ' error' + ('s' if error_count != 1 else '') + ')' if error_count else ''}", expanded=bool(error_count)):
            if errors:
                st.markdown('<p style="color:#E8384D;font-size:.7rem;text-transform:uppercase;letter-spacing:.1em;margin-bottom:.4rem;">Errors</p>', unsafe_allow_html=True)
                for err in errors[-5:]:
                    st.markdown(
                        f'<div style="background:rgba(232,56,77,.1);border-left:2px solid #E8384D;padding:.3rem .5rem;margin:.3rem 0;border-radius:3px;">'
                        f'<p style="color:#E8384D;font-size:.72rem;margin:0;word-break:break-all;">{err}</p>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                if st.button("Clear errors", key="clear_errors_debug"):
                    st.session_state.errors = []
                    st.rerun()
            else:
                st.markdown('<p style="color:rgba(255,255,255,.3);font-size:.75rem;">No errors this session</p>', unsafe_allow_html=True)

            # App version / env info
            st.markdown(
                f'<p style="color:rgba(255,255,255,.25);font-size:.65rem;margin-top:.5rem;">'
                f'Mode: {"demo" if _demo_active() else "live"} · '
                f'Step: {step}'
                f'</p>',
                unsafe_allow_html=True,
            )

        # ── Start over ────────────────────────────────────────────────────────
        if step not in ("auth", "search"):
            st.markdown('<div style="height:.5rem;"></div>', unsafe_allow_html=True)
            # Step 1: Show "Start Over" button normally
            if not st.session_state.get("_confirm_restart", False):
                if st.button("↺ Start over", key="restart_btn", use_container_width=True):
                    st.session_state["_confirm_restart"] = True
                    st.rerun()
            # Step 2: Show confirmation
            else:
                st.markdown(
                    '<p style="color:rgba(255,255,255,.7);font-size:.72rem;margin-bottom:.3rem;">This clears all progress. Sure?</p>',
                    unsafe_allow_html=True,
                )
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("Yes, restart", key="restart_confirm_yes", use_container_width=True):
                        _audit("restart", "user confirmed start over")
                        st.session_state.clear()
                        st.rerun()
                with col_no:
                    if st.button("Cancel", key="restart_confirm_no", use_container_width=True):
                        st.session_state["_confirm_restart"] = False
                        st.rerun()


# ---------------------------------------------------------------------------
# Breadcrumb
# ---------------------------------------------------------------------------
def _render_breadcrumb() -> None:
    """Render macro journey breadcrumb — shown on all steps except search."""
    step = st.session_state.get("step", "search")
    if step == "search":
        return  # No breadcrumb on home

    # Map step to stage index (1-based)
    if step == "results":
        active = 2
    elif step in ("path_a",):
        active = 3
    elif step in ("path_b", "path_c", "guided_form"):
        active = 3
    elif step in ("handoff", "colleague_handoff"):
        active = 4
    else:
        active = 2

    stages = ["Search", "Results", "Build", "Review"]
    chips = ""
    for i, label in enumerate(stages, 1):
        if i < active:
            # Completed
            color = "#006B73"
            bg = "rgba(0,107,115,0.08)"
            border = "rgba(0,107,115,0.25)"
            prefix = "✓ "
        elif i == active:
            # Current
            color = "#006B73"
            bg = "rgba(0,194,203,0.12)"
            border = "#00C2CB"
            prefix = ""
        else:
            # Future
            color = "#8C9BAA"
            bg = "transparent"
            border = "rgba(13,27,42,0.10)"
            prefix = ""

        connector = (
            '<span style="color:rgba(13,27,42,0.15);font-size:.8rem;margin:0 4px;">›</span>'
            if i < len(stages) else ""
        )
        chips += (
            f'<span style="display:inline-flex;align-items:center;background:{bg};'
            f'color:{color};border:1px solid {border};border-radius:100px;'
            f'padding:3px 12px;font-size:.75rem;font-weight:600;">'
            f'{prefix}{label}</span>{connector}'
        )

    st.markdown(
        f'<div style="display:flex;align-items:center;gap:4px;margin-bottom:1.25rem;">'
        f'{chips}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    inject_styles()
    initialize_session_state()
    render_sidebar()

    # Scroll to top whenever the step changes
    step = st.session_state.step
    if st.session_state.get("_prev_step") != step:
        _scroll_top()
        st.session_state._prev_step = step

    # Inject Cmd+Enter keyboard shortcut on form/handoff pages
    if _HAS_UX_HELPERS and step in ("path_b", "path_c", "handoff"):
        inject_keyboard_submit()

    # Breadcrumb — shown on every step except search (function returns early for search)
    _render_breadcrumb()

    # ── Shared draft entry via URL params ─────────────────────────────────────
    _qp_draft_id = None
    _qp_role = None
    try:
        _qp_draft_id = st.query_params.get("draft_id")
        _qp_role = st.query_params.get("role")
    except Exception:
        try:
            _qp = st.experimental_get_query_params()
            _qp_draft_id = (_qp.get("draft_id") or [None])[0]
            _qp_role = (_qp.get("role") or [None])[0]
        except Exception:
            pass

    if _qp_draft_id and _qp_role and not st.session_state.get("shared_draft_loaded"):
        _handle_shared_draft_url(_qp_draft_id, _qp_role)

    # Route
    try:
        if step == "auth":
            handle_auth()
        elif step == "search":
            handle_search()
        elif step == "results":
            handle_results()
        elif step == "path_a":
            handle_reuse()
        elif step == "path_b":
            handle_chapter_form("remix")
        elif step == "path_c":
            handle_create_conversation()
            if _HAS_UX_HELPERS:
                inject_chat_autofocus()
        elif step == "handoff":
            handle_handoff()
        elif step == "complete":
            handle_complete()
        elif step == "shared_form":
            if _HAS_GUIDED_FORM:
                from components.shared_draft_entry import render_shared_draft_entry
                render_shared_draft_entry(
                    spec=st.session_state.spec,
                    role=st.session_state.get("shared_role", "tech"),
                    product_name=st.session_state.get("shared_product_name", ""),
                    draft_id=st.session_state.get("draft_id", ""),
                )
            else:
                st.info("Shared form requires the guided form component.")
    except Exception as e:
        err = format_error(e)
        _audit("error", err)
        st.session_state.errors.append(err)
        st.rerun()


if __name__ == "__main__":
    main()
