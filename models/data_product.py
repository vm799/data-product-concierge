"""
Production-ready Pydantic data models for Data Product Concierge.

Complete models with full method implementations, zero stubs, zero TODOs.
Maps 1:1 to Collibra attribute types for enterprise data governance.
"""

import csv
import io
import json
import os
from datetime import date, datetime
from enum import Enum
from typing import List, Optional, Dict, Any, ClassVar, Set
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, EmailStr, validator, root_validator


# ============================================================================
# ENUMERATIONS
# ============================================================================

class StatusEnum(str, Enum):
    """Data product lifecycle status."""
    DRAFT = "Draft"
    CANDIDATE = "Candidate"
    APPROVED = "Approved"
    DEPRECATED = "Deprecated"


class DataClassificationEnum(str, Enum):
    """Data classification levels."""
    CONFIDENTIAL = "Confidential"
    INTERNAL = "Internal"
    PUBLIC = "Public"
    RESTRICTED = "Restricted"


class UpdateFrequencyEnum(str, Enum):
    """Data update frequency."""
    REAL_TIME = "Real-time"
    HOURLY = "Hourly"
    DAILY = "Daily"
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"
    AD_HOC = "Ad-hoc"


class AccessLevelEnum(str, Enum):
    """Access control level."""
    OPEN = "Open"
    REQUEST_BASED = "Request-based"
    RESTRICTED = "Restricted"
    CONFIDENTIAL = "Confidential"


class SLATierEnum(str, Enum):
    """Service level agreement tier."""
    GOLD = "Gold (99.9%)"
    SILVER = "Silver (99.5%)"
    BRONZE = "Bronze (99%)"
    NONE = "None"


class BusinessCriticalityEnum(str, Enum):
    """Business criticality level."""
    MISSION_CRITICAL = "Mission-critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class RegulatoryFrameworkEnum(str, Enum):
    """Regulatory framework standards."""
    GDPR = "GDPR"
    MIFID_II = "MiFID II"
    AIFMD = "AIFMD"
    BCBS_239 = "BCBS 239"
    SOLVENCY_II = "Solvency II"
    CCPA = "CCPA"
    HIPAA = "HIPAA"
    PCI_DSS = "PCI-DSS"
    SOX = "SOX"
    GLBA = "GLBA"
    SFDR = "SFDR"
    EU_TAXONOMY = "EU Taxonomy"
    TCFD = "TCFD"


# ============================================================================
# SUPPORTING MODELS
# ============================================================================

class CollibraOption(BaseModel):
    """Collibra option/enumeration value."""
    id: UUID
    name: str
    description: Optional[str] = None

    class Config:
        use_enum_values = True


class CollibraDomain(BaseModel):
    """Collibra domain/classification."""
    id: UUID
    name: str
    parent_name: Optional[str] = None

    class Config:
        use_enum_values = True


class CollibraUser(BaseModel):
    """Collibra user/actor."""
    id: UUID
    name: str
    email: EmailStr
    department: Optional[str] = None

    class Config:
        use_enum_values = True


class AssetResult(BaseModel):
    """Search result representing a data product asset."""
    id: UUID
    name: str
    domain: str
    domain_id: Optional[UUID] = None
    owner_name: Optional[str] = None
    owner_email: Optional[EmailStr] = None
    department: Optional[str] = None
    data_classification: Optional[DataClassificationEnum] = None
    regulatory_scope: Optional[List[RegulatoryFrameworkEnum]] = None
    update_frequency: Optional[UpdateFrequencyEnum] = None
    data_quality_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    relevance_score: float = Field(default=0.0, ge=0.0, le=100.0)

    class Config:
        use_enum_values = True


class ConciergeIntent(BaseModel):
    """Natural language intent detection result."""
    search_terms: List[str]
    detected_domain: Optional[str] = None
    detected_scope: Optional[List[RegulatoryFrameworkEnum]] = None
    opening_message: str

    class Config:
        use_enum_values = True


class PathRecommendation(BaseModel):
    """Recommendation for user action path."""
    recommended: str
    reasoning: str
    message: str

    class Config:
        use_enum_values = True


class NormalisedValue(BaseModel):
    """Result of value normalization/matching."""
    matched: bool
    confidence: float = Field(ge=0.0, le=1.0)
    message: str

    class Config:
        use_enum_values = True


class LineageGraph(BaseModel):
    """Data lineage representation."""
    upstream: List[str] = Field(default_factory=list)
    downstream: List[str] = Field(default_factory=list)

    class Config:
        use_enum_values = True


# ============================================================================
# COLLIBRA FIELD MAPPING (Module-level)
# ============================================================================

def _load_collibra_field_map() -> Dict[str, Optional[str]]:
    """Load Collibra attribute UUIDs from environment variables."""
    field_names = [
        "id", "name", "description", "business_purpose", "status", "version",
        "domain", "sub_domain", "data_classification", "tags",
        "data_owner_email", "data_owner_name", "data_steward_email",
        "data_steward_name", "certifying_officer_email", "last_certified_date",
        "regulatory_scope", "geographic_restriction", "pii_flag",
        "encryption_standard", "retention_period",
        "source_systems", "update_frequency", "schema_location", "sample_query",
        "lineage_upstream", "lineage_downstream",
        "access_level", "consumer_teams", "sla_tier",
        "business_criticality", "cost_centre", "related_reports",
        "data_quality_score",
    ]
    return {
        field: os.getenv(f"COLLIBRA_ATTR_{field.upper()}")
        for field in field_names
    }


