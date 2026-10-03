"""LLM task tool: extract logistics facts from a customer email (forced function call)."""

from __future__ import annotations

from email_agent.tools.builder import function_tool

REPORT_EMAIL_EXTRACTION_TOOL_NAME = "report_email_extraction"

REPORT_EMAIL_EXTRACTION_TOOL = function_tool(
    name=REPORT_EMAIL_EXTRACTION_TOOL_NAME,
    description=(
        "Report logistics facts and open questions extracted from the customer email. "
        "Only include information explicitly stated in the email. "
        "Use snake_case keys in facts for whatever is stated (examples: order_id, price, "
        "currency, origin, destination, cargo_type, weight, volume, pallet_count, "
        "deadline, incoterms, contact_name) — not a fixed list; omit any key not in the email."
    ),
    parameters={
        "type": "object",
        "properties": {
            "subject_id": {
                "type": ["string", "null"],
                "description": (
                    "Stable identifier for this shipment or lane if stated (e.g. order_id, "
                    "PO number, booking number, quote ref, route label). Null if none."
                ),
            },
            "facts": {
                "type": "object",
                "additionalProperties": True,
                "description": (
                    "Required when the email states any shipment detail: non-empty object with "
                    "snake_case keys (origin, destination, weight_kg, volume_cbm, incoterms, "
                    "cargo_type, pallet_count, mode, lcl_or_fcl, etc.). Never leave {} if the "
                    "email mentions lane, cargo, weight, volume, or incoterms."
                ),
            },
            "open_questions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Specific questions the customer is asking.",
            },
        },
        "required": ["facts", "open_questions"],
    },
)
