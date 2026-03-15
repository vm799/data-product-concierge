"""
Shared field metadata registry for Data Product Concierge.

Single source of truth for all DataProductSpec field metadata:
labels, questions, explanations, owners, options, Collibra mappings.

No imports required — pure data module.
"""

# ============================================================================
# FIELD REGISTRY
# ============================================================================
# Keys match DataProductSpec field names exactly.
# Every entry has: label, question, explanation, owner, required, can_be_na,
# options, collibra_source, collibra_endpoint.
# Optional keys (na_label) may also be present on some entries.

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
    "last_certified_date": {
        "label": "Last Certified Date",
        "owner": "tech",
        "collibra_source": "Asset attribute (Last Certified Date)",
        "collibra_endpoint": "GET /assets/{id}/attributes → type='Last Certified Date'",
        "question": "When was this data product last formally certified? (YYYY-MM-DD)",
        "explanation": "Certification date is used by governance teams to track recertification cadence and compliance with the review cycle.",
        "options": [],
        "required": False,
        "can_be_na": True,
        "na_label": "Not yet certified",
    },
    # ---- NEW: SNOWFLAKE BUILD ----
    "materialization_type": {
        "label": "Materialization Type",
        "owner": "tech",
        "collibra_source": "",
        "collibra_endpoint": "",
        "question": "How should this data be stored in Snowflake?",
        "explanation": "Choose Table for persisted data, View for a logical SQL query, Dynamic Table for auto-refreshed transforms.",
        "options": ["Table", "View", "Materialized View", "Dynamic Table", "External Table"],
        "required": False,
        "can_be_na": True,
    },
    "snowflake_role": {
        "label": "Snowflake Access Role",
        "owner": "tech",
        "collibra_source": "",
        "collibra_endpoint": "",
        "question": "Which Snowflake role gets SELECT access to this product?",
        "explanation": "The role used in the GRANT SELECT statement in the generated DDL. e.g. ROLE_ESG_READ",
        "options": [],
        "required": False,
        "can_be_na": True,
    },
    "column_definitions": {
        "label": "Column Definitions",
        "owner": "tech",
        "collibra_source": "",
        "collibra_endpoint": "",
        "question": "List the columns this product will expose.",
        "explanation": "One per line: COLUMN_NAME TYPE [NOT NULL]. e.g. FUND_ID VARCHAR NOT NULL. Used to generate the Snowflake CREATE TABLE statement.",
        "options": [],
        "required": False,
        "can_be_na": True,
    },
    "refresh_cron": {
        "label": "Refresh Schedule (Cron)",
        "owner": "tech",
        "collibra_source": "",
        "collibra_endpoint": "",
        "question": "What is the refresh schedule for this data product?",
        "explanation": "Standard cron expression in UTC. e.g. '0 6 * * 1-5' for 6am Mon-Fri. Leave blank for on-demand.",
        "options": [],
        "required": False,
        "can_be_na": True,
    },
    "sample_query": {
        "label": "Sample SQL Query",
        "owner": "tech",
        "collibra_source": "",
        "collibra_endpoint": "",
        "question": "Provide a sample SELECT query that defines this view or dynamic table.",
        "explanation": "Used as the body of the CREATE VIEW or DYNAMIC TABLE DDL. Can be filled in by the tech team.",
        "options": [],
        "required": False,
        "can_be_na": True,
    },
    "lineage_upstream": {
        "label": "Upstream Dependencies",
        "owner": "tech",
        "collibra_source": "",
        "collibra_endpoint": "",
        "question": "What data sources feed into this product?",
        "explanation": "List the upstream tables, APIs, or data products this product reads from. Supports data lineage tracking in Collibra.",
        "options": [],
        "required": False,
        "can_be_na": True,
    },
    "lineage_downstream": {
        "label": "Downstream Consumers",
        "owner": "tech",
        "collibra_source": "",
        "collibra_endpoint": "",
        "question": "What reports or systems consume this product?",
        "explanation": "List the dashboards, models, or systems that read from this product. Used to assess impact of changes.",
        "options": [],
        "required": False,
        "can_be_na": True,
    },
    # ---- NEW: OPERATIONAL ----
    "delivery_method": {
        "label": "Delivery Method",
        "owner": "tech",
        "collibra_source": "",
        "collibra_endpoint": "",
        "question": "How is this data product accessed by consumers?",
        "explanation": "The technical mechanism consumers use to read the data.",
        "options": ["SQL Table", "SQL View", "REST API", "Kafka", "File Export"],
        "required": False,
        "can_be_na": True,
    },
    "review_cycle": {
        "label": "Review Cycle",
        "owner": "tech",
        "collibra_source": "",
        "collibra_endpoint": "",
        "question": "How often should this data product be formally reviewed?",
        "explanation": "Sets the certification cadence. Governance teams use this to schedule reviews.",
        "options": ["Annual", "Semi-Annual", "Quarterly", "Monthly"],
        "required": False,
        "can_be_na": True,
    },
    "incident_contact": {
        "label": "Incident Contact Email",
        "owner": "tech",
        "collibra_source": "",
        "collibra_endpoint": "",
        "question": "Who should be contacted if there is a data incident with this product?",
        "explanation": "On-call email or alias for the team responsible for incident response.",
        "options": [],
        "required": False,
        "can_be_na": True,
    },
    # ---- NEW: COLLIBRA REGISTRATION ----
    "asset_type": {
        "label": "Collibra Asset Type",
        "owner": "tech",
        "collibra_source": "",
        "collibra_endpoint": "",
        "question": "What type of asset is this in Collibra?",
        "explanation": "Maps to the Collibra asset type taxonomy. 'Data Product' is the most common for this tool.",
        "options": ["Data Product", "Data Set", "Report", "API", "Stream"],
        "required": False,
        "can_be_na": True,
    },
    "collibra_community": {
        "label": "Collibra Community",
        "owner": "tech",
        "collibra_source": "",
        "collibra_endpoint": "",
        "question": "Which Collibra community should this asset belong to?",
        "explanation": "Top-level organisational container in Collibra. Typically matches a business unit or data domain.",
        "options": [],
        "required": False,
        "can_be_na": True,
    },
    # ========================================================================
    # PANEL A — ACCESS & LICENSING (L0 gaps)
    # ========================================================================
    "access_procedure": {
        "label": "Access Procedure",
        "owner": "business",
        "collibra_source": "Asset attribute (Data Product Access Procedure)",
        "collibra_endpoint": "GET /assets/{id}/attributes → type='Access Procedure'",
        "question": "How should someone request access to this data product? Describe the steps or link to the access request form.",
        "explanation": "A clear access procedure lets consumers self-serve. Without it, teams email the owner directly — creating bottlenecks and inconsistent approvals.",
        "options": [],
        "required": False,
        "can_be_na": True,
        "na_label": "Access is managed directly by the data owner",
    },
    "data_licensing_flag": {
        "label": "Licensing Restrictions Apply",
        "owner": "business",
        "collibra_source": "Vocabulary domain (data_licensing vocab)",
        "collibra_endpoint": "GET /assets/{id}/attributes → type='Data Licensing Restrictions Applied'",
        "question": "Are there data licensing restrictions on this product? (e.g. vendor data that limits redistribution or use cases)",
        "explanation": "Licensing restrictions prevent legal exposure. Bloomberg, MSCI, and similar vendor data often restricts internal redistribution. This flag triggers a legal review before downstream use.",
        "options": ["Yes", "No"],
        "required": False,
        "can_be_na": False,
    },
    "data_licensing_details": {
        "label": "Licensing Restriction Details",
        "owner": "business",
        "collibra_source": "Asset attribute (Data Licensing Restriction Details)",
        "collibra_endpoint": "GET /assets/{id}/attributes → type='Data Licensing Restriction Details'",
        "question": "Describe the licensing restrictions — which vendor, what limits apply, and which use cases are excluded.",
        "explanation": "The details help downstream teams understand exactly what they can and cannot do with this data. Be specific: e.g. 'Bloomberg Terminal data — internal use only, no redistribution, no derived products for external clients.'",
        "options": [],
        "required": False,
        "can_be_na": True,
        "na_label": "Not applicable",
    },
    "data_sovereignty_flag": {
        "label": "Sovereignty Restrictions Apply",
        "owner": "business",
        "collibra_source": "Vocabulary domain (data_sovereignty vocab)",
        "collibra_endpoint": "GET /assets/{id}/attributes → type='Data Sovereignty Restrictions Apply'",
        "question": "Are there data sovereignty restrictions — i.e. does the law of a specific country govern how this data is handled?",
        "explanation": "Data sovereignty is distinct from geographic storage restrictions. Sovereignty determines *which country's law* governs the data (e.g. EU GDPR applies even if the data is stored in a UK data centre). Common for cross-border transfers.",
        "options": ["Yes", "No"],
        "required": False,
        "can_be_na": False,
    },
    "data_sovereignty_details": {
        "label": "Sovereignty Restriction Details",
        "owner": "business",
        "collibra_source": "Asset attribute (Data Sovereignty Restriction Details)",
        "collibra_endpoint": "GET /assets/{id}/attributes → type='Data Sovereignty Restriction Details'",
        "question": "Which country's law applies and what restrictions does it impose on this data?",
        "explanation": "E.g. 'Subject to EU GDPR — data subject rights apply; cross-border transfers require Standard Contractual Clauses.' Be specific so legal can verify compliance.",
        "options": [],
        "required": False,
        "can_be_na": True,
        "na_label": "Not applicable",
    },
    "data_subject_areas": {
        "label": "Data Subject Areas",
        "owner": "business",
        "collibra_source": "Linked Asset (Data Subject Area type in Collibra)",
        "collibra_endpoint": "GET /assets/{id}/relations → filter type='Data Subject Area'",
        "question": "Which categories of data subjects does this product cover? E.g. Employees, Clients, Counterparties, Individual Investors.",
        "explanation": "Data subject areas are required for GDPR Article 30 records of processing activities. They determine which rights (access, erasure, portability) apply to this product.",
        "options": ["Employees", "Clients", "Individual Investors", "Counterparties", "Prospects", "Fund Managers", "Retail Clients", "Professional Clients"],
        "required": False,
        "can_be_na": True,
        "na_label": "Does not contain personal data",
    },
    "governing_body": {
        "label": "Governing Body",
        "owner": "business",
        "collibra_source": "Linked Asset (Governing Body asset type in Collibra)",
        "collibra_endpoint": "GET /assets/{id}/relations → filter type='Governing Body'",
        "question": "Which governance committee or forum oversees this data product? E.g. Data Governance Council, ESG Data Steering Group, Risk Data Committee.",
        "explanation": "Linking a governing body enables escalation paths and ensures the right stakeholders are notified during certification reviews or regulatory enquiries.",
        "options": [],
        "required": False,
        "can_be_na": True,
        "na_label": "No formal governing body assigned",
    },
    # ========================================================================
    # PANEL B — EXTENDED OWNERSHIP (L1)
    # ========================================================================
    "data_domain_owner_email": {
        "label": "Domain Owner Email",
        "owner": "business",
        "collibra_source": "Asset responsibility (Domain Owner role)",
        "collibra_endpoint": "GET /assets/{id}/responsibilities → role='Data Domain Owner' → user.email",
        "question": "Who is the domain-level owner above this data product? This is typically a Chief Data Officer, Head of Data, or domain lead.",
        "explanation": "The domain owner sits above individual product owners and provides strategic oversight for the whole domain. They resolve conflicts between products and set domain-wide policies.",
        "options": [],
        "required": False,
        "can_be_na": True,
        "na_label": "Same as data owner / not separately assigned",
    },
    "data_custodian_email": {
        "label": "Data Custodian Email",
        "owner": "tech",
        "collibra_source": "Asset responsibility (Data Custodian role)",
        "collibra_endpoint": "GET /assets/{id}/responsibilities → role='Data Custodian' → user.email",
        "question": "Who is technically responsible for the storage, processing, and access controls of this data? (Data Custodian)",
        "explanation": "The custodian is accountable for the physical and technical implementation — ensuring secure storage, appropriate backups, and access controls are in place. Distinct from the steward (quality) and owner (accountability).",
        "options": [],
        "required": False,
        "can_be_na": True,
        "na_label": "Covered by the data steward",
    },
    "expected_release_date": {
        "label": "Expected Release Date",
        "owner": "business",
        "collibra_source": "Asset attribute (Expected Release Date)",
        "collibra_endpoint": "GET /assets/{id}/attributes → type='Expected Release Date'",
        "question": "When is this data product expected to go live in production? (YYYY-MM-DD)",
        "explanation": "The release date appears in Collibra so consuming teams can plan their integration work and downstream dependencies accordingly.",
        "options": [],
        "required": False,
        "can_be_na": True,
        "na_label": "Release date not yet defined",
    },
    "business_capability": {
        "label": "Business Capability",
        "owner": "business",
        "collibra_source": "Linked Asset (Business Capability asset type in Collibra)",
        "collibra_endpoint": "GET /assets/{id}/relations → filter type='Business Capability'",
        "question": "Which business capability does this data product enable? E.g. ESG Reporting, Portfolio Risk Analytics, Client Onboarding, Regulatory Disclosure.",
        "explanation": "Linking to a business capability connects the data product to the firm's capability map, enabling impact analysis and supporting architecture reviews.",
        "options": [],
        "required": False,
        "can_be_na": True,
        "na_label": "Not mapped to a capability",
    },
    # ========================================================================
    # PANEL C — DATA DETAIL (L1-L2)
    # ========================================================================
    "business_terms": {
        "label": "Business Terms",
        "owner": "business",
        "collibra_source": "Linked Asset (Business Term asset type — Business Term Glossary)",
        "collibra_endpoint": "GET /assets/{id}/relations → filter type='Business Term'",
        "question": "Which business terms from the glossary apply to this data product? E.g. 'Net Asset Value', 'Carbon Intensity', 'AUM'.",
        "explanation": "Linking business terms creates a connection between the data product and the corporate glossary. This helps analysts discover the product when searching by business concept.",
        "options": [],
        "required": False,
        "can_be_na": True,
        "na_label": "No specific terms linked",
    },
    "release_notes": {
        "label": "Release Notes",
        "owner": "business",
        "collibra_source": "Asset attribute (Release Notes)",
        "collibra_endpoint": "GET /assets/{id}/attributes → type='Release Notes'",
        "question": "Are there any release notes or change log entries for this version of the data product?",
        "explanation": "Release notes inform downstream consumers of what changed between versions — new fields, breaking schema changes, deprecated columns. Essential for consumers who rely on stable schemas.",
        "options": [],
        "required": False,
        "can_be_na": True,
        "na_label": "First version — no prior releases",
    },
    "data_latency": {
        "label": "Data Latency",
        "owner": "tech",
        "collibra_source": "Asset attribute (Data Latency)",
        "collibra_endpoint": "GET /assets/{id}/attributes → type='Data Latency'",
        "question": "What is the typical delay between data being captured at source and being available in this product? E.g. 'Under 5 minutes', '15-30 minutes', 'T+1 day'.",
        "explanation": "Latency is critical for time-sensitive use cases like intraday risk monitoring or real-time client reporting. Consumers need to know if they're looking at live or stale data.",
        "options": [],
        "required": False,
        "can_be_na": True,
        "na_label": "Latency not measured",
    },
    "data_history_from": {
        "label": "Historical Data From",
        "owner": "tech",
        "collibra_source": "Asset attribute (Data History From Date)",
        "collibra_endpoint": "GET /assets/{id}/attributes → type='Data History'",
        "question": "How far back does the historical data in this product go? Enter the earliest available date. (YYYY-MM-DD)",
        "explanation": "History depth determines whether backtesting and historical reporting are possible. Some regulatory calculations (e.g. SFDR PAI) require 3+ years of history.",
        "options": [],
        "required": False,
        "can_be_na": True,
        "na_label": "History depth not determined",
    },
    "data_publishing_time": {
        "label": "Publishing Time",
        "owner": "tech",
        "collibra_source": "Asset attribute (Data Publishing Time)",
        "collibra_endpoint": "GET /assets/{id}/attributes → type='Data Publishing Time'",
        "question": "At what time of day is data typically published and available? E.g. '06:00 UTC', 'By 09:30 London time', 'Within 1 hour of market close'.",
        "explanation": "Publishing time helps downstream teams schedule their jobs. Knowing that data arrives at 06:00 UTC means reports can be scheduled for 06:30 with confidence.",
        "options": [],
        "required": False,
        "can_be_na": True,
        "na_label": "No fixed publishing schedule",
    },
    # ========================================================================
    # PANEL D — TECH DEPTH (L2, colleague handoff expansion)
    # ========================================================================
    "target_systems": {
        "label": "Target Systems",
        "owner": "tech",
        "collibra_source": "Linked Asset (Target System relations in Collibra)",
        "collibra_endpoint": "GET /assets/{id}/relations → filter type='Target System'",
        "question": "Which downstream systems consume or are fed by this data product? E.g. Tableau Server, Bloomberg AIM, Axioma Risk, SFDR reporting platform.",
        "explanation": "Target systems complement downstream lineage. They identify the *systems* (vs. the logical data products) that depend on this product, enabling infrastructure impact analysis.",
        "options": [],
        "required": False,
        "can_be_na": True,
        "na_label": "Target systems not yet identified",
    },
    "target_dpro": {
        "label": "Target DPRO",
        "owner": "tech",
        "collibra_source": "Linked Asset (Data Product Registration Object in Collibra)",
        "collibra_endpoint": "GET /assets/{id}/relations → filter type='Target DPRO'",
        "question": "What is the Collibra Data Product Registration Object (DPRO) that this data product maps to?",
        "explanation": "The DPRO is the canonical Collibra registration record for a data product. Linking here ensures the business spec and technical asset are reconciled in governance.",
        "options": [],
        "required": False,
        "can_be_na": True,
        "na_label": "DPRO not yet assigned",
    },
    "critical_data_elements": {
        "label": "Critical Data Elements",
        "owner": "tech",
        "collibra_source": "Linked Asset (CDE designations in Collibra)",
        "collibra_endpoint": "GET /assets/{id}/relations → filter type='Critical Data Element'",
        "question": "Which fields or columns in this data product have been designated as Critical Data Elements (CDEs)? List the column names.",
        "explanation": "CDEs are the most business-critical fields that require enhanced data quality monitoring and governance. BCBS 239 requires banks to identify and monitor CDEs across risk data. List each CDE on a separate line.",
        "options": [],
        "required": False,
        "can_be_na": True,
        "na_label": "No CDEs designated",
    },
}