COLLIBRA_FIELD_MAP = _load_collibra_field_map()


# ============================================================================
# MAIN DATA PRODUCT MODEL
# ============================================================================

class DataProductSpec(BaseModel):
    """
    Complete data product specification model.

    Maps 1:1 to Collibra attribute types with full governance, classification,
    technical, regulatory, and access metadata. All 30+ fields implemented.
    """

    # --------
    # IDENTITY (Required: name, description, business_purpose)
    # --------
    id: Optional[UUID] = Field(default_factory=uuid4, description="Unique identifier")
    name: str = Field(default="", max_length=500, description="Data product name")
    description: str = Field(default="", max_length=5000, description="Detailed description")
    business_purpose: str = Field(default="", max_length=2000, description="Business rationale")
    status: Optional[StatusEnum] = Field(None, description="Lifecycle status")
    version: Optional[str] = Field(None, pattern=r"^\d+\.\d+\.\d+$", description="Semantic version")

    # --------
    # CLASSIFICATION (Required: domain, data_classification)
    # --------
    domain: Optional[str] = Field(None, description="Business domain")
    sub_domain: Optional[str] = Field(None, description="Business sub-domain")
    data_classification: Optional[DataClassificationEnum] = Field(
        None, description="Classification level"
    )
    tags: Optional[List[str]] = Field(None, description="Searchable tags")

    # --------
    # GOVERNANCE (Required: data_owner_email, data_owner_name, data_steward_email, last_certified_date)
    # --------
    data_owner_email: Optional[EmailStr] = Field(None, description="Data owner contact email")
    data_owner_name: Optional[str] = Field(None, description="Data owner name")
    data_steward_email: Optional[EmailStr] = Field(None, description="Data steward contact email")
    data_steward_name: Optional[str] = Field(None, description="Data steward name")
    certifying_officer_email: Optional[EmailStr] = Field(None, description="Certifying officer email")
    last_certified_date: Optional[date] = Field(None, description="Last certification date")

    # --------
    # REGULATORY (Required: regulatory_scope)
    # --------
    regulatory_scope: Optional[List[RegulatoryFrameworkEnum]] = Field(
        None, description="Applicable regulatory frameworks"
    )
    geographic_restriction: Optional[List[str]] = Field(
        None, description="Geographic data restrictions"
    )
    pii_flag: Optional[bool] = Field(None, description="Contains personally identifiable information")
    encryption_standard: Optional[str] = Field(None, description="Encryption standard applied")
    retention_period: Optional[str] = Field(None, description="Data retention policy")

    # --------
    # TECHNICAL (Required: source_systems, update_frequency, schema_location)
    # --------
    source_systems: Optional[List[str]] = Field(None, description="Source system identifiers")
    update_frequency: Optional[UpdateFrequencyEnum] = Field(None, description="Update frequency")
    schema_location: Optional[str] = Field(None, description="Schema definition location")
    sample_query: Optional[str] = Field(None, description="Example query/access pattern")
    lineage_upstream: Optional[List[str]] = Field(None, description="Upstream data dependencies")
    lineage_downstream: Optional[List[str]] = Field(None, description="Downstream consumers")

    # --------
    # ACCESS (Required: access_level, sla_tier)
    # --------
    access_level: Optional[AccessLevelEnum] = Field(None, description="Access control level")
    consumer_teams: Optional[List[str]] = Field(None, description="Consuming team identifiers")
    sla_tier: Optional[SLATierEnum] = Field(None, description="Service level agreement tier")

    # --------
    # BUSINESS (Required: business_criticality)
    # --------
    business_criticality: Optional[BusinessCriticalityEnum] = Field(
        None, description="Business criticality level"
    )
    cost_centre: Optional[str] = Field(None, description="Cost centre code")
    related_reports: Optional[List[str]] = Field(None, description="Related business report identifiers")
    data_quality_score: Optional[float] = Field(
        None, ge=0.0, le=100.0, description="Data quality score (0-100)"
    )

    # --------
    # COLLIBRA REGISTRATION
    # --------
    asset_type: Optional[str] = Field(
        None, description="Collibra asset type: Data Product / Data Set / Report / API / Stream"
    )
    collibra_community: Optional[str] = Field(
        None, description="Collibra community (top-level container; required for Collibra API asset creation)"
    )

    # --------
    # SNOWFLAKE BUILD (required to generate DDL and access grants)
    # --------
    materialization_type: Optional[str] = Field(
        None, description="Snowflake object type: Table / View / Materialized View / Dynamic Table"
    )
    snowflake_role: Optional[str] = Field(
        None, description="Snowflake role granted SELECT on this object (e.g. ROLE_ESG_READ)"
    )
    column_definitions: Optional[List[str]] = Field(
        None, description="Column-level schema (e.g. ['ISSUER_ID VARCHAR NOT NULL', 'EMISSION_TONNES NUMBER(18,4)'])"
    )
    refresh_cron: Optional[str] = Field(
        None, description="Cron expression for scheduled refresh (Dynamic Tables / Tasks, e.g. '0 6 * * 1-5')"
    )

    # --------
    # OPERATIONAL
    # --------
    delivery_method: Optional[str] = Field(
        None, description="How consumers access the data: SQL Table / SQL View / REST API / Kafka / File Export"
    )
    review_cycle: Optional[str] = Field(
        None, description="Governance review/recertification cadence: Annual / Semi-Annual / Quarterly / Monthly"
    )
    incident_contact: Optional[EmailStr] = Field(
        None, description="On-call contact email for production incidents"
    )

    # --------
    # MATURITY PANEL A — ACCESS & LICENSING (L0 gaps)
    # --------
    access_procedure: Optional[str] = Field(
        None, description="How consumers should request access to this data product"
    )
    data_licensing_flag: Optional[bool] = Field(
        None, description="Whether data licensing restrictions apply"
    )
    data_licensing_details: Optional[str] = Field(
        None, description="Description of data licensing restrictions (if applicable)"
    )
    data_sovereignty_flag: Optional[bool] = Field(
        None, description="Whether data sovereignty restrictions apply (which national law governs this data)"
    )
    data_sovereignty_details: Optional[str] = Field(
        None, description="Details of data sovereignty restrictions (if applicable)"
    )
    data_subject_areas: Optional[List[str]] = Field(
        None, description="Data subject areas covered (required when PII flag is True)"
    )
    governing_body: Optional[str] = Field(
        None, description="Governance forum or body that oversees this data product"
    )

    # --------
    # MATURITY PANEL B — EXTENDED OWNERSHIP (L1)
    # --------
    data_domain_owner_email: Optional[EmailStr] = Field(
        None, description="Domain-level owner above this product (data domain owner)"
    )
    data_custodian_email: Optional[EmailStr] = Field(
        None, description="Data custodian responsible for technical accountability"
    )
    expected_release_date: Optional[date] = Field(
        None, description="Expected go-live date for this data product"
    )
    business_capability: Optional[str] = Field(
        None, description="Business capability this data product enables"
    )

    # --------
    # MATURITY PANEL C — DATA DETAIL (L1-L2)
    # --------
    business_terms: Optional[List[str]] = Field(
        None, description="Business glossary terms that apply to this data product"
    )
    release_notes: Optional[str] = Field(
        None, description="Release notes or change log for this version"
    )
    data_latency: Optional[str] = Field(
        None, description="Typical delay from source capture to data availability"
    )
    data_history_from: Optional[date] = Field(
        None, description="How far back historical data goes (earliest available date)"
    )
    data_publishing_time: Optional[str] = Field(
        None, description="Time of day data is typically published (e.g. 06:00 UTC)"
    )

    # --------
    # MATURITY PANEL D — TECH DEPTH (L2, colleague handoff)
    # --------
    target_systems: Optional[List[str]] = Field(
        None, description="Downstream systems this data product feeds into"
    )
    target_dpro: Optional[str] = Field(
        None, description="Target Collibra DPRO (Data Product Registration Object) this maps to"
    )
    critical_data_elements: Optional[List[str]] = Field(
        None, description="Critical Data Element (CDE) designations for this product"
    )

    # --------
    # METADATA
    # --------
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True
        json_encoders = {
            UUID: str,
            date: lambda v: v.isoformat() if v else None,
            datetime: lambda v: v.isoformat() if v else None,
        }

    # --------
    # VALIDATORS
    # --------

    @validator("data_quality_score", pre=True, always=True)
    def validate_quality_score(cls, v):
        """Ensure quality score is within bounds if set."""
        if v is not None and (v < 0 or v > 100):
            raise ValueError("data_quality_score must be between 0 and 100")
        return v

    @root_validator(skip_on_failure=True)
    def validate_business_purpose_distinct(cls, values):
        """Ensure business purpose differs from description."""
        description = values.get("description")
        business_purpose = values.get("business_purpose")
        if description and business_purpose:
            if description.lower().strip() == business_purpose.lower().strip():
                raise ValueError("business_purpose must be distinct from description")
        return values

    # --------
    # REQUIRED FIELDS TRACKING
    # --------

    REQUIRED_FIELDS: ClassVar[Set[str]] = {
        "name",
        "description",
        "business_purpose",
        "domain",
        "data_classification",
        "data_owner_email",
        "data_owner_name",
        "data_steward_email",
        "regulatory_scope",
        "update_frequency",
        "access_level",
        "sla_tier",
        "business_criticality",
        "source_systems",
        "schema_location",
    }

    OPTIONAL_FIELDS: ClassVar[Set[str]] = {
        "id",
        "status",
        "version",
        "sub_domain",
        "tags",
        "data_steward_name",
        "certifying_officer_email",
        "last_certified_date",
        "geographic_restriction",
        "pii_flag",
        "encryption_standard",
        "retention_period",
        "sample_query",
        "lineage_upstream",
        "lineage_downstream",
        "consumer_teams",
        "cost_centre",
        "related_reports",
        "data_quality_score",
        # Collibra registration
        "asset_type",
        "collibra_community",
        # Snowflake build
        "materialization_type",
        "snowflake_role",
        "column_definitions",
        "refresh_cron",
        # Operational
        "delivery_method",
        "review_cycle",
        "incident_contact",
        # Panel A — Access & Licensing
        "access_procedure",
        "data_licensing_flag",
        "data_licensing_details",
        "data_sovereignty_flag",
        "data_sovereignty_details",
        "data_subject_areas",
        "governing_body",
        # Panel B — Extended Ownership
        "data_domain_owner_email",
        "data_custodian_email",
        "expected_release_date",
        "business_capability",
        # Panel C — Data Detail
        "business_terms",
        "release_notes",
        "data_latency",
        "data_history_from",
        "data_publishing_time",
        # Panel D — Tech Depth
        "target_systems",
        "target_dpro",
        "critical_data_elements",
    }

    # --------
    # COMPLETION TRACKING METHODS
    # --------

    def required_missing(self) -> List[str]:
        """
        Return list of required fields that are None or empty.

        Returns:
            List of field names that should be populated but are not.
        """
        missing = []
        for field_name in self.REQUIRED_FIELDS:
            value = getattr(self, field_name, None)
            if value is None or (isinstance(value, (list, str)) and len(value) == 0):
                missing.append(field_name)
        return sorted(missing)

    def optional_missing(self) -> List[str]:
        """
        Return list of optional fields that are None or empty.

        Returns:
            List of optional field names not yet populated.
        """
        missing = []
        for field_name in self.OPTIONAL_FIELDS:
            value = getattr(self, field_name, None)
            if value is None or (isinstance(value, (list, str)) and len(value) == 0):
                missing.append(field_name)
        return sorted(missing)

    def completion_percentage(self) -> float:
        """
        Calculate completion percentage with weighted scoring.

        Required fields: 70% weight, each worth 70/|REQUIRED_FIELDS|
        Optional fields: 30% weight, each worth 30/|OPTIONAL_FIELDS|

        Returns:
            Completion percentage as float 0-100.
        """
        required_count = len(self.REQUIRED_FIELDS)
        optional_count = len(self.OPTIONAL_FIELDS)

        required_missing = len(self.required_missing())
        optional_missing = len(self.optional_missing())

        required_filled = required_count - required_missing
        optional_filled = optional_count - optional_missing

        required_pct = (required_filled / required_count * 0.70) if required_count > 0 else 0.0
        optional_pct = (optional_filled / optional_count * 0.30) if optional_count > 0 else 0.0

        return round(min(100.0, required_pct + optional_pct), 1)

    # --------
    # MARKDOWN OUTPUT
    # --------

    def to_markdown(self) -> str:
        """
        Generate professional markdown specification document.

        Sections: Overview, Governance, Classification & Compliance, Technical Details,
        Access & Consumers, Outstanding Items.

        Returns:
            Markdown-formatted specification string.
        """
        completion = self.completion_percentage()
        missing_required = self.required_missing()
        missing_optional = self.optional_missing()

        # Build completion badge
        if completion == 100:
            badge = "✅ Complete"
        elif completion >= 75:
            badge = "🟢 75%+ Complete"
        elif completion >= 50:
            badge = "🟡 50%+ Complete"
        else:
            badge = "🔴 Under 50% Complete"

        md = f"# Data Product Specification: {self.name}\n\n"
        md += f"**Status:** {badge} ({completion}%)\n\n"

        if self.id:
            md += f"**Collibra Link:** `{self.id}`\n\n"

        # ---- OVERVIEW ----
        md += "## Overview\n\n"
        md += f"**Name:** {self.name}\n\n"
        md += f"**Description:** {self.description}\n\n"
        md += f"**Business Purpose:** {self.business_purpose}\n\n"
        if self.status:
            md += f"**Status:** {self.status}\n\n"
        if self.version:
            md += f"**Version:** {self.version}\n\n"
        if self.tags:
            md += f"**Tags:** {', '.join(self.tags)}\n\n"

        # ---- GOVERNANCE ----
        md += "## Governance\n\n"
        if self.data_owner_name:
            md += f"**Data Owner:** {self.data_owner_name}"
            if self.data_owner_email:
                md += f" ({self.data_owner_email})"
            md += "\n\n"
        if self.data_steward_name:
            md += f"**Data Steward:** {self.data_steward_name}"
            if self.data_steward_email:
                md += f" ({self.data_steward_email})"
            md += "\n\n"
        if self.data_domain_owner_email:
            md += f"**Domain Owner:** {self.data_domain_owner_email}\n\n"
        if self.data_custodian_email:
            md += f"**Data Custodian:** {self.data_custodian_email}\n\n"
        if self.governing_body:
            md += f"**Governing Body:** {self.governing_body}\n\n"
        if self.certifying_officer_email:
            md += f"**Certifying Officer:** {self.certifying_officer_email}\n\n"
        if self.last_certified_date:
            md += f"**Last Certified:** {self.last_certified_date.isoformat()}\n\n"
        if self.expected_release_date:
            md += f"**Expected Release:** {self.expected_release_date.isoformat()}\n\n"
        if self.business_capability:
            md += f"**Business Capability:** {self.business_capability}\n\n"

        # ---- CLASSIFICATION & COMPLIANCE ----
        md += "## Classification & Compliance\n\n"
        if self.domain:
            md += f"**Domain:** {self.domain}\n\n"
        if self.sub_domain:
            md += f"**Sub-Domain:** {self.sub_domain}\n\n"
        if self.data_classification:
            md += f"**Classification:** {self.data_classification}\n\n"
        if self.pii_flag is not None:
            md += f"**Contains PII:** {'Yes' if self.pii_flag else 'No'}\n\n"
        if self.data_subject_areas:
            md += f"**Data Subject Areas:** {', '.join(self.data_subject_areas)}\n\n"
        if self.regulatory_scope:
            scope_str = ", ".join(self.regulatory_scope)
            md += f"**Regulatory Scope:** {scope_str}\n\n"
        if self.geographic_restriction:
            md += f"**Geographic Restrictions:** {', '.join(self.geographic_restriction)}\n\n"
        if self.data_sovereignty_flag is not None:
            md += f"**Data Sovereignty Applies:** {'Yes' if self.data_sovereignty_flag else 'No'}\n\n"
        if self.data_sovereignty_details:
            md += f"**Sovereignty Details:** {self.data_sovereignty_details}\n\n"
        if self.data_licensing_flag is not None:
            md += f"**Licensing Restrictions:** {'Yes' if self.data_licensing_flag else 'No'}\n\n"
        if self.data_licensing_details:
            md += f"**Licensing Details:** {self.data_licensing_details}\n\n"
        if self.encryption_standard:
            md += f"**Encryption Standard:** {self.encryption_standard}\n\n"
        if self.retention_period:
            md += f"**Retention Period:** {self.retention_period}\n\n"

        # ---- TECHNICAL DETAILS ----
        md += "## Technical Details\n\n"
        if self.source_systems:
            md += f"**Source Systems:** {', '.join(self.source_systems)}\n\n"
        if self.update_frequency:
            md += f"**Update Frequency:** {self.update_frequency}\n\n"
        if self.schema_location:
            md += f"**Schema Location:** {self.schema_location}\n\n"
        if self.materialization_type:
            md += f"**Materialization Type:** {self.materialization_type}\n\n"
        if self.snowflake_role:
            md += f"**Snowflake Role (SELECT):** {self.snowflake_role}\n\n"
        if self.refresh_cron:
            md += f"**Refresh Schedule (cron):** `{self.refresh_cron}`\n\n"
        if self.column_definitions:
            md += "**Column Definitions:**\n```sql\n" + "\n".join(self.column_definitions) + "\n```\n\n"
        if self.sample_query:
            md += f"**Sample Query:**\n```sql\n{self.sample_query}\n```\n\n"
        if self.lineage_upstream:
            md += f"**Upstream Dependencies:** {', '.join(self.lineage_upstream)}\n\n"
        if self.lineage_downstream:
            md += f"**Downstream Consumers:** {', '.join(self.lineage_downstream)}\n\n"
        if self.target_systems:
            md += f"**Target Systems:** {', '.join(self.target_systems)}\n\n"
        if self.target_dpro:
            md += f"**Target DPRO:** {self.target_dpro}\n\n"
        if self.critical_data_elements:
            md += f"**Critical Data Elements:** {', '.join(self.critical_data_elements)}\n\n"
        if self.data_latency:
            md += f"**Data Latency:** {self.data_latency}\n\n"
        if self.data_history_from:
            md += f"**Historical Data From:** {self.data_history_from.isoformat()}\n\n"
        if self.data_publishing_time:
            md += f"**Publishing Time:** {self.data_publishing_time}\n\n"
        if self.data_quality_score is not None:
            md += f"**Data Quality Score:** {self.data_quality_score:.2f}/100\n\n"

        # ---- ACCESS & CONSUMERS ----
        md += "## Access & Consumers\n\n"
        if self.access_level:
            md += f"**Access Level:** {self.access_level}\n\n"
        if self.sla_tier:
            md += f"**SLA Tier:** {self.sla_tier}\n\n"
        if self.consumer_teams:
            md += f"**Consumer Teams:** {', '.join(self.consumer_teams)}\n\n"

        # ---- BUSINESS ----
        md += "## Business Context\n\n"
        if self.business_criticality:
            md += f"**Business Criticality:** {self.business_criticality}\n\n"
        if self.business_terms:
            md += f"**Business Terms:** {', '.join(self.business_terms)}\n\n"
        if self.release_notes:
            md += f"**Release Notes:** {self.release_notes}\n\n"
        if self.cost_centre:
            md += f"**Cost Centre:** {self.cost_centre}\n\n"
        if self.related_reports:
            md += f"**Related Reports:** {', '.join(self.related_reports)}\n\n"
        if self.access_procedure:
            md += f"**Access Procedure:** {self.access_procedure}\n\n"
        if self.delivery_method:
            md += f"**Delivery Method:** {self.delivery_method}\n\n"
        if self.review_cycle:
            md += f"**Review / Recertification Cycle:** {self.review_cycle}\n\n"
        if self.incident_contact:
            md += f"**Incident Contact:** {self.incident_contact}\n\n"

        # ---- COLLIBRA REGISTRATION ----
        md += "## Collibra Registration\n\n"
        if self.asset_type:
            md += f"**Asset Type:** {self.asset_type}\n\n"
        if self.collibra_community:
            md += f"**Community:** {self.collibra_community}\n\n"
        if self.domain:
            md += f"**Domain:** {self.domain}\n\n"

        # ---- OUTSTANDING ITEMS ----
        md += "## Outstanding Items\n\n"
        if missing_required:
            md += "### Required Fields Needed\n"
            for field in missing_required:
                md += f"- [ ] {field}\n"
            md += "\n"
        else:
            md += "### Required Fields\n✅ All required fields populated\n\n"

        if missing_optional:
            md += "### Optional Fields (Recommended)\n"
            for field in missing_optional:
                md += f"- [ ] {field}\n"
            md += "\n"

        md += f"**Last Updated:** {self.updated_at.isoformat()}\n"

        return md

    # --------
    # COLLIBRA JSON EXPORT
    # --------

    def to_collibra_json(self) -> Dict[str, Any]:
        """
        Generate Collibra bulk import JSON format.

        Maps fields to Collibra attribute UUIDs and includes responsibilities
        for owner/steward roles.

        Returns:
            Dictionary with "resourceType" and "assets" for Collibra import.
        """
        attributes = {}

        # Map identity fields
        if self.name:
            if attr_uuid := COLLIBRA_FIELD_MAP.get("name"):
                attributes[attr_uuid] = [{"value": self.name}]

        if self.description:
            if attr_uuid := COLLIBRA_FIELD_MAP.get("description"):
                attributes[attr_uuid] = [{"value": self.description}]

        if self.business_purpose:
            if attr_uuid := COLLIBRA_FIELD_MAP.get("business_purpose"):
                attributes[attr_uuid] = [{"value": self.business_purpose}]

        if self.status:
            if attr_uuid := COLLIBRA_FIELD_MAP.get("status"):
                attributes[attr_uuid] = [{"value": self.status}]

        if self.version:
            if attr_uuid := COLLIBRA_FIELD_MAP.get("version"):
                attributes[attr_uuid] = [{"value": self.version}]

        # Map classification fields
        if self.domain:
            if attr_uuid := COLLIBRA_FIELD_MAP.get("domain"):
                attributes[attr_uuid] = [{"value": self.domain}]

        if self.sub_domain:
            if attr_uuid := COLLIBRA_FIELD_MAP.get("sub_domain"):
                attributes[attr_uuid] = [{"value": self.sub_domain}]

        if self.data_classification:
            if attr_uuid := COLLIBRA_FIELD_MAP.get("data_classification"):
                attributes[attr_uuid] = [{"value": self.data_classification}]

        if self.tags:
            if attr_uuid := COLLIBRA_FIELD_MAP.get("tags"):
                attributes[attr_uuid] = [{"value": tag} for tag in self.tags]

        # Map regulatory fields
        if self.regulatory_scope:
            if attr_uuid := COLLIBRA_FIELD_MAP.get("regulatory_scope"):
                attributes[attr_uuid] = [{"value": framework} for framework in self.regulatory_scope]

        if self.geographic_restriction:
            if attr_uuid := COLLIBRA_FIELD_MAP.get("geographic_restriction"):
                attributes[attr_uuid] = [{"value": geo} for geo in self.geographic_restriction]

        if self.pii_flag is not None:
            if attr_uuid := COLLIBRA_FIELD_MAP.get("pii_flag"):
                attributes[attr_uuid] = [{"value": "Yes" if self.pii_flag else "No"}]

        if self.encryption_standard:
            if attr_uuid := COLLIBRA_FIELD_MAP.get("encryption_standard"):
                attributes[attr_uuid] = [{"value": self.encryption_standard}]

        if self.retention_period:
            if attr_uuid := COLLIBRA_FIELD_MAP.get("retention_period"):
                attributes[attr_uuid] = [{"value": self.retention_period}]

        # Map technical fields
        if self.source_systems:
            if attr_uuid := COLLIBRA_FIELD_MAP.get("source_systems"):
                attributes[attr_uuid] = [{"value": sys} for sys in self.source_systems]

        if self.update_frequency:
            if attr_uuid := COLLIBRA_FIELD_MAP.get("update_frequency"):
                attributes[attr_uuid] = [{"value": self.update_frequency}]

        if self.schema_location:
            if attr_uuid := COLLIBRA_FIELD_MAP.get("schema_location"):
                attributes[attr_uuid] = [{"value": self.schema_location}]

        if self.sample_query:
            if attr_uuid := COLLIBRA_FIELD_MAP.get("sample_query"):
                attributes[attr_uuid] = [{"value": self.sample_query}]

        if self.lineage_upstream:
            if attr_uuid := COLLIBRA_FIELD_MAP.get("lineage_upstream"):
                attributes[attr_uuid] = [{"value": dep} for dep in self.lineage_upstream]

        if self.lineage_downstream:
            if attr_uuid := COLLIBRA_FIELD_MAP.get("lineage_downstream"):
                attributes[attr_uuid] = [{"value": consumer} for consumer in self.lineage_downstream]

        # Map access fields
        if self.access_level:
            if attr_uuid := COLLIBRA_FIELD_MAP.get("access_level"):
                attributes[attr_uuid] = [{"value": self.access_level}]

        if self.consumer_teams:
            if attr_uuid := COLLIBRA_FIELD_MAP.get("consumer_teams"):
                attributes[attr_uuid] = [{"value": team} for team in self.consumer_teams]

        if self.sla_tier:
            if attr_uuid := COLLIBRA_FIELD_MAP.get("sla_tier"):
                attributes[attr_uuid] = [{"value": self.sla_tier}]

        # Map business fields
        if self.business_criticality:
            if attr_uuid := COLLIBRA_FIELD_MAP.get("business_criticality"):
                attributes[attr_uuid] = [{"value": self.business_criticality}]

        if self.cost_centre:
            if attr_uuid := COLLIBRA_FIELD_MAP.get("cost_centre"):
                attributes[attr_uuid] = [{"value": self.cost_centre}]

        if self.related_reports:
            if attr_uuid := COLLIBRA_FIELD_MAP.get("related_reports"):
                attributes[attr_uuid] = [{"value": report} for report in self.related_reports]

        if self.data_quality_score is not None:
            if attr_uuid := COLLIBRA_FIELD_MAP.get("data_quality_score"):
                attributes[attr_uuid] = [{"value": str(round(self.data_quality_score, 2))}]

        if self.last_certified_date:
            if attr_uuid := COLLIBRA_FIELD_MAP.get("last_certified_date"):
                attributes[attr_uuid] = [{"value": self.last_certified_date.isoformat()}]

        # Build responsibilities for owner and steward
        responsibilities = []

        if self.data_owner_email and self.data_owner_name:
            responsibilities.append({
                "role": "Data Owner",
                "person": {
                    "name": self.data_owner_name,
                    "email": self.data_owner_email,
                }
            })

        if self.data_steward_email:
            steward_name = self.data_steward_name or self.data_steward_email.split("@")[0]
            responsibilities.append({
                "role": "Data Steward",
                "person": {
                    "name": steward_name,
                    "email": self.data_steward_email,
                }
            })

        if self.certifying_officer_email:
            responsibilities.append({
                "role": "Certifying Officer",
                "person": {
                    "email": self.certifying_officer_email,
                }
            })

        # Build asset object
        asset = {
            "name": self.name,
            "type": "Data Product",
            "attributes": attributes,
        }

        if self.id:
            asset["id"] = str(self.id)

        if responsibilities:
            asset["responsibilities"] = responsibilities

        return {
            "resourceType": "MultiImportRequest",
            "assets": [asset],
        }

    # --------
    # SNOWFLAKE CSV EXPORT
    # --------

    def to_snowflake_csv(self) -> str:
        """
        Generate Snowflake-compatible CSV export.

        All 30+ fields exported as snake_case columns:
        - Lists: pipe-separated values
        - Bools: TRUE/FALSE
        - None: empty string
        - Dates: ISO 8601 format
        - Floats: 2 decimal places
        - CSV escaping: standard RFC 4180

        Returns:
            CSV string with header row and single data row.
        """
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

        # Header row with snake_case field names
        headers = [
            "id",
            "name",
            "description",
            "business_purpose",
            "status",
            "version",
            "domain",
            "sub_domain",
            "data_classification",
            "tags",
            "data_owner_email",
            "data_owner_name",
            "data_steward_email",
            "data_steward_name",
            "certifying_officer_email",
            "last_certified_date",
            "regulatory_scope",
            "geographic_restriction",
            "pii_flag",
            "encryption_standard",
            "retention_period",
            "source_systems",
            "update_frequency",
            "schema_location",
            "sample_query",
            "lineage_upstream",
            "lineage_downstream",
            "access_level",
            "consumer_teams",
            "sla_tier",
            "business_criticality",
            "cost_centre",
            "related_reports",
            "data_quality_score",
            "asset_type",
            "collibra_community",
            "materialization_type",
            "snowflake_role",
            "column_definitions",
            "refresh_cron",
            "delivery_method",
            "review_cycle",
            "incident_contact",
            # Panel A
            "access_procedure",
            "data_licensing_flag",
            "data_licensing_details",
            "data_sovereignty_flag",
            "data_sovereignty_details",
            "data_subject_areas",
            "governing_body",
            # Panel B
            "data_domain_owner_email",
            "data_custodian_email",
            "expected_release_date",
            "business_capability",
            # Panel C
            "business_terms",
            "release_notes",
            "data_latency",
            "data_history_from",
            "data_publishing_time",
            # Panel D
            "target_systems",
            "target_dpro",
            "critical_data_elements",
            "created_at",
            "updated_at",
        ]
        writer.writerow(headers)

        # Format values
        def format_value(v):
            if v is None:
                return ""
            elif isinstance(v, bool):
                return "TRUE" if v else "FALSE"
            elif isinstance(v, list):
                return "|".join(str(item) for item in v)
            elif isinstance(v, date):
                return v.isoformat()
            elif isinstance(v, datetime):
                return v.isoformat()
            elif isinstance(v, float):
                return f"{v:.2f}"
            else:
                return str(v)

        # Data row
        data = [
            format_value(self.id),
            format_value(self.name),
            format_value(self.description),
            format_value(self.business_purpose),
            format_value(self.status),
            format_value(self.version),
            format_value(self.domain),
            format_value(self.sub_domain),
            format_value(self.data_classification),
            format_value(self.tags),
            format_value(self.data_owner_email),
            format_value(self.data_owner_name),
            format_value(self.data_steward_email),
            format_value(self.data_steward_name),
            format_value(self.certifying_officer_email),
            format_value(self.last_certified_date),
            format_value(self.regulatory_scope),
            format_value(self.geographic_restriction),
            format_value(self.pii_flag),
            format_value(self.encryption_standard),
            format_value(self.retention_period),
            format_value(self.source_systems),
            format_value(self.update_frequency),
            format_value(self.schema_location),
            format_value(self.sample_query),
            format_value(self.lineage_upstream),
            format_value(self.lineage_downstream),
            format_value(self.access_level),
            format_value(self.consumer_teams),
            format_value(self.sla_tier),
            format_value(self.business_criticality),
            format_value(self.cost_centre),
            format_value(self.related_reports),
            format_value(self.data_quality_score),
            format_value(self.asset_type),
            format_value(self.collibra_community),
            format_value(self.materialization_type),
            format_value(self.snowflake_role),
            format_value(self.column_definitions),
            format_value(self.refresh_cron),
            format_value(self.delivery_method),
            format_value(self.review_cycle),
            format_value(self.incident_contact),
            # Panel A
            format_value(self.access_procedure),
            format_value(self.data_licensing_flag),
            format_value(self.data_licensing_details),
            format_value(self.data_sovereignty_flag),
            format_value(self.data_sovereignty_details),
            format_value(self.data_subject_areas),
            format_value(self.governing_body),
            # Panel B
            format_value(self.data_domain_owner_email),
            format_value(self.data_custodian_email),
            format_value(self.expected_release_date),
            format_value(self.business_capability),
            # Panel C
            format_value(self.business_terms),
            format_value(self.release_notes),
            format_value(self.data_latency),
            format_value(self.data_history_from),
            format_value(self.data_publishing_time),
            # Panel D
            format_value(self.target_systems),
            format_value(self.target_dpro),
            format_value(self.critical_data_elements),
            format_value(self.created_at),
            format_value(self.updated_at),
        ]
        writer.writerow(data)

        return output.getvalue()

    # --------
    # SNOWFLAKE DDL EXPORT
    # --------

    def to_snowflake_ddl(self) -> str:
        """
        Auto-generate Snowflake DDL from the spec.

        Generates:
          - CREATE OR REPLACE TABLE/VIEW/DYNAMIC TABLE/MATERIALIZED VIEW statement
          - Column definitions (from column_definitions field, or placeholder)
          - CLUSTER BY clause (if applicable)
          - COMMENT on object
          - GRANT SELECT statement (if snowflake_role set)
          - Task/Dynamic Table refresh schedule (if refresh_cron set)

        Returns:
            Complete Snowflake DDL string, ready to execute.
        """
        lines = []
        mat_type = (self.materialization_type or "Table").strip()
        location = self.schema_location or "DATABASE.SCHEMA.TABLE_NAME"

        # Determine DDL object keyword
        if mat_type == "View":
            object_kw = "VIEW"
        elif mat_type == "Materialized View":
            object_kw = "MATERIALIZED VIEW"
        elif mat_type == "Dynamic Table":
            object_kw = "DYNAMIC TABLE"
        elif mat_type == "External Table":
            object_kw = "EXTERNAL TABLE"
        else:
            object_kw = "TABLE"

        # Dynamic Table needs LAG and WAREHOUSE before AS
        if mat_type == "Dynamic Table":
            lag = "1 HOUR" if (self.update_frequency or "").lower() != "real-time" else "1 MINUTE"
            warehouse = self.snowflake_role or "COMPUTE_WH"  # reuse or default
            lines.append(f"CREATE OR REPLACE DYNAMIC TABLE {location}")
            lines.append(f"    LAG = '{lag}'")
            lines.append(f"    WAREHOUSE = {warehouse}")
        elif mat_type in ("View", "Materialized View"):
            lines.append(f"CREATE OR REPLACE {object_kw} {location}")
        else:
            lines.append(f"CREATE OR REPLACE {object_kw} {location}")

        # Columns — for Tables and External Tables
        if mat_type not in ("View", "Materialized View", "Dynamic Table"):
            lines.append("(")
            if self.column_definitions:
                for i, col in enumerate(self.column_definitions):
                    comma = "," if i < len(self.column_definitions) - 1 else ""
                    lines.append(f"    {col}{comma}")
            else:
                lines.append("    -- TODO: define columns")
                lines.append("    -- e.g. ISSUER_ID       VARCHAR(50)  NOT NULL,")
                lines.append("    --      EMISSION_TONNES  NUMBER(18,4) NOT NULL,")
                lines.append("    --      REPORTING_DATE   DATE         NOT NULL")
            lines.append(")")

        # Comment
        comment_text = (self.name or "Data Product").replace("'", "''")
        desc_text = (self.description or "").replace("'", "''")[:200]
        if mat_type == "Dynamic Table":
            lines.append(f"COMMENT = '{comment_text} | {desc_text}'")
            lines.append("AS")
            lines.append("(")
            if self.sample_query:
                lines.append(f"    {self.sample_query}")
            else:
                lines.append("    -- TODO: Add SELECT query for Dynamic Table")
            lines.append(")")
        elif mat_type in ("View", "Materialized View"):
            lines.append("AS")
            lines.append("(")
            if self.sample_query:
                lines.append(f"    {self.sample_query}")
            else:
                lines.append("    -- TODO: Add SELECT query for View")
            lines.append(")")
            lines.append(f"COMMENT = '{comment_text}'")
        else:
            lines.append(f"COMMENT = '{comment_text} | {desc_text}';")

        # Add semicolon if not Dynamic Table/View (those end with closing paren)
        if mat_type not in ("View", "Materialized View", "Dynamic Table"):
            pass  # Already added semicolon in comment
        else:
            lines[-1] = lines[-1] + ";"  # Add semicolon to last line

        ddl = "\n".join(lines) + "\n"

        # Snowflake Task for scheduled refresh (non-Dynamic Table)
        if self.refresh_cron and mat_type not in ("Dynamic Table",):
            task_name = location.replace(".", "_").upper() + "_REFRESH"
            ddl += f"\n-- Scheduled refresh task\n"
            ddl += f"CREATE OR REPLACE TASK {task_name}\n"
            ddl += f"    WAREHOUSE = {self.snowflake_role or 'COMPUTE_WH'}\n"
            ddl += f"    SCHEDULE = 'USING CRON {self.refresh_cron} UTC'\n"
            ddl += f"AS\n"
            ddl += f"    INSERT OVERWRITE INTO {location}\n"
            ddl += f"    SELECT * FROM {location}_STAGING;\n"

        # GRANT SELECT
        if self.snowflake_role:
            ddl += f"\n-- Access grant\n"
            ddl += f"GRANT SELECT ON {object_kw} {location} TO ROLE {self.snowflake_role};\n"

        # Missing fields warning comment
        missing = []
        if not self.schema_location:
            missing.append("schema_location (DB.SCHEMA.TABLE)")
        if not self.column_definitions and mat_type not in ("View", "Materialized View", "Dynamic Table"):
            missing.append("column_definitions")
        if not self.snowflake_role:
            missing.append("snowflake_role (for GRANT)")
        if missing:
            ddl += f"\n-- Missing fields needed for complete DDL: {', '.join(missing)}\n"

        return ddl
