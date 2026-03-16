# Roadmap — Data Product Concierge

> Status key: ✅ Shipped · 🔨 In progress · 🗓 Planned · 💡 Proposed

---

## Phase 0 — Foundation  *(Shipped)*

### Core infrastructure
- ✅ Streamlit app with wide layout, session state orchestration, demo/live mode switching
- ✅ `src/` package layout with `sys.path` bridge from app root
- ✅ Pydantic v2 `DataProductSpec` — 35+ fields, full validation, enums for all constrained values
- ✅ `to_collibra_json()`, `to_snowflake_csv()`, `to_markdown()` serialisation methods
- ✅ `completion_percentage()`, `required_missing()`, `optional_missing()` computed methods
- ✅ `core/field_registry.py` — single source of truth for field metadata (label, question, explanation, owner, options, required)
- ✅ `core/async_utils.run_async(coro, timeout)` — shared event-loop helper, never redefined locally
- ✅ `_app_state_version` guard — clears widget state on Streamlit version upgrade to prevent selectbox deserialisation errors
- ✅ `_demo_active()` guard — zero AI/API calls in demo mode across all 6 AI touchpoints

### Connectivity
- ✅ APIM token manager with token cache and `get_llm_headers()` (sync)
- ✅ Collibra OAuth2 client
- ✅ asyncpg connection pool wrapper with `ConcurrentEditError` optimistic locking
- ✅ `DraftManager` — spec JSON persistence, role metadata, full audit log

### LLM backends
- ✅ Direct OpenAI (`AsyncOpenAI`) with GPT-4o
- ✅ AWS Bedrock Claude (`boto3.client("bedrock-runtime")`)
- ✅ APIM-routed Azure OpenAI (`AsyncAzureOpenAI`) with per-call header injection via `LLM_VIA_APIM=true`

---

## Phase 1 — AI Wiring & NLQ Pipeline  *(Shipped)*

### NLQ → pre-filled form
- ✅ `nlq_intake.py` — plain-English text area before guided form
- ✅ `chat_turn()` called on intake text to extract all possible fields in one LLM call
- ✅ `_apply_extracted_to_spec()` — merges AI extractions onto blank fields only, never overwrites user data
- ✅ `ai_suggested_fields` session state set — tracks which fields were pre-filled by AI
- ✅ **💡 AI suggestion — review and confirm** badge on every AI-pre-filled field card
- ✅ Accepting a suggestion removes the badge; editing overrides and removes it
- ✅ Skip button for users who prefer to fill manually

### Smart field matching
- ✅ `validate_and_normalise()` wired into guided form Continue handler for option fields
- ✅ High confidence (≥ 70%): silently accepted, green `st.toast("✓ Matched: ...")`
- ✅ Medium confidence (40–70%): `Did you mean "X"?` banner with `Use "X"` / `Keep my value` buttons — button shows actual matched value, not generic label
- ✅ `NormalisedValue.matched` is `Optional[str]` (canonical value) — not a boolean

### Contextual field guidance
- ✅ `explain_field()` wired below each guided form label
- ✅ Cached per `(field_name, domain[:10], cls[:10])` — no repeat LLM calls on same field + context
- ✅ Falls back to static registry explanation in demo mode or on timeout

### Remix governance impact
- ✅ `explain_field_impact()` method added to concierge
- ✅ Triggers on: `data_classification`, `pii_flag`, `regulatory_scope`, `data_sovereignty_flag`
- ✅ Amber `⚡` impact banner shown above the changed field
- ✅ Cached by `(field, hash(old_value), hash(new_value))` — no repeat LLM calls for same change
- ✅ Returns empty string for immaterial changes — no noise

### Completion narrative
- ✅ `generate_completion_message()` wired into `handoff_summary.py`
- ✅ Personalised summary in teal **✨ AI Summary** card at top of handoff screen
- ✅ Cached by spec name — no re-call on page re-render

### Conversational path improvements
- ✅ `is_complete=True` from `chat_turn()` triggers handover screen automatically
- ✅ `with st.spinner("Thinking…")` wraps `chat_turn()` — visual feedback during LLM call
- ✅ `asyncio.TimeoutError` caught separately from generic exceptions in all AI call sites
- ✅ All bare `except Exception` blocks log with `exc_info=True`

---

## Phase 2 — UX Hardening  *(Shipped)*

### Handoff screen
- ✅ Completion bar with colour-coded percentage (green / amber / red)
- ✅ 3-card status grid: Fields Complete · Optional Missing · Required Missing
- ✅ Submit button disabled with explicit instruction: *"Click ← Go back and edit below to complete them"*
- ✅ **Assign & Notify Team** panel — role presets (Data Owner, Tech Team, Data Steward, Compliance)
- ✅ Pre-composed role-specific email body per recipient type
- ✅ `st.link_button` opens `mailto:` in default email client
- ✅ Shareable deep link (`?draft_id=...&role=tech`) for direct role-scoped entry
- ✅ Sent-this-session log of all assignments
- ✅ Audit trail expander with `DraftManager.get_audit_log()`

