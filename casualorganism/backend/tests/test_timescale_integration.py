"""
Integration tests for TimescaleDB time-series storage.

These tests verify the implementation works correctly when TimescaleDB is available.
Tests are skipped if TimescaleDB is not accessible.
"""
import pytest
from datetime import datetime, timedelta
from backend.core.connection_pool import TimescaleConnectionPool
from backend.core.timescale_schema import TimescaleSchemaManager
from backend.core.timescale_metrics import TimescaleMetricsWriter
from backend.core.timescale_queries import TimescaleQueryService
import pandas as pd


@pytest.fixture
async def check_timescale_available():
    """Check if TimescaleDB is available for testing."""
    pool = TimescaleConnectionPool(
        host="localhost",
        port=5432,
        database="postgres",
        user="postgres",
        password="password"
    )
    
    available = await pool.initialize()
    if available:
        await pool.close()
    
    if not available:
        pytest.skip("TimescaleDB not available - skipping integration tests")
    
    return available


@pytest.mark.asyncio
async def test_timescale_connection_pool_initialization(check_timescale_available):
    """
    Test that TimescaleDB connection pool can be initialized.
    
    Requirement 3.1: Use connection pool for TimescaleDB
    """
    pool = TimescaleConnectionPool(
        host="localhost",
        port=5432,
        database="postgres",
        user="postgres",
        password="password"
    )
    
    success = await pool.initialize()
    assert success, "TimescaleDB connection pool should initialize successfully"
    
    # Test health check
    healthy = await pool.health_check()
    assert healthy, "TimescaleDB connection should be healthy"
    
    await pool.close()


