"""
Prometheus metrics for API service and workers.

Requirements:
- 18.1: API service SHALL expose Prometheus metrics endpoint
- 18.2: Worker pool SHALL expose Prometheus metrics endpoint
- 18.3: Collect metrics for request rate, error rate, and P95 latency
- 18.4: Collect metrics for database connection pool utilization
- 18.5: Collect metrics for cache hit rate
- 18.6: Collect metrics for queue depth and worker utilization
"""

from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry
from prometheus_fastapi_instrumentator import Instrumentator, metrics
from prometheus_fastapi_instrumentator.metrics import Info as MetricInfo
from typing import Callable, Optional
import time


class PrometheusMetrics:
    """
    Centralized Prometheus metrics for the Causal Organism platform.
    
    Provides custom metrics for:
    - Cache performance (hit rate, miss rate)
    - Connection pool utilization
    - Queue depth
    - Worker utilization
    - Custom business metrics
    """
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        """
        Initialize Prometheus metrics.
        
        Args:
            registry: Optional custom registry (useful for testing)
        """
        self.registry = registry
        
        # Cache metrics
        self.cache_hits = Counter(
            'cache_hits_total',
            'Total number of cache hits',
            ['cache_layer', 'cache_type'],
            registry=registry
        )
        
        self.cache_misses = Counter(
            'cache_misses_total',
            'Total number of cache misses',
            ['cache_layer', 'cache_type'],
            registry=registry
        )
        
        self.cache_size = Gauge(
            'cache_size_bytes',
            'Current cache size in bytes',
            ['cache_layer'],
            registry=registry
        )
        
        self.cache_items = Gauge(
            'cache_items_count',
            'Current number of items in cache',
            ['cache_layer'],
            registry=registry
        )
        
        # Connection pool metrics
        self.connection_pool_active = Gauge(
            'connection_pool_active_connections',
            'Number of active connections in pool',
            ['pool_name', 'database_type'],
            registry=registry
        )
        
        self.connection_pool_idle = Gauge(
            'connection_pool_idle_connections',
            'Number of idle connections in pool',
            ['pool_name', 'database_type'],
            registry=registry
        )
        
        self.connection_pool_waiting = Gauge(
            'connection_pool_waiting_requests',
            'Number of requests waiting for connection',
            ['pool_name', 'database_type'],
            registry=registry
        )
        
        self.connection_pool_max = Gauge(
            'connection_pool_max_connections',
            'Maximum number of connections in pool',
            ['pool_name', 'database_type'],
            registry=registry
        )
        
        self.connection_pool_timeouts = Counter(
            'connection_pool_timeouts_total',
            'Total number of connection pool timeouts',
            ['pool_name', 'database_type'],
            registry=registry
        )
        
        # Queue metrics
        self.queue_depth = Gauge(
            'queue_depth',
            'Current depth of task queue',
            ['queue_name'],
            registry=registry
        )
        
        self.queue_enqueued = Counter(
            'queue_enqueued_total',
            'Total number of tasks enqueued',
            ['queue_name', 'task_type'],
            registry=registry
        )
        
        self.queue_dequeued = Counter(
            'queue_dequeued_total',
            'Total number of tasks dequeued',
            ['queue_name', 'task_type'],
            registry=registry
        )
        
        # Worker metrics
        self.worker_active = Gauge(
            'worker_active_count',
            'Number of active workers',
            ['worker_type'],
            registry=registry
        )
        
        self.worker_tasks_completed = Counter(
            'worker_tasks_completed_total',
            'Total number of tasks completed by workers',
            ['worker_type', 'task_type', 'status'],
            registry=registry
        )
        
        self.worker_task_duration = Histogram(
            'worker_task_duration_seconds',
            'Duration of worker task execution',
            ['worker_type', 'task_type'],
            buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
            registry=registry
        )
        
        # Circuit breaker metrics
        self.circuit_breaker_state = Gauge(
            'circuit_breaker_state',
            'Circuit breaker state (0=closed, 1=open, 2=half_open)',
            ['service_name'],
            registry=registry
        )
        
        self.circuit_breaker_failures = Counter(
            'circuit_breaker_failures_total',
            'Total number of circuit breaker failures',
            ['service_name'],
            registry=registry
        )
        
        self.circuit_breaker_successes = Counter(
            'circuit_breaker_successes_total',
            'Total number of circuit breaker successes',
            ['service_name'],
            registry=registry
        )
        
        # Graph metrics
        self.graph_nodes = Gauge(
            'graph_nodes_count',
            'Number of nodes in organizational graph',
            registry=registry
        )
        
        self.graph_edges = Gauge(
            'graph_edges_count',
            'Number of edges in organizational graph',
            registry=registry
        )
        
        self.graph_update_duration = Histogram(
            'graph_update_duration_seconds',
            'Duration of graph update operations',
            ['update_type'],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
            registry=registry
        )
        
        # Export metrics
        self.export_requests = Counter(
            'export_requests_total',
            'Total number of export requests',
            ['export_type', 'status'],
            registry=registry
        )
        
        self.export_duration = Histogram(
            'export_duration_seconds',
            'Duration of export operations',
            ['export_type'],
            buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
            registry=registry
        )
        
        self.export_size = Histogram(
            'export_size_bytes',
            'Size of exported files',
            ['export_type'],
            buckets=[1024, 10240, 102400, 1048576, 10485760, 104857600],
            registry=registry
        )
        
        # Intervention metrics
        self.intervention_proposals = Counter(
            'intervention_proposals_total',
            'Total number of intervention proposals',
            ['intervention_type', 'impact_level'],
            registry=registry
        )
        
        self.intervention_executions = Counter(
            'intervention_executions_total',
            'Total number of intervention executions',
            ['intervention_type', 'status'],
            registry=registry
        )
        
        self.intervention_rollbacks = Counter(
            'intervention_rollbacks_total',
            'Total number of intervention rollbacks',
            ['intervention_type', 'reason'],
            registry=registry
        )
        
        # Rate limit metrics
        # Requirement 20.8: Expose metrics for rate limit hits per endpoint
        self.rate_limit_hits = Counter(
            'rate_limit_hits_total',
            'Total number of rate limit hits (requests blocked)',
            ['endpoint', 'limit_type'],
            registry=registry
        )
        
        self.rate_limit_requests = Counter(
            'rate_limit_requests_total',
            'Total number of requests checked against rate limits',
            ['endpoint', 'limit_type', 'result'],
            registry=registry
        )
    
    def record_cache_hit(self, cache_layer: str, cache_type: str):
        """Record a cache hit."""
        self.cache_hits.labels(cache_layer=cache_layer, cache_type=cache_type).inc()
    
    def record_cache_miss(self, cache_layer: str, cache_type: str):
        """Record a cache miss."""
        self.cache_misses.labels(cache_layer=cache_layer, cache_type=cache_type).inc()
    
    def update_cache_size(self, cache_layer: str, size_bytes: int):
        """Update cache size metric."""
        self.cache_size.labels(cache_layer=cache_layer).set(size_bytes)
    
    def update_cache_items(self, cache_layer: str, count: int):
        """Update cache items count."""
        self.cache_items.labels(cache_layer=cache_layer).set(count)
    
    def update_connection_pool_metrics(
        self,
        pool_name: str,
        database_type: str,
        active: int,
        idle: int,
        waiting: int,
        max_connections: int
    ):
        """Update connection pool metrics."""
        self.connection_pool_active.labels(
            pool_name=pool_name,
            database_type=database_type
        ).set(active)
        
        self.connection_pool_idle.labels(
            pool_name=pool_name,
            database_type=database_type
        ).set(idle)
        
        self.connection_pool_waiting.labels(
            pool_name=pool_name,
            database_type=database_type
        ).set(waiting)
        
        self.connection_pool_max.labels(
            pool_name=pool_name,
            database_type=database_type
        ).set(max_connections)
    
    def record_connection_pool_timeout(self, pool_name: str, database_type: str):
        """Record a connection pool timeout."""
        self.connection_pool_timeouts.labels(
            pool_name=pool_name,
            database_type=database_type
        ).inc()
    
    def update_queue_depth(self, queue_name: str, depth: int):
        """Update queue depth metric."""
        self.queue_depth.labels(queue_name=queue_name).set(depth)
    
    def record_queue_enqueue(self, queue_name: str, task_type: str):
        """Record a task enqueue."""
        self.queue_enqueued.labels(queue_name=queue_name, task_type=task_type).inc()
    
    def record_queue_dequeue(self, queue_name: str, task_type: str):
        """Record a task dequeue."""
        self.queue_dequeued.labels(queue_name=queue_name, task_type=task_type).inc()
    
    def update_worker_count(self, worker_type: str, count: int):
        """Update active worker count."""
        self.worker_active.labels(worker_type=worker_type).set(count)
    
    def record_worker_task_completion(
        self,
        worker_type: str,
        task_type: str,
        status: str,
        duration_seconds: float
    ):
        """Record a worker task completion."""
        self.worker_tasks_completed.labels(
            worker_type=worker_type,
            task_type=task_type,
            status=status
        ).inc()
        
        self.worker_task_duration.labels(
            worker_type=worker_type,
            task_type=task_type
        ).observe(duration_seconds)
    
    def update_circuit_breaker_state(self, service_name: str, state: str):
        """
        Update circuit breaker state.
        
        Args:
            service_name: Name of the external service
            state: State (CLOSED=0, OPEN=1, HALF_OPEN=2)
        """
        state_value = {"CLOSED": 0, "OPEN": 1, "HALF_OPEN": 2}.get(state, 0)
        self.circuit_breaker_state.labels(service_name=service_name).set(state_value)
    
    def record_circuit_breaker_failure(self, service_name: str):
        """Record a circuit breaker failure."""
        self.circuit_breaker_failures.labels(service_name=service_name).inc()
    
    def record_circuit_breaker_success(self, service_name: str):
        """Record a circuit breaker success."""
        self.circuit_breaker_successes.labels(service_name=service_name).inc()
    
    def update_graph_metrics(self, node_count: int, edge_count: int):
        """Update graph size metrics."""
        self.graph_nodes.set(node_count)
        self.graph_edges.set(edge_count)
    
    def record_graph_update(self, update_type: str, duration_seconds: float):
        """Record a graph update operation."""
        self.graph_update_duration.labels(update_type=update_type).observe(duration_seconds)
    
    def record_export_request(self, export_type: str, status: str):
        """Record an export request."""
        self.export_requests.labels(export_type=export_type, status=status).inc()
    
    def record_export_completion(
        self,
        export_type: str,
        duration_seconds: float,
        size_bytes: int
    ):
        """Record an export completion."""
        self.export_duration.labels(export_type=export_type).observe(duration_seconds)
        self.export_size.labels(export_type=export_type).observe(size_bytes)
    
    def record_intervention_proposal(self, intervention_type: str, impact_level: str):
        """Record an intervention proposal."""
        self.intervention_proposals.labels(
            intervention_type=intervention_type,
            impact_level=impact_level
        ).inc()
    
    def record_intervention_execution(self, intervention_type: str, status: str):
        """Record an intervention execution."""
        self.intervention_executions.labels(
            intervention_type=intervention_type,
            status=status
        ).inc()
    
    def record_intervention_rollback(self, intervention_type: str, reason: str):
        """Record an intervention rollback."""
        self.intervention_rollbacks.labels(
            intervention_type=intervention_type,
            reason=reason
        ).inc()
    
    def increment_rate_limit_hits(self, endpoint: str, limit_type: str):
        """
        Record a rate limit hit (request blocked).
        
        Requirements:
        - 20.8: Expose metrics for rate limit hits per endpoint
        
        Args:
            endpoint: API endpoint path
            limit_type: Type of limit (user, ip, endpoint)
        """
        self.rate_limit_hits.labels(endpoint=endpoint, limit_type=limit_type).inc()
    
    def record_rate_limit_check(self, endpoint: str, limit_type: str, result: str):
        """
        Record a rate limit check.
        
        Requirements:
        - 20.8: Expose metrics for rate limit hits per endpoint
        
        Args:
            endpoint: API endpoint path
            limit_type: Type of limit (user, ip, endpoint)
            result: Result of check (allowed, blocked)
        """
        self.rate_limit_requests.labels(
            endpoint=endpoint,
            limit_type=limit_type,
            result=result
        ).inc()


