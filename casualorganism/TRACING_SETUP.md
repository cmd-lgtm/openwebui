# Distributed Tracing Setup Guide

This guide explains how to set up and use distributed tracing with OpenTelemetry and Jaeger for the Causal Organism platform.

## Overview

The platform uses OpenTelemetry for distributed tracing, which provides:
- End-to-end request tracing across API and worker services
- Database query timing (Neo4j, Redis, TimescaleDB)
- External API call timing
- Trace context propagation across service boundaries
- 30-day trace retention
- Search and visualization UI

## Requirements

This implementation satisfies the following requirements:
- **16.1**: API_Service emits OpenTelemetry traces for all incoming requests
- **16.2**: Worker_Pool emits OpenTelemetry traces for all task executions
- **16.3**: System propagates trace context across service boundaries
- **16.4**: System includes database query timing in traces
- **16.5**: System includes external API call timing in traces
- **16.6**: System sends traces to centralized collector (Jaeger)
- **16.7**: System retains traces for 30 days
- **16.8**: System provides UI to search traces by request ID, endpoint, or time range

## Quick Start

### 1. Start Services with Tracing

```bash
# Start all services including Jaeger
docker-compose -f docker-compose.yml -f docker-compose.tracing.yml up -d

# Or use the combined command
docker-compose -f docker-compose.yml -f docker-compose.tracing.yml up
```

### 2. Access Jaeger UI

Open your browser and navigate to:
```
http://localhost:16686
```

### 3. Search Traces

In the Jaeger UI:
1. Select service: `api-service` or `worker-service`
2. Select operation (endpoint) or leave blank for all
3. Set time range
4. Click "Find Traces"

## Architecture

### Components

1. **API Service** (`api-service`)
   - Automatically traces all FastAPI endpoints
   - Traces database queries (Neo4j, Redis, TimescaleDB)
   - Traces external HTTP calls
   - Adds trace ID to response headers

2. **Worker Service** (`worker-service`)
   - Automatically traces all Celery tasks
   - Traces database operations
   - Traces external API calls

3. **Jaeger**
   - Collects traces from all services
   - Stores traces for 30 days
   - Provides search and visualization UI

### Trace Flow

```
Client Request
    ↓
API Service (creates trace)
    ↓
Database Query (child span)
    ↓
Queue Task (propagates trace context)
    ↓
Worker Service (continues trace)
    ↓
Database Query (child span)
    ↓
External API Call (child span)
```

## Configuration

### Environment Variables

Configure tracing via environment variables:

```bash
# Enable/disable tracing
TRACING_ENABLED=true

# Exporter type (jaeger or otlp)
TRACING_EXPORTER=jaeger

# Jaeger configuration
JAEGER_HOST=localhost
JAEGER_PORT=6831

# OTLP configuration (for Tempo, etc.)
OTLP_ENDPOINT=http://tempo:4317

# Service metadata
SERVICE_VERSION=1.0.0
ENVIRONMENT=development

# Debug: Enable console export
TRACING_CONSOLE=false
```

### Sampling Configuration

Edit `config/jaeger-sampling.json` to configure sampling rates:

```json
{
  "service_strategies": [
    {
      "service": "api-service",
      "type": "probabilistic",
      "param": 1.0,  // 100% sampling
      "operation_strategies": [
        {
          "operation": "health_check",
          "type": "probabilistic",
          "param": 0.1  // 10% sampling for health checks
        }
      ]
    }
  ]
}
```

## Usage

### Automatic Instrumentation

Most tracing happens automatically:

```python
# FastAPI endpoints are automatically traced
@app.get("/api/graph/stats")
def get_graph_stats():
    # This entire function is traced automatically
    return state.graph.get_stats()

# Celery tasks are automatically traced
@celery_app.task
def run_causal_analysis():
    # This entire task is traced automatically
    return analyze_data()

# Database queries are automatically traced
await neo4j_pool.execute_read(query, params)  # Traced
await timescale_pool.execute_read(query, params)  # Traced
```

### Manual Instrumentation

For custom spans:

```python
from backend.core.tracing import setup_api_tracing

# Get tracer
tracing_config = setup_api_tracing(app)
tracer = tracing_config.get_tracer()

# Create custom span
with tracer.start_as_current_span("custom_operation") as span:
    span.set_attribute("custom.attribute", "value")
    result = do_something()
    span.set_attribute("result.count", len(result))
```

