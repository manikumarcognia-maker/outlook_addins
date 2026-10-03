"""Parse forced single-tool LLM responses (Gemini / LangChain AIMessage.tool_calls)."""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import AIMessage


def parse_forced_tool_call(message: AIMessage, expected_tool_name: str) -> dict[str, Any]:
    """Return validated tool call args dict; fail fast on missing or wrong tool."""
    invalid = getattr(message, "invalid_tool_calls", None) or []
    if invalid:
        raise ValueError(f"Invalid tool call from model: {invalid}")

    tool_calls = getattr(message, "tool_calls", None) or []
    if not tool_calls:
        raise ValueError("Model did not return a tool call.")

    call = tool_calls[0]
    name = call.get("name") if isinstance(call, dict) else getattr(call, "name", None)
    if name != expected_tool_name:
        raise ValueError(f"Unexpected tool name: {name!r}")

    args = call.get("args") if isinstance(call, dict) else getattr(call, "args", None)
    if args is None:
        raise ValueError("Tool call missing args.")

    if isinstance(args, str):
        try:
            args = json.loads(args)
        except json.JSONDecodeError as exc:
            raise ValueError("Tool call args were not valid JSON.") from exc

    if not isinstance(args, dict):
        raise ValueError("Tool call args must be a JSON object.")

    return args