def setup_api_metrics(app, prometheus_metrics: PrometheusMetrics) -> Instrumentator:
    """
    Setup Prometheus metrics for FastAPI application.
    
    Requirements:
    - 18.1: Expose /metrics endpoint
    - 18.3: Add metrics for request rate, error rate, and P95 latency
    
    Args:
        app: FastAPI application
        prometheus_metrics: PrometheusMetrics instance
    
    Returns:
        Instrumentator instance
    """
    # Create instrumentator with custom registry if provided
    instrumentator = Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        should_respect_env_var=True,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/metrics", "/health/live", "/health/ready"],
        env_var_name="ENABLE_METRICS",
        inprogress_name="http_requests_inprogress",
        inprogress_labels=True,
        registry=prometheus_metrics.registry
    )
    
    # Add default metrics from prometheus_fastapi_instrumentator
    instrumentator.add(
        metrics.default()
    )
    
    # Add request count metric
    instrumentator.add(
        metrics.requests()
    )
    
    # Add latency metric with custom buckets for P95 tracking
    instrumentator.add(
        metrics.latency(
            buckets=[0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.0, 5.0, 10.0]
        )
    )
    
    # Instrument the app
    instrumentator.instrument(app)
    
    # Expose metrics endpoint
    instrumentator.expose(app, endpoint="/metrics", include_in_schema=False)
    
    return instrumentator


# Global metrics instance
_metrics_instance: Optional[PrometheusMetrics] = None


def get_metrics() -> PrometheusMetrics:
    """Get the global metrics instance."""
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = PrometheusMetrics()
    return _metrics_instance


def initialize_metrics(registry: Optional[CollectorRegistry] = None) -> PrometheusMetrics:
    """
    Initialize the global metrics instance.
    
    Args:
        registry: Optional custom registry
    
    Returns:
        PrometheusMetrics instance
    """
    global _metrics_instance
    _metrics_instance = PrometheusMetrics(registry=registry)
    return _metrics_instance
