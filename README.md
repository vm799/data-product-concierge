# Data Product Concierge ✦

```
 ╔═══════════════════════════════════════════════════════════════════╗
 ║                                                                   ║
 ║     "Describe your data product in plain English.                 ║
 ║      We'll do the governance paperwork."                          ║
 ║                                                                   ║
 ╚═══════════════════════════════════════════════════════════════════╝
```

> **From a blank 35-field form to an AI-guided confirmation workflow.**
> Describe your data product once. AI extracts what it can. You confirm, not type.

---

## What We Built — and Why

Data governance has a UX problem. Anyone who wants to register a new data product faces a 35-field compliance form. Most fields have constrained values from Collibra that the person filling it in has never seen. They either give up, fill it in wrong, or pass it to someone else who then has to chase them for context.

The Concierge flips this. Instead of presenting a form, it asks one question: *"Describe your data product."* A large language model reads the answer, maps it to every governance field it can extract, and pre-fills the form. The user reviews AI suggestions — clicking Continue to accept each one — rather than composing 35 answers from scratch.

The result: a fully validated Collibra-ready specification, assembled collaboratively between a business user, an AI, and a data engineer, with a complete audit trail.

---

## How AI Is Used — and How We Constrained It

AI is not decorative here. It is wired into six specific points in the journey where it measurably reduces effort and error. Each point has explicit guardrails.

```
  USER INPUT                 AI ROLE                      GUARDRAIL
  ──────────────────────────────────────────────────────────────────
  Plain-English description  Extract governance fields    _apply_extracted_to_spec()
                             via chat_turn()              checks current value before
                                                          every field set — skips
                                                          anything already non-empty.
                                                          AI cannot overwrite you.

  Free-text enum input       Fuzzy-match to Collibra      Confidence clamped in Python:
  ("SFDR art 9")             canonical value              min(1.0, max(0.0, score))
                             via validate_and_normalise() If score < 0.7, matched=None
                                                          is set in code — regardless
                                                          of what the model returned.

  Field label rendered       Generate context-aware       Falls back to static registry
                             1-sentence hint              text on any exception or
                             via explain_field()          timeout. Page never breaks.

  Governance field changed   Explain material             Only fires on 4 specific
  on remix path              implication                  fields. Prompt: "return an
                             via explain_field_impact()   empty string if no significant
                                                          implications." Code checks for
                                                          "no significant" prefix and
                                                          suppresses the banner.

  Spec complete              Personalised summary         Cached by spec name in session
                             via generate_completion_     state — one LLM call maximum.
                             message()                    If it fails, the page renders
                                                          without the summary card.

  Search query entered       Seed name, description,      LLM only generates free-text
                             business_purpose             fields. domain and
                             via seed_new_product()       regulatory_scope are injected
                                                          from the already-parsed intent
                                                          object — not from LLM output.
```

### What the AI cannot do

- **It cannot submit.** The Submit button is disabled in Python until `spec.required_missing()` returns an empty list. The AI has no path to trigger submission.
- **It cannot approve a classification.** It suggests a value and explains the governance implication. A human clicks Continue to accept it or types to override.
- **It cannot write to Collibra.** Export produces a JSON file. Collibra import is a manual step outside the app.
- **It cannot overwrite your data.** `_apply_extracted_to_spec()` checks `if current is None or current == "" or current == []` before every field assignment. Extractions are skipped silently if the field already has a value.

### Hallucination controls — how each one actually works

