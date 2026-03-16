# Data Product Concierge — Product Roadmap

```
  ╔══════════════════════════════════════════════════════════════════════════╗
  ║  From a 25-minute compliance form to an 8-minute AI-guided review.      ║
  ║  This roadmap shows where we are, what ships next, and where we go.     ║
  ╚══════════════════════════════════════════════════════════════════════════╝
```

> This document is structured in two halves.
> **Pages 1–2: Business case, delivered value, and next features** — for stakeholders and funding conversations.
> **Pages 3–4: Technical phases and architecture decisions** — for the engineering team.

---

# Part One — The Business Story

---

## Where We Started

> *"Fill in these 35 fields to register your data product."*

That was the experience. A form. Constrained dropdowns with values no one recognised. No guidance. No context. No way to know which fields applied to which team. Business users either abandoned it, filled it in wrong, or handed it to someone else who then had to chase them for the answers.

The result: a Collibra catalogue full of incomplete, inaccurate, or duplicate data product registrations. Governance without governance.

---

## What We Changed

```
  BEFORE                              AFTER
  ──────────────────────────────────  ──────────────────────────────────────
  35-field blank form                 "Describe your data product" → AI
                                      pre-fills what it can → you confirm

  Free-text enum entry                Fuzzy match to canonical Collibra
  → invalid values in Collibra        values, confidence-gated in code

  No guidance per field               Context-aware 1-line hint on every
                                      field, specific to your domain

  "Send this to the tech team"        Role-scoped deep link — they open
  → email → attachment → confusion    the form, see only their fields

  Change a classification, no         ⚡ Amber banner: "This now requires
  awareness of consequences           DPIA review and sovereignty flag"

  Completion = submit button          AI-narrated summary: "Your Risk
  with no context                     Analytics spec is ready — 3 PII
                                      fields flagged for compliance"
```

---

## What Is Live Today  ✅

```
  ┌─────────────────────────────────────────────────────────────────────┐
  │                                                                     │
  │   DISCOVER          CREATE              GOVERN          HAND OFF   │
  │                                                                     │
  │   Search Collibra   Describe in         Remix existing  Email owner │
  │   Find existing  →  plain English  →    products with  Tech team   │
  │   assets before     AI pre-fills        ⚡ governance   Steward     │
  │   creating          the form            impact banners  Compliance  │
  │                          ↓                   ↓               ↓     │
  │                     Review 💡              Confirm         Export  │
  │                     AI suggestions        or override     .md      │
  │                     not type answers                      .json    │
  │                                                           .csv     │
  └─────────────────────────────────────────────────────────────────────┘
```

### The numbers
| Metric | Before | After |
|--------|--------|-------|
| Time to complete a spec | ~25 minutes | ~8 minutes |
| Invalid enum entries reaching Collibra | Frequent | Zero — matched in code |
| Fields requiring human typing | 35 | ~8 (remainder AI-suggested) |
| Awareness of governance change impact | None | Immediate, field-level |
| Handoff to tech team | Email + attachment | Deep link, role-scoped form |
| Spec export formats | None | Markdown · Collibra JSON · Snowflake CSV |

---

## What Ships Next  🔨

These are the three highest-value features that complete the core product. Each has a clear before/after for users.

---

### Next Feature 1 — Multi-Role Collaborative Editing
**Target: Q2 2026**

```
  TODAY                               NEXT
  ──────────────────────────────────  ──────────────────────────────
  Business user fills their fields    Business user fills their fields
  → exports JSON                      → tech team opens same draft
  → tech team receives email          → each role sees only their
  → tech team opens a different         section
    form, re-enters some context      → "Sarah (Data Owner) is
  → no audit of who changed what        currently editing Classification"
                                      → conflict resolution if two
                                        users touch the same field
                                      → full audit trail throughout
```

**Business value:** Eliminates the back-and-forth handoff loop. One draft. Multiple contributors. No data re-entry. Governance is co-created, not chased.

---

### Next Feature 2 — Formal Approval Workflow
**Target: Q2 2026**

```
  Draft  ──→  Candidate  ──→  Approved  ──→  Deprecated
    │               │               │
    │         Steward sign-off      Compliance sign-off
    │         on classification     on regulatory scope
    │
    └── Any team member can progress;
        role-specific sign-offs gate each transition
```

