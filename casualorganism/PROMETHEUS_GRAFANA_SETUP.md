# Prometheus and Grafana Monitoring Setup

This document describes the performance monitoring implementation for the Causal Organism platform using Prometheus and Grafana.

## Overview

The monitoring stack provides comprehensive observability for:
- API service performance (request rate, latency, errors)
- Worker service performance (task execution, queue depth)
- Infrastructure metrics (connection pools, cache, circuit breakers)
- Custom business metrics (graph size, interventions, exports)

## Requirements Implemented

- **18.1**: API service exposes `/metrics` endpoint on port 8000
- **18.2**: Worker service exposes `/metrics` endpoint on port 9090
- **18.3**: Metrics collected for request rate, error rate, and P95 latency
- **18.4**: Metrics collected for database connection pool utilization
- **18.5**: Metrics collected for cache hit rate
- **18.6**: Metrics collected for queue depth and worker utilization
- **18.7**: Grafana dashboards for API, worker, and infrastructure metrics
- **18.8**: Alert configured for P95 latency >2 seconds
- **18.9**: Alert configured for error rate >5%

## Architecture

```
┌─────────────┐     ┌─────────────┐
│ API Service │────▶│ Prometheus  │
│ :8000       │     │ :9090       │
└─────────────┘     └──────┬──────┘
                           │
┌─────────────┐            │
│   Worker    │────────────┤
│ :9090       │            │
└─────────────┘            │
                           ▼
                    ┌─────────────┐
                    │   Grafana   │
                    │ :3001       │
                    └─────────────┘
```

## Components

### 1. Prometheus Metrics (API Service)

The API service uses `prometheus-fastapi-instrumentator` to automatically collect:
- HTTP request count by method, handler, and status
- HTTP request duration histograms (for P95/P99 calculation)
- Active requests in progress

Custom metrics collected:
- `cache_hits_total` / `cache_misses_total` - Cache performance
- `connection_pool_active_connections` - Active database connections
- `connection_pool_idle_connections` - Idle database connections
- `connection_pool_waiting_requests` - Requests waiting for connections
- `connection_pool_timeouts_total` - Connection pool timeout events
- `graph_nodes_count` / `graph_edges_count` - Graph size
- `circuit_breaker_state` - Circuit breaker status (0=CLOSED, 1=OPEN, 2=HALF_OPEN)
- `circuit_breaker_failures_total` / `circuit_breaker_successes_total` - Circuit breaker events

**Endpoint**: `http://localhost:8000/metrics`

### 2. Prometheus Metrics (Worker Service)

The worker service exposes metrics on a dedicated HTTP server (port 9090):
- `worker_tasks_completed_total` - Task completions by type and status
- `worker_task_duration_seconds` - Task execution duration histogram
- `worker_active_count` - Number of active workers
- `queue_depth` - Current queue depth by queue name
- `queue_enqueued_total` / `queue_dequeued_total` - Queue operations
- `export_requests_total` - Export requests by type and status
- `export_duration_seconds` - Export duration histogram
- `export_size_bytes` - Export file size histogram
- `intervention_proposals_total` - Intervention proposals by type
- `intervention_executions_total` - Intervention executions by status
- `intervention_rollbacks_total` - Intervention rollbacks by reason

**Endpoint**: `http://localhost:9090/metrics`

### 3. Prometheus Server

Prometheus scrapes metrics from both services every 15 seconds and stores them with 30-day retention.

**Configuration**: `config/prometheus.yml`
**Alert Rules**: `config/prometheus-alerts.yml`
**Web UI**: `http://localhost:9090`

Key configuration:
```yaml
scrape_interval: 15s
evaluation_interval: 15s
storage.tsdb.retention.time: 30d
```

Scrape targets:
- `api-service` (backend:8000/metrics)
- `worker-service` (worker:9090/metrics)
- `prometheus` (self-monitoring)

### 4. Alert Rules

Configured alerts (evaluated every 30 seconds):

#### API Performance Alerts
- **HighAPILatency**: P95 latency >2 seconds for 5 minutes (WARNING)
- **HighAPIErrorRate**: Error rate >5% for 5 minutes (CRITICAL)
- **APIServiceDown**: API service unreachable for 1 minute (CRITICAL)

#### Worker Performance Alerts
- **HighWorkerTaskFailureRate**: Task failure rate >10% for 5 minutes (WARNING)
- **WorkerServiceDown**: Worker service unreachable for 1 minute (CRITICAL)
- **HighQueueDepth**: Queue depth >100 for 10 minutes (WARNING)

#### Database Alerts
- **ConnectionPoolExhausted**: Pool utilization >90% for 5 minutes (WARNING)
- **ConnectionPoolTimeouts**: Timeouts occurring >0.1/sec for 5 minutes (WARNING)

#### Cache Alerts
- **LowCacheHitRate**: Hit rate <50% for 10 minutes (INFO)

#### Circuit Breaker Alerts
- **CircuitBreakerOpen**: Circuit breaker OPEN for 2 minutes (WARNING)
- **HighCircuitBreakerFailureRate**: Failure rate >20% for 5 minutes (WARNING)

### 5. Grafana Dashboards

Three pre-configured dashboards are automatically provisioned:

#### API Service Metrics Dashboard
- Request rate by method and handler
- P95 and P99 latency
- Error rate with 5% threshold line
- Active requests
- Cache hit rate
- Connection pool utilization
- Graph size (nodes and edges)
- Circuit breaker state

