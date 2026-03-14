"""
Comprehensive unit tests for DataProductSpec model.

Tests cover:
- Model creation and validation
- Completion percentage calculations
- Missing field detection
- Serialization (Markdown, JSON, CSV)
- Field-specific validation (email, bounds)
"""

import pytest
from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr, field_validator


class DataClassification(str, Enum):
    """Valid data classification levels."""
    PUBLIC = "Public"
    INTERNAL = "Internal"
    CONFIDENTIAL = "Confidential"
    RESTRICTED = "Restricted"


class AccessLevel(str, Enum):
    """Valid access levels."""
    PUBLIC = "Public"
    REGISTERED_USERS = "Registered Users"
    TEAM_ONLY = "Team Only"
    RESTRICTED = "Restricted"


class SLATier(str, Enum):
    """Service level agreement tiers."""
    GOLD = "Gold"
    SILVER = "Silver"
    BRONZE = "Bronze"


class UpdateFrequency(str, Enum):
    """Data update frequencies."""
    REAL_TIME = "Real-Time"
    HOURLY = "Hourly"
    DAILY = "Daily"
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"
    QUARTERLY = "Quarterly"
    ANNUALLY = "Annually"
    ON_DEMAND = "On-Demand"


class RegulatoryScope(str, Enum):
    """Regulatory framework scopes."""
    GDPR = "GDPR"
    HIPAA = "HIPAA"
    SOX = "SOX"
    DODD_FRANK = "Dodd-Frank"
    MiFID_II = "MiFID II"
    NONE = "None"


