"""
OpenTelemetry distributed tracing configuration.

This module provides centralized tracing setup for the Causal Organism platform.
It configures OpenTelemetry instrumentation for FastAPI, Celery, Redis, and HTTP clients.

Requirements:
- 16.1: API_Service SHALL emit OpenTelemetry traces for all incoming requests
- 16.2: Worker_Pool SHALL emit OpenTelemetry traces for all task executions
- 16.3: System SHALL propagate trace context across service boundaries
- 16.4: System SHALL include database query timing in traces
- 16.5: System SHALL include external API call timing in traces
- 16.6: System SHALL send traces to centralized collector (Jaeger/Tempo)
"""

import os
from typing import Optional
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

# Try to import Jaeger exporter, but make it optional
try:
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    JAEGER_AVAILABLE = True
except ImportError:
    JAEGER_AVAILABLE = False
    JaegerExporter = None


class TracingConfig:
    """
    Centralized tracing configuration for the platform.
    
    Supports multiple exporters:
    - Jaeger (default): For development and testing
    - OTLP: For production with Tempo or other OTLP-compatible backends
    """
    
    def __init__(
        self,
        service_name: str,
        service_version: str = "1.0.0",
        exporter_type: str = "jaeger",
        jaeger_host: str = "localhost",
        jaeger_port: int = 6831,
        otlp_endpoint: Optional[str] = None,
        enable_console_export: bool = False
    ):
        """
        Initialize tracing configuration.
        
        Args:
            service_name: Name of the service (e.g., "api-service", "worker-service")
            service_version: Version of the service
            exporter_type: Type of exporter ("jaeger" or "otlp")
            jaeger_host: Jaeger agent host
            jaeger_port: Jaeger agent port
            otlp_endpoint: OTLP collector endpoint (for Tempo, etc.)
            enable_console_export: Enable console exporter for debugging
        """
        self.service_name = service_name
        self.service_version = service_version
        self.exporter_type = exporter_type
        self.jaeger_host = jaeger_host
        self.jaeger_port = jaeger_port
        self.otlp_endpoint = otlp_endpoint
        self.enable_console_export = enable_console_export
        self.tracer_provider = None
        self.propagator = TraceContextTextMapPropagator()
    
    def setup_tracing(self) -> TracerProvider:
        """
        Set up OpenTelemetry tracing with configured exporter.
        
        Returns:
            TracerProvider instance
        """
        # Create resource with service information
        resource = Resource(attributes={
            SERVICE_NAME: self.service_name,
            SERVICE_VERSION: self.service_version,
            "deployment.environment": os.getenv("ENVIRONMENT", "development")
        })
        
        # Create tracer provider
        self.tracer_provider = TracerProvider(resource=resource)
        
        # Configure exporter based on type
        if self.exporter_type == "jaeger":
            if not JAEGER_AVAILABLE:
                raise ValueError(
                    "Jaeger exporter not available. Install with: pip install opentelemetry-exporter-jaeger"
                )
            exporter = JaegerExporter(
                agent_host_name=self.jaeger_host,
                agent_port=self.jaeger_port,
            )
        elif self.exporter_type == "otlp":
            if not self.otlp_endpoint:
                raise ValueError("OTLP endpoint must be provided for OTLP exporter")
            exporter = OTLPSpanExporter(endpoint=self.otlp_endpoint)
        else:
            raise ValueError(f"Unsupported exporter type: {self.exporter_type}")
        
        # Add batch span processor
        self.tracer_provider.add_span_processor(
            BatchSpanProcessor(exporter)
        )
        
        # Add console exporter for debugging if enabled
        if self.enable_console_export:
            from opentelemetry.sdk.trace.export import ConsoleSpanExporter
            console_exporter = ConsoleSpanExporter()
            self.tracer_provider.add_span_processor(
                BatchSpanProcessor(console_exporter)
            )
        
        # Set as global tracer provider
        trace.set_tracer_provider(self.tracer_provider)
        
        return self.tracer_provider
    
    def instrument_fastapi(self, app):
        """
        Instrument FastAPI application with OpenTelemetry.
        
        Requirements:
        - 16.1: Emit traces for all incoming requests
        - 16.3: Propagate trace context across service boundaries
        
        Args:
            app: FastAPI application instance
        """
        FastAPIInstrumentor.instrument_app(app)
    
    def instrument_celery(self):
        """
        Instrument Celery with OpenTelemetry.
        
        Requirements:
        - 16.2: Emit traces for all task executions
        - 16.3: Propagate trace context across service boundaries
        """
        CeleryInstrumentor().instrument()
    
    def instrument_redis(self):
        """
        Instrument Redis client with OpenTelemetry.
        
        Requirements:
        - 16.4: Include database query timing in traces
        """
        RedisInstrumentor().instrument()
    
    def instrument_httpx(self):
        """
        Instrument HTTPX HTTP client with OpenTelemetry.
        
        Requirements:
        - 16.5: Include external API call timing in traces
        
        This automatically instruments all HTTPX requests with tracing spans
        that include:
        - HTTP method and URL
        - Request and response headers
        - Status code
        - Request/response timing
        """
        HTTPXClientInstrumentor().instrument()
    
    def trace_http_call(self, method: str, url: str):
        """
        Manual decorator for tracing HTTP calls (for non-HTTPX clients).
        
        Requirements:
        - 16.5: Include external API call timing in traces
        
        Usage:
            @tracing_config.trace_http_call("POST", "https://api.example.com/endpoint")
            async def call_external_api(data):
                ...
        """
        def decorator(func):
            from functools import wraps
            import asyncio
            
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                with self.get_tracer().start_as_current_span(
                    f"http.{method.lower()}",
                    kind=trace.SpanKind.CLIENT
                ) as span:
                    span.set_attribute("http.method", method)
                    span.set_attribute("http.url", url)
                    
                    try:
                        result = await func(*args, **kwargs)
                        span.set_status(trace.Status(trace.StatusCode.OK))
                        return result
                    except Exception as e:
                        span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                        span.record_exception(e)
                        raise
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                with self.get_tracer().start_as_current_span(
                    f"http.{method.lower()}",
                    kind=trace.SpanKind.CLIENT
                ) as span:
                    span.set_attribute("http.method", method)
                    span.set_attribute("http.url", url)
                    
                    try:
                        result = func(*args, **kwargs)
                        span.set_status(trace.Status(trace.StatusCode.OK))
                        return result
                    except Exception as e:
                        span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                        span.record_exception(e)
                        raise
            
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    def get_tracer(self, name: str = None):
        """
        Get a tracer instance for manual instrumentation.
        
        Args:
            name: Tracer name (defaults to service name)
        
        Returns:
            Tracer instance
        """
        return trace.get_tracer(name or self.service_name)
    
    def get_current_trace_id(self) -> Optional[str]:
        """
        Get the current trace ID for logging and response headers.
        
        Requirements:
        - 16.3: Add trace ID to response headers
        - 16.3: Propagate trace IDs across service boundaries
        
        Returns:
            Trace ID as hex string, or None if no active span
        """
        span = trace.get_current_span()
        if span and span.get_span_context().is_valid:
            trace_id = span.get_span_context().trace_id
            return format(trace_id, '032x')
        return None
    
    def get_current_span_id(self) -> Optional[str]:
        """
        Get the current span ID for logging and debugging.
        
        Requirements:
        - 16.3: Propagate trace context across service boundaries
        
        Returns:
            Span ID as hex string, or None if no active span
        """
        span = trace.get_current_span()
        if span and span.get_span_context().is_valid:
            span_id = span.get_span_context().span_id
            return format(span_id, '016x')
        return None
    
    def inject_trace_context(self, carrier: dict) -> dict:
        """
        Inject trace context into a carrier (e.g., HTTP headers).
        
        Requirements:
        - 16.3: Propagate trace IDs across service boundaries
        
        This is useful for manual propagation when making HTTP requests
        or sending messages to queues.
        
        Args:
            carrier: Dictionary to inject context into (e.g., HTTP headers)
        
        Returns:
            Updated carrier with trace context
        
        Example:
            headers = {}
            tracing_config.inject_trace_context(headers)
            response = httpx.post(url, headers=headers)
        """
        self.propagator.inject(carrier)
        return carrier
    
    def extract_trace_context(self, carrier: dict):
        """
        Extract trace context from a carrier (e.g., HTTP headers).
        
        Requirements:
        - 16.3: Propagate trace IDs across service boundaries
        
        This is useful for manual extraction when receiving HTTP requests
        or consuming messages from queues.
        
        Args:
            carrier: Dictionary to extract context from (e.g., HTTP headers)
        
        Returns:
            Context object that can be used to continue the trace
        
        Example:
            context = tracing_config.extract_trace_context(request.headers)
            with tracer.start_as_current_span("operation", context=context):
                ...
        """
        return self.propagator.extract(carrier)
    
    def shutdown(self):
        """
        Shutdown tracing and flush remaining spans.
        """
        if self.tracer_provider:
            self.tracer_provider.shutdown()


