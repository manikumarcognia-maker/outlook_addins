"""Build OpenAI-style function declarations for Gemini / LangChain bind_tools."""

from __future__ import annotations

from typing import Any


def function_tool(
    name: str,
    description: str,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    """One LLM task tool (schema only — no Python implementation)."""
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": parameters,
        },
    }
