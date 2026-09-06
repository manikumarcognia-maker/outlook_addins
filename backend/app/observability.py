import json
import logging
import time
from collections.abc import Iterator
from contextlib import contextmanager
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter, SpanExportResult
from opentelemetry.trace import Status, StatusCode

SERVICE_NAME = "fr8labs-outlook-addin-backend"
_tracer: trace.Tracer | None = None
_observability_configured = False


class _FileSpanExporter(SpanExporter):
    """Writes finished OpenTelemetry spans to the application log file."""

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    def export(self, spans: list[ReadableSpan]) -> SpanExportResult:
        for span in spans:
            duration_ms = 0.0
            if span.start_time and span.end_time:
                duration_ms = (span.end_time - span.start_time) / 1_000_000

            attributes = {
                key: _serialize_attribute(value)
                for key, value in (span.attributes or {}).items()
            }
            self._logger.info(
                "OTEL_SPAN | name=%s | trace_id=%s | span_id=%s | duration_ms=%.2f | status=%s | attributes=%s",
                span.name,
                format(span.context.trace_id, "032x"),
                format(span.context.span_id, "016x"),
                duration_ms,
                span.status.status_code.name if span.status else "UNSET",
                json.dumps(attributes, default=str),
            )
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:
        return None


def _serialize_attribute(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple)):
        return [_serialize_attribute(item) for item in value]
    return str(value)


def configure_observability(log_file: Path, log_level: str = "INFO") -> logging.Logger:
    """Configure root logging and OpenTelemetry tracing (spans → log file)."""
    global _tracer, _observability_configured

    app_logger = logging.getLogger("fr8labs")
    if _observability_configured:
        return app_logger

    log_file.parent.mkdir(parents=True, exist_ok=True)
    level = getattr(logging, log_level.upper(), logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root.addHandler(console)

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    # Keep application logs readable — hide per-request HTTP wire logs.
    for noisy_logger in ("httpx", "httpcore", "google_genai.models"):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)

    otel_logger = logging.getLogger("fr8labs.otel")
    resource = Resource.create({"service.name": SERVICE_NAME})
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(SimpleSpanProcessor(_FileSpanExporter(otel_logger)))
    trace.set_tracer_provider(provider)
    _tracer = trace.get_tracer(SERVICE_NAME)

    app_logger.info("Observability configured | log_file=%s | log_level=%s", log_file, log_level)
    _observability_configured = True
    return app_logger


def get_tracer() -> trace.Tracer:
    if _tracer is None:
        return trace.get_tracer(SERVICE_NAME)
    return _tracer


@contextmanager
def trace_step(step: str, logger: logging.Logger, **attributes: Any) -> Iterator[None]:
    """Create an OTel span and log step start/end with timing."""
    tracer = get_tracer()
    safe_attrs = {key: _serialize_attribute(value) for key, value in attributes.items()}
    started = time.perf_counter()

    logger.info("STEP_START | %s | %s", step, json.dumps(safe_attrs, default=str))

    with tracer.start_as_current_span(step, attributes=safe_attrs) as span:
        try:
            yield
        except Exception as exc:
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            span.record_exception(exc)
            elapsed_ms = (time.perf_counter() - started) * 1000
            logger.exception(
                "STEP_ERROR | %s | elapsed_ms=%.1f | error=%s",
                step,
                elapsed_ms,
                exc,
            )
            raise
        else:
            elapsed_ms = (time.perf_counter() - started) * 1000
            span.set_status(Status(StatusCode.OK))
            logger.info("STEP_END | %s | elapsed_ms=%.1f", step, elapsed_ms)