#### Worker Service Metrics Dashboard
- Task completion rate (success vs failure)
- Task duration (P95)
- Queue depth with warning/critical thresholds
- Active worker count
- Task failure rate
- Export task duration
- Export file size
- Export requests per second

#### Infrastructure Metrics Dashboard
- Connection pool active/idle connections
- Connection pool utilization percentage
- Connection pool timeouts
- Cache hit rate by layer
- Cache operations (hits vs misses)
- Circuit breaker failures
- Circuit breaker state
- Graph update duration
- Intervention metrics (proposals, executions, rollbacks)

**Web UI**: `http://localhost:3001` (admin/admin)

## Deployment

### Using Docker Compose

The monitoring stack is included in `docker-compose.yml`:

```bash
# Start all services including monitoring
docker-compose up -d

# View Prometheus
open http://localhost:9090

# View Grafana
open http://localhost:3001
```

### Kubernetes Deployment

For Kubernetes, deploy Prometheus and Grafana using Helm charts or manifests in `k8s/monitoring/`.

## Accessing Metrics

### Prometheus Queries

Example queries:

```promql
# P95 API latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job="api-service"}[5m]))

# Error rate percentage
(sum(rate(http_requests_total{job="api-service",status=~"5.."}[5m])) / sum(rate(http_requests_total{job="api-service"}[5m]))) * 100

# Cache hit rate
(sum(rate(cache_hits_total[5m])) / (sum(rate(cache_hits_total[5m])) + sum(rate(cache_misses_total[5m])))) * 100

# Connection pool utilization
(connection_pool_active_connections / connection_pool_max_connections) * 100

# Queue depth
queue_depth{queue_name="celery"}

# Worker task rate
rate(worker_tasks_completed_total{status="success"}[5m])
```

### Grafana Dashboards

1. Open Grafana at `http://localhost:3001`
2. Login with `admin/admin`
3. Navigate to Dashboards
4. Select:
   - "API Service Metrics" for API performance
   - "Worker Service Metrics" for worker performance
   - "Infrastructure Metrics" for system health

## Alerting Integration

### Alertmanager (Optional)

To receive alert notifications, configure Alertmanager:

1. Create `config/alertmanager.yml`:
```yaml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'cluster']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'

receivers:
  - name: 'default'
    email_configs:
      - to: 'alerts@example.com'
        from: 'prometheus@example.com'
        smarthost: 'smtp.example.com:587'
        auth_username: 'prometheus@example.com'
        auth_password: 'password'
```

2. Add Alertmanager to `docker-compose.yml`:
```yaml
alertmanager:
  image: prom/alertmanager:latest
  ports:
    - "9093:9093"
  volumes:
    - ./config/alertmanager.yml:/etc/alertmanager/alertmanager.yml
```

3. Update Prometheus config to use Alertmanager:
```yaml
alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### Grafana Alerts

Grafana can also send alerts via:
- Email
- Slack
- PagerDuty
- Webhook
- And many more

Configure in Grafana UI: Alerting → Notification channels

## Metrics Retention

- **Prometheus**: 30 days (configurable via `--storage.tsdb.retention.time`)
- **Grafana**: Queries Prometheus, no separate retention

For long-term storage, consider:
- Thanos (long-term Prometheus storage)
- Cortex (multi-tenant Prometheus)
- VictoriaMetrics (high-performance TSDB)

## Performance Considerations

### Cardinality

Keep metric cardinality low to avoid performance issues:
- Avoid high-cardinality labels (user IDs, request IDs)
- Use aggregation for high-volume metrics
- Monitor Prometheus memory usage

### Scrape Interval

Current: 15 seconds
- Increase for lower overhead
- Decrease for higher resolution

### Query Performance

- Use recording rules for expensive queries
- Limit time range in dashboards
- Use downsampling for historical data

## Troubleshooting

### Metrics Not Appearing

1. Check service is running:
```bash
curl http://localhost:8000/metrics
curl http://localhost:9090/metrics
```

2. Check Prometheus targets:
- Open `http://localhost:9090/targets`
- Verify all targets are "UP"

3. Check Prometheus logs:
```bash
docker-compose logs prometheus
```

### High Memory Usage

Prometheus memory usage scales with:
- Number of time series
- Scrape interval
- Retention period

Solutions:
- Reduce retention time
- Increase scrape interval
- Reduce metric cardinality
- Add more memory

### Grafana Dashboard Not Loading

1. Check Prometheus datasource:
- Grafana → Configuration → Data Sources
- Test connection

2. Check dashboard JSON syntax:
```bash
cat config/grafana/provisioning/dashboards/*.json | jq .
```

## Best Practices

1. **Monitor the monitors**: Set up alerts for Prometheus and Grafana health
2. **Use labels wisely**: Keep cardinality low, use meaningful labels
3. **Document custom metrics**: Add comments explaining what each metric measures
4. **Test alerts**: Trigger test alerts to verify notification channels
5. **Regular review**: Review dashboards and alerts monthly, remove unused ones
6. **Capacity planning**: Use metrics to predict when to scale resources
7. **SLO tracking**: Define and track Service Level Objectives (SLOs)

## References

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [FastAPI Instrumentator](https://github.com/trallnag/prometheus-fastapi-instrumentator)