### Download options
- ✅ Markdown specification (`.md`)
- ✅ Collibra bulk import (`.json`)
- ✅ Snowflake DATA_GOVERNANCE ingest (`.csv`)
- ✅ Inline download in conversational path (always visible once name is set)

### Deployment pipeline
- ✅ `streamlit` removed from `requirements.txt` — Streamlit Cloud manages the runtime, no version conflicts
- ✅ `packages.txt` deleted — asyncpg ships pre-built manylinux wheels for Python 3.12 / Linux x86_64
- ✅ `runtime.txt` — `python-3.12`
- ✅ `requirements-dev.txt` — pytest deps separated from production
- ✅ `Dockerfile` — `gcc` + `python3-dev` for asyncpg source-build fallback

---

## Phase 3 — Collaborative Editing & Governance Depth  *(Planned — Q2 2026)*

### Multi-role simultaneous editing
- 🗓 Role-locked field sections — business user sees only their fields, tech user sees only theirs, steward sees all
- 🗓 Real-time presence indicator: "Sarah (Data Owner) is currently editing Classification"
- 🗓 `DraftManager` WebSocket or polling bridge for live co-edit without full page reload
- 🗓 Conflict resolution UI — show diff when two users edit the same field, let owner resolve

### Approval workflow
- 🗓 Spec moves through `Draft → Candidate → Approved → Deprecated` lifecycle states
- 🗓 Each transition requires sign-off from a specific role (e.g. Data Steward must approve classification)
- 🗓 Email notification on transition with spec diff
- 🗓 `approved_at`, `approved_by` fields written to Collibra on approval

### Governance rules engine
- 🗓 Server-side validation rules: `data_classification=Confidential` → `pii_flag` required, `data_sovereignty_flag` required
- 🗓 Rules expressed as `FieldRule` Pydantic models in `field_registry.py` — not hardcoded in UI
- 🗓 Violated rules shown as inline guardrail cards, not just toast warnings

---

## Phase 4 — Discovery Intelligence  *(Planned — Q3 2026)*

### Semantic search upgrade
- 🗓 Vector embeddings for asset descriptions and business purposes
- 🗓 Semantic similarity search alongside Collibra keyword search
- 🗓 "More like this" from any search result card
- 🗓 Search history and recent views in sidebar

### Duplicate detection
- 🗓 Before a user starts a new spec, compare NLQ input against existing products via embeddings
- 🗓 If similarity > threshold: show `This looks similar to [Payments Fraud Detection v2] — remix instead?`
- 🗓 Reduces spec sprawl without blocking creation

### Lineage visualisation
- 🗓 Upstream / downstream dependency graph rendered from `lineage_upstream`, `lineage_downstream` fields
- 🗓 Click through to related data products
- 🗓 Impact analysis: "Deprecating this product affects 4 downstream consumers"

### Maturity scoring
- 🗓 `score_spec_completeness(spec)` wired into maturity dashboard UI
- 🗓 Per-dimension scores: governance, technical, operational, compliance
- 🗓 Maturity badge on asset cards in search results

---

## Phase 5 — Enterprise Integrations  *(Planned — Q4 2026)*

### Collibra write-back
- 🗓 On submit: `POST /assets` + `PATCH /assets/{id}/attributes` with full spec
- 🗓 Collibra asset ID stored in spec, shown in completion screen
- 🗓 Update path: `PATCH` existing asset if `collibra_id` is set

### Snowflake DDL generation
- 🗓 From `column_definitions` + `materialization_type` + `schema_location`: generate `CREATE TABLE` / `CREATE VIEW` DDL
- 🗓 Download as `.sql` from handoff screen
- 🗓 Optional: push DDL to a Snowflake staging environment via Snowflake connector

### Slack / Teams notifications
- 🗓 Webhook integration — notify `#data-governance` channel on spec submission
- 🗓 Configurable per-team webhooks by domain
- 🗓 Mention the nominated data owner by Slack handle

### SSO and RBAC
- 🗓 SAML / OIDC integration via APIM — replace manual email entry for user identity
- 🗓 Role inferred from OIDC claims — business users cannot see tech fields, read-only users cannot edit
- 🗓 Audit log enriched with real user identities

---

## Phase 6 — AI Agent Upgrade  *(Proposed — 2027)*

### Autonomous spec research
- 💡 Given a product name and domain, AI browses firm's internal data catalogue and pre-fills lineage, source systems, related reports — no user input needed for those fields
- 💡 Confidence scores surfaced per extracted field

### Regulatory change monitoring
- 💡 Scheduled job: compare regulatory scope of all Approved specs against published regulatory change feed (ESMA, FCA, SEC)
- 💡 Flag specs that may need re-review due to regulatory update
- 💡 Generate draft impact summary for affected data stewards

### Proactive quality alerts
- 💡 Monitor `data_quality_score` trend across Approved products
- 💡 Alert data owner if score drops below SLA threshold
- 💡 Suggest spec amendments (e.g. retention period mismatch with observed data freshness)

### Natural language spec diff
- 💡 "What changed between v1 and v2 of this spec?" → AI narrates the diff in business terms
- 💡 Shown in audit trail expander alongside raw field changes

---

*Last updated: March 2026*