| Layer | What's in the code |
|-------|-------------------|
| **System prompt grounding rule** | `concierge.py` line 50: *"Only state facts that appear in the data provided. Do not invent field values, regulatory implications, technical capabilities, or team structures that were not mentioned. If something is unknown, say so plainly."* This is an LLM instruction — it reduces but cannot eliminate invention. The layers below enforce the constraint technically. |
| **JSON mode on all extraction calls** | `_call_openai()` passes `response_format={"type":"json_object"}` to the OpenAI API when `json_mode=True`. The API then guarantees valid JSON output — no prose wrapping, no markdown fences, no hallucinated text around the payload. Used for: `chat_turn`, `validate_and_normalise`, `seed_new_product`, chapter explanations. |
| **Enum options in every extraction prompt** | `chat_turn` injects `VALID OPTIONS FOR KEY FIELDS: {enum_options}` into every call, listing every acceptable value for classification, frequency, access level, regulatory scope, and more. The prompt rule: *"For enum fields: use the EXACT string from valid options above. Do not invent options."* |
| **Confidence threshold enforced in Python** | `validate_and_normalise()` line 644: `confidence = min(1.0, max(0.0, response_json.get("confidence", 0.0)))`. Line 647: `matched = response_json.get("matched") if confidence >= 0.7 else None`. Even if the model assigns confidence 0.65 and returns a matched value, the Python code discards the match. The gate is in code, not model self-restraint. |
| **Structured vs. free-text separation** | `seed_new_product()` asks the LLM to generate only `name`, `description`, `business_purpose` (free-text). `domain` and `regulatory_scope` — the fields most likely to hallucinate — are injected from `ConciergeIntent`, which was extracted via a separate structured call on the search query. Code comment: *"Inject structured fields directly from intent — no LLM hallucination risk."* |
| **Spec state passed as ground truth** | `chat_turn` includes `CURRENT SPEC STATE: {spec_state}` in every prompt, showing what is already captured. The model sees `"domain": "Risk"` already set and cannot re-assign it via extraction — because `_apply_extracted_to_spec` skips non-empty fields on the receiving end. |
| **Temperature calibrated to task** | 0.1 for `validate_and_normalise` (maximum determinism for enum matching). 0.2 for `explain_field_impact` and `seed_new_product` (factual, low creativity). 0.3 for `chat_turn` and `explain_field` (conversational, still constrained). Never 0.7+. |
| **JSON parse failure fallback** | Every `json.loads()` is wrapped in try/except. `validate_and_normalise` returns `NormalisedValue(matched=None, confidence=0.3, message="Could not confidently match...")` on parse failure. `chat_turn` falls back to `_preview_chat_turn()`, a deterministic rule engine. The user never sees a raw model error. |
| **Human-in-the-loop badge** | Every AI-suggested field is added to `ai_suggested_fields` session state. The UI renders a **💡 AI suggestion — review and confirm** badge. The badge disappears only when the user clicks Continue (accepts) or types a new value (overrides). Nothing is silently committed. |
| **Demo mode kill-switch** | `_demo_active()` is checked at the top of every AI call path. When true, the function returns immediately with static fallback data. Zero LLM calls in demo mode — by code path, not by config hope. |
| **Timeout fallbacks** | Every `run_async()` call has an explicit timeout (8s for field-level calls, 20s for NLQ intake). `asyncio.TimeoutError` is caught before the generic `Exception` handler. On timeout: static fallback returned, warning logged, page continues rendering. |

```mermaid
flowchart TD
    A[System prompt\ngrounding rule] --> B[JSON mode\nAPI-enforced]
    B --> C[Enum options\nin every prompt]
    C --> D[Confidence threshold\nenforced in Python]
    D --> E[Human 💡 badge\nreview and confirm]
    E --> F[Demo mode\nkill-switch]
    F --> G[Timeout fallback\n8s / 20s]

    style A fill:#f8f9fa,stroke:#6c757d
    style B fill:#f8f9fa,stroke:#6c757d
    style C fill:#f8f9fa,stroke:#6c757d
    style D fill:#fff3cd,stroke:#ffc107
    style E fill:#cce5ff,stroke:#004085
    style F fill:#f8d7da,stroke:#721c24
    style G fill:#f8f9fa,stroke:#6c757d
```

### Model drift controls — how each one actually works