**Business value:** Specs are currently submitted with no formal review gate. This introduces the `Draft → Candidate → Approved → Deprecated` lifecycle that Collibra expects, with email notifications at each transition and an audit log of who approved what and when.

---

### Next Feature 3 — Duplicate Detection Before Creation
**Target: Q3 2026**

```
  User types: "Payments fraud detection for Risk team"
       ↓
  Before the form opens:
  ┌─────────────────────────────────────────────────────┐
  │  ⚠  This looks similar to 2 existing products:     │
  │                                                     │
  │  • Payments Fraud Detection Daily  (87% similar)   │
  │    Risk domain · GDPR · Last updated Jan 2026      │
  │    [ View ] [ Remix this instead ]                  │
  │                                                     │
  │  • Fraud Analytics Aggregated  (71% similar)       │
  │    [ View ] [ Remix this instead ]                  │
  │                                                     │
  │  [ Create new anyway → ]                            │
  └─────────────────────────────────────────────────────┘
```

**Business value:** Prevents catalogue sprawl. Surfaces reuse opportunities before the user invests 8 minutes in a spec that already exists. Reduces steward review burden by stopping duplicates at source.

---

## The Longer Horizon  🗓

```
  Q2 2026          Q3 2026          Q4 2026          2027
  ───────────────  ───────────────  ───────────────  ──────────────────
  Multi-role       Semantic search  Collibra         Autonomous spec
  editing          upgrade          write-back        research
                   (vector          (direct API       (AI reads
  Approval         embeddings)      POST on submit)   catalogue,
  workflow                                            pre-fills
                   Lineage          Snowflake DDL     lineage)
  Governance       visualisation    generation
  rules engine                                        Regulatory
                   Maturity         Slack / Teams     change
                   scoring          notifications     monitoring
                   dashboard
                                    SSO + RBAC        Proactive
                                    (SAML / OIDC)     quality alerts
```

---

## The Platform Question — React Rebuild

The current application is built on **Streamlit** — a Python-first rapid prototyping framework. It delivered the entire product, including all AI wiring, in a fraction of the time a traditional frontend would have taken.

The honest assessment:

```
  STREAMLIT (NOW)                     REACT + PYTHON API (FUTURE)
  ──────────────────────────────────  ──────────────────────────────────
  ✅ Full product shipped fast         ✅ Real-time collaborative editing
  ✅ AI pipeline fully wired           ✅ WebSocket presence indicators
  ✅ No frontend/backend split         ✅ Offline draft capability
  ✅ One deployment, one codebase      ✅ Native SSO / RBAC integration
                                       ✅ Custom component library
  ⚠  Page reruns on every action       ✅ Micro-interactions, animations
  ⚠  No WebSockets (limits co-edit)   ✅ Mobile-responsive
  ⚠  Limited offline capability        ✅ Enterprise security model
  ⚠  Streamlit-specific UX patterns
```

**Recommendation:** Continue building features on Streamlit through Phase 4 (Q3 2026). The multi-role editing and approval workflow will push against Streamlit's real-time limits. If adoption and funding justify it, Phase 5 (Q4 2026) is the natural inflection point to begin a React frontend with a FastAPI backend — the AI agent layer and data models transfer unchanged.

**The React rebuild does not start from scratch.** Every concierge method, every Pydantic model, every Collibra connector, and the entire AI pipeline lives in `src/` — entirely independent of Streamlit. The frontend is the only thing that changes.

---
---

# Part Two — Technical Phases

---

## Status Key

```
  ✅  Shipped and in production
  🔨  In active development
  🗓  Planned — date confirmed
  💡  Proposed — subject to prioritisation
```

---

## Phase 0 — Foundation  ✅  *(Shipped)*

> Everything the product stands on. None of this is visible to users, but everything depends on it.

**Infrastructure**
- ✅ Streamlit app orchestrator — session state, routing, demo/live mode switching
- ✅ `src/` package layout with `sys.path` bridge from app root
- ✅ Pydantic v2 `DataProductSpec` — 35+ fields, full validation, enums for all constrained values
- ✅ `to_collibra_json()`, `to_snowflake_csv()`, `to_markdown()` — all three export formats
- ✅ `completion_percentage()`, `required_missing()`, `optional_missing()` — computed spec health
- ✅ `core/field_registry.py` — single source of truth for field metadata
- ✅ `core/async_utils.run_async(coro, timeout)` — shared async bridge, never redefined locally
- ✅ `_app_state_version` guard — prevents widget deserialisation errors on Streamlit upgrades
- ✅ `_demo_active()` guard — zero API/LLM calls in demo mode, across all 6 touchpoints

