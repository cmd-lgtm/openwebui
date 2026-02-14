"""
Enhanced graph builder that writes computed metrics to TimescaleDB.

This module extends the existing graph building functionality to persist
metrics to TimescaleDB for historical trend analysis.

Requirements:
- 12.1: Write computed metrics with timestamps
"""
from typing import Optional, Dict, Any
import pandas as pd
from datetime import datetime
from backend.core.timescale_metrics import TimescaleMetricsWriter
from backend.core.connection_pool import TimescaleConnectionPool


class GraphBuilderWithTimescale:
    """
    Wrapper around graph builders that persists metrics to TimescaleDB.
    
    This class can wrap either OrganizationalGraph or Neo4jAdapter and
    automatically write computed metrics to TimescaleDB after enrichment.
    """
    
    def __init__(
        self,
        graph_adapter,
        timescale_pool: Optional[TimescaleConnectionPool] = None
    ):
        """
        Initialize the graph builder with TimescaleDB integration.
        
        Args:
            graph_adapter: Either OrganizationalGraph or Neo4jAdapter instance
            timescale_pool: TimescaleDB connection pool (optional)
        """
        self.graph = graph_adapter
        self.timescale_pool = timescale_pool
        self.metrics_writer = None
        
        if timescale_pool and timescale_pool._initialized:
            self.metrics_writer = TimescaleMetricsWriter(timescale_pool.pool)
    
    def build(self, data: Dict[str, Any]):
        """
        Build the graph using the underlying adapter.
        
        Args:
            data: Graph data with employees and interactions
        """
        self.graph.build(data)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get graph statistics.
        
        Returns:
            Dictionary with node_count, edge_count, density
        """
        return self.graph.get_stats()
    
    async def enrich_and_export(
        self,
        output_file: Optional[str] = None,
        write_to_timescale: bool = True,
        timestamp: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Calculate graph metrics and optionally write to TimescaleDB.
        
        Args:
            output_file: Optional CSV file path for export
            write_to_timescale: Whether to write metrics to TimescaleDB
            timestamp: Timestamp for metrics (defaults to now)
        
        Returns:
            DataFrame with enriched employee metrics
        
        Requirements:
        - 12.1: Write computed metrics with timestamps
        """
        # Get enriched metrics from underlying graph adapter
        df = self.graph.enrich_and_export(output_file)
        
        # Write to TimescaleDB if enabled and writer is available
        if write_to_timescale and self.metrics_writer:
            await self._write_metrics_to_timescale(df, timestamp)
        
        return df
    
    async def _write_metrics_to_timescale(
        self,
        df: pd.DataFrame,
        timestamp: Optional[datetime] = None
    ):
        """
        Write metrics DataFrame to TimescaleDB.
        
        Args:
            df: DataFrame with employee metrics
            timestamp: Timestamp for all metrics (defaults to now)
        
        Requirement 12.1: Batch writes for efficiency
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        try:
            # Write metrics in batch for efficiency
            count = await self.metrics_writer.write_metrics_from_dataframe(df, timestamp)
            print(f"Wrote {count} employee metrics to TimescaleDB at {timestamp}")
        except Exception as e:
            print(f"Error writing metrics to TimescaleDB: {e}")
    
    async def write_single_employee_metrics(
        self,
        employee_id: str,
        metrics: Dict[str, float],
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Write metrics for a single employee to TimescaleDB.
        
        Useful for incremental updates after graph changes.
        
        Args:
            employee_id: Employee identifier
            metrics: Dictionary with centrality and burnout metrics
            timestamp: Timestamp for metrics (defaults to now)
        
        Returns:
            True if successful, False otherwise
        """
        if not self.metrics_writer:
            return False
        
        return await self.metrics_writer.write_employee_metrics(
            employee_id, metrics, timestamp
        )
    
    def close(self):
        """Close the underlying graph adapter."""
        if hasattr(self.graph, 'close'):
            self.graph.close()


async def initialize_timescale_for_graph_builder(
    host: str = "localhost",
    port: int = 5432,
    database: str = "postgres",
    user: str = "postgres",
    password: str = "password"
) -> Optional[TimescaleConnectionPool]:
    """
    Initialize TimescaleDB connection pool for graph builder.
    
    Args:
        host: TimescaleDB host
        port: TimescaleDB port
        database: Database name
        user: Database user
        password: Database password
    
    Returns:
        Initialized TimescaleConnectionPool or None if initialization fails
    """
    from backend.core.timescale_schema import TimescaleSchemaManager
    
    pool = TimescaleConnectionPool(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password
    )
    
    # Initialize connection pool
    if await pool.initialize():
        print("TimescaleDB connection pool initialized")
        
        # Create schema if not exists
        schema_manager = TimescaleSchemaManager(pool.pool)
        await schema_manager.create_schema()
        print("TimescaleDB schema initialized")
        
        return pool
    else:
        print("Failed to initialize TimescaleDB connection pool")
        return None