| Risk | What's in the code |
|------|--------------------|
| **Response schema changes** | All extraction calls use `.get("key", default)` with safe defaults — `0.0` for confidence, `None` for matched, `{}` for extracted fields. An additional key the model starts returning is silently ignored. A missing key uses the default. No crash. |
| **Model returns invalid JSON** | `json.loads()` is wrapped in try/except everywhere. Fallback data structures are defined per-method and returned on any parse error. |
| **Model interprets enum differently over time** | Enum values are passed verbatim in every prompt. The matching threshold is enforced in Python, not inferred from the model's confidence text. A model that starts over-confidently matching wrong enums will still be blocked by `min(1.0, max(0.0, score))` and `if confidence >= 0.7`. |
| **Provider deprecates model version** | `OPENAI_MODEL`, `APIM_OPENAI_DEPLOYMENT`, `BEDROCK_MODEL_ID` are all env-var controlled. Switch model version without touching code. |
| **Prompt injection via user input** | User-supplied text is always placed in `{"role": "user", "content": prompt}` — never string-interpolated into the `system` message. A user who types *"Ignore previous instructions"* is speaking to the model as a user, not overriding the system prompt. |
| **Bedrock markdown fences** | Even with JSON mode, Bedrock may wrap responses in ` ```json ` fences. Every parsing block in the codebase strips these before `json.loads()`. The app handles both backends identically. |

---

## The Journey at a Glance

```
  ┌─────────────────────────────────────────────────────────┐
  │                                                         │
  │  1. DISCOVER          2. DESCRIBE          3. VALIDATE  │
  │                                                         │
  │  Search Collibra  →   "Payments fraud  →   Review AI   │
  │  for existing         detection for       suggestions  │
  │  products first       Risk team,          field by     │
  │                       GDPR + MiFID II"    field        │
  │                              ↓                ↓        │
  │                         AI extracts      💡 badge on   │
  │                         what it can      each pre-fill │
  │                                                         │
  │  4. GOVERN            5. HAND OFF         6. SUBMIT    │
  │                                                         │
  │  Remix triggers   →   Email owner,    →   Collibra     │
  │  ⚡ governance        tech team,          JSON export  │
  │  impact banners       steward with        + audit trail│
  │                       deep link                        │
  │                                                         │
  └─────────────────────────────────────────────────────────┘
```

```mermaid
flowchart LR
    Search([Search Collibra]) --> Exists{Already exists?}
    Exists -->|Yes| Remix[Remix existing]
    Exists -->|No| NLQ[NLQ intake]
    Remix --> PrePop[Guided form\npre-populated]
    NLQ --> Extract[AI extraction\nchat_turn]
    Extract --> Badges[Guided form\nwith 💡 badges]
    PrePop --> Complete{All fields\ncomplete?}
    Badges --> Complete
    Complete -->|No — loop back| Badges
    Complete -->|Yes| Handoff([Handoff screen])
    Handoff --> Export[Export\n.md / .json / .csv]
    Handoff --> Submit[Submit for\nreview]