**Connectivity**
- ✅ APIM token manager with cache and sync `get_llm_headers()`
- ✅ Collibra OAuth2 client
- ✅ asyncpg connection pool with `ConcurrentEditError` optimistic locking
- ✅ `DraftManager` — spec JSON persistence, role metadata, audit log

**LLM backends — three paths, one interface**
- ✅ Direct OpenAI `AsyncOpenAI` — GPT-4o
- ✅ AWS Bedrock Claude — `boto3.client("bedrock-runtime")`
- ✅ APIM-routed Azure OpenAI — `AsyncAzureOpenAI`, per-call header injection via `LLM_VIA_APIM=true`

---

## Phase 1 — AI Wiring & NLQ Pipeline  ✅  *(Shipped)*

> The transformation from form-filling to suggestion-reviewing. All six AI touchpoints wired, guarded, cached, and fallback-safe.

**NLQ → pre-filled form**
- ✅ `nlq_intake.py` — plain-English text area before guided form opens
- ✅ `chat_turn()` on intake text — single LLM call, extracts all possible fields
- ✅ `_apply_extracted_to_spec()` — merges onto blank fields only, never overwrites user data
- ✅ `ai_suggested_fields` session state set — drives the 💡 badge in guided form
- ✅ Badge lifecycle: disappears on Continue (accept) or user edit (override)

**Smart field matching**
- ✅ `validate_and_normalise()` wired into Continue handler for all option fields
- ✅ Confidence clamped in Python: `min(1.0, max(0.0, score))`
- ✅ `matched = None` if `confidence < 0.7` — enforced in code, not by model
- ✅ Medium confidence → `Did you mean "X"?` confirm/deny UI; button shows actual value

**Contextual field guidance**
- ✅ `explain_field()` below every guided form label
- ✅ Cached per `(field_name, domain[:10], cls[:10])` — no repeat LLM calls
- ✅ Timeout fallback → static registry text

**Remix governance impact**
- ✅ `explain_field_impact()` on: `data_classification`, `pii_flag`, `regulatory_scope`, `data_sovereignty_flag`
- ✅ Cached by `(field, hash(old_value), hash(new_value))` — one call per unique change
- ✅ Returns `""` for immaterial changes — code strips "no significant" prefix responses

**Completion narrative**
- ✅ `generate_completion_message()` wired into handoff screen
- ✅ Cached by spec name — one call maximum per session

**Conversational path**
- ✅ `is_complete=True` from `chat_turn()` auto-triggers handover
- ✅ `with st.spinner("Thinking…")` wraps every LLM call — visual feedback
- ✅ `asyncio.TimeoutError` caught separately from generic exceptions everywhere
- ✅ All `except Exception` blocks log `exc_info=True`

---

## Phase 2 — UX Hardening  ✅  *(Shipped)*

> End-to-end flow review: every screen tested, every dead-end fixed.

**Handoff screen**
- ✅ Completion bar — colour-coded: green ≥80% · amber ≥50% · red <50%
- ✅ 3-card status grid: Fields Complete · Optional Missing · Required Missing
- ✅ Submit blocked with explicit instruction: *"Click ← Go back and edit below"*
- ✅ Assign & Notify panel — Data Owner · Tech Team · Data Steward · Compliance presets
- ✅ Role-specific pre-composed email body per recipient type
- ✅ `mailto:` link button — opens default email client
- ✅ Shareable deep link `?draft_id=...&role=tech` — role-scoped form entry
- ✅ Audit trail expander via `DraftManager.get_audit_log()`

**Downloads**
- ✅ Markdown · Collibra JSON · Snowflake CSV
- ✅ Inline download available in conversational path from the moment name is set

**Deployment**
- ✅ `streamlit` removed from `requirements.txt` — platform manages runtime
- ✅ `packages.txt` deleted — asyncpg uses pre-built manylinux wheels on Python 3.12 / Linux x86_64
- ✅ `runtime.txt` — `python-3.12`
- ✅ `requirements-dev.txt` — pytest deps separated from production
- ✅ `Dockerfile` — `gcc` + `python3-dev` for asyncpg source-build fallback on other platforms

---

## Phase 3 — Collaborative Editing & Governance Depth  🗓  *(Q2 2026)*

