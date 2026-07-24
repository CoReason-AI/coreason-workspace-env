import structlog
import logging
import logging.config
import sys
import os
from opentelemetry import context, trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as OTLPHttpSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter as OTLPGrpcSpanExporter
from opentelemetry.sdk.resources import Resource

def setup_telemetry(log_level: int = logging.INFO):
    """
    Bootstraps the open-source ambient telemetry stack (structlog + OpenTelemetry).
    Replaces standard logging with structlog configured for ContextVars,
    and hijacks third-party standard logging so they inherit ContextVars.
    Also initializes the OpenTelemetry TracerProvider and OTLPSpanExporter.
    """
    # 0. Initialize OpenTelemetry TracerProvider with OTLP Exporter (if enabled)
    if os.environ.get("OTEL_SDK_DISABLED", "false").lower() != "true":
        # Default to gRPC for the Open Shell Sandbox OTEL collector sidecar
        otel_protocol = os.environ.get("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc").lower()
        if otel_protocol == "http/protobuf":
            otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318/v1/traces")
            otlp_exporter = OTLPHttpSpanExporter(endpoint=otlp_endpoint)
        else:
            # gRPC default endpoint
            otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
            otlp_exporter = OTLPGrpcSpanExporter(endpoint=otlp_endpoint, insecure=True)

        resource = Resource.create({"service.name": "coreason-workspace-env"})
        
        provider = TracerProvider(resource=resource)
        span_processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(span_processor)
        trace.set_tracer_provider(provider)

    # 1. Configure structlog to merge ContextVars globally
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # 2. Hijack standard logging (FastAPI, Langchain) to route through structlog
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.dev.ConsoleRenderer(colors=True),
        ],
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

def set_ambient_session(session_id: str):
    """
    Binds the session ID globally to structlog ContextVars.
    This guarantees that deeply nested async functions inherit the trace ID 
    without passing it manually, avoiding memory leaks via native async safety.
    """
    # Bind to structlog for all subsequent log messages in this async tree
    structlog.contextvars.bind_contextvars(session_id=session_id)
        
    return None

def get_ambient_session() -> str:
    """
    Retrieves the ambient session_id from structlog contextvars.
    """
    return structlog.contextvars.get_contextvars().get("session_id", "unknown")