```

---

## For the Business

### What it does

The Data Product Concierge guides business and technical teams through the full lifecycle of a data product: finding what already exists, creating a new specification, remixing an existing one, and handing it off to the right people.

The core insight: instead of asking a business user to fill in 35 governance fields from scratch, the Concierge asks them to describe their data product in one paragraph. AI extracts every field it can and pre-fills the form. The user reviews suggestions rather than types.

The user reviews AI suggestions rather than composing answers from scratch. For constrained option fields, the AI fuzzy-matches free-text input to canonical Collibra values — catching typos and shorthand before they reach the catalogue.

---

### Three ways to get started

**1 — Search first**
Type what you need: `payments fraud GDPR` or `ESG fund holdings steward sarah`. The Concierge searches Collibra and returns matching assets with classification badges, ownership, regulatory scope, and data quality indicators. If something already exists, use it. If not, click **Create from this** to seed a new spec from the search result.

**2 — Describe your data product (NLQ)**
Before the guided form opens, you see a single text area:

> *"Payments fraud detection dataset for the Risk Analytics team. Covers GDPR and MiFID II, updated daily from the transaction ledger. Internal use only, steward is sarah.jones@firm.com."*

The Concierge reads this, calls the AI, and pre-fills every field it can extract — name, domain, regulatory scope, data owner, steward email, update frequency, classification. You then move through the form confirming suggestions with a click, not typing. Fields pre-filled by AI show a **💡 AI suggestion — review and confirm** badge so you always know what the system guessed versus what you entered.

**3 — Conversational chat**
Prefer to talk through it? The Concierge asks short, grouped questions in seven topic blocks and builds the spec as you answer in natural language.

| Say this | What happens |
|----------|-------------|
| `skip` | Defers the field — you revisit it at the end |
| `not needed` | Marks the field N/A (e.g. no regulatory scope for internal tooling) |
| `help` | Explains what the field means and why it matters in governance |
| `hand over` | Passes the partial spec to your tech team immediately |

---

### Remix an existing product

Browse to any existing data product, click **Remix**. The form opens pre-populated with all its values. You edit only what has changed.

When you touch a governance-sensitive field — classification, PII flag, regulatory scope, or data sovereignty — an amber **⚡ governance impact** banner explains the material implication before you confirm:

> *Changing Data Classification from Internal to Confidential now requires a DPIA review and data sovereignty flag.*

---

### Smart field matching

When you type a value for a constrained field — say `SFDR art 9` into Regulatory Scope — the Concierge fuzzy-matches your input to the canonical Collibra value.

| Confidence | What happens |
|------------|-------------|
| High (≥ 70%) | Silently accepted, green toast `✓ Matched: SFDR Article 9` |
| Medium (40–70%) | Inline banner: `Did you mean "SFDR Article 9"?` with confirm / keep buttons |
| Low (< 40%) | Warning caption, your value passed through unchanged |

For constrained option fields in live mode, unrecognised values are matched or flagged before reaching Collibra.

---

### Context-aware field guidance

Every field shows a one-line hint written for your specific context. The hint for *Data Classification* reads differently when you are in the Risk domain versus the Marketing domain. Click **Continue** to accept it, or type to override.

---

### Handoff and submission

When business fields are complete, the Concierge generates a personalised summary:

> *"Your Risk Analytics Fraud Detection spec is ready for steward review — 3 PII fields flagged for compliance, 2 regulatory frameworks registered."*

From the handoff screen:

- **Download** as Markdown (human-readable), Collibra JSON (bulk import), or Snowflake CSV (DATA_GOVERNANCE schema ingest)
- **Email** the data owner, tech team, data steward, or compliance officer — pre-composed role-specific body per recipient type, with a shareable deep link that opens the draft in a role-scoped session
- **Submit** for formal governance review — the button is disabled with a clear instruction until all required fields are complete: *"Click ← Go back and edit below to complete them"*
- **Audit trail** — every change, who made it, when — requires a Postgres connection (`POSTGRES_DSN`)

---

### Ingredient label

Every data product has a compact governance card: classification, regulatory scope, PII flag, SLA tier, retention period, owner, steward, and data quality score. It answers *"can I use this data?"* at a glance.

---

### The UX details that matter

Small decisions compound. Here is what was built into every interaction:

```
  MOMENT                        WHAT WAS BUILT
  ────────────────────────────  ──────────────────────────────────────────
  Typing a free-text enum       Spinner appears. AI matches silently at
  value and pressing Continue   high confidence. Asks you to confirm at
                                medium. Warns at low. Shows you the exact
                                matched value in the button: Use "SFDR
                                Article 9" — not a generic "Use suggestion".

  Moving through the form       💡 badge marks every AI-suggested field.
                                Accepting it removes the badge. Typing a
                                new value removes it too. Skipping leaves
                                it — the suggestion is still there when
                                you come back.

  Changing a sensitive field    ⚡ amber banner appears above the field
  on a remix                    before you commit. Cached — if you change
                                the same field to the same value again,
                                no second LLM call is made.

  LLM taking time to respond    Spinner: "Thinking…". The form does not
                                freeze or show a blank screen.

  Required fields missing at    Submit button is disabled. The error
  submission                    names the specific missing fields and
                                says exactly what to do: *"Click ← Go
                                back and edit below to complete them."*

  Collibra values mismatched    Smart disambiguation UI: confirm the
  (medium confidence)           correct value or keep yours — one click
                                either way, no re-typing.

  Session state from an older   Version guard at app startup clears
  Streamlit version             stale widget state automatically.
                                You never see a deserialization error.
```

---

### Built to be robust — what happens when things go wrong

The application is designed to degrade gracefully. No screen breaks. No raw errors shown to users.

```
  WHAT FAILS                   WHAT THE USER SEES
  ──────────────────────────   ────────────────────────────────────────
  LLM call times out (8–20s)   Static field hint from the registry.
                               Form continues. Warning logged silently.

  LLM returns invalid JSON     Deterministic fallback response.
                               Chat path continues uninterrupted.

  validate_and_normalise fails Your original value is passed through.
                               No match attempted. No error shown.

  generate_completion_message  Handoff screen renders normally.
  fails                        AI summary card simply absent.

  Postgres unavailable         App runs fully without draft persistence.
                               Audit trail not available until reconnected.

  Credentials missing /        Demo mode activates automatically.
  APIM unreachable             Full UI available on sample data.
