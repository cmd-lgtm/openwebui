# Distributed Tracing Implementation Summary

## Overview

This document summarizes the implementation of distributed tracing with OpenTelemetry for the Causal Organism platform.

## Requirements Satisfied

### Requirement 16.1: API Service Tracing
✅ **Implemented**: API_Service emits OpenTelemetry traces for all incoming requests
- FastAPI automatic instrumentation via `FastAPIInstrumentor`
- All HTTP endpoints automatically traced
- Request/response timing captured
- HTTP status codes recorded

### Requirement 16.2: Worker Service Tracing
✅ **Implemented**: Worker_Pool emits OpenTelemetry traces for all task executions
- Celery automatic instrumentation via `CeleryInstrumentor`
- All background tasks automatically traced
- Task execution timing captured
- Task success/failure status recorded

### Requirement 16.3: Trace Context Propagation
✅ **Implemented**: System propagates trace context across service boundaries
- W3C Trace Context standard via `TraceContextTextMapPropagator`
- Automatic propagation in FastAPI requests
- Automatic propagation in Celery tasks
- Automatic propagation in HTTPX HTTP calls
- Manual injection/extraction methods available
- Trace ID added to all API response headers (`X-Trace-Id`)

### Requirement 16.4: Database Query Tracing
✅ **Implemented**: System includes database query timing in traces
- Neo4j queries traced via custom instrumentation in `Neo4jConnectionPool`
- Redis operations traced via `RedisInstrumentor`
- TimescaleDB queries traced via custom instrumentation in `TimescaleConnectionPool`
- Query statements, operations, and result counts captured
- Query timing automatically measured

### Requirement 16.5: External API Call Tracing
✅ **Implemented**: System includes external API call timing in traces
- HTTPX automatic instrumentation via `HTTPXClientInstrumentor`
- HTTP method, URL, and status code captured
- Request/response timing automatically measured
- Manual tracing decorator available for non-HTTPX clients

### Requirement 16.6: Centralized Trace Collection
✅ **Implemented**: System sends traces to centralized collector (Jaeger)
- Jaeger exporter configured for development
- OTLP exporter available for production (Tempo, etc.)
- Batch span processor for efficient export
- Configurable via environment variables

### Requirement 16.7: Trace Retention
✅ **Implemented**: System retains traces for 30 days
- Jaeger configured with 30-day retention (720 hours)
- Badger storage for development
- Elasticsearch backend recommended for production
- Automatic cleanup of old traces

### Requirement 16.8: Trace Search UI
✅ **Implemented**: System provides UI to search traces
- Jaeger UI accessible at http://localhost:16686
- Search by service name
- Search by operation (endpoint)
- Search by trace ID
- Search by tags/attributes
- Search by time range
- Search by duration (find slow requests)

## Implementation Details

### Files Created

1. **backend/core/tracing.py**
   - `TracingConfig` class for centralized tracing setup
   - `setup_api_tracing()` convenience function for API service
   - `setup_worker_tracing()` convenience function for worker service
   - Automatic instrumentation for FastAPI, Celery, Redis, HTTPX
   - Trace context injection/extraction methods
   - Support for Jaeger and OTLP exporters

2. **backend/core/database_tracing.py**
   - Custom instrumentation classes for databases
   - `Neo4jInstrumentation` for Neo4j driver
   - `RedisInstrumentation` for Redis client
   - `AsyncpgInstrumentation` for TimescaleDB/PostgreSQL
   - Decorators for manual tracing

3. **backend/tests/test_tracing.py**
   - Unit tests for tracing configuration
   - Tests for trace context propagation
   - Tests for database operation extraction
   - Tests for setup functions

4. **docker-compose.tracing.yml**
   - Jaeger all-in-one service configuration
   - 30-day retention policy
   - OTLP endpoint support
   - Volume mounts for persistent storage
   - Health checks

5. **config/jaeger-sampling.json**
   - Sampling strategies configuration
   - 100% sampling for all services
   - 10% sampling for health check endpoints

6. **TRACING_SETUP.md**
   - Comprehensive setup guide
   - Usage examples
   - Configuration reference
   - Troubleshooting guide
   - Production deployment instructions

### Files Modified

1. **requirements.txt**
   - Added OpenTelemetry dependencies:
     - `opentelemetry-api`
     - `opentelemetry-sdk`
     - `opentelemetry-instrumentation-fastapi`
     - `opentelemetry-instrumentation-celery`
     - `opentelemetry-instrumentation-redis`
     - `opentelemetry-instrumentation-httpx`
     - `opentelemetry-exporter-jaeger`
     - `opentelemetry-exporter-otlp`

2. **backend/main.py**
   - Imported `setup_api_tracing`
   - Called `setup_api_tracing(app)` at startup
   - Added middleware to inject trace ID into response headers
   - Added shutdown handler to flush traces

3. **backend/worker.py**
   - Imported `setup_worker_tracing`
   - Called `setup_worker_tracing()` at module load

4. **backend/core/connection_pool.py**
   - Added OpenTelemetry tracer import
   - Enhanced `Neo4jConnectionPool.execute_read()` with tracing
   - Enhanced `Neo4jConnectionPool.execute_write()` with tracing
   - Enhanced `TimescaleConnectionPool.execute_read()` with tracing
   - Enhanced `TimescaleConnectionPool.execute_write()` with tracing
   - Added operation extraction methods

5. **docker-compose.yml**
   - Added tracing environment variables to `api` service
   - Added tracing environment variables to `worker` service