# ============================================================================
# ORDERED FIELD LISTS FOR GUIDED FLOW
# ============================================================================

GUIDED_BUSINESS_REQUIRED = [
    "name", "description", "business_purpose",
    "domain", "data_classification", "regulatory_scope",
    "pii_flag",
    "data_owner_name", "data_owner_email", "data_steward_email",
    "access_level", "sla_tier", "business_criticality",
    "consumer_teams",
]

GUIDED_BUSINESS_OPTIONAL = [
    "tags", "cost_centre", "related_reports",
    "certifying_officer_email", "last_certified_date", "sub_domain",
]

GUIDED_TECH_FIELDS = [
    "source_systems", "update_frequency", "schema_location",
    "materialization_type", "snowflake_role", "column_definitions", "refresh_cron",
    "sample_query", "lineage_upstream", "lineage_downstream",
    "geographic_restriction", "encryption_standard", "retention_period",
    "version", "delivery_method", "review_cycle", "incident_contact",
    "asset_type", "collibra_community",
]

GUIDED_AUTO_FIELDS = ["id", "created_at", "updated_at", "status", "data_quality_score"]

# ============================================================================
# MATURITY ENHANCEMENT PANEL FIELD LISTS
# ============================================================================

GUIDED_PANEL_ACCESS_LICENSING = [
    "access_procedure",
    "data_licensing_flag",
    "data_licensing_details",
    "data_sovereignty_flag",
    "data_sovereignty_details",
    "governing_body",
]

