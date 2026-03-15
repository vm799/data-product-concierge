"""
Conversational CREATE flow for Data Product Concierge.

Layout: chat (left 60%) + live spec panel (right 40%).

FIELD LIFECYCLE
  Each required field has one of four states tracked in session_state.field_status:
    pending    → not yet asked
    answered   → captured from user
    not_needed → user confirmed "N/A / doesn't apply"
    deferred   → skipped, revisited at the end

FIELD OWNERSHIP (who fills what)
  business → asked in conversation with business user
  tech     → handed to technical team after business pass
  auto     → Collibra auto-populates (id, timestamps, quality score)

HANDOVER FLOW
  When all "business" required fields are answered/not_needed/deferred,
  the UI offers:
    - "I've done my part — hand to tech team"
    - Handover email to tech/data analyst (mailto or SMTP)
    - Partial spec download (Markdown, JSON, CSV)
  Business user can also trigger this at any time with "hand over".

COLLIBRA AUTO-POPULATED FIELDS (shown as read-only in spec panel)
  id, created_at, updated_at, status (workflow-managed), data_quality_score

Preview mode uses a local rule engine — no LLM required.
Live mode routes through concierge.chat_turn().
"""

import asyncio
import json
import re
import random
from typing import Optional, Tuple
from urllib.parse import quote

import streamlit as st

from models.data_product import (
    DataProductSpec,
    DataClassificationEnum,
    RegulatoryFrameworkEnum,
    UpdateFrequencyEnum,
    AccessLevelEnum,
    SLATierEnum,
    BusinessCriticalityEnum,
)


# ============================================================================
# FIELD METADATA REGISTRY
# Combines: label, question, explanation, valid options, owner, Collibra source
# ============================================================================

