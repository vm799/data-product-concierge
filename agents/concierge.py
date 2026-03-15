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
        "You are the Data Product Concierge for a global asset management firm. "
        "Your job is to guide portfolio managers, analysts, and operations staff through "
        "finding, adapting, or creating data products in Collibra. "
        "\n\nTONE: Semi-formal, direct, and genuinely helpful. Write like a knowledgeable colleague, "
        "not a customer service bot. Short sentences. Active voice. "
        "\n\nRULES:"
        "\n- Never use hollow openers: no 'Certainly', 'Absolutely', 'Great question', "
        "'Of course', 'Fantastic', 'I would be happy to', 'Sure thing', or similar filler. "
        "\n- Do not use em dashes (the — character). Use a comma, colon, or period instead. "
        "\n- Reference specific product names, domains, and field values from the data given to you. "
        "Do not speak in generalities when specifics are available. "
        "\n- Only state facts that appear in the data provided. Do not invent field values, "
        "regulatory implications, technical capabilities, or team structures that were not mentioned. "
        "If something is unknown, say so plainly. "
        "\n- Keep narrative responses to 2-3 sentences. Field explanations: 1 sentence only. "
        "\n- Explain any technical term the first time you use it, in plain English."
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

    async def _call_llm(
        self, messages: list[dict], temperature: float = 0.3, json_mode: bool = False
    ) -> str:
        """
        Dispatch LLM call to configured backend (OpenAI or Bedrock).

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            temperature: Sampling temperature (0.0-1.0).
            json_mode: When True, enforces JSON-only output (OpenAI response_format).
                       Use for all structured extraction calls to prevent hallucination drift.

        Returns:
            str: LLM response text.
        """
        try:
            if self.llm_provider == "bedrock":
                return await self._call_bedrock(messages, temperature)
            else:
                return await self._call_openai(messages, temperature, json_mode=json_mode)
        except Exception as e:
            logger.error(
                f"LLM call failed: {str(e)}",
                extra={"request_id": self.request_id, "error_type": type(e).__name__},
            )
            raise

    async def _call_openai(
        self, messages: list[dict], temperature: float, json_mode: bool = False
    ) -> str:
        """
        Call OpenAI API with async client.

        json_mode=True forces response_format=json_object, which eliminates markdown
        fences and hallucinated prose around JSON — making extraction deterministic.
        Only use when the prompt explicitly asks for JSON output.
        """
        kwargs: dict = dict(
            model=self.openai_model,
            messages=messages,
            temperature=temperature,
            max_tokens=2000,
        )
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        response = await self.openai_client.chat.completions.create(**kwargs)
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
            response_text = await self._call_llm(messages, temperature=0.2, json_mode=True)
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
            response_text = await self._call_llm(messages, temperature=0.2, json_mode=True)
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

        prompt = f"""Write a 2-3 sentence introduction to chapter {chapter_num} of a data product specification form.

Product: {context_str}
Progress: {completion_pct}% complete
Chapter: {chapter_name}
{remaining_str}

Instructions:
- Mention the current progress (e.g. "{completion_pct}% done") and what this chapter covers, in plain English.
- Reference the product name or domain if available.
- If all required fields are on track, say so simply.
- Do not use em dashes. Do not use hollow phrases like "Great!", "Fantastic", or "Let's dive in".
- Write like a knowledgeable colleague, not a chatbot. Semi-formal, direct.
- 2-3 sentences only. No preamble."""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        try:
            response = await self._call_llm(messages, temperature=0.3)
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
        prompt = f"""Explain this data product field in exactly one sentence for non-technical users at an asset management firm.

Field: {field_name}
Context: {context}

Rules:
- One sentence. No more.
- Explain why this field matters in practice, not what it is in theory.
- Use plain English. If a technical term is necessary, define it in the same sentence.
- Do not start with the field name. Do not use em dashes.
- Only reference facts in the context above. Do not invent regulatory implications or team structures.

Example: "This tells your team which information security rules apply, so you know whether this data can be shared externally or must stay confidential."

Now write one sentence for '{field_name}':"""

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
            response_text = await self._call_llm(messages, temperature=0.1, json_mode=True)
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

        prompt = f"""Write a handoff note for the technical team building this data product.

--- SPEC DATA (use only these facts) ---
Product: {spec.name}
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
--- END SPEC DATA ---

Write 3-4 short paragraphs:
1. What this product is and why it exists (use the description and business_purpose above verbatim or paraphrased closely)
2. Who will use it and at what access level (only if access_level or consumer_teams are set)
3. What the technical team needs to do next (only reference schema_location, source_systems, and update_frequency from the data above)
4. Outstanding fields that still need completing before go-live

Rules:
- Only use facts from the spec data above. Do not invent source systems, teams, schemas, or regulatory requirements.
- Do not use em dashes. Write in plain, direct English.
- No hollow openers. Start paragraph 1 directly with the product name.
- If a field is "not set", acknowledge it is still needed rather than inventing a value."""

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

        prompt = f"""Write a 2-3 sentence message confirming that a data product specification is complete.

Product: {spec.name}
Owner: {spec.data_owner_name or 'not assigned'}
Reference: {spec.id or 'pending'}
Domain: {spec.domain or 'not set'}
Completion: {spec.completion_percentage()}%

Rules:
- Reference the product name and owner directly.
- Mention that the next step is publishing to Collibra, and include the reference ID if available.
- Do not start with "Fantastic", "Great", "Excellent", or any hollow opener.
- Do not use em dashes. Write plainly and warmly, like a colleague confirming good news.
- 2-3 sentences only.

Example: "'{spec.name}' is now complete and ready to submit. {spec.data_owner_name or 'The team'} can follow up via Collibra using reference {spec.id or 'pending'}."

Now write the message:"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        try:
            response = await self._call_llm(messages, temperature=0.3)
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

    async def explain_chapter_fields(
        self, chapter_num: int, chapter_name: str, spec: DataProductSpec
    ) -> dict:
        """
        Generate context-aware explanations for all fields in a chapter.

        One LLM call returns a JSON dict {field_name: explanation} for every
        field in the chapter. Explanations reference the specific product being
        built (name, domain, regulatory scope) so guidance is relevant, not generic.

        Args:
            chapter_num: Chapter number (1-5).
            chapter_name: Human-readable chapter name.
            spec: DataProductSpec with fields populated so far (for context).

        Returns:
            dict: {field_name: "1-sentence explanation"} for all chapter fields.
        """
        chapter_fields = {
            1: ["name", "description", "business_purpose", "status", "version"],
            2: ["domain", "sub_domain", "data_classification", "tags"],
            3: [
                "data_owner_name", "data_owner_email", "data_steward_name",
                "data_steward_email", "certifying_officer_email", "last_certified_date",
            ],
            4: [
                "regulatory_scope", "geographic_restriction", "pii_flag",
                "encryption_standard", "retention_period", "source_systems",
                "update_frequency", "schema_location",
            ],
            5: [
                "access_level", "consumer_teams", "sla_tier",
                "business_criticality", "cost_centre", "related_reports",
            ],
        }
        fields = chapter_fields.get(chapter_num, [])
        fields_json = json.dumps(fields)

        product_context = spec.name or "a new data product"
        domain_context = f" in the {spec.domain} domain" if spec.domain else ""
        reg_context = (
            f" governed by {', '.join(str(r) for r in spec.regulatory_scope)}"
            if spec.regulatory_scope
            else ""
        )

        prompt = f"""Return a JSON object with one-sentence explanations for each data product field listed below.

