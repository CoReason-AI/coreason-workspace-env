"""
Observability Service — Alias wrapper over TraceService for backward compatibility.
"""
from src.core.services.trace_service import TraceService, trace_service

ObservabilityService = TraceService
observability_service = trace_service

__all__ = ["ObservabilityService", "observability_service", "TraceService", "trace_service"]