### Trace Context Propagation

Trace context is automatically propagated for:
- FastAPI requests (via middleware)
- Celery tasks (via instrumentation)
- HTTPX HTTP calls (via instrumentation)
- Database queries (via connection pool)

For manual propagation:

```python
# Inject trace context into HTTP headers
headers = {}
tracing_config.inject_trace_context(headers)
response = httpx.post(url, headers=headers)

# Extract trace context from headers
context = tracing_config.extract_trace_context(request.headers)
with tracer.start_as_current_span("operation", context=context):
    process_request()
```

### Response Headers

Every API response includes the trace ID:

```
X-Trace-Id: 4bf92f3577b34da6a3ce929d0e0e4736
```

Use this to:
- Correlate logs with traces
- Search for specific requests in Jaeger
- Debug issues reported by users

## Searching Traces

### By Service and Operation

1. Select service: `api-service`
2. Select operation: `GET /api/graph/stats`
3. Click "Find Traces"

### By Trace ID

1. Enter trace ID in search box (from X-Trace-Id header)
2. Click "Find Traces"

### By Tags

Search by custom attributes:
```
http.status_code=500
db.system=neo4j
error=true
```

### By Duration

Find slow requests:
1. Set "Min Duration" to filter slow traces
2. Example: `>2s` for requests slower than 2 seconds

## Production Deployment

### Using Elasticsearch Backend

For production, use Elasticsearch for persistent storage:

1. Uncomment the Elasticsearch section in `docker-compose.tracing.yml`
2. Comment out the all-in-one Jaeger service
3. Restart services

### Using Tempo (OTLP)

To use Grafana Tempo instead of Jaeger:

1. Set environment variable:
   ```bash
   TRACING_EXPORTER=otlp
   OTLP_ENDPOINT=http://tempo:4317
   ```

2. Deploy Tempo:
   ```yaml
   tempo:
     image: grafana/tempo:latest
     ports:
       - "4317:4317"  # OTLP gRPC
       - "3200:3200"  # Tempo HTTP
   ```

### Kubernetes Deployment

For Kubernetes, use the Jaeger Operator:

```bash
# Install Jaeger Operator
kubectl create namespace observability
kubectl create -f https://github.com/jaegertracing/jaeger-operator/releases/download/v1.51.0/jaeger-operator.yaml -n observability

# Deploy Jaeger instance
kubectl apply -f k8s/jaeger.yaml
```

## Monitoring

### Trace Metrics

Monitor these metrics:
- Trace volume (traces/second)
- Span volume (spans/second)
- Error rate (errors/total traces)
- P95/P99 latency

### Jaeger Health

Check Jaeger health:
```bash
curl http://localhost:14269/
```

### Storage Usage

Monitor Badger storage:
```bash
docker exec jaeger du -sh /badger/data
```

## Troubleshooting

### No Traces Appearing

1. Check tracing is enabled:
   ```bash
   docker-compose logs api | grep "Tracing enabled"
   ```

2. Check Jaeger is running:
   ```bash
   docker-compose ps jaeger
   curl http://localhost:14269/
   ```

3. Check network connectivity:
   ```bash
   docker-compose exec api ping jaeger
   ```

### Traces Not Propagating

1. Verify trace ID in response headers:
   ```bash
   curl -v http://localhost:8000/api/graph/stats | grep X-Trace-Id
   ```

2. Check trace context in logs:
   ```python
   trace_id = tracing_config.get_current_trace_id()
   print(f"Current trace: {trace_id}")
   ```

### High Storage Usage

1. Reduce sampling rate in `config/jaeger-sampling.json`
2. Reduce retention period (default: 30 days)
3. Use Elasticsearch with index lifecycle management

## Best Practices

1. **Sampling**: Use 100% sampling in development, adjust for production
2. **Attributes**: Add meaningful attributes to spans for better searchability
3. **Error Handling**: Always record exceptions in spans
4. **Performance**: Tracing adds ~1-2ms overhead per request
5. **Security**: Don't include sensitive data in span attributes

## References

- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
- [OpenTelemetry Python](https://opentelemetry-python.readthedocs.io/)
