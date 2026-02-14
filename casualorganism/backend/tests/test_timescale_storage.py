"""
Tests for TimescaleDB time-series storage implementation.

This test suite verifies:
- Schema creation (hypertables, indexes)
- Data retention and downsampling configuration
- Metrics writing (single and batch)
- Historical trend queries with date range filtering
"""
import pytest
import asyncpg
from datetime import datetime, timedelta
from backend.core.timescale_schema import TimescaleSchemaManager
from backend.core.timescale_metrics import TimescaleMetricsWriter, InterventionAuditLogger
from backend.core.timescale_queries import TimescaleQueryService
from backend.core.connection_pool import TimescaleConnectionPool
import pandas as pd


@pytest.fixture
async def timescale_pool():
    """Create TimescaleDB connection pool for testing."""
    pool = TimescaleConnectionPool(
        host="localhost",
        port=5432,
        database="postgres",
        user="postgres",
        password="password"
    )
    
    if await pool.initialize():
        yield pool
        await pool.close()
    else:
        pytest.skip("TimescaleDB not available")


@pytest.fixture
async def schema_manager(timescale_pool):
    """Create schema manager and initialize schema."""
    manager = TimescaleSchemaManager(timescale_pool.pool)
    
    # Clean up any existing test data
    await manager.drop_schema()
    
    # Create fresh schema
    await manager.create_schema()
    
    yield manager
    
    # Clean up after tests
    await manager.drop_schema()


@pytest.fixture
async def metrics_writer(timescale_pool):
    """Create metrics writer."""
    return TimescaleMetricsWriter(timescale_pool.pool)


@pytest.fixture
async def query_service(timescale_pool):
    """Create query service."""
    return TimescaleQueryService(timescale_pool.pool)


@pytest.fixture
async def audit_logger(timescale_pool):
    """Create audit logger."""
    return InterventionAuditLogger(timescale_pool.pool)


class TestSchemaCreation:
    """Test schema creation and hypertable configuration."""
    
    @pytest.mark.asyncio
    async def test_employee_metrics_table_created(self, schema_manager, timescale_pool):
        """
        Test that employee_metrics hypertable is created.
        
        Requirement 12.1: Create employee_metrics hypertable
        """
        async with timescale_pool.pool.acquire() as conn:
            # Check table exists
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = 'employee_metrics'
                )
            """)
            assert exists, "employee_metrics table should exist"
            
            # Check it's a hypertable
            is_hypertable = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM timescaledb_information.hypertables 
                    WHERE hypertable_name = 'employee_metrics'
                )
            """)
            assert is_hypertable, "employee_metrics should be a hypertable"
    
    @pytest.mark.asyncio
    async def test_intervention_audit_log_table_created(self, schema_manager, timescale_pool):
        """
        Test that intervention_audit_log hypertable is created.
        
        Requirement 12.2: Create intervention_audit_log hypertable
        """
        async with timescale_pool.pool.acquire() as conn:
            # Check table exists
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = 'intervention_audit_log'
                )
            """)
            assert exists, "intervention_audit_log table should exist"
            
            # Check it's a hypertable
            is_hypertable = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM timescaledb_information.hypertables 
                    WHERE hypertable_name = 'intervention_audit_log'
                )
            """)
            assert is_hypertable, "intervention_audit_log should be a hypertable"
    
    @pytest.mark.asyncio
    async def test_indexes_created(self, schema_manager, timescale_pool):
        """
        Test that indexes for common queries are created.
        
        Requirement 12.1, 12.2: Add indexes for common queries
        """
        async with timescale_pool.pool.acquire() as conn:
            # Check employee_metrics index
            index_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_indexes 
                    WHERE indexname = 'idx_employee_metrics_employee_id'
                )
            """)
            assert index_exists, "Employee metrics index should exist"
            
            # Check intervention audit log indexes
            audit_index_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_indexes 
                    WHERE indexname = 'idx_intervention_audit_log_intervention_id'
                )
            """)
            assert audit_index_exists, "Intervention audit log index should exist"