**Multi-role simultaneous editing**
- 🗓 Role-locked field sections — business sees theirs, tech sees theirs, steward sees all
- 🗓 Real-time presence: "Sarah (Data Owner) is editing Classification"
- 🗓 `DraftManager` polling bridge for co-edit (WebSocket in React rebuild)
- 🗓 Conflict resolution UI — diff view, owner resolves

**Formal approval workflow**
- 🗓 `Draft → Candidate → Approved → Deprecated` lifecycle transitions
- 🗓 Role-specific sign-offs gate each transition
- 🗓 Email notification with spec diff on every state change
- 🗓 `approved_at`, `approved_by` written to Collibra on approval

**Governance rules engine**
- 🗓 Server-side validation: `classification=Confidential` → `pii_flag` required, `data_sovereignty_flag` required
- 🗓 `FieldRule` Pydantic models in `field_registry.py` — not hardcoded in UI
- 🗓 Violated rules rendered as inline guardrail cards

---

## Phase 4 — Discovery Intelligence  🗓  *(Q3 2026)*

**Semantic search**
- 🗓 Vector embeddings on asset descriptions and business purposes
- 🗓 Semantic similarity alongside Collibra keyword search
- 🗓 "More like this" from any search result card
- 🗓 Search history and recent views in sidebar

**Duplicate detection**
- 🗓 Compare NLQ input against existing products via embeddings before form opens
- 🗓 Similarity > threshold: `This looks similar to X — remix instead?`
- 🗓 Reduces catalogue sprawl without blocking creation

**Lineage visualisation**
- 🗓 Upstream / downstream dependency graph from `lineage_upstream` / `lineage_downstream` fields
- 🗓 Impact analysis: "Deprecating this product affects 4 downstream consumers"

**Maturity scoring**
- 🗓 `score_spec_completeness(spec)` wired into maturity dashboard
- 🗓 Per-dimension scores: governance · technical · operational · compliance
- 🗓 Maturity badge on search result cards

---

## Phase 5 — Enterprise Integrations  🗓  *(Q4 2026)*

**Collibra write-back**
- 🗓 On submit: `POST /assets` + `PATCH /assets/{id}/attributes`
- 🗓 Collibra asset ID stored in spec and shown in completion screen
- 🗓 Remix path: `PATCH` existing asset when `collibra_id` is set

**Snowflake DDL generation**
- 🗓 From `column_definitions` + `materialization_type` + `schema_location`: generate `CREATE TABLE` / `CREATE VIEW`
- 🗓 Download `.sql` from handoff screen
- 🗓 Optional: push DDL to Snowflake staging environment

**Slack / Teams notifications**
- 🗓 Webhook on spec submission → `#data-governance` channel notification
- 🗓 Configurable per-domain webhooks
- 🗓 Mention nominated data owner by handle

**SSO + RBAC**
- 🗓 SAML / OIDC via APIM — real identities in audit log
- 🗓 Role inferred from OIDC claims — field-level visibility enforced server-side
- 🗓 Read-only users cannot edit, business users cannot see tech fields

**React frontend (inflection point)**
- 🗓 FastAPI backend — exposes all concierge methods as REST endpoints
- 🗓 React frontend — replaces Streamlit render layer only; AI pipeline, models, and connectors unchanged
- 🗓 Enables WebSocket co-edit, native SSO, mobile layout, micro-interactions
- 🗓 `src/agents/`, `src/models/`, `src/connectors/` — transferred as-is

---

## Phase 6 — AI Agent Upgrade  💡  *(2027)*

**Autonomous spec research**
- 💡 Given name + domain, AI browses internal catalogue and pre-fills lineage, source systems, related reports
- 💡 Confidence scores surfaced per auto-extracted field

**Regulatory change monitoring**
- 💡 Scheduled job: compare regulatory scope of all Approved specs against published change feeds (ESMA, FCA, SEC)
- 💡 Flag specs requiring re-review; draft impact summary for affected stewards

**Proactive quality alerts**
- 💡 Monitor `data_quality_score` trend across Approved products
- 💡 Alert data owner when score drops below SLA threshold
- 💡 Suggest spec amendments when observed data freshness mismatches retention period

**Natural language spec diff**
- 💡 "What changed between v1 and v2?" → AI narrates the diff in plain English
- 💡 Shown in audit trail alongside raw field changes

---

*Last updated: March 2026 · Status: Phases 0–2 shipped · Phase 3 in design*
