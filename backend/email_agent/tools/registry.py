"""Catalog of email-agent LLM task tools. Add new tools here as phases ship."""

from __future__ import annotations

from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI

from email_agent.tools.refine_search_query import (
    REFINE_SEARCH_QUERY_TOOL,
    REFINE_SEARCH_QUERY_TOOL_NAME,
)
from email_agent.tools.report_email_extraction import (
    REPORT_EMAIL_EXTRACTION_TOOL,
    REPORT_EMAIL_EXTRACTION_TOOL_NAME,
)

_LLM_TASK_TOOLS: dict[str, dict[str, Any]] = {
    REPORT_EMAIL_EXTRACTION_TOOL_NAME: REPORT_EMAIL_EXTRACTION_TOOL,
    REFINE_SEARCH_QUERY_TOOL_NAME: REFINE_SEARCH_QUERY_TOOL,
}


def llm_task_tool_names() -> list[str]:
    return sorted(_LLM_TASK_TOOLS.keys())


def llm_task_tool_declaration(name: str) -> dict[str, Any]:
    try:
        return _LLM_TASK_TOOLS[name]
    except KeyError:
        known = ", ".join(llm_task_tool_names()) or "(none)"
        raise KeyError(f"Unknown LLM task tool: {name!r}. Known tools: {known}") from None


def bind_llm_task_tool(
    llm: ChatGoogleGenerativeAI,
    tool_name: str,
) -> Any:
    """Force the model to call exactly one registered task tool."""
    declaration = llm_task_tool_declaration(tool_name)
    return llm.bind_tools([declaration], tool_choice=tool_name)
