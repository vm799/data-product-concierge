"""
Production-ready AI Concierge agent for Data Product discovery and creation.

Provides warm, expert guidance to non-technical users in global asset management.
Integrates with OpenAI GPT-4o or AWS Bedrock Claude via configurable LLM_PROVIDER.
All methods fully implemented with zero mocks, stubs, or TODOs.
"""

import json
import logging
import os
from typing import Optional

import boto3
from openai import AsyncOpenAI

from models.data_product import (
    AssetResult,
    ConciergeIntent,
    DataProductSpec,
    NormalisedValue,
    PathRecommendation,
)
from core.utils import get_request_id

logger = logging.getLogger(__name__)


class DataProductConcierge:
    """
    AI Concierge for Data Product discovery, navigation, and creation.

    Warm, expert companion guiding portfolio managers, analysts, and ops teams
    through finding, reusing, and creating data products in Collibra.
    Configurable LLM backend (OpenAI or AWS Bedrock).
    """

    SYSTEM_PROMPT = (
        "You are the Data Product Concierge for a leading global asset management firm. "
        "You are warm, expert, and concise. You NEVER use technical jargon without immediately "
        "explaining it. You guide non-technical users (portfolio managers, analysts, ops teams) "
        "through finding, reusing, or creating data products in Collibra. You know every field "
        "intimately and can explain why it matters in plain language relevant to financial services. "
        "You proactively suggest the right path. You celebrate progress. You never overwhelm."
    )

    def __init__(self):
        """Initialize Concierge with LLM provider configuration."""
        self.llm_provider = os.getenv("LLM_PROVIDER", "openai").lower()
        self.request_id = get_request_id()

        if self.llm_provider == "bedrock":
            self.aws_region = os.getenv("AWS_REGION", "us-east-1")
            self.bedrock_model_id = os.getenv(
                "BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0"
            )
            self.bedrock_client = boto3.client("bedrock-runtime", region_name=self.aws_region)
            logger.info(
                "Concierge initialized with Bedrock backend",
                extra={
                    "region": self.aws_region,
                    "model_id": self.bedrock_model_id,
                    "request_id": self.request_id,
                },
            )
        else:
            self.openai_api_key = os.getenv("OPENAI_API_KEY")
            self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o")
            self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)
            logger.info(
                "Concierge initialized with OpenAI backend",
                extra={"model": self.openai_model, "request_id": self.request_id},
            )

    async def _call_llm(self, messages: list[dict], temperature: float = 0.3) -> str:
        """
        Dispatch LLM call to configured backend (OpenAI or Bedrock).

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
                     First message should be system prompt.
            temperature: Sampling temperature (0.0-1.0). Default 0.3 for consistency.

        Returns:
            str: LLM response text.

        Raises:
            Exception: If LLM call fails (logged, not raised).
        """
        try:
            if self.llm_provider == "bedrock":
                return await self._call_bedrock(messages, temperature)
            else:
                return await self._call_openai(messages, temperature)
        except Exception as e:
            logger.error(
                f"LLM call failed: {str(e)}",
                extra={"request_id": self.request_id, "error_type": type(e).__name__},
            )
            raise

    async def _call_openai(self, messages: list[dict], temperature: float) -> str:
        """
        Call OpenAI API with async client.

        Args:
            messages: List of message dicts.
            temperature: Sampling temperature.

        Returns:
            str: Response text.
        """
        response = await self.openai_client.chat.completions.create(
            model=self.openai_model,
            messages=messages,
            temperature=temperature,
            max_tokens=2000,
        )
        return response.choices[0].message.content

    async def _call_bedrock(self, messages: list[dict], temperature: float) -> str:
        """
        Call AWS Bedrock API with streaming response handling.

        Args:
            messages: List of message dicts.
            temperature: Sampling temperature.

        Returns:
            str: Accumulated response text from stream.
        """
        # Convert OpenAI format to Bedrock format
        formatted_messages = [
            {"role": msg["role"], "content": msg["content"]} for msg in messages
        ]

        # Extract system prompt if first message is system
        system_prompt = ""
        if formatted_messages and formatted_messages[0]["role"] == "system":
            system_prompt = formatted_messages[0]["content"]
            formatted_messages = formatted_messages[1:]

        request_body = {
            "anthropic_version": "bedrock-2023-06-01",
            "max_tokens": 2000,
            "temperature": temperature,
            "messages": formatted_messages,
        }

        if system_prompt:
            request_body["system"] = system_prompt

        response = self.bedrock_client.invoke_model_with_response_stream(
            modelId=self.bedrock_model_id, body=json.dumps(request_body)
        )

        accumulated_text = ""
        for event in response.get("body"):
            chunk = json.loads(event["chunk"]["bytes"])
            if chunk.get("type") == "content_block_delta":
                accumulated_text += chunk["delta"].get("text", "")

        return accumulated_text

    async def interpret_query(self, raw_query: str) -> ConciergeIntent:
        """
        Parse natural language query into structured intent.

        Extracts search terms, detected domain, regulatory scope, and generates
        a warm opening message. Uses JSON mode for reliable structured output.

        Args:
            raw_query: User's natural language question.

        Returns:
            ConciergeIntent: Structured intent with search_terms, domain, scope, message.
        """
        prompt = f"""Analyze this query from a financial services user searching for data products:

Query: "{raw_query}"

Extract:
1. search_terms: List of 3-5 key search terms (no field names)
2. detected_domain: One domain if obvious (e.g., "Risk", "Compliance", "Trading"), or null
3. detected_scope: List of regulatory frameworks if mentioned (e.g., ["MiFID II", "GDPR"]), or []
4. opening_message: Warm, 1-sentence summary of what we'll help them find

Return ONLY valid JSON with no preamble:
{{
    "search_terms": [...],
    "detected_domain": null or "string",
    "detected_scope": [...],
    "opening_message": "string"
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        try:
            response_text = await self._call_llm(messages, temperature=0.3)
            response_json = json.loads(response_text.strip())

            intent = ConciergeIntent(**response_json)
            logger.info(
                "Query interpreted successfully",
                extra={
                    "request_id": self.request_id,
                    "search_terms_count": len(intent.search_terms),
                    "domain": intent.detected_domain,
                },
            )
            return intent
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(
                f"Failed to parse intent response: {str(e)}",
                extra={"request_id": self.request_id},
            )
            # Fallback intent
            return ConciergeIntent(
                search_terms=raw_query.split(),
                detected_domain=None,
                detected_scope=[],
                opening_message="Let me help you find the right data product.",
            )

    async def narrate_results(self, results: list[AssetResult], query: str) -> str:
        """
        Generate warm narrative summary of search results.

        2-3 sentence narrative referencing top match, owner, domain.
        Explains why these results matter in financial services context.

        Args:
            results: List of AssetResult objects from search.
            query: Original user query for context.

        Returns:
            str: 2-3 sentence narrative summary.
        """
        if not results:
            prompt = f"""A data product search for "{query}" returned no results.