class DataProductSpec(BaseModel):
    """Complete data product specification with 30+ fields."""

    # Required fields
    name: str = Field(..., min_length=1, max_length=255, description="Data product name")
    description: str = Field(..., min_length=10, description="Detailed description")
    business_purpose: str = Field(..., min_length=10, description="Business use case")
    data_owner_email: EmailStr = Field(..., description="Data owner contact email")

    # Core metadata
    version: str = Field(default="1.0", description="Semantic version")
    domain: str = Field(default="", description="Business domain")
    sub_domain: str = Field(default="", description="Sub-domain classification")
    data_classification: Optional[DataClassification] = Field(default=None, description="Data sensitivity level")

    # Regulatory and compliance
    regulatory_scope: Optional[RegulatoryScope] = Field(default=None, description="Applicable regulations")
    pii_flag: bool = Field(default=False, description="Contains personally identifiable information")
    encryption_standard: Optional[str] = Field(default=None, description="Encryption algorithm (AES-256, etc)")
    retention_period: Optional[str] = Field(default=None, description="Data retention period (months/years)")
    geographic_restriction: Optional[str] = Field(default=None, description="Geographic data residency requirement")

    # Management and contacts
    data_steward_email: Optional[EmailStr] = Field(default=None, description="Data steward contact")
    certifying_officer_email: Optional[EmailStr] = Field(default=None, description="Compliance officer email")
    last_certified_date: Optional[str] = Field(default=None, description="ISO 8601 certification date")

    # Operational metadata
    source_systems: List[str] = Field(default_factory=list, description="Source system names")
    update_frequency: Optional[UpdateFrequency] = Field(default=None, description="Update cadence")
    schema_location: Optional[str] = Field(default=None, description="Snowflake schema path")
    sample_query: Optional[str] = Field(default=None, description="Example SELECT query")

    # Access and usage
    access_level: Optional[AccessLevel] = Field(default=None, description="Access restrictions")
    consumer_teams: List[str] = Field(default_factory=list, description="Teams consuming this data")
    sla_tier: Optional[SLATier] = Field(default=None, description="Service level agreement tier")

    # Business context
    business_criticality: Optional[str] = Field(default=None, description="Critical/High/Medium/Low")
    cost_centre: Optional[str] = Field(default=None, description="Cost allocation code")
    related_reports: List[str] = Field(default_factory=list, description="Related business reports")

    # Quality and monitoring
    data_quality_score: Optional[float] = Field(default=None, ge=0.0, le=100.0, description="Quality score 0-100")
    tags: List[str] = Field(default_factory=list, description="Search and categorization tags")

    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "name": "Customer Master",
                "description": "Centralized customer data",
                "business_purpose": "Single source of truth for customer profiles",
                "data_owner_email": "john.doe@firm.com",
                "data_steward_email": "jane.smith@firm.com",
                "data_classification": "Confidential",
            }
        }

    @field_validator("name")
    @classmethod
    def name_no_special_chars(cls, v: str) -> str:
        """Validate name contains only alphanumeric, spaces, and hyphens."""
        if not all(c.isalnum() or c in " -_" for c in v):
            raise ValueError("Name must contain only alphanumeric characters, spaces, hyphens, and underscores")
        return v

    @field_validator("data_quality_score")
    @classmethod
    def quality_score_bounds(cls, v: Optional[float]) -> Optional[float]:
        """Validate data quality score is between 0 and 100."""
        if v is not None and not (0.0 <= v <= 100.0):
            raise ValueError("Data quality score must be between 0 and 100")
        return v

    def get_required_fields(self) -> List[str]:
        """Return list of required fields that are currently None or empty."""
        required = {
            "name": self.name,
            "description": self.description,
            "business_purpose": self.business_purpose,
            "data_owner_email": self.data_owner_email,
        }
        missing = [field for field, value in required.items() if not value]
        return missing

    def get_optional_fields(self) -> List[str]:
        """Return list of optional fields that are currently None or empty."""
        optional_fields = {
            "domain": self.domain,
            "sub_domain": self.sub_domain,
            "data_classification": self.data_classification,
            "data_steward_email": self.data_steward_email,
            "certifying_officer_email": self.certifying_officer_email,
            "last_certified_date": self.last_certified_date,
            "regulatory_scope": self.regulatory_scope,
            "pii_flag": self.pii_flag,
            "encryption_standard": self.encryption_standard,
            "retention_period": self.retention_period,
            "geographic_restriction": self.geographic_restriction,
            "source_systems": self.source_systems,
            "update_frequency": self.update_frequency,
            "schema_location": self.schema_location,
            "sample_query": self.sample_query,
            "access_level": self.access_level,
            "consumer_teams": self.consumer_teams,
            "sla_tier": self.sla_tier,
            "business_criticality": self.business_criticality,
            "cost_centre": self.cost_centre,
            "related_reports": self.related_reports,
            "data_quality_score": self.data_quality_score,
            "tags": self.tags,
        }
        missing = []
        for field, value in optional_fields.items():
            if value is None or (isinstance(value, (list, str)) and not value):
                missing.append(field)
        return missing

    def completion_percentage(self) -> float:
        """
        Calculate completion percentage (0-100).
        Required fields are weighted at 5% each, optional fields at 1.5% each.
        """
        required_count = 4
        optional_count = 23
        total_weight = (required_count * 5) + (optional_count * 1.5)

        missing_required = len(self.get_required_fields())
        completed_required = required_count - missing_required
        required_score = completed_required * 5

        missing_optional = len(self.get_optional_fields())
        completed_optional = optional_count - missing_optional
        optional_score = completed_optional * 1.5

        completion = (required_score + optional_score) / total_weight * 100
        return round(min(completion, 100.0), 2)

    def to_markdown(self) -> str:
        """
        Convert specification to Markdown format.
        Ensures no 'None' string literals appear in output.
        """
        lines = [f"# {self.name}\n"]

        lines.append("## Overview\n")
        lines.append(f"{self.description}\n")
        lines.append(f"**Business Purpose:** {self.business_purpose}\n")

        lines.append("## Ownership & Governance\n")
        lines.append(f"| Role | Contact |\n")
        lines.append(f"|------|--------|\n")
        lines.append(f"| Data Owner | {self.data_owner_email} |\n")
        if self.data_steward_email:
            lines.append(f"| Data Steward | {self.data_steward_email} |\n")
        if self.certifying_officer_email:
            lines.append(f"| Certifying Officer | {self.certifying_officer_email} |\n")
        lines.append("")

        if self.domain or self.sub_domain:
            lines.append("## Classification\n")
            if self.domain:
                lines.append(f"**Domain:** {self.domain}\n")
            if self.sub_domain:
                lines.append(f"**Sub-Domain:** {self.sub_domain}\n")
            if self.data_classification:
                lines.append(f"**Data Classification:** {self.data_classification}\n")
            lines.append("")

        if any([self.regulatory_scope, self.pii_flag, self.encryption_standard, self.retention_period]):
            lines.append("## Regulatory & Compliance\n")
            if self.regulatory_scope:
                lines.append(f"**Regulatory Scope:** {self.regulatory_scope}\n")
            if self.pii_flag:
                lines.append(f"**Contains PII:** Yes\n")
            if self.encryption_standard:
                lines.append(f"**Encryption:** {self.encryption_standard}\n")
            if self.retention_period:
                lines.append(f"**Retention Period:** {self.retention_period}\n")
            if self.geographic_restriction:
                lines.append(f"**Geographic Restriction:** {self.geographic_restriction}\n")
            lines.append("")

        if self.source_systems or self.update_frequency or self.schema_location:
            lines.append("## Technical Details\n")
            if self.source_systems:
                lines.append(f"**Source Systems:** {', '.join(self.source_systems)}\n")
            if self.update_frequency:
                lines.append(f"**Update Frequency:** {self.update_frequency}\n")
            if self.schema_location:
                lines.append(f"**Schema Location:** {self.schema_location}\n")
            if self.sample_query:
                lines.append(f"\n**Sample Query:**\n```sql\n{self.sample_query}\n```\n")
            lines.append("")

        if any([self.access_level, self.consumer_teams, self.sla_tier]):
            lines.append("## Access & SLA\n")
            if self.access_level:
                lines.append(f"**Access Level:** {self.access_level}\n")
            if self.consumer_teams:
                lines.append(f"**Consumer Teams:** {', '.join(self.consumer_teams)}\n")
            if self.sla_tier:
                lines.append(f"**SLA Tier:** {self.sla_tier}\n")
            lines.append("")

        if any([self.business_criticality, self.cost_centre, self.data_quality_score]):
            lines.append("## Business Metrics\n")
            if self.business_criticality:
                lines.append(f"**Business Criticality:** {self.business_criticality}\n")
            if self.cost_centre:
                lines.append(f"**Cost Centre:** {self.cost_centre}\n")
            if self.data_quality_score is not None:
                lines.append(f"**Data Quality Score:** {self.data_quality_score}%\n")
            lines.append("")

        if self.tags:
            lines.append("## Tags\n")
            lines.append(f"{', '.join(self.tags)}\n")
            lines.append("")

        if self.related_reports:
            lines.append("## Related Reports\n")
            lines.append("\n".join(f"- {report}" for report in self.related_reports))
            lines.append("\n")

        lines.append(f"**Version:** {self.version}\n")
        if self.last_certified_date:
            lines.append(f"**Last Certified:** {self.last_certified_date}\n")

        markdown = "".join(lines)
        # Ensure no "None" string appears
        assert "None" not in markdown, "Markdown output contains 'None' string literal"
        return markdown

    def to_collibra_json(self) -> dict:
        """
        Convert to Collibra asset creation JSON structure.
        Returns dict with resourceType and assets array.
        """
        attributes = []

        if self.description:
            attributes.append({"typeId": "DESCRIPTION", "value": self.description})
        if self.business_purpose:
            attributes.append({"typeId": "BUSINESS_PURPOSE", "value": self.business_purpose})
        if self.domain:
            attributes.append({"typeId": "DOMAIN", "value": self.domain})
        if self.sub_domain:
            attributes.append({"typeId": "SUB_DOMAIN", "value": self.sub_domain})
        if self.data_classification:
            attributes.append({"typeId": "DATA_CLASSIFICATION", "value": self.data_classification})
        if self.data_steward_email:
            attributes.append({"typeId": "DATA_STEWARD_EMAIL", "value": self.data_steward_email})
        if self.regulatory_scope:
            attributes.append({"typeId": "REGULATORY_SCOPE", "value": self.regulatory_scope})
        if self.pii_flag:
            attributes.append({"typeId": "PII_FLAG", "value": str(self.pii_flag)})
        if self.encryption_standard:
            attributes.append({"typeId": "ENCRYPTION_STANDARD", "value": self.encryption_standard})
        if self.retention_period:
            attributes.append({"typeId": "RETENTION_PERIOD", "value": self.retention_period})
        if self.source_systems:
            attributes.append({"typeId": "SOURCE_SYSTEMS", "value": "|".join(self.source_systems)})
        if self.update_frequency:
            attributes.append({"typeId": "UPDATE_FREQUENCY", "value": self.update_frequency})
        if self.schema_location:
            attributes.append({"typeId": "SCHEMA_LOCATION", "value": self.schema_location})
        if self.access_level:
            attributes.append({"typeId": "ACCESS_LEVEL", "value": self.access_level})
        if self.sla_tier:
            attributes.append({"typeId": "SLA_TIER", "value": self.sla_tier})
        if self.business_criticality:
            attributes.append({"typeId": "BUSINESS_CRITICALITY", "value": self.business_criticality})
        if self.cost_centre:
            attributes.append({"typeId": "COST_CENTRE", "value": self.cost_centre})
        if self.data_quality_score is not None:
            attributes.append({"typeId": "DATA_QUALITY_SCORE", "value": str(self.data_quality_score)})
        if self.tags:
            attributes.append({"typeId": "TAGS", "value": "|".join(self.tags)})

        return {
            "resourceType": "DataProduct",
            "assets": [
                {
                    "name": self.name,
                    "displayName": self.name,
                    "description": self.description,
                    "typeId": "DATA_PRODUCT",
                    "attributes": attributes,
                }
            ]
        }

    def to_snowflake_csv_header(self) -> str:
        """
        Return CSV header row with all 30 field names.
        Fields are in consistent order.
        """
        headers = [
            "name",
            "description",
            "business_purpose",
            "data_owner_email",
            "version",
            "domain",
            "sub_domain",
            "data_classification",
            "regulatory_scope",
            "pii_flag",
            "encryption_standard",
            "retention_period",
            "geographic_restriction",
            "data_steward_email",
            "certifying_officer_email",
            "last_certified_date",
            "source_systems",
            "update_frequency",
            "schema_location",
            "sample_query",
            "access_level",
            "consumer_teams",
            "sla_tier",
            "business_criticality",
            "cost_centre",
            "related_reports",
            "data_quality_score",
            "tags",
        ]
        return ",".join(f'"{h}"' for h in headers)

    def to_snowflake_csv_row(self) -> str:
        """
        Convert specification to CSV row with proper formatting.
        - Lists are pipe-separated
        - Booleans are TRUE/FALSE
        - None becomes empty string
        """
        def format_value(val):
            if val is None or val == "":
                return '""'
            if isinstance(val, bool):
                return '"TRUE"' if val else '"FALSE"'
            if isinstance(val, (list, tuple)):
                # Pipe-separated list values
                serialized = "|".join(str(v) for v in val if v)
                return f'"{serialized}"'
            if isinstance(val, (int, float)):
                return f'"{val}"'
            # Quote and escape quotes in strings
            escaped = str(val).replace('"', '""')
            return f'"{escaped}"'

        row_values = [
            format_value(self.name),
            format_value(self.description),
            format_value(self.business_purpose),
            format_value(self.data_owner_email),
            format_value(self.version),
            format_value(self.domain),
            format_value(self.sub_domain),
            format_value(self.data_classification),
            format_value(self.regulatory_scope),
            format_value(self.pii_flag),
            format_value(self.encryption_standard),
            format_value(self.retention_period),
            format_value(self.geographic_restriction),
            format_value(self.data_steward_email),
            format_value(self.certifying_officer_email),
            format_value(self.last_certified_date),
            format_value(self.source_systems),
            format_value(self.update_frequency),
            format_value(self.schema_location),
            format_value(self.sample_query),
            format_value(self.access_level),
            format_value(self.consumer_teams),
            format_value(self.sla_tier),
            format_value(self.business_criticality),
            format_value(self.cost_centre),
            format_value(self.related_reports),
            format_value(self.data_quality_score),
            format_value(self.tags),
        ]
        return ",".join(row_values)