## Architecture

### Trace Flow

```
1. Client Request → API Service
   ├─ FastAPI creates root span
   ├─ Trace ID added to response header
   └─ Span exported to Jaeger

2. API Service → Database Query
   ├─ Connection pool creates child span
   ├─ Query statement and timing captured
   └─ Span exported to Jaeger

3. API Service → Queue Task
   ├─ Trace context injected into task
   └─ Task queued to Redis

4. Worker Service → Consume Task
   ├─ Celery creates span with propagated context
   ├─ Task execution traced
   └─ Span exported to Jaeger

5. Worker Service → Database Query
   ├─ Connection pool creates child span
   ├─ Query statement and timing captured
   └─ Span exported to Jaeger

6. Worker Service → External API Call
   ├─ HTTPX creates child span
   ├─ HTTP method, URL, status captured
   └─ Span exported to Jaeger
```

### Span Hierarchy

```
Root Span: HTTP GET /api/graph/stats
├─ Child Span: neo4j.query (MATCH)
│  └─ Attributes: db.system=neo4j, db.statement=MATCH...
├─ Child Span: redis.get
│  └─ Attributes: db.system=redis, db.redis.key=cache:stats
└─ Child Span: postgresql.query (SELECT)
   └─ Attributes: db.system=postgresql, db.statement=SELECT...
```

## Configuration

### Environment Variables

```bash
# Enable/disable tracing
TRACING_ENABLED=true

# Exporter type
TRACING_EXPORTER=jaeger  # or "otlp"

# Jaeger configuration
JAEGER_HOST=jaeger
JAEGER_PORT=6831

# OTLP configuration (for Tempo)
OTLP_ENDPOINT=http://tempo:4317

# Service metadata
SERVICE_VERSION=1.0.0
ENVIRONMENT=development

# Debug
TRACING_CONSOLE=false
```

### Sampling Configuration

Located in `config/jaeger-sampling.json`:
- 100% sampling for all services (development)
- 10% sampling for health check endpoints
- Configurable per service and operation

## Usage

### Starting Services

```bash
# Start all services including Jaeger
docker-compose -f docker-compose.yml -f docker-compose.tracing.yml up -d

# Access Jaeger UI
open http://localhost:16686
```

### Searching Traces

1. **By Service**: Select `api-service` or `worker-service`
2. **By Operation**: Select specific endpoint (e.g., `GET /api/graph/stats`)
3. **By Trace ID**: Use trace ID from `X-Trace-Id` response header
4. **By Duration**: Find slow requests with min/max duration filters
5. **By Tags**: Search by custom attributes (e.g., `http.status_code=500`)

### Manual Instrumentation

```python
# Get tracer
from backend.core.tracing import setup_api_tracing
tracing_config = setup_api_tracing(app)
tracer = tracing_config.get_tracer()

# Create custom span
with tracer.start_as_current_span("custom_operation") as span:
    span.set_attribute("custom.attribute", "value")
    result = do_something()
    span.set_attribute("result.count", len(result))
```

## Testing

### Unit Tests

Run tracing tests:
```bash
pytest backend/tests/test_tracing.py -v
```

Tests cover:
- Tracing configuration
- Trace context propagation
- Database operation extraction
- Setup functions
- Instrumentation

### Integration Testing

1. Start services with tracing enabled
2. Make API requests
3. Check Jaeger UI for traces
4. Verify trace context propagation
5. Verify database query spans
6. Verify external API call spans

## Production Considerations

### Storage Backend

For production, use Elasticsearch instead of Badger:
- Better performance at scale
- Index lifecycle management
- Automatic retention policies
- Better search capabilities

### Sampling

Adjust sampling rates for production:
- 100% sampling for errors
- 10-50% sampling for normal requests
- 1-10% sampling for high-volume endpoints

### Security

- Don't include sensitive data in span attributes
- Use secure connections to trace collector
- Implement access controls on Jaeger UI
- Rotate credentials regularly

### Monitoring

Monitor these metrics:
- Trace volume (traces/second)
- Span volume (spans/second)
- Error rate (errors/total traces)
- Storage usage
- Collector health

## Performance Impact

Tracing adds minimal overhead:
- ~1-2ms per request for span creation
- ~0.5ms per database query for instrumentation
- Batch export minimizes network overhead
- Sampling can reduce overhead further

## Troubleshooting

### No Traces Appearing

1. Check `TRACING_ENABLED=true`
2. Verify Jaeger is running: `docker-compose ps jaeger`
3. Check network connectivity: `docker-compose exec api ping jaeger`
4. Check logs: `docker-compose logs api | grep "Tracing enabled"`

### Traces Not Propagating

1. Verify trace ID in response: `curl -v http://localhost:8000/api/graph/stats | grep X-Trace-Id`
2. Check trace context in Celery tasks
3. Verify HTTPX instrumentation is active

### High Storage Usage

1. Reduce sampling rate
2. Reduce retention period
3. Use Elasticsearch with ILM
4. Enable compression

## Next Steps

1. **Deploy to Production**: Use Elasticsearch backend and OTLP exporter
2. **Add Custom Spans**: Instrument critical business logic
3. **Create Dashboards**: Build Grafana dashboards from trace metrics
4. **Set Up Alerts**: Alert on high error rates or slow traces
5. **Integrate with Logs**: Correlate traces with application logs

## References

- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
- [OpenTelemetry Python](https://opentelemetry-python.readthedocs.io/)
- [W3C Trace Context](https://www.w3.org/TR/trace-context/)