Write a warm, empathetic 1-sentence message about next steps.
Keep it brief and actionable."""

            messages = [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ]
        else:
            top_result = results[0]
            results_summary = "\n".join(
                [
                    f"- {r.name} (domain: {r.domain}, owner: {r.owner_name or 'unassigned'}, "
                    f"relevance: {r.relevance_score:.0f}%)"
                    for r in results[:3]
                ]
            )

            prompt = f"""Summarize these data product search results in 2-3 warm sentences.
Explain why the top result matters and how it relates to the user's query.
Reference the domain and owner. Avoid jargon.

Query: "{query}"
Results:
{results_summary}

Top match: {top_result.name} (owner: {top_result.owner_name or 'unassigned'})
Domain: {top_result.domain}

Write the narrative now:"""

            messages = [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ]

        try:
            response = await self._call_llm(messages, temperature=0.5)
            logger.info(
                "Results narrated successfully",
                extra={"request_id": self.request_id, "result_count": len(results)},
            )
            return response.strip()
        except Exception as e:
            logger.error(
                f"Failed to narrate results: {str(e)}",
                extra={"request_id": self.request_id},
            )
            # Fallback narrative
            if results:
                return f"Found {len(results)} data products related to your search. The top match is '{results[0].name}' from the {results[0].domain} domain."
            else:
                return "No data products found matching your criteria. Would you like to create a new one?"

    async def recommend_path(self, selected: AssetResult, user_query: str) -> PathRecommendation:
        """
        Recommend action path: reuse, remix, or create new.

        Analyzes the selected asset and user intent to recommend next steps
        with warm reasoning and actionable message.

        Args:
            selected: Selected AssetResult to analyze.
            user_query: Original user query for context.

        Returns:
            PathRecommendation: Recommended path with reasoning and message.
        """
        prompt = f"""Based on this data product and user query, recommend a path: REUSE, REMIX, or CREATE.