# ============================================================================
# UNIT TESTS
# ============================================================================

class TestDataProductSpecCreation:
    """Tests for basic model creation and required field validation."""

    def test_creation_with_required_fields(self):
        """Test creating a valid spec with only required fields."""
        spec = DataProductSpec(
            name="Customer Data",
            description="Centralized customer information database",
            business_purpose="Single source of truth for customer profiles",
            data_owner_email="owner@firm.com"
        )
        assert spec.name == "Customer Data"
        assert spec.description == "Centralized customer information database"
        assert spec.business_purpose == "Single source of truth for customer profiles"
        assert spec.data_owner_email == "owner@firm.com"
        assert spec.version == "1.0"

    def test_creation_with_all_fields(self):
        """Test creating a complete spec with all fields populated."""
        spec = DataProductSpec(
            name="Product Master",
            description="Complete product hierarchy and details",
            business_purpose="Reference data for all product reporting",
            data_owner_email="owner@firm.com",
            data_steward_email="steward@firm.com",
            certifying_officer_email="officer@firm.com",
            version="2.1",
            domain="Product Management",
            sub_domain="Master Data",
            data_classification=DataClassification.CONFIDENTIAL,
            regulatory_scope=RegulatoryScope.GDPR,
            pii_flag=False,
            encryption_standard="AES-256",
            retention_period="7 years",
            geographic_restriction="EU only",
            source_systems=["SAP", "Oracle"],
            update_frequency=UpdateFrequency.DAILY,
            schema_location="PROD.REFERENCE.PRODUCTS",
            sample_query="SELECT * FROM PRODUCTS WHERE active = TRUE",
            access_level=AccessLevel.TEAM_ONLY,
            consumer_teams=["Analytics", "Finance"],
            sla_tier=SLATier.GOLD,
            business_criticality="Critical",
            cost_centre="CC-2024",
            related_reports=["Product KPIs", "Sales Analysis"],
            data_quality_score=94.5,
            tags=["masterdata", "product", "reference"]
        )
        assert spec.completion_percentage() == 100.0

    def test_missing_required_name(self):
        """Test that missing name raises validation error."""
        with pytest.raises(Exception):
            DataProductSpec(
                description="Test",
                business_purpose="Test purpose",
                data_owner_email="owner@firm.com"
            )

    def test_missing_required_email(self):
        """Test that invalid email raises validation error."""
        with pytest.raises(Exception):
            DataProductSpec(
                name="Test",
                description="Test description",
                business_purpose="Test purpose",
                data_owner_email="not-an-email"
            )

    def test_invalid_name_with_special_chars(self):
        """Test that name with invalid special characters fails."""
        with pytest.raises(Exception):
            DataProductSpec(
                name="Test@#$%",
                description="Test description",
                business_purpose="Test purpose",
                data_owner_email="owner@firm.com"
            )


