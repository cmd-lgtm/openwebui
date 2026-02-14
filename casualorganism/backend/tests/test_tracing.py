"""
Tests for distributed tracing implementation.

Requirements:
- 16.1: API_Service SHALL emit OpenTelemetry traces for all incoming requests
- 16.2: Worker_Pool SHALL emit OpenTelemetry traces for all task executions
- 16.3: System SHALL propagate trace context across service boundaries
- 16.4: System SHALL include database query timing in traces
- 16.5: System SHALL include external API call timing in traces
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.core.tracing import TracingConfig, setup_api_tracing, setup_worker_tracing
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider


class TestTracingConfig:
    """Test TracingConfig class."""
    
    def test_tracing_config_initialization(self):
        """Test that TracingConfig initializes correctly."""
        config = TracingConfig(
            service_name="test-service",
            service_version="1.0.0",
            exporter_type="jaeger",
            jaeger_host="localhost",
            jaeger_port=6831
        )
        
        assert config.service_name == "test-service"
        assert config.service_version == "1.0.0"
        assert config.exporter_type == "jaeger"
        assert config.jaeger_host == "localhost"
        assert config.jaeger_port == 6831
    
    @patch('backend.core.tracing.JaegerExporter')
    @patch('backend.core.tracing.TracerProvider')
    def test_setup_tracing_with_jaeger(self, mock_tracer_provider, mock_jaeger_exporter):
        """Test that tracing setup works with Jaeger exporter."""
        config = TracingConfig(
            service_name="test-service",
            exporter_type="jaeger",
            jaeger_host="localhost",
            jaeger_port=6831
        )
        
        provider = config.setup_tracing()
        
        # Verify Jaeger exporter was created
        mock_jaeger_exporter.assert_called_once()
        
        # Verify tracer provider was created
        assert config.tracer_provider is not None
    
    def test_get_tracer(self):
        """Test that get_tracer returns a tracer instance."""
        config = TracingConfig(
            service_name="test-service",
            exporter_type="jaeger"
        )
        
        # Setup tracing first
        with patch('backend.core.tracing.JaegerExporter'):
            config.setup_tracing()
        
        tracer = config.get_tracer()
        assert tracer is not None
    
    def test_get_current_trace_id_no_span(self):
        """Test that get_current_trace_id returns None when no active span."""
        config = TracingConfig(
            service_name="test-service",
            exporter_type="jaeger"
        )
        
        trace_id = config.get_current_trace_id()
        assert trace_id is None
    
    def test_get_current_trace_id_with_span(self):
        """Test that get_current_trace_id returns trace ID when span is active."""
        config = TracingConfig(
            service_name="test-service",
            exporter_type="jaeger"
        )
        
        # Setup tracing
        with patch('backend.core.tracing.JaegerExporter'):
            config.setup_tracing()
        
        tracer = config.get_tracer()
        
        # Create a span
        with tracer.start_as_current_span("test-span") as span:
            trace_id = config.get_current_trace_id()
            
            # Verify trace ID is a valid hex string
            assert trace_id is not None
            assert len(trace_id) == 32  # 128-bit trace ID as hex
            assert all(c in '0123456789abcdef' for c in trace_id)
    
    def test_inject_trace_context(self):
        """Test that inject_trace_context adds trace headers."""
        config = TracingConfig(
            service_name="test-service",
            exporter_type="jaeger"
        )
        
        # Setup tracing
        with patch('backend.core.tracing.JaegerExporter'):
            config.setup_tracing()
        
        tracer = config.get_tracer()
        
        # Create a span and inject context
        with tracer.start_as_current_span("test-span"):
            carrier = {}
            config.inject_trace_context(carrier)
            
            # Verify traceparent header was added
            assert 'traceparent' in carrier
            assert carrier['traceparent'].startswith('00-')  # W3C trace context format


class TestSetupFunctions:
    """Test setup convenience functions."""
    
    @patch.dict('os.environ', {
        'TRACING_ENABLED': 'true',
        'TRACING_EXPORTER': 'jaeger',
        'JAEGER_HOST': 'localhost',
        'JAEGER_PORT': '6831'
    })
    @patch('backend.core.tracing.FastAPIInstrumentor')
    @patch('backend.core.tracing.RedisInstrumentor')
    @patch('backend.core.tracing.HTTPXClientInstrumentor')
    @patch('backend.core.tracing.JaegerExporter')
    def test_setup_api_tracing(
        self,
        mock_jaeger,
        mock_httpx,
        mock_redis,
        mock_fastapi
    ):
        """Test that setup_api_tracing configures all instrumentations."""
        mock_app = Mock()
        
        config = setup_api_tracing(mock_app, service_name="test-api")
        
        assert config is not None
        assert config.service_name == "test-api"
        
        # Verify instrumentations were called
        mock_fastapi.return_value.instrument_app.assert_called_once_with(mock_app)
        mock_redis.return_value.instrument.assert_called_once()
        mock_httpx.return_value.instrument.assert_called_once()
    
    @patch.dict('os.environ', {'TRACING_ENABLED': 'false'})
    def test_setup_api_tracing_disabled(self):
        """Test that setup_api_tracing returns None when disabled."""
        mock_app = Mock()
        
        config = setup_api_tracing(mock_app)
        
        assert config is None
    
    @patch.dict('os.environ', {
        'TRACING_ENABLED': 'true',
        'TRACING_EXPORTER': 'jaeger',
        'JAEGER_HOST': 'localhost',
        'JAEGER_PORT': '6831'
    })
    @patch('backend.core.tracing.CeleryInstrumentor')
    @patch('backend.core.tracing.RedisInstrumentor')
    @patch('backend.core.tracing.HTTPXClientInstrumentor')
    @patch('backend.core.tracing.JaegerExporter')
    def test_setup_worker_tracing(
        self,
        mock_jaeger,
        mock_httpx,
        mock_redis,
        mock_celery
    ):
        """Test that setup_worker_tracing configures all instrumentations."""
        config = setup_worker_tracing(service_name="test-worker")
        
        assert config is not None
        assert config.service_name == "test-worker"
        
        # Verify instrumentations were called
        mock_celery.return_value.instrument.assert_called_once()
        mock_redis.return_value.instrument.assert_called_once()
        mock_httpx.return_value.instrument.assert_called_once()


class TestDatabaseTracing:
    """Test database tracing instrumentation."""
    
    def test_neo4j_operation_extraction(self):
        """Test that Neo4j operation extraction works correctly."""
        from backend.core.connection_pool import Neo4jConnectionPool
        
        pool = Neo4jConnectionPool(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="password"
        )
        
        # Test various Cypher operations
        assert pool._extract_operation("MATCH (n) RETURN n") == "MATCH"
        assert pool._extract_operation("CREATE (n:Node)") == "CREATE"
        assert pool._extract_operation("MERGE (n:Node)") == "MERGE"
        assert pool._extract_operation("DELETE n") == "DELETE"
        assert pool._extract_operation("  MATCH (n)") == "MATCH"  # Leading whitespace
        assert pool._extract_operation("unknown query") == "UNKNOWN"
    
    def test_sql_operation_extraction(self):
        """Test that SQL operation extraction works correctly."""
        from backend.core.connection_pool import TimescaleConnectionPool
        
        pool = TimescaleConnectionPool(
            host="localhost",
            port=5432,
            database="test",
            user="postgres",
            password="password"
        )
        
        # Test various SQL operations
        assert pool._extract_sql_operation("SELECT * FROM table") == "SELECT"
        assert pool._extract_sql_operation("INSERT INTO table VALUES (1)") == "INSERT"
        assert pool._extract_sql_operation("UPDATE table SET x=1") == "UPDATE"
        assert pool._extract_sql_operation("DELETE FROM table") == "DELETE"
        assert pool._extract_sql_operation("  SELECT *") == "SELECT"  # Leading whitespace
        assert pool._extract_sql_operation("unknown query") == "UNKNOWN"


class TestTraceContextPropagation:
    """
    Test trace context propagation across service boundaries.
    
    Requirements:
    - 16.3: System SHALL propagate trace context across service boundaries
    """
    
    @patch('backend.core.tracing.JaegerExporter')
    def test_trace_context_propagation(self, mock_jaeger):
        """Test that trace context can be injected and extracted."""
        config = TracingConfig(
            service_name="test-service",
            exporter_type="jaeger"
        )
        
        config.setup_tracing()
        tracer = config.get_tracer()
        
        # Service A: Create span and inject context
        with tracer.start_as_current_span("service-a-operation") as span_a:
            trace_id_a = span_a.get_span_context().trace_id
            
            # Inject context into carrier (e.g., HTTP headers)
            carrier = {}
            config.inject_trace_context(carrier)
            
            # Verify carrier has trace context
            assert 'traceparent' in carrier
            
            # Service B: Extract context and create child span
            context = config.extract_trace_context(carrier)
            
            # Note: In a real scenario, Service B would use this context
            # to create a child span that continues the trace
            # For this test, we just verify the context was extracted
            assert context is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