def setup_api_tracing(app, service_name: str = "api-service") -> TracingConfig:
    """
    Convenience function to set up tracing for API service.
    
    Reads configuration from environment variables:
    - TRACING_ENABLED: Enable/disable tracing (default: true)
    - TRACING_EXPORTER: Exporter type ("jaeger" or "otlp", default: jaeger)
    - JAEGER_HOST: Jaeger agent host (default: localhost)
    - JAEGER_PORT: Jaeger agent port (default: 6831)
    - OTLP_ENDPOINT: OTLP collector endpoint
    - TRACING_CONSOLE: Enable console export for debugging (default: false)
    
    Args:
        app: FastAPI application instance
        service_name: Service name for tracing
    
    Returns:
        TracingConfig instance
    """
    # Check if tracing is enabled
    if os.getenv("TRACING_ENABLED", "true").lower() != "true":
        print("Tracing disabled by configuration")
        return None
    
    # Read configuration from environment
    exporter_type = os.getenv("TRACING_EXPORTER", "jaeger")
    jaeger_host = os.getenv("JAEGER_HOST", "localhost")
    jaeger_port = int(os.getenv("JAEGER_PORT", "6831"))
    otlp_endpoint = os.getenv("OTLP_ENDPOINT")
    enable_console = os.getenv("TRACING_CONSOLE", "false").lower() == "true"
    
    # Create tracing config
    tracing_config = TracingConfig(
        service_name=service_name,
        service_version=os.getenv("SERVICE_VERSION", "1.0.0"),
        exporter_type=exporter_type,
        jaeger_host=jaeger_host,
        jaeger_port=jaeger_port,
        otlp_endpoint=otlp_endpoint,
        enable_console_export=enable_console
    )
    
    # Setup tracing
    tracing_config.setup_tracing()
    
    # Instrument FastAPI
    tracing_config.instrument_fastapi(app)
    
    # Instrument Redis
    tracing_config.instrument_redis()
    
    # Instrument HTTPX
    tracing_config.instrument_httpx()
    
    print(f"Tracing enabled for {service_name} with {exporter_type} exporter")
    
    return tracing_config