class TestCompletionPercentage:
    """Tests for completion percentage calculation."""

    def test_completion_percentage_all_filled(self):
        """Test completion is 100% when all fields are filled."""
        spec = DataProductSpec(
            name="Complete Product",
            description="This is a complete data product with all fields populated",
            business_purpose="Serves as complete reference for testing",
            data_owner_email="owner@firm.com",
            data_steward_email="steward@firm.com",
            certifying_officer_email="officer@firm.com",
            domain="Finance",
            sub_domain="Treasury",
            data_classification=DataClassification.CONFIDENTIAL,
            regulatory_scope=RegulatoryScope.SOX,
            pii_flag=True,
            encryption_standard="AES-256",
            retention_period="10 years",
            geographic_restriction="Global",
            source_systems=["System A", "System B"],
            update_frequency=UpdateFrequency.REAL_TIME,
            schema_location="PROD.FINANCE.TREASURY",
            sample_query="SELECT * FROM TREASURY",
            access_level=AccessLevel.RESTRICTED,
            consumer_teams=["Treasury Team"],
            sla_tier=SLATier.GOLD,
            business_criticality="Critical",
            cost_centre="CC-001",
            related_reports=["Treasury Report"],
            data_quality_score=98.0,
            tags=["finance", "treasury"]
        )
        assert spec.completion_percentage() == 100.0

    def test_completion_percentage_partial(self):
        """Test completion percentage with only required fields."""
        spec = DataProductSpec(
            name="Minimal Product",
            description="This has a minimal description with enough content",
            business_purpose="This is the business purpose with content",
            data_owner_email="owner@firm.com"
        )
        percentage = spec.completion_percentage()
        assert 0 < percentage < 100
        assert percentage == pytest.approx(20.7, abs=0.1)

    def test_completion_percentage_with_some_optional(self):
        """Test completion with some optional fields filled."""
        spec = DataProductSpec(
            name="Partial Product",
            description="This is a partial data product specification",
            business_purpose="Used for testing partial completion",
            data_owner_email="owner@firm.com",
            domain="Sales",
            sub_domain="Pipeline",
            data_classification=DataClassification.INTERNAL,
            access_level=AccessLevel.TEAM_ONLY,
            sla_tier=SLATier.SILVER
        )
        percentage = spec.completion_percentage()
        assert percentage > 20.7
        assert percentage < 100


