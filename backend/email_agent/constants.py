"""Shared constants for the email-thread agent."""

RETRIEVAL_MAX_ATTEMPTS = 3
RETRIEVAL_BACKOFF_BASE_SEC = 2

THREAD_FOLD_WHEN_OVER = 10
THREAD_RECENT_KEEP = 3
# When summary is still empty, fold narrative after this many messages (before FOLD_WHEN_OVER).
THREAD_SUMMARY_BOOTSTRAP_AT = 2

DEFAULT_SHIPMENT_SUBJECT_ID = "general"
OPEN_QUESTIONS_FACT_KEY = "open_questions"

SYNTHESIS_LLM_EMPTY_RETRIES = 2