```

Every AI call catches `asyncio.TimeoutError` separately from generic exceptions — so expected latency spikes don't flood error logs. Every exception path logs `exc_info=True` so genuine failures are traceable in production.

---

### Demo mode

No credentials needed to explore the full app. Demo mode activates automatically when no APIM connection is configured. All three creation paths and every screen run on sample data. Every AI feature's UI is exercised — on deterministic preview functions, not live LLM calls. A sidebar toggle switches between demo and live data in any environment.

---

---

## For the Engineering Team

### Architecture

```
app.py                          ← Streamlit orchestrator, session state, routing
src/
  agents/
    concierge.py                ← All LLM methods, APIM / OpenAI / Bedrock routing
  components/
    nlq_intake.py               ← NLQ → field extraction screen (pre-form)
    guided_form.py              ← Card-by-card form, AI badges, disambiguation, impact banners
    conversation_create.py      ← Conversational chat path, field lifecycle FSM
    handoff_summary.py          ← Completion dashboard, exports, team assignment, audit trail
    chapter_form.py             ← Tech fields form (data engineer path)
    search_bar.py               ← Collibra search, NLQ intent detection
    asset_cards.py              ← Search result cards with governance badges
    ingredient_label.py         ← Governance "nutrition label" component
    maturity_dashboard.py       ← Data product maturity scoring
    draft_banner.py             ← Persistent draft state banner
    shared_draft_entry.py       ← Shared URL / role-scoped draft entry
    use_case_intake.py          ← Business use-case intake screen
    styles.py                   ← Global CSS tokens and render helpers
  connectors/
    apim_auth.py                ← APIM token manager, sync LLM header injection
    collibra_auth.py            ← Collibra OAuth2 client
    postgres.py                 ← asyncpg connection pool wrapper
  core/
    async_utils.py              ← run_async(coro, timeout) — single shared helper, never redefine locally
    collibra_client.py          ← Collibra REST API client
    field_registry.py           ← Single source of truth for all field metadata
    utils.py                    ← Shared utilities (request IDs, logging helpers)
  models/
    data_product.py             ← Pydantic v2 models, enums, serialisation methods
    draft_manager.py            ← asyncpg draft persistence, audit log, optimistic locking
```

---

### AI pipeline

All AI calls are guarded by `_demo_active()`. Zero LLM calls in demo mode.

| Method | Trigger | Notes |
|--------|---------|-------|
| `chat_turn(msg, history, spec, valid_options)` | NLQ intake + chat path | Returns `{extracted, response, field_status, is_complete}` |
| `seed_new_product(query, intent)` | Create from search | Extracts name, domain, business purpose, regulatory scope |
| `explain_field(field_name, context)` | Guided form field label | 1-sentence hint; cached per `(field, domain[:10], cls[:10])` |
| `validate_and_normalise(field, value, options)` | Continue handler | Returns `NormalisedValue(matched: Optional[str], confidence, message)` |
| `explain_field_impact(field, old, new, context)` | Remix governance fields | Amber banner; cached by `(field, hash(old), hash(new))`; `""` if immaterial |
| `generate_completion_message(spec)` | Handoff screen | Personalised summary; cached by spec name |
| `recommend_path(intent, existing)` | Use-case intake | `PathRecommendation` with confidence and reasoning |
| `clarify_intent(query, candidates)` | Search — ambiguous | Disambiguation question |
| `explain_asset(asset, query)` | Search result expanded | Explains relevance to query |
| `score_spec_completeness(spec)` | Maturity dashboard | Structured scoring beyond `completion_percentage()` |
| `generate_description(partial_spec)` | Description field | Drafts description from name + domain + purpose |

Async pattern: all LLM methods are `async def`. Streamlit is single-threaded — use `run_async(coro, timeout)` from `core.async_utils` everywhere. Never define a local event loop helper.

---

### LLM routing

Three backends, selected by environment variable:

```bash
# Direct OpenAI (default — local dev)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o