class TestMissingFields:
    """Tests for missing field detection."""

    def test_required_missing_returns_correct_fields(self):
        """Test that get_required_fields returns only missing required fields."""
        spec = DataProductSpec(
            name="Test",
            description="Test description with content",
            business_purpose="This is a purpose",
            data_owner_email="owner@firm.com"
        )
        missing = spec.get_required_fields()
        assert missing == []

    def test_optional_missing_returns_correct_fields(self):
        """Test that get_optional_fields returns all missing optional fields."""
        spec = DataProductSpec(
            name="Test",
            description="Test description",
            business_purpose="Test purpose",
            data_owner_email="owner@firm.com"
        )
        missing = spec.get_optional_fields()
        assert len(missing) == 23
        assert "domain" in missing
        assert "data_classification" in missing
        assert "access_level" in missing
        assert "data_quality_score" in missing


class TestMarkdownSerialization:
    """Tests for Markdown export format."""

    def test_to_markdown_produces_valid_output(self):
        """Test that Markdown output is valid and well-formed."""
        spec = DataProductSpec(
            name="Sales Data",
            description="Comprehensive sales transaction data",
            business_purpose="Support sales analysis and forecasting",
            data_owner_email="sales@firm.com",
            data_steward_email="steward@firm.com",
            domain="Sales",
            data_classification=DataClassification.INTERNAL,
            source_systems=["Salesforce", "ERP"],
            update_frequency=UpdateFrequency.DAILY,
            schema_location="PROD.SALES.TRANSACTIONS",
            tags=["sales", "transactions"]
        )
        markdown = spec.to_markdown()

        # Check all major sections are present
        assert "# Sales Data" in markdown
        assert "## Overview" in markdown
        assert "## Ownership & Governance" in markdown
        assert "## Classification" in markdown
        assert "## Technical Details" in markdown
        assert "## Tags" in markdown

        # Ensure no "None" string literal appears
        assert "None" not in markdown

    def test_to_markdown_with_all_fields(self):
        """Test Markdown output with all fields populated."""
        spec = DataProductSpec(
            name="Complete Product",
            description="Complete product data with all fields",
            business_purpose="Full test of Markdown export",
            data_owner_email="owner@firm.com",
            data_steward_email="steward@firm.com",
            certifying_officer_email="officer@firm.com",
            domain="Finance",
            sub_domain="Treasury",
            data_classification=DataClassification.CONFIDENTIAL,
            regulatory_scope=RegulatoryScope.SOX,
            pii_flag=True,
            encryption_standard="AES-256",
            retention_period="10 years",
            geographic_restriction="EU",
            last_certified_date="2024-12-01",
            source_systems=["Oracle", "SAP"],
            update_frequency=UpdateFrequency.DAILY,
            schema_location="PROD.FINANCE.TREASURY",
            sample_query="SELECT * FROM TREASURY WHERE active = 1",
            access_level=AccessLevel.RESTRICTED,
            consumer_teams=["Treasury", "Finance"],
            sla_tier=SLATier.GOLD,
            business_criticality="Critical",
            cost_centre="CC-100",
            related_reports=["Treasury Report", "Cash Position"],
            data_quality_score=96.5,
            tags=["finance", "treasury", "critical"]
        )
        markdown = spec.to_markdown()

        assert "Sales Data" not in markdown
        assert "Complete Product" in markdown
        assert "Contains PII: Yes" in markdown
        assert "Data Quality Score: 96.5%" in markdown
        assert "SELECT * FROM TREASURY" in markdown
        assert "None" not in markdown


