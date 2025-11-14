"""
Story 2.5: Intent Classification & Domain Routing

Classifies user queries into knowledge domains using GPT-4o function calling.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json

from openai import OpenAI
import os

logger = logging.getLogger(__name__)


# Define the 7 PLC knowledge domains
DOMAINS = {
    "assessment": "Formative and summative assessments, grading practices, evaluation methods",
    "collaboration": "Team structures, collaborative norms, meeting protocols, teamwork",
    "leadership": "Principal and administrator guidance, change management, leadership practices",
    "curriculum": "Guaranteed and viable curriculum, standards alignment, curriculum design",
    "data_analysis": "RTI, Response to Intervention, MTSS, data-driven decisions, progress monitoring",
    "school_culture": "PLC implementation, culture building, professional learning communities",
    "student_learning": "Student-centered practices, engagement, motivation, achievement"
}


# Function calling schema for GPT-4o
CLASSIFICATION_FUNCTION = {
    "name": "classify_query_domain",
    "description": "Classify a PLC (Professional Learning Community) query into knowledge domains",
    "parameters": {
        "type": "object",
        "properties": {
            "primary_domain": {
                "type": "string",
                "enum": list(DOMAINS.keys()),
                "description": "The primary knowledge domain for this query"
            },
            "secondary_domains": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": list(DOMAINS.keys())
                },
                "description": "Additional relevant domains (max 2)"
            },
            "needs_clarification": {
                "type": "boolean",
                "description": "Whether the query is too vague and needs clarification"
            },
            "clarification_question": {
                "type": "string",
                "description": "A question to help clarify the user's intent (if needs_clarification is true)"
            },
            "confidence": {
                "type": "number",
                "description": "Confidence score 0-1 for the classification"
            }
        },
        "required": ["primary_domain", "secondary_domains", "needs_clarification", "confidence"]
    }
}


class IntentRouter:
    """Routes queries to appropriate knowledge domains using GPT-4o."""

    def __init__(self, api_key: Optional[str] = None, cache_ttl_seconds: int = 3600):
        """Initialize the intent router.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            cache_ttl_seconds: Time to live for cached classifications
        """
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.cache: Dict[str, Dict] = {}
        self.cache_ttl = timedelta(seconds=cache_ttl_seconds)

    def _get_system_prompt(self) -> str:
        """Get the system prompt for intent classification.

        Returns:
            System prompt string
        """
        domain_descriptions = "\n".join([
            f"- {domain}: {description}"
            for domain, description in DOMAINS.items()
        ])

        return f"""You are an expert at classifying questions about Professional Learning Communities (PLCs) into knowledge domains.

Available domains:
{domain_descriptions}

Your task is to:
1. Identify the PRIMARY domain that best fits the user's question
2. Identify up to 2 SECONDARY domains if the question spans multiple areas
3. Determine if the question is TOO VAGUE and needs clarification
4. If vague, suggest a clarifying question to help narrow down the user's intent
5. Provide a confidence score (0-1) for your classification

Guidelines:
- Be specific: choose the most directly relevant domain
- A question about "assessment" should go to "assessment", not "data_analysis"
- A question about "team meetings" should go to "collaboration"
- A question about "RTI process" should go to "data_analysis"
- If the question mentions multiple domains explicitly, include them as secondary
- Mark as needs_clarification if the question is:
  * Too broad ("How do I do PLCs?")
  * Unclear what aspect they're asking about
  * Missing key context

Be decisive - most questions should NOT need clarification unless truly vague."""

    def classify(self, query: str) -> Dict:
        """Classify a user query into knowledge domains.

        Args:
            query: User's question or query

        Returns:
            Classification dictionary with domains and metadata
        """
        # Check cache
        cache_key = query.lower().strip()
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if datetime.utcnow() < cached['expires_at']:
                logger.info(f"Cache hit for query: {query[:50]}...")
                return cached['result']
            else:
                # Expired, remove from cache
                del self.cache[cache_key]

        try:
            # Call GPT-4o with function calling
            response = self.client.chat.completions.create(
                model="gpt-4o",
                temperature=0.1,  # Low temperature for consistency
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": f"Classify this PLC query: {query}"}
                ],
                functions=[CLASSIFICATION_FUNCTION],
                function_call={"name": "classify_query_domain"}
            )

            # Extract function call result
            function_call = response.choices[0].message.function_call
            result = json.loads(function_call.arguments)

            # Ensure secondary_domains doesn't include primary
            if result['primary_domain'] in result.get('secondary_domains', []):
                result['secondary_domains'].remove(result['primary_domain'])

            # Limit secondary domains to 2
            result['secondary_domains'] = result.get('secondary_domains', [])[:2]

            # Cache the result
            self.cache[cache_key] = {
                'result': result,
                'expires_at': datetime.utcnow() + self.cache_ttl
            }

            logger.info(f"Classified query into domain: {result['primary_domain']}")
            return result

        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            # Return a default classification
            return {
                "primary_domain": "school_culture",  # Safe default
                "secondary_domains": [],
                "needs_clarification": False,
                "confidence": 0.3,
                "error": str(e)
            }

    def get_domain_description(self, domain: str) -> Optional[str]:
        """Get the description for a domain.

        Args:
            domain: Domain name

        Returns:
            Domain description or None
        """
        return DOMAINS.get(domain)

    def get_all_domains(self) -> Dict[str, str]:
        """Get all available domains and their descriptions.

        Returns:
            Dictionary of domain names to descriptions
        """
        return DOMAINS.copy()

    def clear_cache(self):
        """Clear the classification cache."""
        self.cache.clear()
        logger.info("Classification cache cleared")