# Enterprise — route via APIM gateway (Azure OpenAI)
LLM_VIA_APIM=true
APIM_OPENAI_DEPLOYMENT=gpt-4o
APIM_OPENAI_API_VERSION=2024-02-01

# AWS Bedrock Claude alternative
LLM_PROVIDER=bedrock
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
AWS_REGION=us-east-1
```

APIM path: `APIMTokenManager.get_llm_headers()` (sync — not async) returns fresh auth headers per call. `AsyncAzureOpenAI` is initialised once with `api_key="placeholder"`; headers are injected via `extra_headers` on each `_call_openai()`.

```mermaid
flowchart TD
    Start([LLM call]) --> APIM{LLM_VIA_APIM\n= true?}
    APIM -->|Yes| AzureOAI[AsyncAzureOpenAI\nvia APIM gateway]
    AzureOAI --> APIMHeaders[APIM injects auth\nheaders per call]
    APIM -->|No| Bedrock{LLM_PROVIDER\n= bedrock?}
    Bedrock -->|Yes| BRT[boto3 Bedrock\nClaude]
    Bedrock -->|No| Direct[AsyncOpenAI\ndirect — default]
```

---

### Data model

`DataProductSpec` — Pydantic v2, v1-compat patterns (`.dict()` not `.model_dump()`).

Key computed methods:
```python
spec.completion_percentage() -> float          # weighted required vs optional
spec.required_missing()      -> List[str]      # unfilled required field names
spec.optional_missing()      -> List[str]      # unfilled optional field names
spec.to_collibra_json()      -> dict           # Collibra bulk import
spec.to_snowflake_csv()      -> str            # DATA_GOVERNANCE schema ingest
spec.to_markdown()           -> str            # human-readable spec document
```

`NormalisedValue`:
```python
class NormalisedValue(BaseModel):
    matched: Optional[str]   # canonical enum value, or None if no match
    confidence: float         # 0.0–1.0
    message: str              # human-readable note
```

`DraftManager` — asyncpg-backed. Stores spec JSON, role metadata, and full audit log. `ConcurrentEditError` raised when two sessions edit the same draft simultaneously (optimistic locking on `updated_at`).

---

### Key session state

| Key | Type | Purpose |
|-----|------|---------|
| `spec` | `DataProductSpec` | Live spec being edited |
| `nlq_done` | `bool` | Skip NLQ intake on re-render |
| `ai_suggested_fields` | `set[str]` | Fields pre-filled by AI — drives 💡 badge |
| `concierge` | `DataProductConcierge` | Shared AI instance, one per session |
| `field_status` | `dict[str, str]` | Chat path FSM: pending / answered / not_needed / deferred |
| `show_handover` | `bool` | Triggers handover screen in chat path |
| `chat_history` | `list[dict]` | Full chat history for LLM context window |
| `disambig_{field}` | `dict` | Pending disambiguation: `{raw, matched}` |
| `impact_msg_{field}` | `str` | Cached governance impact message |
| `completion_narrative_{name}` | `str` | Cached AI completion summary |
| `_app_state_version` | `str` | Clears widget state on version upgrade to prevent deserialisation errors |

---

### Environment variables

```toml
# Collibra / APIM (required for live mode)
APIM_BASE_URL            = "https://apim.firm.internal"
APIM_CLIENT_ID           = "..."
APIM_CLIENT_SECRET       = "..."
APIM_SUBSCRIPTION_KEY    = "..."

# LLM — choose one block above
OPENAI_API_KEY           = "sk-..."
OPENAI_MODEL             = "gpt-4o"

# App
APP_BASE_URL             = "https://your-app.streamlit.app"

# Database (optional — draft persistence)
POSTGRES_DSN             = "postgresql://user:pass@host/db"
```

Copy `.streamlit/secrets.toml.example` → `.streamlit/secrets.toml` and fill values.

---

### Local development

```bash
git clone <repo>
cd data-product-concierge
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# fill in credentials (or leave blank for demo mode)
streamlit run app.py
```

Demo mode starts automatically when `APIM_BASE_URL` is unset — no credentials needed.

---

### Deployment

**Streamlit Cloud** — push to GitHub, connect repo, set secrets in the Streamlit Cloud dashboard. Do not include `streamlit` in `requirements.txt`; the platform manages it.

**Docker**
```bash
docker build -t data-product-concierge .
docker run -p 8501:8501 \
  -e APIM_BASE_URL=... \
  -e OPENAI_API_KEY=... \
  data-product-concierge