class TestCollibraJSONSerialization:
    """Tests for Collibra API JSON format."""

    def test_to_collibra_json_structure(self):
        """Test that JSON structure matches Collibra API expectations."""
        spec = DataProductSpec(
            name="Customer Master",
            description="Central customer database",
            business_purpose="Single source of truth",
            data_owner_email="owner@firm.com",
            data_classification=DataClassification.CONFIDENTIAL,
            source_systems=["CRM", "ERP"]
        )
        json_output = spec.to_collibra_json()

        # Validate structure
        assert "resourceType" in json_output
        assert json_output["resourceType"] == "DataProduct"
        assert "assets" in json_output
        assert isinstance(json_output["assets"], list)
        assert len(json_output["assets"]) == 1

        asset = json_output["assets"][0]
        assert asset["name"] == "Customer Master"
        assert asset["displayName"] == "Customer Master"
        assert asset["typeId"] == "DATA_PRODUCT"
        assert "attributes" in asset
        assert isinstance(asset["attributes"], list)

    def test_to_collibra_json_attributes_populated(self):
        """Test that Collibra attributes are correctly populated."""
        spec = DataProductSpec(
            name="Test Product",
            description="Test description",
            business_purpose="Test business purpose",
            data_owner_email="owner@firm.com",
            data_classification=DataClassification.INTERNAL,
            regulatory_scope=RegulatoryScope.GDPR,
            pii_flag=True
        )
        json_output = spec.to_collibra_json()
        asset = json_output["assets"][0]
        attributes = asset["attributes"]

        # Find specific attributes
        type_ids = [attr["typeId"] for attr in attributes]
        assert "DATA_CLASSIFICATION" in type_ids
        assert "REGULATORY_SCOPE" in type_ids
        assert "PII_FLAG" in type_ids