Product: {product_context}{domain_context}{reg_context}
Chapter {chapter_num}: {chapter_name}
Fields: {fields_json}

Rules for each explanation:
- One sentence only. Plain English. No em dashes.
- Explain the practical consequence of this field, not its definition.
- If a domain or regulatory framework is in scope, reference it specifically (e.g. "GDPR" or "SFDR") only if it is listed above. Do not invent regulatory context.
- Do not start with the field name as the subject.
- Do not use hollow phrases like "This important field..." or "This field allows you to...".

Return ONLY a JSON object in this exact format, no preamble:
{{
  "field_name": "One sentence.",
  ...
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        try:
            response_text = await self._call_llm(messages, temperature=0.2, json_mode=True)
            # Strip markdown code fences if present (Bedrock may still add them)
            clean = response_text.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            explanations = json.loads(clean.strip())
            logger.info(
                "Chapter field explanations generated",
                extra={
                    "request_id": self.request_id,
                    "chapter_num": chapter_num,
                    "field_count": len(explanations),
                },
            )
            return explanations
        except Exception as e:
            logger.error(
                f"Failed to generate chapter field explanations: {str(e)}",
                extra={"request_id": self.request_id, "chapter_num": chapter_num},
            )
            # Fallback: generic per-field explanation
            return {f: f"{f} is required to complete your data product specification." for f in fields}

    async def seed_new_product(self, query: str, intent: "ConciergeIntent") -> dict:
        """
        Draft initial field values for a CREATE flow from the user's query.

        Uses the already-parsed ConciergeIntent (detected_domain, detected_scope)
        to avoid hallucination on structured fields. Only generates free-text fields
        (name, description, business_purpose) via LLM.

        Args:
            query: Original user query string.
            intent: ConciergeIntent parsed from the query.

        Returns:
            dict: Partial spec fields {name, description, business_purpose,
                  domain, regulatory_scope}. Falls back to {} on error.
        """
        domain = intent.detected_domain or ""
        reg_scope = intent.detected_scope or []

        prompt = f"""A user at an asset management firm submitted this query to find or create a data product:

"{query}"

Using only what they literally said, draft three fields for their specification.

Return ONLY valid JSON:
{{
    "name": "3-6 word title, title case. Derived directly from their words. No generic suffixes like 'Data Product' or 'Dataset'.",
    "description": "2-3 sentences. Describe what data this product contains. Use their exact terminology. Do not add capabilities, systems, or use cases they did not mention.",
    "business_purpose": "1-2 sentences. Explain the business need they expressed. Quote or closely paraphrase their words."
}}

Critical rules:
- Do not invent source systems, regulatory frameworks, team names, or technical capabilities.
- If the query is vague, keep the drafted fields vague rather than filling gaps with assumptions.
- Do not use em dashes in the output.
- name, description, and business_purpose are the only fields to return."""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        try:
            response_text = await self._call_llm(messages, temperature=0.2, json_mode=True)
            clean = response_text.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            seed = json.loads(clean.strip())

            # Inject structured fields directly from intent — no LLM hallucination risk
            if domain:
                seed["domain"] = domain
            if reg_scope:
                seed["regulatory_scope"] = reg_scope

            logger.info(
                "New product seeded from query",
                extra={
                    "request_id": self.request_id,
                    "detected_domain": domain,
                    "detected_scope": reg_scope,
                    "seeded_name": seed.get("name", ""),
                },
            )
            return seed
        except Exception as e:
            logger.error(
                f"Failed to seed new product: {str(e)}",
                extra={"request_id": self.request_id},
            )
            return {}

    async def chat_turn(
        self,
        user_message: str,
        history: list[dict],
        spec: "DataProductSpec",
        valid_options: dict,
    ) -> dict:
        """
        Process one conversational turn for the CREATE flow.

        Extracts spec field values from natural language, confirms capture,
        and asks about the next missing required field.

        Args:
            user_message: Latest message from the user.
            history: Prior conversation messages [{role, content}].
            spec: DataProductSpec accumulated so far.
            valid_options: Collibra-fed option lists (source_systems, etc.).

        Returns:
            dict with keys: response (str), extracted (dict), is_complete (bool)
        """
        missing = spec.required_missing()

        spec_state = {
            "name": spec.name or "(not set)",
            "description": spec.description or "(not set)",
            "business_purpose": spec.business_purpose or "(not set)",
            "domain": spec.domain or "(not set)",
            "data_classification": str(spec.data_classification) if spec.data_classification else "(not set)",
            "data_owner_name": spec.data_owner_name or "(not set)",
            "data_owner_email": str(spec.data_owner_email) if spec.data_owner_email else "(not set)",
            "data_steward_email": str(spec.data_steward_email) if spec.data_steward_email else "(not set)",
            "regulatory_scope": [str(r) for r in spec.regulatory_scope] if spec.regulatory_scope else [],
            "source_systems": spec.source_systems or [],
            "update_frequency": str(spec.update_frequency) if spec.update_frequency else "(not set)",
            "schema_location": spec.schema_location or "(not set)",
            "access_level": str(spec.access_level) if spec.access_level else "(not set)",
            "sla_tier": str(spec.sla_tier) if spec.sla_tier else "(not set)",
            "business_criticality": str(spec.business_criticality) if spec.business_criticality else "(not set)",
        }

        history_text = "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in history[-6:]
        )

        enum_options = {
            "data_classification": ["Confidential", "Internal", "Public", "Restricted"],
            "update_frequency": ["Real-time", "Hourly", "Daily", "Weekly", "Monthly", "Ad-hoc"],
            "access_level": ["Open", "Request-based", "Restricted", "Confidential"],
            "sla_tier": ["Gold (99.9%)", "Silver (99.5%)", "Bronze (99%)", "None"],
            "business_criticality": ["Mission-critical", "High", "Medium", "Low"],
            "regulatory_scope": ["GDPR", "MiFID II", "AIFMD", "BCBS 239", "Solvency II",
                                  "CCPA", "HIPAA", "PCI-DSS", "SOX", "GLBA", "SFDR", "EU Taxonomy", "TCFD"],
            "source_systems": valid_options.get("source_systems", []),
            "consumer_teams": valid_options.get("consumer_teams", []),
        }

        prompt = f"""You are a warm, expert Data Product Concierge at a global asset management firm.
You are having a CONVERSATION with a user to help them create a new data product specification.

CURRENT SPEC STATE:
{json.dumps(spec_state, indent=2)}

REQUIRED FIELDS STILL MISSING:
{', '.join(missing) if missing else 'None — all required fields are complete!'}

RECENT CONVERSATION:
{history_text}

USER'S LATEST MESSAGE:
"{user_message}"

VALID OPTIONS FOR KEY FIELDS:
{json.dumps(enum_options, indent=2)}

YOUR TASK:
1. Extract any field values the user just provided. Be generous: if it is reasonably clear, capture it.
2. Write a response (2-3 sentences):
   - Confirm what was captured, using the actual values.
   - Ask about the next 1-2 missing required fields.
   - For enum fields, include the valid options in the question naturally.
3. Set is_complete=true only when no required fields remain after extraction.

RESPONSE TONE RULES:
- Write like a knowledgeable colleague. Semi-formal, direct.
- Do not open with "Certainly", "Absolutely", "Great", "Fantastic", or similar filler.
- Do not use em dashes (—). Use commas or periods instead.
- Only confirm values the user actually provided. Do not paraphrase or embellish their answers.

EXTRACTION RULES:
- For list fields (regulatory_scope, source_systems): extract as JSON array.
- For enum fields: use the EXACT string from valid options above. Do not invent options.
- If user says "skip" or "not sure", note it and move to the next field.

Return ONLY valid JSON:
{{
    "response": "2-3 sentence response following the tone rules above.",
    "extracted": {{
        "field_name": value
    }},
    "is_complete": false
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        try:
            response_text = await self._call_llm(messages, temperature=0.3, json_mode=True)
            clean = response_text.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            result = json.loads(clean.strip())
            logger.info(
                "Chat turn processed",
                extra={
                    "request_id": self.request_id,
                    "fields_extracted": list(result.get("extracted", {}).keys()),
                    "is_complete": result.get("is_complete", False),
                },
            )
            return {
                "response": result.get("response", "Got it! What else can you tell me?"),
                "extracted": result.get("extracted", {}),
                "is_complete": bool(result.get("is_complete", False)) and not missing,
            }
        except Exception as e:
            logger.error(f"Chat turn failed: {str(e)}", extra={"request_id": self.request_id})
            next_field = missing[0].replace("_", " ") if missing else None
            return {
                "response": (
                    "Got it, I've noted that."
                    + (f" Now, could you tell me your **{next_field}**?" if next_field else " Great progress — we're almost there!")
                ),
                "extracted": {},
                "is_complete": False,
            }