def setup_worker_tracing(service_name: str = "worker-service") -> TracingConfig:
    """
    Convenience function to set up tracing for Celery workers.
    
    Reads configuration from environment variables (same as setup_api_tracing).
    
    Args:
        service_name: Service name for tracing
    
    Returns:
        TracingConfig instance
    """
    # Check if tracing is enabled
    if os.getenv("TRACING_ENABLED", "true").lower() != "true":
        print("Tracing disabled by configuration")
        return None
    
    # Read configuration from environment
    exporter_type = os.getenv("TRACING_EXPORTER", "jaeger")
    jaeger_host = os.getenv("JAEGER_HOST", "localhost")
    jaeger_port = int(os.getenv("JAEGER_PORT", "6831"))
    otlp_endpoint = os.getenv("OTLP_ENDPOINT")
    enable_console = os.getenv("TRACING_CONSOLE", "false").lower() == "true"
    
    # Create tracing config
    tracing_config = TracingConfig(
        service_name=service_name,
        service_version=os.getenv("SERVICE_VERSION", "1.0.0"),
        exporter_type=exporter_type,
        jaeger_host=jaeger_host,
        jaeger_port=jaeger_port,
        otlp_endpoint=otlp_endpoint,
        enable_console_export=enable_console
    )
    
    # Setup tracing
    tracing_config.setup_tracing()
    
    # Instrument Celery
    tracing_config.instrument_celery()
    
    # Instrument Redis
    tracing_config.instrument_redis()
    
    # Instrument HTTPX
    tracing_config.instrument_httpx()
    
    print(f"Tracing enabled for {service_name} with {exporter_type} exporter")
    
    return tracing_config
