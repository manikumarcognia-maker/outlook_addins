"""LLM task tools — function declarations for forced model calls (not executable app tools).

Add a new module per tool (e.g. refine_search_query.py), register in registry.py.
"""

from email_agent.tools.builder import function_tool
from email_agent.tools.registry import (
    bind_llm_task_tool,
    llm_task_tool_declaration,
    llm_task_tool_names,
)
from email_agent.tools.refine_search_query import (
    REFINE_SEARCH_QUERY_TOOL,
    REFINE_SEARCH_QUERY_TOOL_NAME,
)
from email_agent.tools.report_email_extraction import (
    REPORT_EMAIL_EXTRACTION_TOOL,
    REPORT_EMAIL_EXTRACTION_TOOL_NAME,
)

__all__ = [
    "REFINE_SEARCH_QUERY_TOOL",
    "REFINE_SEARCH_QUERY_TOOL_NAME",
    "REPORT_EMAIL_EXTRACTION_TOOL",
    "REPORT_EMAIL_EXTRACTION_TOOL_NAME",
    "bind_llm_task_tool",
    "function_tool",
    "llm_task_tool_declaration",
    "llm_task_tool_names",
]
