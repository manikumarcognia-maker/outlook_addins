"""Input validation helpers for email_agent."""


def require_non_empty(value: str, name: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError(f"{name} is required and cannot be empty.")
    return stripped