GUIDED_PANEL_EXTENDED_OWNERSHIP = [
    "data_domain_owner_email",
    "data_custodian_email",
    "expected_release_date",
    "business_capability",
]

GUIDED_PANEL_DATA_DETAIL = [
    "business_terms",
    "release_notes",
    "data_latency",
    "data_history_from",
    "data_publishing_time",
]

GUIDED_PANEL_TECH_DEPTH = [
    "target_systems",
    "target_dpro",
    "critical_data_elements",
]

# ============================================================================
# FIELD STATUS CONSTANTS
# ============================================================================

FIELD_STATUS_ANSWERED   = "answered"
FIELD_STATUS_PENDING    = "pending"
FIELD_STATUS_SKIPPED    = "skipped"
FIELD_STATUS_NOT_NEEDED = "not_needed"
FIELD_STATUS_AUTO       = "auto"

# ============================================================================
# HELPER
# ============================================================================


def get_field_meta(field_name: str) -> dict:
    """Return FIELD_REGISTRY entry for field_name, or a safe default."""
    return FIELD_REGISTRY.get(field_name, {
        "label": field_name.replace("_", " ").title(),
        "question": f"Please provide the {field_name.replace('_', ' ')}.",
        "explanation": "",
        "owner": "tech",
        "required": False,
        "can_be_na": True,
        "options": [],
        "collibra_source": "",
        "collibra_endpoint": "",
    })