```

---

### Dependencies

```
httpx==0.27.2           # HTTP client (OpenAI + Collibra)
pydantic[email]==2.10.3
asyncpg==0.30.0         # Draft persistence (pre-built wheels on Linux x86_64 / Python 3.12)
openai==1.57.0          # GPT-4o direct or APIM-routed
boto3==1.35.80          # Bedrock alternative
python-dotenv==1.0.1
```

Dev-only (`requirements-dev.txt`, not deployed):
```
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0
```

---

## What Engineering Needs to Know

### The async contract

Streamlit reruns the entire script on every user interaction. It is single-threaded. Every `async def` method in the concierge must be called via `run_async(coro, timeout)` from `core/async_utils.py`. This is the **only** place in the codebase that bridges async coroutines to Streamlit's synchronous render loop.

```
  DO                                    DON'T
  ──────────────────────────────────    ──────────────────────────────────
  from core.async_utils import          asyncio.get_event_loop().run_until_
  run_async                             complete(concierge.chat_turn(...))

  result = run_async(                   loop = asyncio.new_event_loop()
      concierge.chat_turn(...),         loop.run_until_complete(...)
      timeout=20,
  )
```

If you define a local `_run_async` helper anywhere, the app will break under Streamlit's thread model in production. One helper. One place.

---

### The demo mode contract

`_demo_active()` in `app.py` must gate **every** AI call, **every** Collibra call, and **every** database call. If you add a new AI touchpoint, add the guard:

```python
try:
    from app import _demo_active
    if _demo_active():
        return STATIC_FALLBACK
except Exception:
    pass  # safe — treat as live mode
```

Demo mode is not just for demos. It is the failure mode when credentials are missing. Without this guard, a misconfigured production deployment will call OpenAI with every page render.

---

### The AI suggestion badge lifecycle

```
  nlq_intake.py                guided_form.py
  ─────────────────────────    ─────────────────────────────────────────
  chat_turn() extracts         Field is rendered with 💡 badge
  {domain: "Risk", ...}
       ↓                       User clicks Continue (accepts)
  _apply_extracted_to_spec()   → field removed from ai_suggested_fields
  marks field in               → badge disappears
  ai_suggested_fields set
                               User types a new value (overrides)
                               → field removed from ai_suggested_fields
                               → badge disappears

                               User skips the field
                               → badge stays (AI suggestion still pending)
```

`ai_suggested_fields` is a `set[str]` in session state. It is cleared when a field is accepted or overridden, never on page rerun. This is intentional — the badge persists across rerenders until the user acts.

```mermaid
stateDiagram-v2
    [*] --> Suggested : AI extracts field\n_apply_extracted_to_spec

    Suggested --> Accepted : User clicks Continue
    Suggested --> Overridden : User types new value
    Suggested --> Suggested : User skips field\nbadge stays

    Accepted --> [*]
    Overridden --> [*]

    note right of Suggested
        Field in ai_suggested_fields.
        💡 badge rendered in UI.
    end note
    note right of Accepted
        Field removed from\nai_suggested_fields.
        Badge disappears.
    end note
    note right of Overridden
        Field removed from\nai_suggested_fields.
        Badge disappears.
    end note
```

---

### Disambiguation flow

When `validate_and_normalise()` returns `0.4 ≤ confidence < 0.7`:

```
  Continue pressed
       ↓
  _maybe_normalise() → needs_disambig=True, matched="SFDR Article 9"
       ↓
  st.session_state["disambig_regulatory_scope"] = {
      "raw": "sfdr art 9",
      "matched": "SFDR Article 9",   ← clean string, no message wrapping
  }
       ↓
  return ("idle") — field NOT advanced, form stays on same card
       ↓
  Next render: disambiguation block fires BEFORE field widget
       ↓
  User clicks Use "SFDR Article 9" → matched value assigned, field advances
  User clicks Keep my value        → raw value assigned, field advances