FIELD_REGISTRY = {
    # ---- IDENTITY ----
    "name": {
        "label": "Product Name",
        "owner": "business",
        "collibra_source": "Direct asset attribute (name)",
        "collibra_endpoint": "GET /assets/{id} → .name",
        "question": "What would you call this data product? Aim for 3–6 words — clear enough that a colleague instantly knows what it is.",
        "explanation": "The product name is the first thing people see in Collibra search results. A specific name (e.g. 'ESG Fund Holdings Daily' rather than 'ESG Data') helps teams find and trust it.",
        "options": [],
        "required": True,
        "can_be_na": False,
    },
    "description": {
        "label": "Description",
        "owner": "business",
        "collibra_source": "Asset attribute (Description)",
        "collibra_endpoint": "GET /assets/{id}/attributes → type='Description'",
        "question": "In 2–3 sentences, what data does this product contain? Imagine explaining it to a colleague who's never seen it.",
        "explanation": "The description is what analysts read to decide if this is the right data product for their work. Think of it as the 'back of the box'.",
        "options": [],
        "required": True,
        "can_be_na": False,
    },
    "business_purpose": {
        "label": "Business Purpose",
        "owner": "business",
        "collibra_source": "Asset attribute (Business Purpose)",
        "collibra_endpoint": "GET /assets/{id}/attributes → type='Business Purpose'",
        "question": "Why does this data product exist — what specific business question or workflow does it enable?",
        "explanation": "The business purpose justifies why this product was created. It's referenced in governance reviews and determines how it's prioritised for maintenance.",
        "options": [],
        "required": True,
        "can_be_na": False,
    },
    "domain": {
        "label": "Business Domain",
        "owner": "business",
        "collibra_source": "Collibra Domain (parent container)",
        "collibra_endpoint": "GET /domains → select from list; GET /assets/{id} → .domain",
        "question": "Which business domain does this belong to? E.g. Risk, Trading, ESG, Client Data, Reference Data, Operations, Compliance.",
        "explanation": "The domain determines which governance team oversees this product and which policies automatically apply. It also controls who can find it in Collibra.",
        "options": ["Risk & Analytics", "Sustainable Investing", "Reference Data", "Client Data", "Market Data", "Operations", "Compliance", "Trading"],
        "required": True,
        "can_be_na": False,
    },
    "data_classification": {
        "label": "Data Classification",
        "owner": "business",
        "collibra_source": "Vocabulary domain (data_classification vocab)",
        "collibra_endpoint": "GET /assets?domainId=COLLIBRA_VOCAB_DATA_CLASSIFICATION → options; GET /assets/{id}/attributes → value",
        "question": "How sensitive is this data? Choose the classification that applies.",
        "explanation": "Classification drives security controls. **Confidential** = restricted to authorised individuals + audit logging. **Internal** = all staff. **Public** = can be shared externally. **Restricted** = specific named teams only.",
        "options": ["Confidential", "Internal", "Public", "Restricted"],
        "required": True,
        "can_be_na": False,
    },
    "regulatory_scope": {
        "label": "Regulatory Frameworks",
        "owner": "business",
        "collibra_source": "Vocabulary domain (regulatory_scope vocab) — multi-value",
        "collibra_endpoint": "GET /assets?domainId=COLLIBRA_VOCAB_REGULATORY_SCOPE → options; GET /assets/{id}/attributes → multi-value",
        "question": "Which regulations apply to this data? You can name several. Common ones:\n- **GDPR** — personal data of EU persons\n- **MiFID II** — trading and investment activity\n- **SFDR** — ESG/sustainable finance disclosures\n- **AIFMD** — alternative investment funds\n- **BCBS 239** — risk data aggregation\n- **TCFD** — climate financial disclosures\n- **DORA** — operational resilience",
        "explanation": "Regulatory scope determines audit trails, retention rules, and access controls. GDPR triggers data subject rights; MiFID II requires specific record-keeping — getting this right matters for compliance sign-off.",
        "options": ["GDPR", "MiFID II", "AIFMD", "BCBS 239", "Solvency II", "SFDR", "EU Taxonomy", "TCFD", "DORA", "CCPA", "HIPAA", "SOX", "PCI-DSS"],
        "required": True,
        "can_be_na": True,
        "na_label": "No specific regulatory framework applies",
    },
    "data_owner_name": {
        "label": "Data Owner Name",
        "owner": "business",
        "collibra_source": "Asset responsibility (Owner role) — GET /assets/{id}/responsibilities",
        "collibra_endpoint": "GET /assets/{id}/responsibilities → role='Data Owner' → user.name",
        "question": "Who is accountable for this data product? This is usually a senior manager or team lead. What's their full name?",
        "explanation": "The data owner is the person compliance contacts for audits and regulatory requests. They're also shown on the Collibra asset card so consumers know who to approach.",
        "options": [],
        "required": True,
        "can_be_na": False,
    },
    "data_owner_email": {
        "label": "Data Owner Email",
        "owner": "business",
        "collibra_source": "Asset responsibility (Owner role) — email field",
        "collibra_endpoint": "GET /assets/{id}/responsibilities → role='Data Owner' → user.email",
        "question": "What's the data owner's email address?",
        "explanation": "This email receives access request notifications, quality alerts, and governance review reminders automatically from Collibra.",
        "options": [],
        "required": True,
        "can_be_na": False,
    },
    "data_steward_email": {
        "label": "Data Steward Email",
        "owner": "business",
        "collibra_source": "Asset responsibility (Data Steward role)",
        "collibra_endpoint": "GET /assets/{id}/responsibilities → role='Data Steward' → user.email",
        "question": "Who handles day-to-day data quality issues and access approvals? What's the data steward's email?",
        "explanation": "The steward is the operational contact — they deal with quality queries, access requests, and schema changes. Different from the owner (who is accountable but not necessarily hands-on).",
        "options": [],
        "required": True,
        "can_be_na": False,
    },
    "access_level": {
        "label": "Access Level",
        "owner": "business",
        "collibra_source": "Vocabulary domain (access_level vocab)",
        "collibra_endpoint": "GET /assets?domainId=COLLIBRA_VOCAB_ACCESS_LEVEL → options; GET /assets/{id}/attributes → value",
        "question": "Who can access this data and how? Choose the level that fits.",
        "explanation": "**Open** = anyone in the firm can access. **Request-based** = analysts submit a request, owner approves (most common). **Restricted** = specific named teams only. **Confidential** = highly sensitive, individual approvals.",
        "options": ["Open", "Request-based", "Restricted", "Confidential"],
        "required": True,
        "can_be_na": False,
    },
    "sla_tier": {
        "label": "SLA Tier",
        "owner": "business",
        "collibra_source": "Vocabulary domain (sla_tier vocab)",
        "collibra_endpoint": "GET /assets?domainId=COLLIBRA_VOCAB_SLA_TIER → options; GET /assets/{id}/attributes → value",
        "question": "What uptime commitment should this data product carry?",
        "explanation": "**Gold (99.9%)** = 8.7 hours downtime/year, priority incident response. **Silver (99.5%)** = 43 hours. **Bronze (99%)** = 87 hours. **None** = best-effort, no formal SLA. Gold is typically for systems feeding live trading or regulatory reporting.",
        "options": ["Gold (99.9%)", "Silver (99.5%)", "Bronze (99%)", "None"],
        "required": True,
        "can_be_na": False,
    },
    "business_criticality": {
        "label": "Business Criticality",
        "owner": "business",
        "collibra_source": "Vocabulary domain (business_criticality vocab)",
        "collibra_endpoint": "GET /assets?domainId=COLLIBRA_VOCAB_BUSINESS_CRITICALITY → options",
        "question": "How critical is this data product to business operations?",
        "explanation": "**Mission-critical** = feeds core business functions (e.g. trade execution, regulatory reporting) — fastest incident response. **High** = important but business can operate briefly without it. **Medium** = useful but not time-sensitive. **Low** = analytics, non-urgent reporting.",
        "options": ["Mission-critical", "High", "Medium", "Low"],
        "required": True,
        "can_be_na": False,
    },
    # ---- TECH TEAM FILLS ----
    "source_systems": {
        "label": "Source Systems",
        "owner": "tech",
        "collibra_source": "Asset relations → Source System asset type (SOURCE_SYSTEM_TYPE_ID)",
        "collibra_endpoint": "GET /assets/{id}/relations → filter relation_type='Sources'; GET /assets?typeId=SOURCE_SYSTEM_TYPE_ID → available systems",
        "question": "Where does this data come from? List the upstream systems. E.g. Bloomberg, internal DWH, Snowflake, Salesforce, FIX engine.",
        "explanation": "Source systems appear in Collibra's data lineage graph. They help engineers trace data issues and assess the impact of upstream changes on downstream consumers.",
        "options": [],
        "required": True,
        "can_be_na": False,
    },
    "update_frequency": {
        "label": "Update Frequency",
        "owner": "tech",
        "collibra_source": "Vocabulary domain (update_frequency vocab)",
        "collibra_endpoint": "GET /assets?domainId=COLLIBRA_VOCAB_UPDATE_FREQUENCY → options",
        "question": "How often does this data refresh?",
        "explanation": "Update frequency lets consumers know when fresh data arrives so they can schedule their models, reports, and dashboards accordingly.",
        "options": ["Real-time", "Hourly", "Daily", "Weekly", "Monthly", "Ad-hoc"],
        "required": True,
        "can_be_na": False,
    },
    "schema_location": {
        "label": "Schema / Table Location",
        "owner": "tech",
        "collibra_source": "Asset attribute (Schema Location / Technical Asset link)",
        "collibra_endpoint": "GET /assets/{id}/attributes → type='Schema Location'",
        "question": "What's the exact database table or file path? E.g. `ANALYTICS_DB.ESG.SCOPE1_EMISSIONS` or `s3://data-lake/risk/positions/`.",
        "explanation": "This is how engineers and analysts physically connect to the data. It must be exact — Collibra uses it to link the business asset to the technical asset in lineage.",
        "options": [],
        "required": True,
        "can_be_na": False,
    },
    # ---- OPTIONAL — business ----
    "consumer_teams": {
        "label": "Consumer Teams",
        "owner": "business",
        "collibra_source": "Asset relations → Business Domain asset type (BUSINESS_DOMAIN_TYPE_ID)",
        "collibra_endpoint": "GET /assets/{id}/relations → filter relation_type='Consumes'; GET /assets?typeId=BUSINESS_DOMAIN_TYPE_ID",
        "question": "Which business teams will use this data product? E.g. Portfolio Management, ESG Research, Compliance, Client Reporting.",
        "explanation": "Consumer teams are linked in Collibra so the data owner understands their audience and can notify them of changes. Access requests are also routed to these teams.",
        "options": [],
        "required": False,
        "can_be_na": True,
        "na_label": "Not yet defined — to be confirmed by tech team",
    },
    "tags": {
        "label": "Tags",
        "owner": "business",
        "collibra_source": "Asset tags (multi-value attribute)",
        "collibra_endpoint": "GET /assets/{id}/attributes → type='Tags'",
        "question": "Any keywords that help people discover this in Collibra? E.g. 'emissions, carbon, scope-1, SFDR'.",
        "explanation": "Tags power Collibra's search. Good tags mean teams find your product without knowing its exact name.",
        "options": [],
        "required": False,
        "can_be_na": True,
        "na_label": "No specific tags",
    },
    "cost_centre": {
        "label": "Cost Centre",
        "owner": "business",
        "collibra_source": "Asset attribute (Cost Centre)",
        "collibra_endpoint": "GET /assets/{id}/attributes → type='Cost Centre'",
        "question": "What's the cost centre code for this product? (Used for internal chargeback.) E.g. CC-4521-ESG.",
        "explanation": "Cost centre enables finance to chargeback data platform costs to the right business line. Ask your Finance BP if you're unsure.",
        "options": [],
        "required": False,
        "can_be_na": True,
        "na_label": "No cost centre — platform absorbs the cost",
    },
    "related_reports": {
        "label": "Related Reports",
        "owner": "business",
        "collibra_source": "Asset relations → Report asset type",
        "collibra_endpoint": "GET /assets/{id}/relations → filter type='Report'",
        "question": "Which reports or dashboards depend on this data product? E.g. SFDR PAI Report, Monthly ESG Scorecard.",
        "explanation": "Linked reports appear in Collibra's impact analysis. If this data product changes, Collibra can automatically notify the owners of the linked reports.",
        "options": [],
        "required": False,
        "can_be_na": True,
        "na_label": "No known reports yet",
    },
    # ---- OPTIONAL — tech ----
    "pii_flag": {
        "label": "Contains PII",
        "owner": "tech",
        "collibra_source": "Asset attribute (PII Flag) — boolean",
        "collibra_endpoint": "GET /assets/{id}/attributes → type='PII Flag'",
        "question": "Does this data product contain personally identifiable information (names, emails, IDs, financial details of individuals)?",
        "explanation": "Flagging PII triggers GDPR obligations: data subject access rights, deletion requests, breach notification timelines. Essential for compliance team sign-off.",
        "options": ["Yes", "No"],
        "required": False,
        "can_be_na": False,
    },
    "encryption_standard": {
        "label": "Encryption Standard",
        "owner": "tech",
        "collibra_source": "Vocabulary domain (encryption_standard vocab)",
        "collibra_endpoint": "GET /assets?domainId=COLLIBRA_VOCAB_ENCRYPTION_STANDARD → options",
        "question": "What encryption standard is applied to this data at rest and in transit?",
        "explanation": "Required for Confidential data. AES-256 is the firm standard for sensitive financial data; TLS-1.3 covers transit encryption.",
        "options": ["AES-256", "TLS-1.3", "AES-128", "None"],
        "required": False,
        "can_be_na": True,
        "na_label": "Platform default encryption applies",
    },
    "retention_period": {
        "label": "Retention Period",
        "owner": "tech",
        "collibra_source": "Asset attribute (Retention Period / Retention Days)",
        "collibra_endpoint": "GET /assets/{id}/attributes → type='Retention Period'",
        "question": "How long must this data be retained? E.g. '7 years' (MiFID II), '5 years' (GDPR), '1 year'.",
        "explanation": "Retention is driven by regulatory requirements. MiFID II trading data = 7 years. GDPR = no longer than necessary. Getting this wrong risks regulatory breach.",
        "options": [],
        "required": False,
        "can_be_na": True,
        "na_label": "Follows standard platform retention policy",
    },
    "geographic_restriction": {
        "label": "Geographic Restrictions",
        "owner": "tech",
        "collibra_source": "Vocabulary domain (geographic_restriction vocab) — multi-value",
        "collibra_endpoint": "GET /assets?domainId=COLLIBRA_VOCAB_GEOGRAPHIC_RESTRICTION → options",
        "question": "Are there geographic restrictions on where this data can be processed or stored? E.g. EU-only, no US transfer.",
        "explanation": "GDPR restricts personal data transfers outside the EU unless safeguards are in place. Knowing this upfront prevents costly data residency violations.",
        "options": ["EU only", "UK only", "US only", "APAC only", "EU + UK", "No restriction", "Custom"],
        "required": False,
        "can_be_na": True,
        "na_label": "No geographic restrictions",
    },
    "sub_domain": {
        "label": "Sub-Domain",
        "owner": "tech",
        "collibra_source": "Asset attribute (Sub-Domain)",
        "collibra_endpoint": "GET /assets/{id}/attributes → type='Sub-Domain'",
        "question": "Is there a more specific sub-domain within the business domain? E.g. 'Climate & Carbon' within 'ESG'.",
        "explanation": "Sub-domains enable finer-grained discovery and policy application within large business domains.",
        "options": [],
        "required": False,
        "can_be_na": True,
        "na_label": "No sub-domain",
    },
    "schema_location": {
        "label": "Schema / Table Location",
        "owner": "tech",
        "collibra_source": "Asset attribute (Schema Location)",
        "collibra_endpoint": "GET /assets/{id}/attributes → type='Schema Location'",
        "question": "What's the exact database table or file path? E.g. `ANALYTICS_DB.ESG.SCOPE1_EMISSIONS` or `s3://data-lake/risk/positions/`.",
        "explanation": "This is how engineers and analysts physically connect to the data. It must be exact — Collibra uses it to link the business asset to the technical asset in lineage.",
        "options": [],
        "required": True,
        "can_be_na": False,
    },
    "version": {
        "label": "Version",
        "owner": "tech",
        "collibra_source": "Asset attribute (Version)",
        "collibra_endpoint": "GET /assets/{id}/attributes → type='Version'",
        "question": "What version is this data product? Use semantic versioning: e.g. 1.0.0.",
        "explanation": "Versioning helps consumers know when breaking schema changes occur. Major version bumps = breaking changes; minor = new fields; patch = fixes.",
        "options": [],
        "required": False,
        "can_be_na": True,
        "na_label": "Not versioned yet — start at 1.0.0",
    },
    "certifying_officer_email": {
        "label": "Certifying Officer Email",
        "owner": "tech",
        "collibra_source": "Asset responsibility (Certifying Officer role)",
        "collibra_endpoint": "GET /assets/{id}/responsibilities → role='Certifying Officer' → user.email",
        "question": "Who will formally certify this data product meets quality and compliance standards? What's their email?",
        "explanation": "Certification is a formal sign-off that the data product is fit for purpose. Often a Chief Data Officer, Head of Data Governance, or equivalent.",
        "options": [],
        "required": False,
        "can_be_na": True,
        "na_label": "To be assigned by governance team",
    },
}