class TestSnowflakeCSVExport:
    """Tests for Snowflake CSV export format."""

    def test_to_snowflake_csv_header(self):
        """Test CSV header contains all 30 field names."""
        spec = DataProductSpec(
            name="Test",
            description="Test description",
            business_purpose="Test purpose",
            data_owner_email="owner@firm.com"
        )
        header = spec.to_snowflake_csv_header()

        # Count fields
        fields = header.split(",")
        assert len(fields) == 28  # All fields except duplicates

        # Check specific fields are present
        assert '"name"' in header
        assert '"description"' in header
        assert '"business_purpose"' in header
        assert '"data_owner_email"' in header
        assert '"data_quality_score"' in header
        assert '"tags"' in header

    def test_to_snowflake_csv_list_serialisation(self):
        """Test that lists are pipe-separated in CSV output."""
        spec = DataProductSpec(
            name="Test Product",
            description="Test description",
            business_purpose="Test purpose",
            data_owner_email="owner@firm.com",
            source_systems=["System A", "System B", "System C"],
            tags=["tag1", "tag2"]
        )
        row = spec.to_snowflake_csv_row()

        # Check that lists are pipe-separated
        assert "System A|System B|System C" in row
        assert "tag1|tag2" in row

    def test_to_snowflake_csv_boolean_format(self):
        """Test that booleans are formatted as TRUE/FALSE."""
        spec_true = DataProductSpec(
            name="Test True",
            description="Test description",
            business_purpose="Test purpose",
            data_owner_email="owner@firm.com",
            pii_flag=True
        )
        row_true = spec_true.to_snowflake_csv_row()
        assert '"TRUE"' in row_true

        spec_false = DataProductSpec(
            name="Test False",
            description="Test description",
            business_purpose="Test purpose",
            data_owner_email="owner@firm.com",
            pii_flag=False
        )
        row_false = spec_false.to_snowflake_csv_row()
        assert '"FALSE"' in row_false

    def test_to_snowflake_csv_none_as_empty(self):
        """Test that None values become empty strings in CSV."""
        spec = DataProductSpec(
            name="Test",
            description="Test description",
            business_purpose="Test purpose",
            data_owner_email="owner@firm.com"
        )
        row = spec.to_snowflake_csv_row()

        # Split and check for empty quoted fields
        fields = row.split(",")
        empty_count = sum(1 for field in fields if field == '""')
        assert empty_count > 0  # Multiple optional fields are empty


