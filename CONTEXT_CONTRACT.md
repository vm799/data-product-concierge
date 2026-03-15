# Data Product Concierge — Context Contract

**Version:** 1.0
**Last Updated:** March 2026
**Audience:** AI systems, developers, product managers, designers
**Status:** Active & binding for all development

---

## Executive Summary

The **Data Product Concierge** is a **Streamlit-based discovery and curation interface** for enterprise data products in Collibra. Its singular purpose is to make finding, reusing, and creating governed data products **effortless for non-technical users** (portfolio managers, analysts, ops teams) at asset management firms.

The app is **NOT a data catalog replacement, data governance system, or analytics platform.** It is a **guided experience layer** on top of Collibra, powered by LLM-driven concierge that speaks plain English.

---

## Core Purpose

**Primary Mission:**
Enable business users to discover existing data products, evaluate whether they meet their needs, and either reuse them directly or create new governed products with minimal friction.

**Target User:**
- Portfolio managers, research analysts, risk officers, ops teams
- Minimal technical knowledge (no SQL, no API calls)
- High time pressure (need answers fast)
- Compliance-conscious (must follow governance rules)

**Key Outcome:**
Reduce time-to-data from weeks of back-and-forth emails to minutes of guided exploration.

---

## Non-Negotiable Principles

### ✓ MUST DO

1. **Zero Mock Data**
   - Never fabricate Collibra assets, users, domains, or vocabularies
   - If Collibra is unreachable, show graceful error with retry — never show fake results
   - Live API calls only; no stubs or sample data in production

2. **Plain Language First**
   - Every field, every button, every error message must be understandable by a portfolio manager
   - No jargon without immediate plain-English explanation
   - Concierge tone: warm, expert, never condescending

3. **Security by Default**
   - APIM Gateway + JWT auth required for ALL external calls
   - No hardcoded credentials, URLs, or secrets in code
   - Environment variables for all configuration
   - Data classification badges always visible (Confidential ≠ Internal)

4. **Concierge Everywhere**
   - User is NEVER in silence — every screen has a message
   - Concierge celebrates progress, explains why fields matter, validates free-text input
   - No raw Python tracebacks, HTTP status codes, or technical jargon surfaced to UI

5. **Single Golden Thread**
   - No split-column layouts, no sidebars, no multi-panel views
   - One clear path from "I need data" → discovery → evaluation → creation/handoff
   - Mobile-friendly responsive design (though not primary use case)

### ✗ MUST NOT

1. **No Mock Data Under Any Circumstance**
   - Collibra unreachable? Show error, offer retry, let user contact support
   - Do NOT show fake domains, users, or data products
   - Preview mode (for UI testing) is OK — clearly labeled as "Preview Mode" on screen

2. **No Opinionated Data Governance**
   - App does NOT enforce governance rules (that's Collibra's job)
   - App DOES make governance *visible* (required fields, classifications, regulatory scope)
   - App DOES NOT make compliance decisions for users

3. **No Duplicate Governance**
   - App is NOT a second source of truth
   - All metadata lives in Collibra — app is read-mostly, write-minimal
   - Edits go back to Collibra, not a separate database (except for session tracking)