# Which fields to ask in the business conversation (ordered)
BUSINESS_FLOW_ORDER = [
    "name", "description", "business_purpose",
    "domain", "data_classification", "regulatory_scope",
    "data_owner_name", "data_owner_email", "data_steward_email",
    "access_level", "sla_tier", "business_criticality",
    "consumer_teams", "tags", "cost_centre", "related_reports",
]

# Which fields tech team fills (shown in handover)
TECH_FLOW_ORDER = [
    "source_systems", "update_frequency", "schema_location",
    "pii_flag", "encryption_standard", "retention_period",
    "geographic_restriction", "sub_domain", "version",
    "certifying_officer_email",
]

# Collibra auto-populates these — no user input needed
AUTO_COLLIBRA_FIELDS = {
    "id": "UUID generated by Collibra on asset creation",
    "created_at": "Set automatically by Collibra when asset is first saved",
    "updated_at": "Updated automatically on every edit",
    "status": "Managed by Collibra lifecycle workflow (Draft → Candidate → Approved → Deprecated)",
    "data_quality_score": "Computed by Collibra Data Quality & Observability module from linked quality rules",
}

# All required fields (superset for required_missing check)
ALL_REQUIRED = {"name", "description", "business_purpose", "domain", "data_classification",
                "data_owner_name", "data_owner_email", "data_steward_email", "regulatory_scope",
                "access_level", "sla_tier", "business_criticality",
                "source_systems", "update_frequency", "schema_location"}