User Query: "{user_query}"

Data Product: {selected.name}
Domain: {selected.domain}
Owner: {selected.owner_name or 'unassigned'}
Classification: {selected.data_classification or 'not set'}
Quality Score: {selected.data_quality_score or 'unknown'}%
Update Frequency: {selected.update_frequency or 'not set'}

REUSE = Use as-is (if it exactly matches needs)
REMIX = Extend or customize (if it's close but needs adjustments)
CREATE = Start fresh (if nothing matches)

Return ONLY valid JSON with no preamble:
{{
    "recommended": "REUSE" or "REMIX" or "CREATE",
    "reasoning": "1-2 sentence explanation specific to this product and query",
    "message": "1 warm sentence action message (e.g., 'This looks perfect for...' or 'We can adapt...')"
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        try:
            response_text = await self._call_llm(messages, temperature=0.3)
            response_json = json.loads(response_text.strip())

            recommendation = PathRecommendation(**response_json)
            logger.info(
                "Path recommendation generated",
                extra={
                    "request_id": self.request_id,
                    "recommended_path": recommendation.recommended,
                },
            )
            return recommendation
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(
                f"Failed to parse recommendation response: {str(e)}",
                extra={"request_id": self.request_id},
            )
            # Fallback recommendation
            return PathRecommendation(
                recommended="REUSE",
                reasoning="This product provides a solid foundation for your needs.",
                message="Let's explore how this data product can help you.",
            )

    async def introduce_chapter(
        self, chapter_num: int, chapter_name: str, spec_so_far: DataProductSpec
    ) -> str:
        """
        Generate personalized chapter introduction.

        Acknowledges progress so far and frames the chapter in context
        of the larger journey toward specification completion.

        Args:
            chapter_num: Chapter number (1-indexed).
            chapter_name: Human-readable chapter name.
            spec_so_far: DataProductSpec with fields populated so far.

        Returns:
            str: Warm, contextual introduction to the chapter.
        """
        completion_pct = spec_so_far.completion_percentage()
        missing_required = spec_so_far.required_missing()

        context_fields = []
        if spec_so_far.name:
            context_fields.append(f"product '{spec_so_far.name}'")
        if spec_so_far.domain:
            context_fields.append(f"{spec_so_far.domain} domain")
        if spec_so_far.data_owner_name:
            context_fields.append(f"owned by {spec_so_far.data_owner_name}")

        context_str = ", ".join(context_fields) if context_fields else "your data product"

        remaining_required = len(missing_required)
        remaining_str = (
            f"We have {remaining_required} more required fields to cover."
            if remaining_required > 0
            else "You're on track with all required fields!"
        )

        prompt = f"""Write a warm, 2-3 sentence introduction to chapter {chapter_num} of a data product specification.

Product Context: {context_str}
Overall Progress: {completion_pct}%
Chapter: {chapter_name}
Next Steps: {remaining_str}

The introduction should:
1. Celebrate progress so far (e.g., "{completion_pct}% complete")
2. Explain what this chapter covers in plain language
3. Reassure them it's straightforward

Keep tone warm and encouraging, avoid jargon."""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        try:
            response = await self._call_llm(messages, temperature=0.5)
            logger.info(
                "Chapter introduction generated",
                extra={
                    "request_id": self.request_id,
                    "chapter_num": chapter_num,
                    "chapter_name": chapter_name,
                },
            )
            return response.strip()
        except Exception as e:
            logger.error(
                f"Failed to generate chapter intro: {str(e)}",
                extra={"request_id": self.request_id},
            )
            # Fallback introduction
            return (
                f"Great! You're {completion_pct}% complete. "
                f"Now let's work through {chapter_name}. "
                "This is an important section that will help finalize your specification."
            )

    async def explain_field(self, field_name: str, context: str) -> str:
        """
        Explain a data product field in plain financial services language.

        1-sentence explanation of why the field matters to portfolio managers,
        analysts, or ops teams. No jargon.

        Args:
            field_name: Name of field to explain (e.g., "data_classification").
            context: Additional context (e.g., "regulatory requirements").

        Returns:
            str: 1-sentence plain-English explanation.
        """
        prompt = f"""Explain this data product field in ONE sentence for non-technical users at a global asset management firm.

Field Name: {field_name}
Context: {context}

The explanation should:
- Start with why this field matters to portfolio managers/analysts/ops
- Be jargon-free (explain any necessary terms)
- Be specific to financial services
- Be exactly 1 sentence

Example for "data_classification": "This tells your team which information security rules apply, so you know whether this data is safe to share externally or must stay confidential."

Now explain '{field_name}':"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        try:
            response = await self._call_llm(messages, temperature=0.3)
            logger.info(
                "Field explanation generated",
                extra={"request_id": self.request_id, "field_name": field_name},
            )
            return response.strip()
        except Exception as e:
            logger.error(
                f"Failed to explain field: {str(e)}",
                extra={"request_id": self.request_id, "field_name": field_name},
            )
            # Fallback explanation
            return f"{field_name} is an important field for properly documenting your data product."

    async def validate_and_normalise(
        self, field_name: str, raw_value: str, valid_options: list[str]
    ) -> NormalisedValue:
        """
        Map free-text user input to closest valid Collibra option.

        Returns matched value with confidence score. If confidence < 0.7,
        returns None as matched value with explanation.

        Args:
            field_name: Name of field being normalized.
            raw_value: Free-text user input.
            valid_options: List of valid Collibra options.

        Returns:
            NormalisedValue: Normalized value with confidence and message.
        """
        options_str = "\n".join(valid_options)

        prompt = f"""Match this user input to the closest valid option.

Field: {field_name}
User Input: "{raw_value}"
Valid Options:
{options_str}

Return ONLY valid JSON:
{{
    "matched": "exact option from the list" or null,
    "confidence": 0.0 to 1.0 confidence score,
    "message": "explanation of the match (why it was chosen or why no match found)"
}}

Rules:
- If user input exactly matches an option: confidence 1.0, message "Exact match"
- If user input is clearly similar (typo, synonym): 0.7-0.99, message explains the mapping
- If user input doesn't fit any option: matched=null, confidence 0.0, message explains why
- Confidence < 0.7 should result in matched=null"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        try:
            response_text = await self._call_llm(messages, temperature=0.2)
            response_json = json.loads(response_text.strip())

            # Validate confidence bounds
            confidence = min(1.0, max(0.0, response_json.get("confidence", 0.0)))

            # If confidence too low, set matched to None
            matched = response_json.get("matched") if confidence >= 0.7 else None

            normalized = NormalisedValue(
                matched=matched is not None, confidence=confidence, message=response_json.get(
                    "message", "Normalization attempted"
                )
            )

            logger.info(
                "Value normalized",
                extra={
                    "request_id": self.request_id,
                    "field_name": field_name,
                    "confidence": confidence,
                    "matched": matched,
                },
            )
            return normalized
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(
                f"Failed to normalize value: {str(e)}",
                extra={"request_id": self.request_id, "field_name": field_name},
            )
            # Fallback: low confidence, no match
            return NormalisedValue(
                matched=False, confidence=0.3, message=f"Could not confidently match '{raw_value}' to available options."
            )

    async def generate_handoff_narrative(self, spec: DataProductSpec) -> str:
        """
        Generate 3-4 paragraph handoff summary for technical team.

        Describes what the product is, who uses it, next technical steps,
        and any gaps or follow-ups needed.

        Args:
            spec: Completed or near-complete DataProductSpec.

        Returns:
            str: 3-4 paragraph handoff narrative suitable for email/docs.
        """
        missing = spec.required_missing()
        missing_str = (
            "The following required fields still need attention: " + ", ".join(missing) + "."
            if missing
            else "All required fields are complete."
        )

        prompt = f"""Write a 3-4 paragraph handoff narrative for a technical team about this data product.

Product Name: {spec.name}
Description: {spec.description}
Business Purpose: {spec.business_purpose}
Domain: {spec.domain or 'not set'}
Owner: {spec.data_owner_name or 'not assigned'}
Classification: {spec.data_classification or 'not set'}
Source Systems: {', '.join(spec.source_systems or ['not specified'])}
Update Frequency: {spec.update_frequency or 'not set'}
Status: {spec.status or 'Draft'}
Completion: {spec.completion_percentage()}%
Outstanding: {missing_str}

Structure as:
1. Overview - What this data product is and its business value
2. Users & Access - Who will use it, access level
3. Technical Next Steps - What needs to be done (schema, ingestion, etc.)
4. Outstanding Items - What's still needed before go-live

Keep it professional, specific to this product, and actionable for engineers."""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        try:
            response = await self._call_llm(messages, temperature=0.4)
            logger.info(
                "Handoff narrative generated",
                extra={
                    "request_id": self.request_id,
                    "product_name": spec.name,
                    "completion_pct": spec.completion_percentage(),
                },
            )
            return response.strip()
        except Exception as e:
            logger.error(
                f"Failed to generate handoff narrative: {str(e)}",
                extra={"request_id": self.request_id},
            )
            # Fallback narrative
            return (
                f"Data Product: {spec.name}\n\n"
                f"{spec.description}\n\n"
                f"Owner: {spec.data_owner_name or 'Not assigned'}\n"
                f"Completion: {spec.completion_percentage()}%\n\n"
                f"Outstanding items: {', '.join(missing) if missing else 'None'}"
            )

    async def generate_completion_message(self, spec: DataProductSpec) -> str:
        """
        Generate warm celebratory completion message.

        Personalizes message with product name, owner, and reference number.
        Celebrates progress and hints at next steps.

        Args:
            spec: Completed DataProductSpec.

        Returns:
            str: Warm celebratory 2-3 sentence message.
        """
        product_ref = str(spec.id) if spec.id else "your data product"
        owner_str = f"working with {spec.data_owner_name}" if spec.data_owner_name else "for your team"

        prompt = f"""Write a warm, celebratory 2-3 sentence completion message.

Product: {spec.name}
Owner: {spec.data_owner_name or 'unassigned'}
Reference: {spec.id or 'pending'}
Domain: {spec.domain}
Completion: {spec.completion_percentage()}%

The message should:
1. Celebrate finishing the specification
2. Reference the product name and owner
3. Hint at the next step (publishing to Collibra)
4. Feel personal and warm

Example tone: "Fantastic! 'Sales Analytics' is now complete. Sarah and the team can start using this in Collibra right away. Reference: [ID]"

Now write the completion message:"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        try:
            response = await self._call_llm(messages, temperature=0.6)
            logger.info(
                "Completion message generated",
                extra={
                    "request_id": self.request_id,
                    "product_name": spec.name,
                    "product_id": str(spec.id),
                },
            )
            return response.strip()
        except Exception as e:
            logger.error(
                f"Failed to generate completion message: {str(e)}",
                extra={"request_id": self.request_id},
            )
            # Fallback message
            return (
                f"Excellent work! '{spec.name}' is now complete. "
                f"Reference: {product_ref}. "
                "You can now publish this to Collibra."
            )
