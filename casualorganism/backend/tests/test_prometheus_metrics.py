"""
Tests for Prometheus metrics implementation.

Requirements:
- 18.1: API service SHALL expose Prometheus metrics endpoint
- 18.3: Collect metrics for request rate, error rate, and P95 latency
- 18.4: Collect metrics for database connection pool utilization
- 18.5: Collect metrics for cache hit rate
"""

import pytest
from backend.core.prometheus_metrics import PrometheusMetrics, initialize_metrics
from prometheus_client import CollectorRegistry


def test_prometheus_metrics_initialization():
    """Test that PrometheusMetrics can be initialized."""
    registry = CollectorRegistry()
    metrics = PrometheusMetrics(registry=registry)
    
    assert metrics is not None
    assert metrics.registry == registry


def test_cache_metrics():
    """Test cache hit/miss recording."""
    registry = CollectorRegistry()
    metrics = PrometheusMetrics(registry=registry)
    
    # Record cache hits and misses
    metrics.record_cache_hit("L1", "graph_stats")
    metrics.record_cache_hit("L1", "graph_stats")
    metrics.record_cache_miss("L1", "graph_stats")
    
    # Verify metrics were recorded
    cache_hits = registry.get_sample_value(
        'cache_hits_total',
        {'cache_layer': 'L1', 'cache_type': 'graph_stats'}
    )
    cache_misses = registry.get_sample_value(
        'cache_misses_total',
        {'cache_layer': 'L1', 'cache_type': 'graph_stats'}
    )
    
    assert cache_hits == 2.0
    assert cache_misses == 1.0


def test_connection_pool_metrics():
    """Test connection pool metrics update."""
    registry = CollectorRegistry()
    metrics = PrometheusMetrics(registry=registry)
    
    # Update connection pool metrics
    metrics.update_connection_pool_metrics(
        pool_name="neo4j",
        database_type="neo4j",
        active=5,
        idle=10,
        waiting=2,
        max_connections=20
    )
    
    # Verify metrics were recorded
    active = registry.get_sample_value(
        'connection_pool_active_connections',
        {'pool_name': 'neo4j', 'database_type': 'neo4j'}
    )
    idle = registry.get_sample_value(
        'connection_pool_idle_connections',
        {'pool_name': 'neo4j', 'database_type': 'neo4j'}
    )
    waiting = registry.get_sample_value(
        'connection_pool_waiting_requests',
        {'pool_name': 'neo4j', 'database_type': 'neo4j'}
    )
    max_conn = registry.get_sample_value(
        'connection_pool_max_connections',
        {'pool_name': 'neo4j', 'database_type': 'neo4j'}
    )
    
    assert active == 5.0
    assert idle == 10.0
    assert waiting == 2.0
    assert max_conn == 20.0


def test_queue_metrics():
    """Test queue depth and operations metrics."""
    registry = CollectorRegistry()
    metrics = PrometheusMetrics(registry=registry)
    
    # Update queue metrics
    metrics.update_queue_depth("celery", 42)
    metrics.record_queue_enqueue("celery", "causal_analysis")
    metrics.record_queue_dequeue("celery", "causal_analysis")
    
    # Verify metrics were recorded
    depth = registry.get_sample_value(
        'queue_depth',
        {'queue_name': 'celery'}
    )
    enqueued = registry.get_sample_value(
        'queue_enqueued_total',
        {'queue_name': 'celery', 'task_type': 'causal_analysis'}
    )
    dequeued = registry.get_sample_value(
        'queue_dequeued_total',
        {'queue_name': 'celery', 'task_type': 'causal_analysis'}
    )
    
    assert depth == 42.0
    assert enqueued == 1.0
    assert dequeued == 1.0