@pytest.mark.asyncio
async def test_schema_creation_idempotent(check_timescale_available):
    """
    Test that schema creation is idempotent (can be run multiple times).
    
    Requirements:
    - 12.1: Create employee_metrics hypertable
    - 12.2: Create intervention_audit_log hypertable
    """
    pool = TimescaleConnectionPool(
        host="localhost",
        port=5432,
        database="postgres",
        user="postgres",
        password="password"
    )
    
    await pool.initialize()
    
    schema_manager = TimescaleSchemaManager(pool.pool)
    
    # Create schema first time
    await schema_manager.create_schema()
    
    # Create schema second time (should not fail)
    await schema_manager.create_schema()
    
    # Verify tables exist
    async with pool.pool.acquire() as conn:
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name IN ('employee_metrics', 'intervention_audit_log', 'interventions')
        """)
        
        table_names = [row['table_name'] for row in tables]
        assert 'employee_metrics' in table_names
        assert 'intervention_audit_log' in table_names
        assert 'interventions' in table_names
    
    await pool.close()


@pytest.mark.asyncio
async def test_write_and_query_employee_metrics(check_timescale_available):
    """
    Test writing employee metrics and querying them back.
    
    Requirements:
    - 12.1: Write computed metrics with timestamps
    - 12.6: Query TimescaleDB for time-series data
    """
    pool = TimescaleConnectionPool(
        host="localhost",
        port=5432,
        database="postgres",
        user="postgres",
        password="password"
    )
    
    await pool.initialize()
    
    # Initialize schema
    schema_manager = TimescaleSchemaManager(pool.pool)
    await schema_manager.create_schema()
    
    # Write metrics
    metrics_writer = TimescaleMetricsWriter(pool.pool)
    
    test_metrics = {
        'degree_centrality': 0.25,
        'betweenness_centrality': 0.15,
        'clustering_coeff': 0.42,
        'burnout_score': 65.3
    }
    
    success = await metrics_writer.write_employee_metrics(
        employee_id="test_emp_001",
        metrics=test_metrics,
        timestamp=datetime.utcnow()
    )
    
    assert success, "Should successfully write metrics"
    
    # Query metrics back
    query_service = TimescaleQueryService(pool.pool)
    
    trend = await query_service.get_employee_trend(
        employee_id="test_emp_001",
        days=1
    )
    
    assert len(trend) > 0, "Should retrieve at least one metric record"
    assert trend[0]['employee_id'] == "test_emp_001"
    assert trend[0]['burnout_score'] == 65.3
    
    await pool.close()


@pytest.mark.asyncio
async def test_batch_write_performance(check_timescale_available):
    """
    Test batch writing performance for multiple employees.
    
    Requirement 12.1: Batch writes for efficiency
    """
    pool = TimescaleConnectionPool(
        host="localhost",
        port=5432,
        database="postgres",
        user="postgres",
        password="password"
    )
    
    await pool.initialize()
    
    # Initialize schema
    schema_manager = TimescaleSchemaManager(pool.pool)
    await schema_manager.create_schema()
    
    # Create batch of metrics
    metrics_writer = TimescaleMetricsWriter(pool.pool)
    
    batch_size = 100
    metrics_list = [
        {
            'employee_id': f'test_emp_{i:04d}',
            'degree_centrality': 0.1 + i * 0.001,
            'betweenness_centrality': 0.05 + i * 0.0005,
            'clustering_coeff': 0.3 + i * 0.001,
            'burnout_score': 50.0 + i * 0.1
        }
        for i in range(batch_size)
    ]
    
    # Measure write time
    start_time = datetime.utcnow()
    count = await metrics_writer.write_employee_metrics_batch(metrics_list)
    end_time = datetime.utcnow()
    
    write_duration = (end_time - start_time).total_seconds()
    
    assert count == batch_size, f"Should write {batch_size} records"
    assert write_duration < 5.0, f"Batch write should complete in <5 seconds, took {write_duration}s"
    
    print(f"Batch write of {batch_size} records took {write_duration:.3f} seconds")
    
    await pool.close()


@pytest.mark.asyncio
async def test_historical_query_performance(check_timescale_available):
    """
    Test that 90-day trend queries complete within 1 second.
    
    Requirement 12.7: Return 90-day trend data within 1 second
    """
    pool = TimescaleConnectionPool(
        host="localhost",
        port=5432,
        database="postgres",
        user="postgres",
        password="password"
    )
    
    await pool.initialize()
    
    # Initialize schema
    schema_manager = TimescaleSchemaManager(pool.pool)
    await schema_manager.create_schema()
    
    # Write test data spanning 90 days
    metrics_writer = TimescaleMetricsWriter(pool.pool)
    
    base_time = datetime.utcnow() - timedelta(days=90)
    
    # Write one metric per day for 90 days
    for day in range(90):
        timestamp = base_time + timedelta(days=day)
        await metrics_writer.write_employee_metrics(
            employee_id="test_emp_perf",
            metrics={
                'degree_centrality': 0.25,
                'betweenness_centrality': 0.15,
                'clustering_coeff': 0.42,
                'burnout_score': 60.0 + day * 0.1
            },
            timestamp=timestamp
        )
    
    # Query 90-day trend and measure time
    query_service = TimescaleQueryService(pool.pool)
    
    start_time = datetime.utcnow()
    trend = await query_service.get_employee_trend(
        employee_id="test_emp_perf",
        days=90
    )
    end_time = datetime.utcnow()
    
    query_duration = (end_time - start_time).total_seconds()
    
    assert len(trend) == 90, "Should retrieve 90 data points"
    assert query_duration < 1.0, f"90-day query should complete in <1 second, took {query_duration}s"
    
    print(f"90-day trend query took {query_duration:.3f} seconds")
    
    await pool.close()


def test_timescale_modules_importable():
    """
    Test that all TimescaleDB modules can be imported without errors.
    
    This test runs even without TimescaleDB available.
    """
    from backend.core.timescale_schema import TimescaleSchemaManager
    from backend.core.timescale_metrics import TimescaleMetricsWriter, InterventionAuditLogger
    from backend.core.timescale_queries import TimescaleQueryService
    from backend.core.graph_builder_timescale import GraphBuilderWithTimescale
    
    assert TimescaleSchemaManager is not None
    assert TimescaleMetricsWriter is not None
    assert InterventionAuditLogger is not None
    assert TimescaleQueryService is not None
    assert GraphBuilderWithTimescale is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