# ---------------------------------------------------------------------------
# CANONICAL ROLE REGISTRY — single source of truth for colleague roles
# Used by: shared_draft_entry.py, draft_banner.py, handoff_summary.py
# ---------------------------------------------------------------------------

COLLEAGUE_ROLES = {
    "tech": {
        "label": "Data Engineer",
        "icon": "⚡",
        "description": (
            "You've been asked to fill the technical depth fields for this data product — "
            "target systems, DPRO mapping, and Critical Data Elements."
        ),
        "fields": GUIDED_PANEL_TECH_DEPTH,
        "preview_fields": ["target_systems", "target_dpro", "critical_data_elements"],
    },
    "owner": {
        "label": "Data Owner",
        "icon": "🔒",
        "description": (
            "You've been asked to fill the access and licensing details — "
            "how to request access, any restrictions, and the governing body."
        ),
        "fields": GUIDED_PANEL_ACCESS_LICENSING,
        "preview_fields": ["access_procedure", "data_licensing_flag", "governing_body"],
    },
    "steward": {
        "label": "Data Steward",
        "icon": "👥",
        "description": (
            "You've been asked to fill the extended ownership fields — "
            "domain owner, data custodian, expected release date, and business capability."
        ),
        "fields": GUIDED_PANEL_EXTENDED_OWNERSHIP,
        "preview_fields": ["data_domain_owner_email", "data_custodian_email", "expected_release_date"],
    },
    "compliance": {
        "label": "Compliance Officer",
        "icon": "📊",
        "description": (
            "You've been asked to fill the data detail fields — "
            "business terms, release notes, latency, history depth, and publishing schedule."
        ),
        "fields": GUIDED_PANEL_DATA_DETAIL,
        "preview_fields": ["business_terms", "data_latency", "data_history_from"],
    },
}

VALID_ROLES = set(COLLEAGUE_ROLES.keys())
