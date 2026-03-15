"""
Collibra API Client for Data Product Concierge

Provides async interface to Collibra API for asset management, metadata,
lineage, and user/domain discovery. All methods include comprehensive error
handling, request tracking, and structured logging.
"""

import json
import logging
import os
from typing import Optional

from connectors.collibra_auth import CollibraAuthenticator
from core.utils import format_error, get_request_id, truncate
from models.data_product import (
    AssetResult,
    CollibraAbstractDomain,
    CollibraCode,
    CollibraDomain,
    CollibraOption,
    CollibraUser,
    DataProductSpec,
    LineageGraph,
    LineageNode,
    COLLIBRA_FIELD_MAP,
)

logger = logging.getLogger(__name__)


class CollibraClient:
    """Client for Collibra API interactions."""

    def __init__(self, auth: CollibraAuthenticator):
        """
        Initialize Collibra client.

        Args:
            auth: CollibraAuthenticator instance for API requests
        """
        self.auth = auth
        self._load_env_config()

    def _load_env_config(self) -> None:
        """Load and validate required environment variables."""
        self.data_product_type_id = os.getenv("DATA_PRODUCT_TYPE_ID")
        self.source_system_type_id = os.getenv("SOURCE_SYSTEM_TYPE_ID")
        self.business_domain_type_id = os.getenv("BUSINESS_DOMAIN_TYPE_ID")
        self.owner_role_id = os.getenv("COLLIBRA_OWNER_ROLE_ID")
        self.steward_role_id = os.getenv("COLLIBRA_STEWARD_ROLE_ID")
        self.draft_status_id = os.getenv("COLLIBRA_DRAFT_STATUS_ID")
        self.instance_url = os.getenv("COLLIBRA_INSTANCE_URL", "").rstrip("/")

        self.vocab_domain_map = {
            "data_classification": os.getenv("COLLIBRA_VOCAB_DATA_CLASSIFICATION"),
            "regulatory_scope": os.getenv("COLLIBRA_VOCAB_REGULATORY_SCOPE"),
            "sla_tier": os.getenv("COLLIBRA_VOCAB_SLA_TIER"),
            "access_level": os.getenv("COLLIBRA_VOCAB_ACCESS_LEVEL"),
            "update_frequency": os.getenv("COLLIBRA_VOCAB_UPDATE_FREQUENCY"),
            "business_criticality": os.getenv(
                "COLLIBRA_VOCAB_BUSINESS_CRITICALITY"
            ),
            "geographic_restriction": os.getenv(
                "COLLIBRA_VOCAB_GEOGRAPHIC_RESTRICTION"
            ),
            "encryption_standard": os.getenv("COLLIBRA_VOCAB_ENCRYPTION_STANDARD"),
            "status": os.getenv("COLLIBRA_VOCAB_STATUS"),
        }

        required_vars = [
            self.data_product_type_id,
            self.source_system_type_id,
            self.business_domain_type_id,
            self.owner_role_id,
            self.steward_role_id,
            self.draft_status_id,
        ]

        if not all(required_vars):
            missing = [
                name
                for name, value in [
                    ("DATA_PRODUCT_TYPE_ID", self.data_product_type_id),
                    ("SOURCE_SYSTEM_TYPE_ID", self.source_system_type_id),
                    ("BUSINESS_DOMAIN_TYPE_ID", self.business_domain_type_id),
                    ("COLLIBRA_OWNER_ROLE_ID", self.owner_role_id),
                    ("COLLIBRA_STEWARD_ROLE_ID", self.steward_role_id),
                    ("COLLIBRA_DRAFT_STATUS_ID", self.draft_status_id),
                ]
                if not value
            ]
            logger.warning(f"Missing environment variables: {missing}")

    async def search_assets(
        self, query: str, limit: int = 10
    ) -> list[AssetResult]:
        """
        Search for assets by name.

        Args:
            query: Search term for asset name
            limit: Maximum results to return

        Returns:
            List of AssetResult objects matching the query

        Raises:
            Exception: If API request fails
        """
        request_id = get_request_id()
        try:
            logger.info(
                f"[{request_id}] Searching assets: query={truncate(query)}, "
                f"limit={limit}"
            )

            response = await self.auth.collibra_request(
                method="GET",
                path="/assets",
                params={
                    "nameContains": query,
                    "typeIds": self.data_product_type_id,
                    "limit": limit,
                },
            )

            if not response or "results" not in response:
                logger.warning(f"[{request_id}] Empty search results for {query}")
                return []

            assets = []
            for item in response.get("results", []):
                asset = AssetResult(
                    id=item.get("id"),
                    name=item.get("name"),
                    type=item.get("type", {}).get("name"),
                    domain_name=item.get("domain", {}).get("name"),
                    description=item.get("description", ""),
                )
                assets.append(asset)

            logger.info(
                f"[{request_id}] Found {len(assets)} assets for query {truncate(query)}"
            )
            return assets

        except Exception as e:
            logger.error(f"[{request_id}] Search assets failed: {format_error(e)}")
            raise

    async def get_asset_detail(self, asset_id: str) -> DataProductSpec:
        """
        Fetch complete asset details with attributes, responsibilities, and lineage.

        Args:
            asset_id: Collibra asset ID

        Returns:
            Fully-populated DataProductSpec object

        Raises:
            Exception: If API request fails or asset not found
        """
        request_id = get_request_id()
        try:
            logger.info(f"[{request_id}] Fetching asset detail for {asset_id}")

            base_response = await self.auth.collibra_request(
                method="GET", path=f"/assets/{asset_id}"
            )

            if not base_response:
                logger.error(f"[{request_id}] Asset not found: {asset_id}")
                raise Exception(f"Asset {asset_id} not found")

            spec = DataProductSpec(
                collibra_id=base_response.get("id"),
                name=base_response.get("name", ""),
                description=base_response.get("description", ""),
                domain_id=base_response.get("domain", {}).get("id"),
                domain_name=base_response.get("domain", {}).get("name"),
                status_id=base_response.get("statusId"),
            )

            attributes_response = await self.auth.collibra_request(
                method="GET", path=f"/assets/{asset_id}/attributes"
            )

            if attributes_response and "results" in attributes_response:
                for attr in attributes_response["results"]:
                    self._map_attribute_to_spec(spec, attr)

            responsibilities_response = await self.auth.collibra_request(
                method="GET", path=f"/assets/{asset_id}/responsibilities"
            )

            if responsibilities_response and "results" in responsibilities_response:
                for resp in responsibilities_response["results"]:
                    role_id = resp.get("role", {}).get("id")
                    user_id = resp.get("user", {}).get("id")
                    user_name = resp.get("user", {}).get("name")

                    if role_id == self.owner_role_id and user_id:
                        spec.owner_id = user_id
                        spec.owner_name = user_name
                    elif role_id == self.steward_role_id and user_id:
                        spec.steward_id = user_id
                        spec.steward_name = user_name

            relations_response = await self.auth.collibra_request(
                method="GET", path=f"/assets/{asset_id}/relations"
            )

            if relations_response and "results" in relations_response:
                upstream_nodes = []
                downstream_nodes = []

                for relation in relations_response["results"]:
                    source_id = relation.get("source", {}).get("id")
                    target_id = relation.get("target", {}).get("id")
                    relation_type = relation.get("type", {}).get("name", "")

                    if target_id == asset_id:
                        if source_id:
                            node = LineageNode(
                                asset_id=source_id,
                                asset_name=relation.get("source", {}).get("name"),
                                asset_type=relation.get("source", {}).get("type", {}).get("name"),
                            )
                            upstream_nodes.append(node)
                    elif source_id == asset_id:
                        if target_id:
                            node = LineageNode(
                                asset_id=target_id,
                                asset_name=relation.get("target", {}).get("name"),
                                asset_type=relation.get("target", {}).get("type", {}).get("name"),
                            )
                            downstream_nodes.append(node)

                spec.lineage = LineageGraph(
                    upstream=upstream_nodes, downstream=downstream_nodes
                )

            logger.info(
                f"[{request_id}] Asset detail fetched: {spec.name} "
                f"({len(spec.lineage.upstream) if spec.lineage else 0} upstream, "
                f"{len(spec.lineage.downstream) if spec.lineage else 0} downstream)"
            )
            return spec

        except Exception as e:
            logger.error(
                f"[{request_id}] Get asset detail failed for {asset_id}: "
                f"{format_error(e)}"
            )
            raise

    def _map_attribute_to_spec(
        self, spec: DataProductSpec, attribute: dict
    ) -> None:
        """
        Map a Collibra attribute to DataProductSpec field.

        Args:
            spec: DataProductSpec to update
            attribute: Attribute dict from Collibra API
        """
        type_id = attribute.get("type", {}).get("id")
        if not type_id:
            return

        reverse_map = {v: k for k, v in COLLIBRA_FIELD_MAP.items()}
        field_name = reverse_map.get(type_id)

        if not field_name:
            return

        value = attribute.get("value")

        if field_name == "owner_id":
            spec.owner_id = value
        elif field_name == "owner_name":
            spec.owner_name = value
        elif field_name == "steward_id":
            spec.steward_id = value
        elif field_name == "steward_name":
            spec.steward_name = value
        elif field_name == "data_classification":
            spec.data_classification = value
        elif field_name == "regulatory_scope":
            spec.regulatory_scope = value
        elif field_name == "sla_tier":
            spec.sla_tier = value
        elif field_name == "access_level":
            spec.access_level = value
        elif field_name == "update_frequency":
            spec.update_frequency = value
        elif field_name == "business_criticality":
            spec.business_criticality = value
        elif field_name == "geographic_restriction":
            spec.geographic_restriction = value
        elif field_name == "encryption_standard":
            spec.encryption_standard = value
        elif field_name == "status":
            spec.status = value
        elif field_name == "contact_email":
            spec.contact_email = value
        elif field_name == "retention_days":
            try:
                spec.retention_days = int(value) if value else None
            except (ValueError, TypeError):
                logger.warning(f"Invalid retention_days value: {value}")
        elif field_name == "last_modified":
            spec.last_modified = value

    async def get_valid_options(self, field_name: str) -> list[CollibraOption]:
        """
        Get valid vocabulary options for a field.

        Args:
            field_name: Field name (e.g., 'data_classification')

        Returns:
            List of CollibraOption objects

        Raises:
            Exception: If field not found or API request fails
        """
        request_id = get_request_id()
        try:
            vocab_domain_id = self.vocab_domain_map.get(field_name)
            if not vocab_domain_id:
                logger.warning(f"[{request_id}] No vocab domain for field {field_name}")
                return []

            logger.info(
                f"[{request_id}] Fetching options for field {field_name} "
                f"from domain {vocab_domain_id}"
            )

            response = await self.auth.collibra_request(
                method="GET",
                path="/assets",
                params={"domainId": vocab_domain_id, "limit": 200},
            )

            if not response or "results" not in response:
                logger.warning(
                    f"[{request_id}] No options found for field {field_name}"
                )
                return []

            options = []
            for item in response["results"]:
                option = CollibraOption(
                    id=item.get("id"),
                    name=item.get("name"),
                    description=item.get("description", ""),
                )
                options.append(option)

            logger.info(
                f"[{request_id}] Found {len(options)} options for {field_name}"
            )
            return options

        except Exception as e:
            logger.error(
                f"[{request_id}] Get valid options failed for {field_name}: "
                f"{format_error(e)}"
            )
            raise

    async def get_domains(self) -> list[CollibraDomain]:
        """
        Get list of domains.

        Returns:
            List of CollibraDomain objects

        Raises:
            Exception: If API request fails
        """
        request_id = get_request_id()
        try:
            logger.info(f"[{request_id}] Fetching domains")

            response = await self.auth.collibra_request(
                method="GET",
                path="/domains",
                params={"limit": 500},
            )

            if not response or "results" not in response:
                logger.warning(f"[{request_id}] No domains found")
                return []

            domains = []
            for item in response["results"]:
                domain = CollibraDomain(
                    id=item.get("id"),
                    name=item.get("name"),
                    description=item.get("description", ""),
                    type_name=item.get("type", {}).get("name"),
                )
                domains.append(domain)

            logger.info(f"[{request_id}] Found {len(domains)} domains")
            return domains

        except Exception as e:
            logger.error(f"[{request_id}] Get domains failed: {format_error(e)}")
            raise

    async def get_users(self, search: str = "") -> list[CollibraUser]:
        """
        Get list of users, optionally filtered by name.

        Args:
            search: Optional name filter

        Returns:
            List of CollibraUser objects

        Raises:
            Exception: If API request fails
        """
        request_id = get_request_id()
        try:
            logger.info(
                f"[{request_id}] Fetching users with search={truncate(search)}"
            )

            params = {"limit": 500}
            if search:
                params["nameContains"] = search

            response = await self.auth.collibra_request(
                method="GET",
                path="/users",
                params=params,
            )

            if not response or "results" not in response:
                logger.warning(f"[{request_id}] No users found")
                return []

            users = []
            for item in response["results"]:
                user = CollibraUser(
                    id=item.get("id"),
                    name=item.get("name"),
                    email=item.get("email", ""),
                    full_name=item.get("fullName", ""),
                )
                users.append(user)

            logger.info(
                f"[{request_id}] Found {len(users)} users matching search"
            )
            return users

        except Exception as e:
            logger.error(
                f"[{request_id}] Get users failed: {format_error(e)}"
            )
            raise

    async def get_source_systems(self) -> list[CollibraOption]:
        """
        Get list of source systems.

        Returns:
            List of CollibraOption objects

        Raises:
            Exception: If API request fails
        """
        request_id = get_request_id()
        try:
            logger.info(f"[{request_id}] Fetching source systems")

            response = await self.auth.collibra_request(
                method="GET",
                path="/assets",
                params={"typeId": self.source_system_type_id, "limit": 500},
            )

            if not response or "results" not in response:
                logger.warning(f"[{request_id}] No source systems found")
                return []

            systems = []
            for item in response["results"]:
                system = CollibraOption(
                    id=item.get("id"),
                    name=item.get("name"),
                    description=item.get("description", ""),
                )
                systems.append(system)

            logger.info(f"[{request_id}] Found {len(systems)} source systems")
            return systems

        except Exception as e:
            logger.error(
                f"[{request_id}] Get source systems failed: {format_error(e)}"
            )
            raise

    async def get_consumer_teams(self) -> list[CollibraOption]:
        """
        Get list of consumer teams (business domains).

        Returns:
            List of CollibraOption objects

        Raises:
            Exception: If API request fails
        """
        request_id = get_request_id()
        try:
            logger.info(f"[{request_id}] Fetching consumer teams")

            response = await self.auth.collibra_request(
                method="GET",
                path="/assets",
                params={"typeId": self.business_domain_type_id, "limit": 500},
            )

            if not response or "results" not in response:
                logger.warning(f"[{request_id}] No consumer teams found")
                return []

            teams = []
            for item in response["results"]:
                team = CollibraOption(
                    id=item.get("id"),
                    name=item.get("name"),
                    description=item.get("description", ""),
                )
                teams.append(team)

            logger.info(f"[{request_id}] Found {len(teams)} consumer teams")
            return teams

        except Exception as e:
            logger.error(
                f"[{request_id}] Get consumer teams failed: {format_error(e)}"
            )
            raise

    async def get_asset_lineage(self, asset_id: str) -> LineageGraph:
        """
        Get upstream and downstream lineage for an asset.

        Args:
            asset_id: Collibra asset ID

        Returns:
            LineageGraph with upstream and downstream nodes

        Raises:
            Exception: If API request fails
        """
        request_id = get_request_id()
        try:
            logger.info(f"[{request_id}] Fetching lineage for asset {asset_id}")

            response = await self.auth.collibra_request(
                method="GET",
                path=f"/assets/{asset_id}/relations",
                params={"limit": 500},
            )

            upstream_nodes = []
            downstream_nodes = []

            if response and "results" in response:
                for relation in response["results"]:
                    source_id = relation.get("source", {}).get("id")
                    target_id = relation.get("target", {}).get("id")

                    if target_id == asset_id and source_id:
                        node = LineageNode(
                            asset_id=source_id,
                            asset_name=relation.get("source", {}).get("name"),
                            asset_type=relation.get("source", {}).get("type", {}).get("name"),
                        )
                        upstream_nodes.append(node)
                    elif source_id == asset_id and target_id:
                        node = LineageNode(
                            asset_id=target_id,
                            asset_name=relation.get("target", {}).get("name"),
                            asset_type=relation.get("target", {}).get("type", {}).get("name"),
                        )
                        downstream_nodes.append(node)

            lineage = LineageGraph(upstream=upstream_nodes, downstream=downstream_nodes)

            logger.info(
                f"[{request_id}] Lineage fetched: "
                f"{len(upstream_nodes)} upstream, {len(downstream_nodes)} downstream"
            )
            return lineage

        except Exception as e:
            logger.error(
                f"[{request_id}] Get asset lineage failed for {asset_id}: "
                f"{format_error(e)}"
            )
            raise

    async def create_draft_asset(self, spec: DataProductSpec) -> str:
        """
        Create a new draft data product asset.

        Args:
            spec: DataProductSpec with asset details

        Returns:
            ID of newly created asset

        Raises:
            Exception: If asset creation fails
        """
        request_id = get_request_id()
        try:
            logger.info(
                f"[{request_id}] Creating draft asset: {truncate(spec.name)}"
            )

            asset_payload = {
                "name": spec.name,
                "description": spec.description or "",
                "typeId": self.data_product_type_id,
                "domainId": spec.domain_id,
                "statusId": self.draft_status_id,
            }

            asset_response = await self.auth.collibra_request(
                method="POST",
                path="/assets",
                json_data=asset_payload,
            )

            if not asset_response or "id" not in asset_response:
                logger.error(f"[{request_id}] Asset creation returned invalid response")
                raise Exception("Failed to create asset: invalid response")

            asset_id = asset_response["id"]
            logger.info(f"[{request_id}] Asset created with ID {asset_id}")

            attributes_to_set = {
                "data_classification": spec.data_classification,
                "regulatory_scope": spec.regulatory_scope,
                "sla_tier": spec.sla_tier,
                "access_level": spec.access_level,
                "update_frequency": spec.update_frequency,
                "business_criticality": spec.business_criticality,
                "geographic_restriction": spec.geographic_restriction,
                "encryption_standard": spec.encryption_standard,
                "status": spec.status,
                "contact_email": spec.contact_email,
            }

            if spec.retention_days is not None:
                attributes_to_set["retention_days"] = str(spec.retention_days)

            for field_name, value in attributes_to_set.items():
                if value and field_name in COLLIBRA_FIELD_MAP:
                    type_id = COLLIBRA_FIELD_MAP[field_name]
                    attr_payload = {
                        "typeId": type_id,
                        "value": value,
                    }

                    try:
                        await self.auth.collibra_request(
                            method="POST",
                            path=f"/assets/{asset_id}/attributes",
                            json_data=attr_payload,
                        )
                        logger.debug(
                            f"[{request_id}] Attribute {field_name} set on {asset_id}"
                        )
                    except Exception as e:
                        logger.warning(
                            f"[{request_id}] Failed to set attribute {field_name}: "
                            f"{format_error(e)}"
                        )

            responsibilities = []
            if spec.owner_id:
                responsibilities.append(
                    {
                        "userId": spec.owner_id,
                        "roleId": self.owner_role_id,
                    }
                )

            if spec.steward_id:
                responsibilities.append(
                    {
                        "userId": spec.steward_id,
                        "roleId": self.steward_role_id,
                    }
                )

            for resp in responsibilities:
                try:
                    await self.auth.collibra_request(
                        method="POST",
                        path=f"/assets/{asset_id}/responsibilities",
                        json_data=resp,
                    )
                    logger.debug(
                        f"[{request_id}] Responsibility assigned to {asset_id}"
                    )
                except Exception as e:
                    logger.warning(
                        f"[{request_id}] Failed to assign responsibility: "
                        f"{format_error(e)}"
                    )

            logger.info(
                f"[{request_id}] Draft asset created successfully: {asset_id}"
            )
            return asset_id

        except Exception as e:
            logger.error(
                f"[{request_id}] Create draft asset failed: {format_error(e)}"
            )
            raise

    async def update_asset_attributes(
        self, asset_id: str, spec: DataProductSpec
    ) -> None:
        """
        Update asset attributes, applying only changed values.

        Args:
            asset_id: Collibra asset ID
            spec: DataProductSpec with updated values

        Raises:
            Exception: If update fails
        """
        request_id = get_request_id()
        try:
            logger.info(f"[{request_id}] Updating asset attributes for {asset_id}")

            current_response = await self.auth.collibra_request(
                method="GET",
                path=f"/assets/{asset_id}/attributes",
            )

            current_values = {}
            current_attr_ids = {}

            if current_response and "results" in current_response:
                for attr in current_response["results"]:
                    type_id = attr.get("type", {}).get("id")
                    attr_id = attr.get("id")
                    value = attr.get("value")

                    reverse_map = {v: k for k, v in COLLIBRA_FIELD_MAP.items()}
                    field_name = reverse_map.get(type_id)

                    if field_name:
                        current_values[field_name] = value
                        current_attr_ids[field_name] = attr_id

            updates_made = 0

            attributes_to_update = {
                "data_classification": spec.data_classification,
                "regulatory_scope": spec.regulatory_scope,
                "sla_tier": spec.sla_tier,
                "access_level": spec.access_level,
                "update_frequency": spec.update_frequency,
                "business_criticality": spec.business_criticality,
                "geographic_restriction": spec.geographic_restriction,
                "encryption_standard": spec.encryption_standard,
                "status": spec.status,
                "contact_email": spec.contact_email,
            }

            if spec.retention_days is not None:
                attributes_to_update["retention_days"] = str(spec.retention_days)

            for field_name, new_value in attributes_to_update.items():
                if field_name not in COLLIBRA_FIELD_MAP:
                    continue

                current_value = current_values.get(field_name)

                if new_value == current_value:
                    continue

                type_id = COLLIBRA_FIELD_MAP[field_name]

                if field_name in current_attr_ids:
                    attr_id = current_attr_ids[field_name]
                    patch_payload = {"value": new_value}

                    try:
                        await self.auth.collibra_request(
                            method="PATCH",
                            path=f"/assets/{asset_id}/attributes/{attr_id}",
                            json_data=patch_payload,
                        )
                        updates_made += 1
                        logger.debug(
                            f"[{request_id}] Updated {field_name} on {asset_id}"
                        )
                    except Exception as e:
                        logger.warning(
                            f"[{request_id}] Failed to update {field_name}: "
                            f"{format_error(e)}"
                        )
                else:
                    if new_value:
                        attr_payload = {
                            "typeId": type_id,
                            "value": new_value,
                        }

                        try:
                            await self.auth.collibra_request(
                                method="POST",
                                path=f"/assets/{asset_id}/attributes",
                                json_data=attr_payload,
                            )
                            updates_made += 1
                            logger.debug(
                                f"[{request_id}] Created {field_name} on {asset_id}"
                            )
                        except Exception as e:
                            logger.warning(
                                f"[{request_id}] Failed to create {field_name}: "
                                f"{format_error(e)}"
                            )

            logger.info(
                f"[{request_id}] Asset attributes updated: {updates_made} changes"
            )

        except Exception as e:
            logger.error(
                f"[{request_id}] Update asset attributes failed for {asset_id}: "
                f"{format_error(e)}"
            )
            raise

    async def get_related_reports(self, asset_id: str) -> list[AssetResult]:
        """
        Get reports related to an asset.

        Args:
            asset_id: Collibra asset ID

        Returns:
            List of AssetResult objects for related reports

        Raises:
            Exception: If API request fails
        """
        request_id = get_request_id()
        try:
            logger.info(f"[{request_id}] Fetching related reports for {asset_id}")

            response = await self.auth.collibra_request(
                method="GET",
                path=f"/assets/{asset_id}/relations",
                params={"limit": 500},
            )

            reports = []
            report_type_name = "Report"

            if response and "results" in response:
                for relation in response["results"]:
                    source_type = relation.get("source", {}).get("type", {}).get("name")
                    target_type = relation.get("target", {}).get("type", {}).get("name")

                    if source_type == report_type_name:
                        source_id = relation.get("source", {}).get("id")
                        if source_id and source_id != asset_id:
                            report = AssetResult(
                                id=source_id,
                                name=relation.get("source", {}).get("name"),
                                type=source_type,
                                domain_name=relation.get("source", {}).get("domain", {}).get("name"),
                                description=relation.get("source", {}).get("description", ""),
                            )
                            reports.append(report)

                    if target_type == report_type_name:
                        target_id = relation.get("target", {}).get("id")
                        if target_id and target_id != asset_id:
                            report = AssetResult(
                                id=target_id,
                                name=relation.get("target", {}).get("name"),
                                type=target_type,
                                domain_name=relation.get("target", {}).get("domain", {}).get("name"),
                                description=relation.get("target", {}).get("description", ""),
                            )
                            reports.append(report)

            logger.info(
                f"[{request_id}] Found {len(reports)} related reports for {asset_id}"
            )
            return reports

        except Exception as e:
            logger.error(
                f"[{request_id}] Get related reports failed for {asset_id}: "
                f"{format_error(e)}"
            )
            raise

    async def get_data_quality_score(self, asset_id: str) -> Optional[float]:
        """
        Get data quality score for an asset.

        Args:
            asset_id: Collibra asset ID

        Returns:
            Data quality score as float, or None if not available

        Raises:
            Exception: If API request fails
        """
        request_id = get_request_id()
        try:
            logger.info(f"[{request_id}] Fetching data quality score for {asset_id}")

            response = await self.auth.collibra_request(
                method="GET",
                path=f"/assets/{asset_id}/attributes",
            )

            if not response or "results" not in response:
                logger.warning(f"[{request_id}] No attributes found for {asset_id}")
                return None

            for attr in response["results"]:
                attr_type = attr.get("type", {}).get("name", "").lower()

                if "quality" in attr_type or "dq" in attr_type or "score" in attr_type:
                    try:
                        value = attr.get("value")
                        if value is not None:
                            score = float(value)
                            logger.info(
                                f"[{request_id}] Data quality score retrieved: {score}"
                            )
                            return score
                    except (ValueError, TypeError):
                        logger.warning(
                            f"[{request_id}] Invalid quality score value: {attr.get('value')}"
                        )

            logger.info(
                f"[{request_id}] No data quality score found for {asset_id}"
            )
            return None

        except Exception as e:
            logger.error(
                f"[{request_id}] Get data quality score failed for {asset_id}: "
                f"{format_error(e)}"
            )
            raise