FIELD_STATUS_ANSWERED = "answered"
FIELD_STATUS_NOT_NEEDED = "not_needed"
FIELD_STATUS_DEFERRED = "deferred"
FIELD_STATUS_PENDING = "pending"

_SKIP_PHRASES = {
    "don't know", "dont know", "idk", "not sure", "skip", "pass",
    "n/a", "not applicable", "unsure", "i don't have", "i dont have",
    "come back", "later", "no idea", "unknown", "tbd", "defer",
    "can't answer", "cannot answer", "no answer", "move on",
}

_NA_PHRASES = {
    "not needed", "not required", "doesn't apply", "does not apply",
    "not applicable", "na", "n/a", "no", "none", "not relevant",
    "won't apply", "will not apply", "exempt", "not for us",
}

_HANDOVER_PHRASES = {
    "hand over", "handover", "hand to tech", "send to tech", "pass to tech",
    "done my part", "that's all i know", "thats all i know", "hand off",
    "pass on", "escalate", "forward", "done for now",
}

_CONFIRM_VARIANTS = [
    "✓ Got it —", "✓ Perfect —", "✓ Noted —", "✓ Great —", "✓ Captured —", "✓ Excellent —",
]


# ============================================================================
# HELPERS
# ============================================================================

def _run_async(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


def _is_help_request(text: str) -> bool:
    low = text.lower().strip()
    return any(kw in low for kw in [
        "help", "what", "explain", "why", "how", "mean", "?",
        "don't understand", "dont understand", "confused",
        "what is", "what does", "what are", "what should", "tell me",
    ])


def _is_skip_request(text: str) -> bool:
    low = text.lower().strip()
    return low in _SKIP_PHRASES or any(p in low for p in _SKIP_PHRASES)


def _is_na_request(text: str) -> bool:
    low = text.lower().strip()
    return low in _NA_PHRASES or any(p in low for p in _NA_PHRASES)


def _is_handover_request(text: str) -> bool:
    low = text.lower().strip()
    return any(p in low for p in _HANDOVER_PHRASES)


def _get_field_options(field: str, valid_options: dict) -> list:
    reg = FIELD_REGISTRY.get(field, {})
    base = reg.get("options", [])
    # Supplement with live Collibra options if available
    collibra_key = {
        "source_systems": "source_systems",
        "consumer_teams": "consumer_teams",
        "domain": "domain",
        "tags": "tags",
        "geographic_restriction": "geographic_restriction",
    }.get(field)
    if collibra_key:
        live = valid_options.get(collibra_key, [])
        # Merge: live options take priority, keep base as fallback
        merged = list(live) + [o for o in base if o not in live]
        return merged[:20]  # cap
    return base


def _try_extract(user_text: str, field: str, valid_options: dict) -> object:
    """Extract a value for `field` from `user_text`. Returns None if no match."""
    low = user_text.strip().lower()
    text = user_text.strip()
    options = _get_field_options(field, valid_options)

    if options:
        if field in ("regulatory_scope", "source_systems", "consumer_teams", "tags", "related_reports", "geographic_restriction"):
            matched = [o for o in options if o.lower() in low]
            abbrevs = {
                "mifid": "MiFID II", "gdpr": "GDPR", "sfdr": "SFDR", "tcfd": "TCFD",
                "aifmd": "AIFMD", "bcbs": "BCBS 239", "dora": "DORA", "sox": "SOX",
                "ccpa": "CCPA", "hipaa": "HIPAA", "tcfd": "TCFD",
            }
            for abbr, full in abbrevs.items():
                if abbr in low and full not in matched and full in (options or [full]):
                    matched.append(full)
            if not matched and len(text) > 2:
                parts = [p.strip() for p in re.split(r"[,;/]", text) if len(p.strip()) > 1]
                return parts if parts else None
            return matched if matched else None

        for opt in options:
            if opt.lower() in low or low in opt.lower():
                return opt
        first = low.split()[0] if low.split() else ""
        for opt in options:
            if first in opt.lower():
                return opt
        return None

    if "email" in field:
        m = re.search(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", text, re.IGNORECASE)
        return m.group(0) if m else (text if "@" in text else None)

    if field == "pii_flag":
        if low in ("yes", "true", "y", "contains pii", "has pii"):
            return True
        if low in ("no", "false", "n", "no pii"):
            return False
        return None

    if field in ("name", "description", "business_purpose", "domain", "data_owner_name",
                 "schema_location", "cost_centre", "sub_domain", "version",
                 "retention_period", "certifying_officer_email"):
        return text if len(text) > 2 and not _is_help_request(text) else None

    if field in ("tags", "related_reports", "source_systems", "consumer_teams"):
        parts = [p.strip() for p in re.split(r"[,;/]", text) if len(p.strip()) > 1]
        return parts if parts else None

    return None


def _apply_extracted(spec: DataProductSpec, extracted: dict) -> DataProductSpec:
    updates = {}
    for field, value in extracted.items():
        if not hasattr(spec, field) or value is None:
            continue
        try:
            if field == "data_classification":
                for e in DataClassificationEnum:
                    if e.value.lower() == str(value).lower():
                        updates[field] = e; break
            elif field == "update_frequency":
                for e in UpdateFrequencyEnum:
                    if e.value.lower() == str(value).lower():
                        updates[field] = e; break
            elif field == "access_level":
                for e in AccessLevelEnum:
                    if e.value.lower() == str(value).lower():
                        updates[field] = e; break
            elif field == "sla_tier":
                for e in SLATierEnum:
                    if e.value.lower() == str(value).lower():
                        updates[field] = e; break
            elif field == "business_criticality":
                for e in BusinessCriticalityEnum:
                    if e.value.lower() == str(value).lower():
                        updates[field] = e; break
            elif field == "regulatory_scope":
                matched = []
                for item in (value if isinstance(value, list) else [value]):
                    for e in RegulatoryFrameworkEnum:
                        if e.value.lower() == str(item).lower():
                            matched.append(e); break
                if matched:
                    updates[field] = matched
            elif field == "pii_flag":
                if isinstance(value, bool):
                    updates[field] = value
                elif str(value).lower() in ("true", "yes"):
                    updates[field] = True
                elif str(value).lower() in ("false", "no"):
                    updates[field] = False
            elif isinstance(value, list):
                updates[field] = [str(v) for v in value]
            else:
                updates[field] = str(value)
        except Exception:
            pass
    return spec.model_copy(update=updates) if updates else spec


# ============================================================================
# PREVIEW ENGINE
# ============================================================================

def _preview_chat_turn(
    user_message: str,
    spec: DataProductSpec,
    valid_options: dict,
    field_status: dict,
    current_field: str,
) -> dict:
    """Smart preview-mode conversational engine. Returns {response, extracted, field_status, trigger_handover}."""

    label = FIELD_REGISTRY.get(current_field, {}).get("label", current_field.replace("_", " ").title()) if current_field else ""
    options = _get_field_options(current_field, valid_options) if current_field else []
    can_be_na = FIELD_REGISTRY.get(current_field, {}).get("can_be_na", True)

    # — Handover request —
    if _is_handover_request(user_message):
        return {
            "response": "Of course — let's hand over to the tech team now. I'll generate a summary of what you've captured and what still needs completing.",
            "extracted": {},
            "field_status": field_status,
            "trigger_handover": True,
        }

    if not current_field:
        return {
            "response": "🎉 Everything is captured! Click **Review & Submit** above to finalise your data product.",
            "extracted": {},
            "field_status": field_status,
            "trigger_handover": False,
            "is_complete": True,
        }

    # — Help / explain —
    if _is_help_request(user_message):
        reg = FIELD_REGISTRY.get(current_field, {})
        explanation = reg.get("explanation", "This field documents an important aspect of your data product.")
        question = reg.get("question", f"Could you provide the {label.lower()}?")
        collibra = reg.get("collibra_source", "")
        response = f"**{label}** — {explanation}\n\n{question}"
        if options:
            response += f"\n\n**Available options:** {', '.join(options)}"
        if collibra:
            response += f"\n\n*Collibra source: {collibra}*"
        hints = []
        if can_be_na:
            na_label = reg.get("na_label", "not applicable")
            hints.append(f"'not needed' if {na_label.lower()}")
        hints.append("'skip' to defer")
        response += f"\n\n*(You can also say {' · '.join(hints)})*"
        return {"response": response, "extracted": {}, "field_status": field_status, "trigger_handover": False}

    # — Not needed / N/A —
    if _is_na_request(user_message) and can_be_na:
        na_label = FIELD_REGISTRY.get(current_field, {}).get("na_label", "not applicable")
        new_status = {**field_status, current_field: FIELD_STATUS_NOT_NEEDED}
        response = f"✓ Noted — **{label}** marked as *{na_label}*."
        next_f = _next_field(new_status, field_status)
        if next_f:
            response += "\n\n" + _ask_field(next_f, valid_options)
        else:
            response += "\n\nAll fields covered! Click **Review & Submit** above, or say **'hand over'** to send to the tech team."
        return {"response": response, "extracted": {}, "field_status": new_status, "trigger_handover": False}

    if _is_na_request(user_message) and not can_be_na:
        response = (
            f"**{label}** is a required field that can't be marked N/A — it's needed for Collibra governance. "
            f"Could you give it a go? *(Type 'help' for guidance, 'skip' to come back later.)*"
        )
        return {"response": response, "extracted": {}, "field_status": field_status, "trigger_handover": False}

    # — Skip / defer —
    if _is_skip_request(user_message):
        critical = {"name", "description", "business_purpose"}
        if current_field in critical:
            prompts = {
                "name": "A working title is fine — you can rename it later. What does this data roughly contain? (e.g. 'Risk Positions Data')",
                "description": "Even one sentence works. What kind of data does this product hold?",
                "business_purpose": "Even 'for regulatory reporting' is a perfect start. What's the main use?",
            }
            return {
                "response": f"**{label}** is the one field that really needs an answer — it's the first thing people see in Collibra. {prompts.get(current_field, '')}",
                "extracted": {}, "field_status": field_status, "trigger_handover": False,
            }
        new_status = {**field_status, current_field: FIELD_STATUS_DEFERRED}
        response = f"No problem — I'll come back to **{label}** at the end."
        next_f = _next_field(new_status, field_status)
        if next_f:
            response += "\n\n" + _ask_field(next_f, valid_options)
        return {"response": response, "extracted": {}, "field_status": new_status, "trigger_handover": False}

    # — Extract value —
    value = _try_extract(user_message, current_field, valid_options)
    if value is not None and value != [] and value != "":
        new_status = {**field_status, current_field: FIELD_STATUS_ANSWERED}
        extracted = {current_field: value}
        confirm = random.choice(_CONFIRM_VARIANTS)
        display = ", ".join(str(v) for v in value) if isinstance(value, list) else str(value)
        response = f"{confirm} **{label}**: *{display}*."

        answered_count = sum(1 for s in new_status.values() if s == FIELD_STATUS_ANSWERED)
        if answered_count == 5:
            response += " Five fields captured — you're making great progress! 🚀"
        elif answered_count == 10:
            response += " Ten fields in — nearly done with the business side! 💪"

        next_f = _next_field(new_status, field_status)
        if next_f:
            if field_status.get(next_f) == FIELD_STATUS_DEFERRED:
                response += f"\n\n↩ Coming back to **{FIELD_REGISTRY.get(next_f, {}).get('label', next_f)}** now."
            response += "\n\n" + _ask_field(next_f, valid_options)
        else:
            response += "\n\n🎉 All fields covered! Click **Review & Submit**, or say **'hand over'** to notify the tech team."

        return {"response": response, "extracted": extracted, "field_status": new_status, "trigger_handover": False}

    # — No match —
    if options:
        response = (
            f"I didn't quite catch that for **{label}**. Here are the options:\n\n"
            + "  ·  ".join(f"**{o}**" for o in options)
            + "\n\nWhich fits best? *(or 'skip' to defer · 'help' for explanation)*"
        )
    else:
        question = FIELD_REGISTRY.get(current_field, {}).get("question", f"What's the {label.lower()}?")
        response = f"I need a bit more detail for **{label}**. {question}\n\n*(Type 'help' for context, 'skip' to defer, 'not needed' if it doesn't apply.)*"
    return {"response": response, "extracted": {}, "field_status": field_status, "trigger_handover": False}


def _next_field(new_status: dict, old_status: dict) -> Optional[str]:
    """Return the next field to ask about given updated status."""
    # Non-deferred pending/new first, then deferred at end
    pending = [f for f in BUSINESS_FLOW_ORDER if new_status.get(f, FIELD_STATUS_PENDING) == FIELD_STATUS_PENDING]
    if pending:
        return pending[0]
    deferred = [f for f in BUSINESS_FLOW_ORDER if new_status.get(f) == FIELD_STATUS_DEFERRED]
    return deferred[0] if deferred else None


def _ask_field(field: str, valid_options: dict) -> str:
    """Build a question string for the given field."""
    reg = FIELD_REGISTRY.get(field, {})
    question = reg.get("question", f"What's the {field.replace('_', ' ')}?")
    options = _get_field_options(field, valid_options)
    text = question
    if options and field not in ("name", "description", "business_purpose", "domain", "data_owner_name"):
        text += f"\n\n**Options:** {', '.join(options)}"
    can_be_na = reg.get("can_be_na", False)
    hints = []
    if can_be_na:
        hints.append("'not needed' if it doesn't apply")
    hints.append("'skip' to defer")
    hints.append("'help' to learn more")
    text += f"\n\n*({' · '.join(hints)})*"
    return text


# ============================================================================
# SPEC PANEL
# ============================================================================

_SPEC_SECTIONS = [
    ("Identity", ["name", "description", "business_purpose"]),
    ("Classification", ["domain", "data_classification", "sub_domain", "tags"]),
    ("Governance", ["data_owner_name", "data_owner_email", "data_steward_email", "certifying_officer_email"]),
    ("Regulatory & Compliance", ["regulatory_scope", "geographic_restriction", "pii_flag", "retention_period", "encryption_standard"]),
    ("Technical", ["source_systems", "update_frequency", "schema_location", "version"]),
    ("Access & Business", ["access_level", "consumer_teams", "sla_tier", "business_criticality", "cost_centre", "related_reports"]),
    ("Collibra Auto-Populated", list(AUTO_COLLIBRA_FIELDS.keys())),
]


def _render_live_spec(spec: DataProductSpec, field_status: dict):
    """Render the right-column live spec panel."""
    st.markdown(
        '<p style="font-size:.75rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;'
        'color:var(--teal);margin-bottom:.75rem;">Live Spec Preview</p>',
        unsafe_allow_html=True,
    )

    answered = sum(1 for s in field_status.values() if s == FIELD_STATUS_ANSWERED)
    not_needed = sum(1 for s in field_status.values() if s == FIELD_STATUS_NOT_NEEDED)
    deferred = sum(1 for s in field_status.values() if s == FIELD_STATUS_DEFERRED)
    total_business = len(BUSINESS_FLOW_ORDER)
    completion = spec.completion_percentage()

    st.progress(completion / 100)
    st.caption(
        f"{completion:.0f}% complete · "
        f"{answered} answered · "
        f"{not_needed} N/A · "
        f"{deferred} deferred"
    )

    for section_name, fields in _SPEC_SECTIONS:
        section_rows = []
        for f in fields:
            if f in AUTO_COLLIBRA_FIELDS:
                section_rows.append((f, AUTO_COLLIBRA_FIELDS[f], "auto"))
                continue
            raw = getattr(spec, f, None)
            status = field_status.get(f, FIELD_STATUS_PENDING)
            if raw not in (None, "", [], {}) and status == FIELD_STATUS_ANSWERED:
                display = ", ".join(str(v) for v in raw) if isinstance(raw, list) else str(raw)
                section_rows.append((f, display, "answered"))
            elif status == FIELD_STATUS_NOT_NEEDED:
                reg = FIELD_REGISTRY.get(f, {})
                section_rows.append((f, reg.get("na_label", "Not applicable"), "not_needed"))

        if not section_rows:
            continue

        st.markdown(
            f'<p style="font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;'
            f'color:var(--text-muted);margin:.75rem 0 .3rem;">{section_name}</p>',
            unsafe_allow_html=True,
        )
        for field, display, state in section_rows:
            label = FIELD_REGISTRY.get(field, {}).get("label", field.replace("_", " ").title())
            trunc = display if len(display) < 55 else display[:52] + "…"
            if state == "answered":
                icon, color, text_color = "✓", "var(--teal)", "var(--text-primary)"
            elif state == "not_needed":
                icon, color, text_color = "✗", "rgba(140,155,170,.6)", "var(--text-muted)"
            else:  # auto
                icon, color, text_color = "⚙", "rgba(77,217,192,.4)", "var(--text-muted)"
            st.markdown(
                f'<div style="border-left:2px solid {color};padding:.2rem .5rem;margin:.15rem 0;">'
                f'<span style="font-size:.65rem;color:var(--text-muted);">{icon} {label}</span><br>'
                f'<span style="font-size:.78rem;color:{text_color};font-weight:500;">{trunc}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # Still pending
    pending = [f for f in BUSINESS_FLOW_ORDER if field_status.get(f, FIELD_STATUS_PENDING) == FIELD_STATUS_PENDING]
    deferred_fields = [f for f in BUSINESS_FLOW_ORDER if field_status.get(f) == FIELD_STATUS_DEFERRED]

    if pending or deferred_fields:
        st.markdown(
            '<p style="font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;'
            'color:var(--text-muted);margin:.75rem 0 .3rem;">Remaining</p>',
            unsafe_allow_html=True,
        )
        for f in (pending + deferred_fields)[:6]:
            label = FIELD_REGISTRY.get(f, {}).get("label", f.replace("_", " ").title())
            owner = FIELD_REGISTRY.get(f, {}).get("owner", "business")
            icon = "○" if f in pending else "⏸"
            color = "rgba(245,166,35,.8)" if f in deferred_fields else "var(--text-muted)"
            st.markdown(
                f'<div style="font-size:.72rem;color:{color};padding:.1rem 0;">'
                f'{icon} {label} <span style="opacity:.5;font-size:.65rem;">({owner})</span></div>',
                unsafe_allow_html=True,
            )
        total_remaining = len(pending) + len(deferred_fields)
        if total_remaining > 6:
            st.markdown(
                f'<div style="font-size:.68rem;color:var(--text-muted);padding:.1rem 0;">… and {total_remaining - 6} more</div>',
                unsafe_allow_html=True,
            )


# ============================================================================
# OPTION PILLS
# ============================================================================

def _render_option_pills(field: str, valid_options: dict):
    options = _get_field_options(field, valid_options)
    if not options:
        return
    is_multi = field in ("regulatory_scope", "source_systems", "consumer_teams", "tags", "related_reports")
    label = FIELD_REGISTRY.get(field, {}).get("label", field.replace("_", " ").title())
    st.caption(f"**{label}** — {'select all that apply' if is_multi else 'tap to answer'}:")
    cols = st.columns(min(len(options), 4))
    for i, opt in enumerate(options[:12]):
        with cols[i % 4]:
            if st.button(opt, key=f"pill_{field}_{i}", use_container_width=True):
                st.session_state["_pill_selection"] = opt
                st.rerun()


# ============================================================================
# HANDOVER SECTION
# ============================================================================

def _render_handover_section(spec: DataProductSpec, field_status: dict):
    """Full handover UI: tech fields summary, email composer, download."""
    st.markdown(
        '<div class="dpc-concierge">'
        '✦ <strong>Handover to tech team</strong><br>'
        "You've captured the business context. Below is what still needs completing by your technical or data team — "
        "I've pre-filled what I can, and you can download the partial spec or send it directly."
        '</div>',
        unsafe_allow_html=True,
    )

    # — Tech fields that still need input —
    tech_pending = [f for f in TECH_FLOW_ORDER if field_status.get(f, FIELD_STATUS_PENDING) == FIELD_STATUS_PENDING]
    deferred_business = [f for f in BUSINESS_FLOW_ORDER if field_status.get(f) == FIELD_STATUS_DEFERRED]
    na_fields = [f for f, s in field_status.items() if s == FIELD_STATUS_NOT_NEEDED]

    if tech_pending or deferred_business:
        st.markdown("### Fields for the tech team to complete")
        pending_rows = []
        for f in tech_pending:
            reg = FIELD_REGISTRY.get(f, {})
            pending_rows.append({
                "Field": reg.get("label", f),
                "Required": "✱" if f in ALL_REQUIRED else "opt",
                "Collibra Source": reg.get("collibra_source", "—"),
                "Collibra Endpoint": reg.get("collibra_endpoint", "—"),
            })
        for f in deferred_business:
            reg = FIELD_REGISTRY.get(f, {})
            pending_rows.append({
                "Field": f"{reg.get('label', f)} *(deferred)*",
                "Required": "✱" if f in ALL_REQUIRED else "opt",
                "Collibra Source": reg.get("collibra_source", "—"),
                "Collibra Endpoint": reg.get("collibra_endpoint", "—"),
            })
        if pending_rows:
            import pandas as pd
            st.dataframe(
                pd.DataFrame(pending_rows),
                use_container_width=True,
                hide_index=True,
            )

    # — Auto-populated by Collibra —
    with st.expander("⚙ Fields Collibra auto-populates (no action needed)", expanded=False):
        for field, desc in AUTO_COLLIBRA_FIELDS.items():
            st.markdown(f"**{field}** — {desc}")

    # — N/A fields —
    if na_fields:
        with st.expander(f"✗ {len(na_fields)} field(s) marked Not Applicable", expanded=False):
            for f in na_fields:
                reg = FIELD_REGISTRY.get(f, {})
                st.markdown(f"**{reg.get('label', f)}** — {reg.get('na_label', 'Not applicable')}")

    st.divider()

    # — Downloads —
    st.markdown("### Download partial specification")
    col1, col2, col3 = st.columns(3)
    fname = (spec.name or "data_product").replace(" ", "_").lower()
    with col1:
        st.download_button(
            "⬇ Markdown (.md)",
            data=spec.to_markdown(),
            file_name=f"{fname}_partial_spec.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with col2:
        st.download_button(
            "⬇ Collibra JSON",
            data=json.dumps(spec.to_collibra_json(), indent=2),
            file_name=f"{fname}_collibra.json",
            mime="application/json",
            use_container_width=True,
        )
    with col3:
        st.download_button(
            "⬇ Snowflake CSV",
            data=spec.to_snowflake_csv(),
            file_name=f"{fname}_snowflake.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.divider()

    # — Email handover composer —
    st.markdown("### Notify tech / data team by email")

    recipient_role = st.radio(
        "Send to:",
        ["Tech Team", "Data Analyst", "Data Steward", "Custom email"],
        horizontal=True,
        key="handover_recipient_role",
    )

    default_email = ""
    if recipient_role == "Data Steward" and spec.data_steward_email:
        default_email = str(spec.data_steward_email)

    recipient_email = st.text_input(
        "Recipient email",
        value=default_email,
        placeholder="engineer@firm.com",
        key="handover_email_input",
    )

    # Build email body
    missing_list = "\n".join(
        f"  - {FIELD_REGISTRY.get(f, {}).get('label', f)} "
        f"({'required' if f in ALL_REQUIRED else 'optional'}) "
        f"— Collibra: {FIELD_REGISTRY.get(f, {}).get('collibra_source', '?')}"
        for f in (tech_pending + deferred_business)
    )
    na_list = "\n".join(
        f"  - {FIELD_REGISTRY.get(f, {}).get('label', f)}: {FIELD_REGISTRY.get(f, {}).get('na_label', 'N/A')}"
        for f in na_fields
    ) or "  (none)"

    product_name = spec.name or "(unnamed product)"
    owner_name = spec.data_owner_name or "the data owner"
    owner_email = str(spec.data_owner_email) if spec.data_owner_email else ""

    email_body = f"""Hi,

{owner_name} has started specifying a new data product in the Data Product Concierge and needs your help completing the technical details.

DATA PRODUCT: {product_name}
Description: {spec.description or '(see attached spec)'}
Business Purpose: {spec.business_purpose or '(see attached spec)'}
Domain: {spec.domain or '(not set)'}
Data Owner: {owner_name} {f'({owner_email})' if owner_email else ''}

FIELDS STILL NEEDING COMPLETION:
{missing_list or '  (all technical fields complete)'}

FIELDS MARKED NOT APPLICABLE:
{na_list}

Collibra auto-populates the following fields on asset creation — no action needed:
  - Asset ID (UUID generated by Collibra)
  - Created/Updated timestamps
  - Lifecycle status (managed by workflow)
  - Data Quality Score (computed by DQ module)

Please complete the outstanding fields in the Data Product Concierge or directly in Collibra.

Partial spec attached (download from the app above).

Thanks,
Data Product Concierge
"""

    with st.expander("✉ Preview email", expanded=True):
        st.code(email_body, language=None)

    if recipient_email:
        subject = f"[Action Required] Data Product Spec — {product_name}"
        mailto_link = (
            f"mailto:{quote(recipient_email)}"
            f"?subject={quote(subject)}"
            f"&body={quote(email_body)}"
        )
        st.link_button(
            "✉ Open in email client",
            url=mailto_link,
            use_container_width=True,
            type="primary",
        )
        st.caption("Opens your default email client with the message pre-filled. Attach the downloaded spec.")
    else:
        st.info("Enter a recipient email above to generate the mailto link.")

    st.divider()

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("← Continue answering", key="handover_back", use_container_width=True):
            st.session_state["show_handover"] = False
            st.rerun()
    with col_b:
        if st.button("✅ Submit partial spec", key="handover_submit", use_container_width=True, type="primary"):
            return True

    return False


# ============================================================================
# MAIN RENDER
# ============================================================================

def render_conversation(
    spec: DataProductSpec,
    valid_options: dict,
    is_preview: bool,
) -> Tuple[DataProductSpec, bool]:
    """Render conversational CREATE interface. Returns (updated_spec, is_complete)."""

    st.components.v1.html(
        '<script>try{window.parent.document.querySelector(".main").scrollTo(0,0);}catch(e){}</script>',
        height=0,
    )

    concierge = st.session_state.get("concierge")
    if concierge is None and not is_preview:
        try:
            from agents.concierge import DataProductConcierge
            concierge = DataProductConcierge()
        except Exception:
            concierge = None

    # — Session state init —
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "field_status" not in st.session_state:
        st.session_state.field_status = {}
    if "show_handover" not in st.session_state:
        st.session_state.show_handover = False

    # Always use latest spec from session_state
    spec = st.session_state.get("spec", spec)
    field_status = st.session_state.field_status

    # Opening message
    if not st.session_state.chat_history:
        seeded = st.session_state.get("concierge_seeded", False)
        if seeded and spec.name:
            for f in ("name", "description", "business_purpose", "domain", "regulatory_scope"):
                if getattr(spec, f, None) not in (None, "", []):
                    field_status[f] = FIELD_STATUS_ANSWERED
            st.session_state.field_status = field_status
            parts = [f"I've made a start based on your search:\n\n**Name:** {spec.name}\n**Description:** {spec.description}\n**Business Purpose:** {spec.business_purpose}"]
            if spec.domain:
                parts.append(f"\n**Domain:** {spec.domain}")
            if spec.regulatory_scope:
                parts.append(f"\n**Regulatory Scope:** {', '.join(str(r) for r in spec.regulatory_scope)}")
            parts.append("\n\nDoes that look right? Say **'looks good'** and I'll continue with the next fields.")
            opening = "".join(parts)
        else:
            opening = (
                "Let's build your data product together.\n\n"
                "**What would you call it, and what's it for?** "
                "Speak naturally — I'll handle the structure.\n\n"
                "At any point you can:\n"
                "- Say **'help'** for an explanation of what I'm asking\n"
                "- Say **'not needed'** if a field doesn't apply to your product\n"
                "- Say **'skip'** to defer and come back later\n"
                "- Say **'hand over'** to send the partial spec to your tech team"
            )
        st.session_state.chat_history = [{"role": "assistant", "content": opening}]

    # Compute state
    pending = [f for f in BUSINESS_FLOW_ORDER if field_status.get(f, FIELD_STATUS_PENDING) == FIELD_STATUS_PENDING]
    deferred = [f for f in BUSINESS_FLOW_ORDER if field_status.get(f) == FIELD_STATUS_DEFERRED]
    current_field = pending[0] if pending else (deferred[0] if deferred else None)

    answered = sum(1 for s in field_status.values() if s == FIELD_STATUS_ANSWERED)
    not_needed_count = sum(1 for s in field_status.values() if s == FIELD_STATUS_NOT_NEEDED)
    total_business = len(BUSINESS_FLOW_ORDER)
    business_done = (answered + not_needed_count) >= total_business and not pending

    # — HANDOVER SCREEN —
    if st.session_state.show_handover:
        submitted = _render_handover_section(spec, field_status)
        if submitted:
            st.session_state.step = "handoff"
            st.rerun()
        return spec, False

    # — Header —
    status_parts = [f"**{answered}** answered"]
    if not_needed_count:
        status_parts.append(f"**{not_needed_count}** N/A")
    if deferred:
        status_parts.append(f"**{len(deferred)}** deferred")
    remaining = total_business - answered - not_needed_count
    if remaining > 0:
        status_parts.append(f"**{remaining}** remaining")

    st.markdown(
        f'<div class="dpc-concierge">'
        f'Just talk to me — {" · ".join(status_parts)} of {total_business} fields.<br>'
        f'<span style="font-size:.82em;color:var(--text-muted);">'
        f'Say <em>help</em> · <em>not needed</em> · <em>skip</em> · <em>hand over</em>'
        f'</span></div>',
        unsafe_allow_html=True,
    )

    col_chat, col_spec = st.columns([3, 2], gap="large")

    with col_chat:
        # Chat history
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
                st.markdown(msg["content"])

        # Business fields done — offer handover + submit
        if business_done or not current_field:
            # Check required fields
            spec_missing = spec.required_missing()
            tech_required_missing = [f for f in spec_missing if FIELD_REGISTRY.get(f, {}).get("owner") == "tech"]
            if not tech_required_missing and not spec_missing:
                st.success("All required fields complete — ready to submit!")
                if st.button("✅ Review & Submit", key="conv_submit", use_container_width=True, type="primary"):
                    return spec, True
            else:
                st.info(
                    f"You've completed the business fields! "
                    f"{'The tech team still needs to fill in ' + str(len(tech_required_missing)) + ' technical field(s).' if tech_required_missing else ''}"
                )
            if st.button("📤 Hand over to tech team →", key="conv_handover", use_container_width=True, type="primary"):
                st.session_state.show_handover = True
                st.rerun()
        else:
            # Option pills for current field
            _render_option_pills(current_field, valid_options)

        # Inline download (always available after name is set)
        if spec.name:
            with st.expander("⬇ Download spec so far", expanded=False):
                fname = spec.name.replace(" ", "_").lower()
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    st.download_button("Markdown", spec.to_markdown(), f"{fname}_spec.md", "text/markdown", use_container_width=True)
                with col_d2:
                    st.download_button("JSON", json.dumps(spec.to_collibra_json(), indent=2), f"{fname}.json", "application/json", use_container_width=True)

        # Chat input
        pill_input = st.session_state.get("_pill_selection")
        if "_pill_selection" in st.session_state:
            del st.session_state["_pill_selection"]
        user_input = pill_input or st.chat_input("Type your response… (help · skip · not needed · hand over)")

        if user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})

            if concierge and not is_preview:
                try:
                    result = _run_async(concierge.chat_turn(
                        user_message=user_input,
                        history=st.session_state.chat_history[:-1],
                        spec=spec,
                        valid_options=valid_options,
                    ))
                    result.setdefault("field_status", field_status)
                    result.setdefault("trigger_handover", False)
                except Exception:
                    result = _preview_chat_turn(user_input, spec, valid_options, field_status, current_field)
            else:
                result = _preview_chat_turn(user_input, spec, valid_options, field_status, current_field)

            if result.get("extracted"):
                spec = _apply_extracted(spec, result["extracted"])
                st.session_state.spec = spec

            if result.get("field_status"):
                st.session_state.field_status = result["field_status"]

            if result.get("trigger_handover"):
                st.session_state.show_handover = True

            st.session_state.chat_history.append({
                "role": "assistant",
                "content": result["response"],
            })

            st.rerun()

    with col_spec:
        _render_live_spec(spec, field_status)

    return spec, False