class TestRetentionAndDownsampling:
    """Test data retention policies and continuous aggregates."""
    
    @pytest.mark.asyncio
    async def test_retention_policy_configured(self, schema_manager, timescale_pool):
        """
        Test that 90-day retention policy is configured.
        
        Requirement 12.3: Set 90-day retention for raw data
        """
        async with timescale_pool.pool.acquire() as conn:
            # Check retention policy exists
            policy_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM timescaledb_information.jobs
                    WHERE proc_name = 'policy_retention'
                    AND hypertable_name = 'employee_metrics'
                )
            """)
            assert policy_exists, "Retention policy should be configured"
    
    @pytest.mark.asyncio
    async def test_hourly_aggregate_created(self, schema_manager, timescale_pool):
        """
        Test that continuous aggregate for hourly data is created.
        
        Requirement 12.4: Create continuous aggregate for hourly data
        """
        async with timescale_pool.pool.acquire() as conn:
            # Check continuous aggregate exists
            view_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM timescaledb_information.continuous_aggregates
                    WHERE view_name = 'employee_metrics_hourly'
                )
            """)
            assert view_exists, "Hourly continuous aggregate should exist"
    
    @pytest.mark.asyncio
    async def test_compression_enabled(self, schema_manager, timescale_pool):
        """
        Test that compression is enabled for old data.
        
        Requirement 12.8: Enable compression for old data
        """
        async with timescale_pool.pool.acquire() as conn:
            # Check compression policy exists
            compression_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM timescaledb_information.jobs
                    WHERE proc_name = 'policy_compression'
                    AND hypertable_name = 'employee_metrics'
                )
            """)
            assert compression_exists, "Compression policy should be configured"


class TestMetricsWriting:
    """Test writing metrics to TimescaleDB."""
    
    @pytest.mark.asyncio
    async def test_write_single_employee_metrics(self, schema_manager, metrics_writer):
        """
        Test writing metrics for a single employee.
        
        Requirement 12.1: Write computed metrics with timestamps
        """
        metrics = {
            'degree_centrality': 0.25,
            'betweenness_centrality': 0.15,
            'clustering_coeff': 0.42,
            'burnout_score': 65.3
        }
        
        success = await metrics_writer.write_employee_metrics(
            employee_id="emp_001",
            metrics=metrics,
            timestamp=datetime.utcnow()
        )
        
        assert success, "Should successfully write employee metrics"
        
        # Verify data was written
        count = await metrics_writer.get_metrics_count()
        assert count == 1, "Should have 1 metric record"
    
    @pytest.mark.asyncio
    async def test_write_batch_employee_metrics(self, schema_manager, metrics_writer):
        """
        Test batch writing metrics for multiple employees.
        
        Requirement 12.1: Batch writes for efficiency
        """
        metrics_list = [
            {
                'employee_id': f'emp_{i:03d}',
                'degree_centrality': 0.1 + i * 0.01,
                'betweenness_centrality': 0.05 + i * 0.005,
                'clustering_coeff': 0.3 + i * 0.01,
                'burnout_score': 50.0 + i
            }
            for i in range(10)
        ]
        
        count = await metrics_writer.write_employee_metrics_batch(
            metrics_list=metrics_list,
            timestamp=datetime.utcnow()
        )
        
        assert count == 10, "Should write 10 metric records"
        
        # Verify data was written
        total_count = await metrics_writer.get_metrics_count()
        assert total_count == 10, "Should have 10 metric records"
    
    @pytest.mark.asyncio
    async def test_write_metrics_from_dataframe(self, schema_manager, metrics_writer):
        """
        Test writing metrics from pandas DataFrame.
        
        Requirement 12.1: Write computed metrics with timestamps
        """
        df = pd.DataFrame([
            {
                'employee_id': 'emp_001',
                'degree_centrality': 0.25,
                'betweenness_centrality': 0.15,
                'clustering_coeff': 0.42,
                'burnout_score': 65.3
            },
            {
                'employee_id': 'emp_002',
                'degree_centrality': 0.30,
                'betweenness_centrality': 0.20,
                'clustering_coeff': 0.38,
                'burnout_score': 72.1
            }
        ])
        
        count = await metrics_writer.write_metrics_from_dataframe(df)
        
        assert count == 2, "Should write 2 metric records from DataFrame"


class TestHistoricalQueries:
    """Test querying historical trend data."""
    
    @pytest.mark.asyncio
    async def test_get_employee_trend(self, schema_manager, metrics_writer, query_service):
        """
        Test querying employee trend data with date range filtering.
        
        Requirement 12.6: Query TimescaleDB for time-series data with date range filtering
        """
        # Write test data spanning multiple days
        base_time = datetime.utcnow() - timedelta(days=10)
        
        for day in range(10):
            timestamp = base_time + timedelta(days=day)
            await metrics_writer.write_employee_metrics(
                employee_id="emp_001",
                metrics={
                    'degree_centrality': 0.25 + day * 0.01,
                    'betweenness_centrality': 0.15,
                    'clustering_coeff': 0.42,
                    'burnout_score': 60.0 + day
                },
                timestamp=timestamp
            )
        
        # Query trend data
        trend = await query_service.get_employee_trend(
            employee_id="emp_001",
            days=15
        )
        
        assert len(trend) == 10, "Should retrieve 10 data points"
        assert trend[0]['employee_id'] == "emp_001"
        assert 'timestamp' in trend[0]
        assert 'burnout_score' in trend[0]
    
    @pytest.mark.asyncio
    async def test_get_burnout_alerts(self, schema_manager, metrics_writer, query_service):
        """
        Test querying employees with high burnout scores.
        
        Requirement 12.6: Query TimescaleDB for time-series data
        """
        # Write test data with varying burnout scores
        timestamp = datetime.utcnow()
        
        for i in range(5):
            await metrics_writer.write_employee_metrics(
                employee_id=f"emp_{i:03d}",
                metrics={
                    'degree_centrality': 0.25,
                    'betweenness_centrality': 0.15,
                    'clustering_coeff': 0.42,
                    'burnout_score': 50.0 + i * 10  # 50, 60, 70, 80, 90
                },
                timestamp=timestamp
            )
        
        # Query burnout alerts (threshold 70)
        alerts = await query_service.get_burnout_alerts(
            threshold=70.0,
            days=1
        )
        
        assert len(alerts) == 3, "Should find 3 employees above threshold"
        for alert in alerts:
            assert alert['burnout_score'] >= 70.0
    
    @pytest.mark.asyncio
    async def test_get_metric_statistics(self, schema_manager, metrics_writer, query_service):
        """
        Test getting statistical summary for metrics.
        
        Requirement 12.6: Query TimescaleDB for time-series data
        """
        # Write test data
        timestamp = datetime.utcnow()
        
        for i in range(10):
            await metrics_writer.write_employee_metrics(
                employee_id=f"emp_{i:03d}",
                metrics={
                    'degree_centrality': 0.1 + i * 0.05,
                    'betweenness_centrality': 0.15,
                    'clustering_coeff': 0.42,
                    'burnout_score': 50.0 + i * 5
                },
                timestamp=timestamp
            )
        
        # Query statistics
        stats = await query_service.get_metric_statistics(
            metric_name='burnout_score',
            days=1
        )
        
        assert 'min_value' in stats
        assert 'max_value' in stats
        assert 'avg_value' in stats
        assert stats['min_value'] == 50.0
        assert stats['max_value'] == 95.0


class TestAuditLogging:
    """Test intervention audit logging."""
    
    @pytest.mark.asyncio
    async def test_write_audit_log(self, schema_manager, audit_logger):
        """
        Test writing intervention audit log entries.
        
        Requirement 12.2: Store intervention audit log with timestamps
        """
        success = await audit_logger.log(
            action="intervention_proposed",
            intervention_id="550e8400-e29b-41d4-a716-446655440000",
            details={"type": "reduce_meetings", "target": "emp_001"}
        )
        
        assert success, "Should successfully write audit log"
    
    @pytest.mark.asyncio
    async def test_query_audit_log(self, schema_manager, audit_logger):
        """
        Test querying audit log with filters.
        
        Requirement 12.2: Query audit trail
        """
        intervention_id = "550e8400-e29b-41d4-a716-446655440000"
        
        # Write multiple audit log entries
        await audit_logger.log(
            action="intervention_proposed",
            intervention_id=intervention_id,
            details={"type": "reduce_meetings"}
        )
        
        await audit_logger.log(
            action="intervention_executed",
            intervention_id=intervention_id,
            details={"result": "success"}
        )
        
        # Query audit log
        start_date = datetime.utcnow() - timedelta(hours=1)
        end_date = datetime.utcnow() + timedelta(hours=1)
        
        logs = await audit_logger.query(
            start_date=start_date,
            end_date=end_date,
            intervention_id=intervention_id
        )
        
        assert len(logs) == 2, "Should retrieve 2 audit log entries"
        assert logs[0]['intervention_id'] == intervention_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