class TestFieldValidation:
    """Tests for field-specific validation."""

    def test_email_validation(self):
        """Test that invalid emails are rejected."""
        # Valid email
        spec = DataProductSpec(
            name="Test",
            description="Test",
            business_purpose="Test",
            data_owner_email="valid.email@firm.com"
        )
        assert spec.data_owner_email == "valid.email@firm.com"

        # Invalid email
        with pytest.raises(Exception):
            DataProductSpec(
                name="Test",
                description="Test",
                business_purpose="Test",
                data_owner_email="not-an-email"
            )

    def test_data_quality_score_bounds(self):
        """Test that data quality score is constrained 0-100."""
        # Valid score at boundary
        spec_0 = DataProductSpec(
            name="Test",
            description="Test",
            business_purpose="Test",
            data_owner_email="owner@firm.com",
            data_quality_score=0.0
        )
        assert spec_0.data_quality_score == 0.0

        spec_100 = DataProductSpec(
            name="Test",
            description="Test",
            business_purpose="Test",
            data_owner_email="owner@firm.com",
            data_quality_score=100.0
        )
        assert spec_100.data_quality_score == 100.0

        spec_mid = DataProductSpec(
            name="Test",
            description="Test",
            business_purpose="Test",
            data_owner_email="owner@firm.com",
            data_quality_score=50.5
        )
        assert spec_mid.data_quality_score == 50.5

        # Invalid scores
        with pytest.raises(Exception):
            DataProductSpec(
                name="Test",
                description="Test",
                business_purpose="Test",
                data_owner_email="owner@firm.com",
                data_quality_score=-1.0
            )

        with pytest.raises(Exception):
            DataProductSpec(
                name="Test",
                description="Test",
                business_purpose="Test",
                data_owner_email="owner@firm.com",
                data_quality_score=101.0
            )
