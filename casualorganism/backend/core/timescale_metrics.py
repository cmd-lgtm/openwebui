"""
TimescaleDB metrics writer for storing computed graph metrics with timestamps.

This module handles writing employee metrics to TimescaleDB for historical
trend analysis and anomaly detection.

Requirements:
- 12.1: Write computed metrics with timestamps
"""
import asyncpg
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd


class TimescaleMetricsWriter:
    """
    Writes computed graph metrics to TimescaleDB with timestamps.
    Supports both single and batch writes for efficiency.
    """
    
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
    
    async def write_employee_metrics(
        self,
        employee_id: str,
        metrics: Dict[str, float],
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Write metrics for a single employee.
        
        Args:
            employee_id: Employee identifier
            metrics: Dictionary with keys: degree_centrality, betweenness_centrality,
                    clustering_coeff, burnout_score
            timestamp: Timestamp for the metrics (defaults to now)
        
        Returns:
            True if successful, False otherwise
        
        Requirement 12.1: Write computed metrics with timestamps
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO employee_metrics 
                    (timestamp, employee_id, degree_centrality, betweenness_centrality,
                     clustering_coeff, burnout_score)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, 
                    timestamp,
                    employee_id,
                    metrics.get('degree_centrality'),
                    metrics.get('betweenness_centrality'),
                    metrics.get('clustering_coeff'),
                    metrics.get('burnout_score')
                )
            return True
        except Exception as e:
            print(f"Error writing employee metrics: {e}")
            return False
    
    async def write_employee_metrics_batch(
        self,
        metrics_list: List[Dict[str, Any]],
        timestamp: Optional[datetime] = None
    ) -> int:
        """
        Write metrics for multiple employees in a batch for efficiency.
        
        Args:
            metrics_list: List of dictionaries, each containing:
                         - employee_id: str
                         - degree_centrality: float
                         - betweenness_centrality: float
                         - clustering_coeff: float
                         - burnout_score: float
            timestamp: Timestamp for all metrics (defaults to now)
        
        Returns:
            Number of records successfully written
        
        Requirement 12.1: Batch writes for efficiency
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        if not metrics_list:
            return 0
        
        try:
            async with self.pool.acquire() as conn:
                # Prepare batch insert
                records = [
                    (
                        timestamp,
                        m['employee_id'],
                        m.get('degree_centrality'),
                        m.get('betweenness_centrality'),
                        m.get('clustering_coeff'),
                        m.get('burnout_score')
                    )
                    for m in metrics_list
                ]
                
                # Use COPY for efficient batch insert
                await conn.copy_records_to_table(
                    'employee_metrics',
                    records=records,
                    columns=['timestamp', 'employee_id', 'degree_centrality',
                            'betweenness_centrality', 'clustering_coeff', 'burnout_score']
                )
            
            return len(records)
        except Exception as e:
            print(f"Error writing batch employee metrics: {e}")
            return 0
    
    async def write_metrics_from_dataframe(
        self,
        df: pd.DataFrame,
        timestamp: Optional[datetime] = None
    ) -> int:
        """
        Write metrics from a pandas DataFrame.
        
        Args:
            df: DataFrame with columns: employee_id, degree_centrality,
                betweenness_centrality, clustering_coeff, burnout_score
            timestamp: Timestamp for all metrics (defaults to now)
        
        Returns:
            Number of records successfully written
        """
        if df.empty:
            return 0
        
        # Convert DataFrame to list of dictionaries
        metrics_list = df.to_dict('records')
        return await self.write_employee_metrics_batch(metrics_list, timestamp)
    
    async def get_latest_metrics(
        self,
        employee_id: str,
        limit: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Get the most recent metrics for an employee.
        
        Args:
            employee_id: Employee identifier
            limit: Number of recent records to retrieve
        
        Returns:
            List of metric records ordered by timestamp descending
        """
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT timestamp, employee_id, degree_centrality,
                           betweenness_centrality, clustering_coeff, burnout_score
                    FROM employee_metrics
                    WHERE employee_id = $1
                    ORDER BY timestamp DESC
                    LIMIT $2
                """, employee_id, limit)
                
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error fetching latest metrics: {e}")
            return []
    
    async def get_metrics_count(self) -> int:
        """
        Get total count of metrics records.
        
        Returns:
            Total number of records in employee_metrics table
        """
        try:
            async with self.pool.acquire() as conn:
                count = await conn.fetchval("""
                    SELECT COUNT(*) FROM employee_metrics
                """)
                return count or 0
        except Exception as e:
            print(f"Error getting metrics count: {e}")
            return 0


class InterventionAuditLogger:
    """
    Logs intervention events to TimescaleDB for audit trail.
    """
    
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
    
    async def log(
        self,
        action: str,
        intervention_id: str,
        details: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Write audit log entry for an intervention event.
        
        Args:
            action: Action type (e.g., "intervention_proposed", "intervention_executed")
            intervention_id: UUID of the intervention
            details: Additional details as JSON
            timestamp: Timestamp for the event (defaults to now)
        
        Returns:
            True if successful, False otherwise
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO intervention_audit_log 
                    (timestamp, action, intervention_id, details)
                    VALUES ($1, $2, $3, $4)
                """,
                    timestamp,
                    action,
                    intervention_id,
                    details
                )
            return True
        except Exception as e:
            print(f"Error writing audit log: {e}")
            return False
    
    async def query(
        self,
        start_date: datetime,
        end_date: datetime,
        intervention_id: Optional[str] = None,
        action: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query audit log with filters.
        
        Args:
            start_date: Start of time range
            end_date: End of time range
            intervention_id: Optional filter by intervention ID
            action: Optional filter by action type
        
        Returns:
            List of audit log entries
        """
        try:
            query = """
                SELECT timestamp, action, intervention_id, details
                FROM intervention_audit_log
                WHERE timestamp BETWEEN $1 AND $2
            """
            params = [start_date, end_date]
            
            if intervention_id:
                query += " AND intervention_id = $3"
                params.append(intervention_id)
            
            if action:
                param_num = len(params) + 1
                query += f" AND action = ${param_num}"
                params.append(action)
            
            query += " ORDER BY timestamp DESC"
            
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error querying audit log: {e}")
            return []
