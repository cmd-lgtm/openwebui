"""
TimescaleDB schema initialization for time-series metrics storage.

This module creates hypertables for employee metrics and intervention audit logs,
with appropriate indexes for common queries.

Requirements:
- 12.1: Store employee metrics with timestamps
- 12.2: Store intervention audit log with timestamps
"""
import asyncpg
from typing import Optional


class TimescaleSchemaManager:
    """
    Manages TimescaleDB schema creation and initialization.
    """
    
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
    
    async def create_schema(self):
        """
        Create all required tables, hypertables, and indexes.
        
        Requirements:
        - 12.1: Create employee_metrics hypertable
        - 12.2: Create intervention_audit_log hypertable
        """
        await self._create_employee_metrics_table()
        await self._create_intervention_audit_log_table()
        await self._create_interventions_table()
        await self._create_indexes()
        await self._configure_retention_and_downsampling()
    
    async def _create_employee_metrics_table(self):
        """
        Create employee_metrics hypertable for time-series metrics storage.
        
        Stores computed metrics with timestamps for historical trend analysis.
        """
        async with self.pool.acquire() as conn:
            # Create table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS employee_metrics (
                    timestamp TIMESTAMPTZ NOT NULL,
                    employee_id VARCHAR(50) NOT NULL,
                    degree_centrality FLOAT,
                    betweenness_centrality FLOAT,
                    clustering_coeff FLOAT,
                    burnout_score FLOAT,
                    PRIMARY KEY (timestamp, employee_id)
                )
            """)
            
            # Convert to hypertable for time-series optimization
            # Check if already a hypertable
            is_hypertable = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM timescaledb_information.hypertables 
                    WHERE hypertable_name = 'employee_metrics'
                )
            """)
            
            if not is_hypertable:
                await conn.execute("""
                    SELECT create_hypertable('employee_metrics', 'timestamp', 
                                             if_not_exists => TRUE)
                """)
    
    async def _create_intervention_audit_log_table(self):
        """
        Create intervention_audit_log hypertable for immutable audit trail.
        
        Stores all intervention events with timestamps for compliance and debugging.
        """
        async with self.pool.acquire() as conn:
            # Create table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS intervention_audit_log (
                    timestamp TIMESTAMPTZ NOT NULL,
                    action VARCHAR(50) NOT NULL,
                    intervention_id UUID NOT NULL,
                    details JSONB,
                    PRIMARY KEY (timestamp, intervention_id, action)
                )
            """)
            
            # Convert to hypertable
            is_hypertable = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM timescaledb_information.hypertables 
                    WHERE hypertable_name = 'intervention_audit_log'
                )
            """)
            
            if not is_hypertable:
                await conn.execute("""
                    SELECT create_hypertable('intervention_audit_log', 'timestamp',
                                             if_not_exists => TRUE)
                """)
    
    async def _create_interventions_table(self):
        """
        Create interventions table for intervention state tracking.
        
        Stores current state of interventions (not time-series).
        """
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS interventions (
                    id UUID PRIMARY KEY,
                    type VARCHAR(50) NOT NULL,
                    target_employee_id VARCHAR(50) NOT NULL,
                    params JSONB,
                    reason TEXT,
                    impact_level VARCHAR(20),
                    status VARCHAR(20),
                    proposed_at TIMESTAMPTZ,
                    approved_at TIMESTAMPTZ,
                    executed_at TIMESTAMPTZ,
                    rolled_back_at TIMESTAMPTZ,
                    result JSONB,
                    rollback_data JSONB,
                    error TEXT
                )
            """)
    
    async def _create_indexes(self):
        """
        Create indexes for common query patterns.
        
        Optimizes queries by employee_id, time ranges, and intervention status.
        """
        async with self.pool.acquire() as conn:
            # Employee metrics indexes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_employee_metrics_employee_id 
                ON employee_metrics (employee_id, timestamp DESC)
            """)
            
            # Intervention audit log indexes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_intervention_audit_log_intervention_id 
                ON intervention_audit_log (intervention_id, timestamp DESC)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_intervention_audit_log_action 
                ON intervention_audit_log (action, timestamp DESC)
            """)
            
            # Interventions table indexes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_interventions_status 
                ON interventions (status)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_interventions_target 
                ON interventions (target_employee_id)
            """)
    
    async def drop_schema(self):
        """
        Drop all tables (for testing purposes).
        """
        async with self.pool.acquire() as conn:
            await conn.execute("DROP TABLE IF EXISTS employee_metrics CASCADE")
            await conn.execute("DROP TABLE IF EXISTS intervention_audit_log CASCADE")
            await conn.execute("DROP TABLE IF EXISTS interventions CASCADE")
    
    async def _configure_retention_and_downsampling(self):
        """
        Configure data retention policies and continuous aggregates for downsampling.
        
        Requirements:
        - 12.3: Set 90-day retention for raw data
        - 12.4: Create continuous aggregate for hourly data
        - 12.5: Retain hourly aggregates for 2 years
        - 12.8: Enable compression for old data
        """
        await self._configure_employee_metrics_retention()
        await self._create_hourly_aggregate()
        await self._configure_compression()
    
    async def _configure_employee_metrics_retention(self):
        """
        Set 90-day retention policy for raw employee metrics data.
        
        Requirement 12.3: Raw data retained for 90 days
        """
        async with self.pool.acquire() as conn:
            # Check if retention policy already exists
            existing_policy = await conn.fetchval("""
                SELECT job_id FROM timescaledb_information.jobs
                WHERE proc_name = 'policy_retention'
                AND hypertable_name = 'employee_metrics'
            """)
            
            if not existing_policy:
                await conn.execute("""
                    SELECT add_retention_policy('employee_metrics', 
                                                INTERVAL '90 days',
                                                if_not_exists => TRUE)
                """)
    
    async def _create_hourly_aggregate(self):
        """
        Create continuous aggregate for hourly employee metrics.
        
        Requirements:
        - 12.4: Create continuous aggregate for hourly data
        - 12.5: Retain hourly aggregates for 2 years
        """
        async with self.pool.acquire() as conn:
            # Create continuous aggregate view
            await conn.execute("""
                CREATE MATERIALIZED VIEW IF NOT EXISTS employee_metrics_hourly
                WITH (timescaledb.continuous) AS
                SELECT 
                    time_bucket('1 hour', timestamp) AS hour,
                    employee_id,
                    AVG(degree_centrality) as avg_degree_centrality,
                    AVG(betweenness_centrality) as avg_betweenness_centrality,
                    AVG(clustering_coeff) as avg_clustering_coeff,
                    AVG(burnout_score) as avg_burnout_score,
                    MAX(burnout_score) as max_burnout_score,
                    MIN(burnout_score) as min_burnout_score,
                    COUNT(*) as sample_count
                FROM employee_metrics
                GROUP BY hour, employee_id
                WITH NO DATA
            """)
            
            # Add refresh policy to keep aggregate up to date
            # Check if refresh policy already exists
            existing_refresh = await conn.fetchval("""
                SELECT job_id FROM timescaledb_information.jobs
                WHERE proc_name = 'policy_refresh_continuous_aggregate'
                AND config->>'mat_hypertable_id' = (
                    SELECT id::text FROM _timescaledb_catalog.hypertable 
                    WHERE table_name = 'employee_metrics_hourly'
                )
            """)
            
            if not existing_refresh:
                await conn.execute("""
                    SELECT add_continuous_aggregate_policy('employee_metrics_hourly',
                        start_offset => INTERVAL '3 hours',
                        end_offset => INTERVAL '1 hour',
                        schedule_interval => INTERVAL '1 hour',
                        if_not_exists => TRUE)
                """)
            
            # Add retention policy for hourly aggregates (2 years)
            existing_retention = await conn.fetchval("""
                SELECT job_id FROM timescaledb_information.jobs
                WHERE proc_name = 'policy_retention'
                AND config->>'hypertable_name' = 'employee_metrics_hourly'
            """)
            
            if not existing_retention:
                await conn.execute("""
                    SELECT add_retention_policy('employee_metrics_hourly',
                                                INTERVAL '2 years',
                                                if_not_exists => TRUE)
                """)
    
    async def _configure_compression(self):
        """
        Enable compression for old data to save storage space.
        
        Requirement 12.8: Enable compression for old data
        """
        async with self.pool.acquire() as conn:
            # Enable compression on employee_metrics
            await conn.execute("""
                ALTER TABLE employee_metrics SET (
                    timescaledb.compress,
                    timescaledb.compress_segmentby = 'employee_id',
                    timescaledb.compress_orderby = 'timestamp DESC'
                )
            """)
            
            # Add compression policy (compress data older than 30 days)
            existing_compression = await conn.fetchval("""
                SELECT job_id FROM timescaledb_information.jobs
                WHERE proc_name = 'policy_compression'
                AND hypertable_name = 'employee_metrics'
            """)
            
            if not existing_compression:
                await conn.execute("""
                    SELECT add_compression_policy('employee_metrics',
                                                  INTERVAL '30 days',
                                                  if_not_exists => TRUE)
                """)
