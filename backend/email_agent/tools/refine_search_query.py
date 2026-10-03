"""LLM task tool: refine KB search query from thread context (forced function call)."""

from __future__ import annotations

from email_agent.tools.builder import function_tool

REFINE_SEARCH_QUERY_TOOL_NAME = "refine_search_query"

REFINE_SEARCH_QUERY_TOOL = function_tool(
    name=REFINE_SEARCH_QUERY_TOOL_NAME,
    description=(
        "Rewrite thread context into one dense-retrieval query for the company KB. "
        "Query text should read like internal policy/rate documentation (standalone, "
        "domain terms), not a customer email. Use facts, summary, and latest email together."
    ),
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "Single query string for vector search: declarative, KB-style wording "
                    "(policies, rates, transit, customs, procedures). Standalone; include "
                    "stated IDs/lanes from facts; no invented numbers; not a reply to the customer."
                ),
            },
            "filters": {
                "type": "object",
                "additionalProperties": True,
                "description": (
                    "Optional retrieval filters. Known keys: top_k (int), company_id (string). "
                    "Omit keys to use server defaults."
                ),
            },
        },
        "required": ["query"],
    },
)