4. **No Feature Creep Into Neighboring Spaces**
   - NOT a data quality dashboard (that's another tool)
   - NOT a lineage explorer (Collibra has that)
   - NOT a cost allocation system (that's Finance)
   - NOT a self-serve analytics builder (that's a different product)

5. **No Accessibility Shortcuts**
   - All UI must meet WCAG 2.1 AA minimum
   - No tiny fonts, no color-only status indicators, no keyboard-inaccessible buttons
   - Text contrast must pass standards

---

## Functional Scope

### ✓ IN SCOPE

#### 1. Discovery (Step: "search")
- **Input:** Natural language query ("ESG emissions for European funds")
- **Processing:** Concierge interprets query → extracts search terms → sends to Collibra
- **Output:** Ranked cards with metadata (owner, classification, update frequency, quality score)
- **User action:** "Use as-is", "Adapt this", or "Create from scratch"

#### 2. Path A: Reuse (Step: "path_a")
- **Display:** Full spec card for selected product (all 30 fields visible)
- **Actions:**
  - Email owner (pre-filled template)
  - Copy access request template
  - Switch to remix if user wants to adapt

#### 3. Path B: Remix (Steps: "path_b" + chapters 1-5)
- **Starting point:** Selected product's full spec
- **Interaction:** Chapter-by-chapter guided form (5 chapters)
- **Fields:** All 30 fields, pre-populated from Collibra
- **Validation:** Pill buttons for enums (never dropdowns), free-text with LLM normalization
- **Output:** Delta only — submit changes back to Collibra

#### 4. Path C: Create (Steps: "path_c" + chapters 1-5)
- **Starting point:** Empty DataProductSpec
- **Interaction:** Same 5-chapter form as remix, but all fields start blank
- **Validation:** Required fields marked (15 critical), optional can complete later
- **Output:** New draft asset in Collibra

#### 5. Handoff (Step: "handoff")
- **Display:** Completion gauge, missing fields summary, full markdown spec
- **Exports:**
  - Markdown spec (human-readable)
  - Collibra JSON (bulk import format)
  - Snowflake CSV (for data governance table)
- **Action:** Submit for technical review → creates/updates Collibra asset

#### 6. Completion (Step: "complete")
- **Display:** Success message, reference number, owner notification confirmation
- **Action:** Start new search

### ✗ OUT OF SCOPE

- Editing existing published products (users must go to Collibra)
- Deleting products
- Managing user access / permissions
- Running data quality checks
- Viewing lineage in detail (Collibra has this)
- Scheduling data pipelines
- Writing SQL or creating transformations
- Bulk import of legacy products
- Role-based access control beyond what Collibra provides
- Audit logging (beyond Postgres session tracking)
- Cost allocation or chargeback calculations
- Integration with BI tools (dashboards, analytics)

---

## Quality Standards

### Code Quality
- **Zero stubs, TODOs, or mock data in production**
- Type hints on all functions
- Comprehensive docstrings
- No raw exceptions to UI (wrap in `format_error()`)
- Request ID tracking for all API calls
- Structured logging (not print statements)

### UX Quality
- **Navy + teal design system** (no ad-hoc colors)
- **18px minimum font** (no tiny text)
- **Pill buttons for enums** (never dropdowns)
- **Loading states** for async operations
- **Error messages that explain why** (not just "Error 500")
- **Concierge tone** on every screen

### API Quality
- **Every external call through APIM Gateway** with JWT auth
- **Graceful timeouts** (10s max, user-friendly retry)
- **401 retry logic** (refresh token, try once more, then fail gracefully)
- **No N+1 queries** — batch where possible
- **Request IDs** for debugging

### Testing
- **Unit tests** for all model methods (DataProductSpec export formats)
- **Integration tests** for Collibra client (real API calls, skipif not configured)
- **No mocked API responses** in integration tests — use real Collibra or skip
- **Manual smoke test** before each release (all 3 paths end-to-end)

---

## User Journey Principles

### Flow Must Always Feel Like...

1. **"I'm talking to an expert colleague"**
   - Warm, confident tone
   - Explains WHY fields matter (not just "fill in the blank")
   - Celebrates progress ("You're doing brilliantly")
   - Proactively suggests the right path

2. **"One clear direction"**
   - No confusion about where to go next
   - Previous/Next buttons always visible on forms
   - Chapter progress bar shows you're making progress
   - No modal dialogs or pop-ups that interrupt flow

3. **"Data governance is normal, not scary"**
   - Required fields are clearly marked
   - Each field has a one-sentence plain-English explanation
   - Classifications are color-coded consistently
   - Concierge explains WHY compliance matters (not just "fill this because rules")

4. **"I'm in control"**
   - User can go back at any time
   - User can skip optional fields and complete later
   - User can see draft before final submission
   - User gets three export formats for different purposes

---

## Data & Security Principles

### Data Handling
- **Collibra is source of truth** — app syncs from Collibra, writes back to Collibra
- **PostgreSQL session tracking only** — stores what user submitted (for audit), not live data
- **No PII in logs** — email addresses only in debug logs, never in public error messages
- **No secrets in environment except where necessary** — credentials fetched at startup, cached securely

### Access Control
- **APIM Gateway enforces all authentication** — no duplicate auth in Streamlit
- **User identity extracted from JWT claims** — stored in session audit trail
- **No hard-coded service accounts** — use OAuth2 client credentials or user delegation
- **Streamlit Cloud secrets bridge** — env vars seamlessly from Streamlit secrets

### Compliance
- **GDPR:** PII handling minimal and logged
- **SOX:** Audit trail via session tracking (who created what, when)
- **Data classification respected** — UI shows Confidential/Internal/Public badges
- **Regulatory scope visible** — user sees which frameworks govern the data before using it

---

## Technical Architecture Principles

### Frontend (Streamlit + CSS)
- **No frameworks** beyond Streamlit (no React, no custom JS)
- **Pure CSS design system** (navy + teal + supporting colors)
- **HTML via st.markdown(..., unsafe_allow_html=True)**
- **SVG for complex visuals** (circular gauges, progress bars)
- **Responsive grid** (single column mobile → 880px max-width desktop)

### Backend (Python async)
- **No blocking I/O** — all external calls are async
- **HTTPx for HTTP** (async client)
- **Asyncpg for Postgres** (async pool)
- **Pydantic for validation** — all inputs type-checked
- **Streamlit session_state for state management**

### Concierge (LLM)
- **Configurable provider** (OpenAI or AWS Bedrock)
- **Structured prompts** — deterministic output (JSON mode where available)
- **Fallback gracefully** if LLM fails (never crash on LLM timeout)
- **Temperature 0.3** for consistency (can adjust per method)
- **No fine-tuning** — zero-shot with domain knowledge in system prompt

### Integration Points
- **APIM Gateway** (OAuth2, all downstream calls route through)
- **Collibra REST 2.0 API** (search, fetch, create, update assets)
- **Snowflake** (optional export target)
- **PostgreSQL** (session tracking, audit trail)
- **OpenAI / Bedrock** (concierge LLM)

### Deployment
- **Docker containerized** (Python 3.12 slim)
- **Streamlit Cloud compatible** (environment variables + secrets bridge)
- **Local dev with docker-compose** (Postgres + app)
- **Health checks** (curl to /_stcore/health)
- **No database migrations** — schema auto-created on first run

---

## Success Metrics

### Functional Success
- ✅ User can discover a data product in < 2 minutes
- ✅ User can start adapting/creating within 1 click
- ✅ 90% of form completions reach handoff (not abandoned)
- ✅ Zero raw exceptions show to user (all wrapped)
- ✅ All exports (MD, JSON, CSV) are valid and usable

### UX Success
- ✅ No user asks "What does this field mean?" (concierge explains)
- ✅ No user misclicks because UI is confusing (clear affordances)
- ✅ No user feels lost (concierge guides every step)
- ✅ User completes full 5-chapter creation flow < 10 minutes

### Quality Success
- ✅ Zero mock data leaks to production
- ✅ All external calls route through APIM (auditable)
- ✅ Session tracking captures all submissions (audit trail)
- ✅ No hardcoded secrets in code (all env vars)
- ✅ Integration tests run against real Collibra (or skip if unavailable)

---

## Guardrails for AI Development

### When Claude is asked to enhance the app, it MUST:

1. **Check against this contract first**
   - Does the feature fit the "Primary Mission"?
   - Is it in "IN SCOPE" or does it creep into "OUT OF SCOPE"?
   - Does it violate any "MUST NOT" principles?

2. **Preserve the concierge experience**
   - Every new screen must have a concierge message
   - Every new field must have a plain-English explanation
   - No jargon without explanation

3. **Maintain security**
   - All new API calls must go through APIM
   - All new data must be read from Collibra (no separate schema)
   - All new credentials must be env-var based

4. **Keep it simple**
   - One column, linear flow
   - Pill buttons for selections
   - No new frameworks or dependencies without approval

5. **Test production-ready**
   - No mock data, stubs, or "TODO" code
   - Integration tests on real systems
   - Manual walkthrough of all paths before merge

### Red Flags (Auto-Reject)

- ❌ "Let's add a data quality dashboard" → OUT OF SCOPE
- ❌ "Let's cache Collibra data in a separate database" → Violates "Collibra is source of truth"
- ❌ "Let's use a dropdown for regulatory scope" → Violates design system (pills only)
- ❌ "Let's skip APIM for this internal call" → Security violation
- ❌ "Let's show sample data if Collibra is slow" → Mock data violation
- ❌ "Let's send a password email" → PII / insecure
- ❌ "Let's add React component library X" → Over-engineering

---

## Version History

| Version | Date | Change |
|---------|------|--------|
| 1.0 | Mar 2026 | Initial contract, locked for production |

---

## Approval

**Product Owner:** [Your name]
**Tech Lead:** [Engineering lead]
**Signature:** By merging this to main, all contributors agree to this contract.

---

## How to Use This Document

1. **Before Starting Work:** Read the entire contract
2. **During Design:** Reference "IN SCOPE" / "OUT OF SCOPE" and "Non-Negotiable Principles"
3. **Before Code Review:** Check "Guardrails for AI Development" — does the PR violate any red flags?
4. **Before Release:** Verify all "Success Metrics" are met
5. **If Unsure:** Ask the product owner — better to clarify than ship the wrong thing