def test_worker_metrics():
    """Test worker task completion metrics."""
    registry = CollectorRegistry()
    metrics = PrometheusMetrics(registry=registry)
    
    # Record worker task completion
    metrics.record_worker_task_completion(
        worker_type="celery",
        task_type="causal_analysis",
        status="success",
        duration_seconds=5.5
    )
    
    # Verify metrics were recorded
    completed = registry.get_sample_value(
        'worker_tasks_completed_total',
        {'worker_type': 'celery', 'task_type': 'causal_analysis', 'status': 'success'}
    )
    
    assert completed == 1.0


def test_circuit_breaker_metrics():
    """Test circuit breaker state and event metrics."""
    registry = CollectorRegistry()
    metrics = PrometheusMetrics(registry=registry)
    
    # Update circuit breaker state
    metrics.update_circuit_breaker_state("external_api", "OPEN")
    metrics.record_circuit_breaker_failure("external_api")
    metrics.record_circuit_breaker_success("external_api")
    
    # Verify metrics were recorded
    state = registry.get_sample_value(
        'circuit_breaker_state',
        {'service_name': 'external_api'}
    )
    failures = registry.get_sample_value(
        'circuit_breaker_failures_total',
        {'service_name': 'external_api'}
    )
    successes = registry.get_sample_value(
        'circuit_breaker_successes_total',
        {'service_name': 'external_api'}
    )
    
    assert state == 1.0  # OPEN = 1
    assert failures == 1.0
    assert successes == 1.0


def test_graph_metrics():
    """Test graph size metrics."""
    registry = CollectorRegistry()
    metrics = PrometheusMetrics(registry=registry)
    
    # Update graph metrics
    metrics.update_graph_metrics(node_count=100, edge_count=250)
    
    # Verify metrics were recorded
    nodes = registry.get_sample_value('graph_nodes_count')
    edges = registry.get_sample_value('graph_edges_count')
    
    assert nodes == 100.0
    assert edges == 250.0


def test_export_metrics():
    """Test export request and completion metrics."""
    registry = CollectorRegistry()
    metrics = PrometheusMetrics(registry=registry)
    
    # Record export request and completion
    metrics.record_export_request("employee_metrics", "started")
    metrics.record_export_completion(
        export_type="employee_metrics",
        duration_seconds=30.5,
        size_bytes=1024000
    )
    metrics.record_export_request("employee_metrics", "completed")
    
    # Verify metrics were recorded
    started = registry.get_sample_value(
        'export_requests_total',
        {'export_type': 'employee_metrics', 'status': 'started'}
    )
    completed = registry.get_sample_value(
        'export_requests_total',
        {'export_type': 'employee_metrics', 'status': 'completed'}
    )
    
    assert started == 1.0
    assert completed == 1.0


def test_intervention_metrics():
    """Test intervention proposal, execution, and rollback metrics."""
    registry = CollectorRegistry()
    metrics = PrometheusMetrics(registry=registry)
    
    # Record intervention events
    metrics.record_intervention_proposal("reduce_meetings", "medium")
    metrics.record_intervention_execution("reduce_meetings", "success")
    metrics.record_intervention_rollback("reduce_meetings", "negative_outcome")
    
    # Verify metrics were recorded
    proposals = registry.get_sample_value(
        'intervention_proposals_total',
        {'intervention_type': 'reduce_meetings', 'impact_level': 'medium'}
    )
    executions = registry.get_sample_value(
        'intervention_executions_total',
        {'intervention_type': 'reduce_meetings', 'status': 'success'}
    )
    rollbacks = registry.get_sample_value(
        'intervention_rollbacks_total',
        {'intervention_type': 'reduce_meetings', 'reason': 'negative_outcome'}
    )
    
    assert proposals == 1.0
    assert executions == 1.0
    assert rollbacks == 1.0


def test_global_metrics_instance():
    """Test global metrics instance management."""
    # Initialize global instance
    metrics1 = initialize_metrics()
    
    # Get global instance
    from backend.core.prometheus_metrics import get_metrics
    metrics2 = get_metrics()
    
    # Should be the same instance
    assert metrics1 is metrics2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