```

```mermaid
flowchart TD
    A([User types value\nand presses Continue]) --> B[_maybe_normalise called]
    B --> C{confidence?}
    C -->|< 0.4| D[Warn caption shown\nvalue passed through unchanged]
    C -->|0.4 to 0.7| E[Store in session state\ndisambig_field]
    E --> F[Form stays on same card\nfield NOT advanced]
    F --> G{User chooses}
    G -->|Use matched value| H[Canonical value assigned\nfield advances]
    G -->|Keep my value| I[Raw value assigned\nfield advances]
    C -->|>= 0.7| J[Silent accept\ngreen toast shown]

    style D fill:#fff3cd,stroke:#ffc107
    style E fill:#cce5ff,stroke:#004085
    style J fill:#d4edda,stroke:#28a745
```

`matched` in session state is always the canonical string, never a formatted message. The button renders `f'Use "{matched_display}"'` directly — no regex extraction needed.

---

### Impact banner lifecycle

Triggered only on remix path, only for `{data_classification, pii_flag, regulatory_scope, data_sovereignty_flag}`.

```python
_impact_cache_key = f"impact_{field_name}_{hash(orig_val)}_{hash(new_val)}"
```

Cache key is per field + per change pair. Changing classification Internal → Confidential computes the impact once and stores it. Changing it back (Confidential → Internal) computes a separate entry. The LLM is never called twice for the same `(field, old, new)` triple in a session.

`explain_field_impact()` returns `""` for immaterial changes — the amber banner is not shown. A change from `pii_flag=None` to `pii_flag=False` (explicitly not PII) is material. A change from `name="Foo"` to `name="Bar"` never triggers this method at all.

---

### Session state version guard

```python
_APP_STATE_VERSION = "1.45.1"
if st.session_state.get("_app_state_version") != _APP_STATE_VERSION:
    _keep = {k: v for k, v in st.session_state.items()
             if k in {"draft_id", "user_email", "user_name", "demo_mode"}}
    st.session_state.clear()
    st.session_state.update(_keep)
    st.session_state["_app_state_version"] = _APP_STATE_VERSION
```

This runs at the top of `app.py` before any widget renders. It clears all widget state on version mismatch. This prevents `TypeError: list indices must be integers or slices, not str` that occurs when Streamlit's internal serialisation format changes between minor versions (selectbox stores an integer index in 1.45+, string in 1.40). Update `_APP_STATE_VERSION` when you upgrade Streamlit.

---

### Concierge error contract

Every AI call site follows this pattern:

```python
try:
    with st.spinner("Thinking…"):
        result = run_async(concierge.chat_turn(...), timeout=20)
except asyncio.TimeoutError:
    logger.warning("chat_turn timed out", extra={"field": field_name})
    result = STATIC_FALLBACK        # never None, never an exception
except Exception as exc:
    logger.warning("chat_turn failed", exc_info=True)
    result = STATIC_FALLBACK
```

`asyncio.TimeoutError` is always caught separately before the generic `Exception`. This is not stylistic — timeout is expected behaviour under load and should not fill error logs with stack traces. The generic catch logs `exc_info=True` so genuine errors are observable.

Static fallbacks:
- `explain_field()` → `meta.get("explanation", "")` from field registry
- `validate_and_normalise()` → raw user input passed through unchanged
- `explain_field_impact()` → `""` (no banner shown)
- `generate_completion_message()` → no AI summary card shown (page still renders normally)
- `chat_turn()` → `_preview_chat_turn()` (deterministic rule-engine response)

---

### Deployment checklist

```
  [ ] APIM_BASE_URL set in Streamlit Cloud secrets
  [ ] OPENAI_API_KEY or LLM_VIA_APIM=true configured
  [ ] streamlit NOT in requirements.txt (platform manages it)
  [ ] packages.txt does NOT exist (asyncpg uses pre-built wheels)
  [ ] runtime.txt contains: python-3.12
  [ ] APP_BASE_URL set to production URL (used in shareable draft links)
  [ ] POSTGRES_DSN set if draft persistence is needed
  [ ] _APP_STATE_VERSION updated if Streamlit was upgraded
```
