"""
TimescaleDB query service for historical trend analysis.

This module provides query functions for retrieving time-series metrics
from TimescaleDB with date range filtering.

Requirements:
- 12.6: Query TimescaleDB for time-series data with date range filtering
- 12.7: Return 90-day trend data within 1 second
"""
import asyncpg
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta


class TimescaleQueryService:
    """
    Service for querying historical metrics from TimescaleDB.
    """
    
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
    
    async def get_employee_trend(
        self,
        employee_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        days: int = 90
    ) -> List[Dict[str, Any]]:
        """
        Get historical trend data for a specific employee.
        
        Args:
            employee_id: Employee identifier
            start_date: Start of time range (optional)
            end_date: End of time range (optional)
            days: Number of days to look back if start_date not provided
        
        Returns:
            List of metric records ordered by timestamp
        
        Requirements:
        - 12.6: Query TimescaleDB for time-series data with date range filtering
        - 12.7: Return 90-day trend data within 1 second
        """
        if end_date is None:
            end_date = datetime.utcnow()
        
        if start_date is None:
            start_date = end_date - timedelta(days=days)
        
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT 
                        timestamp,
                        employee_id,
                        degree_centrality,
                        betweenness_centrality,
                        clustering_coeff,
                        burnout_score
                    FROM employee_metrics
                    WHERE employee_id = $1
                      AND timestamp BETWEEN $2 AND $3
                    ORDER BY timestamp ASC
                """, employee_id, start_date, end_date)
                
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error fetching employee trend: {e}")
            return []
    
    async def get_employee_hourly_trend(
        self,
        employee_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        days: int = 90
    ) -> List[Dict[str, Any]]:
        """
        Get hourly aggregated trend data for a specific employee.
        
        Uses continuous aggregate for faster queries on long time ranges.
        
        Args:
            employee_id: Employee identifier
            start_date: Start of time range (optional)
            end_date: End of time range (optional)
            days: Number of days to look back if start_date not provided
        
        Returns:
            List of hourly aggregated metric records
        
        Requirement 12.4: Query continuous aggregate for hourly data
        """
        if end_date is None:
            end_date = datetime.utcnow()
        
        if start_date is None:
            start_date = end_date - timedelta(days=days)
        
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT 
                        hour as timestamp,
                        employee_id,
                        avg_degree_centrality as degree_centrality,
                        avg_betweenness_centrality as betweenness_centrality,
                        avg_clustering_coeff as clustering_coeff,
                        avg_burnout_score as burnout_score,
                        max_burnout_score,
                        min_burnout_score,
                        sample_count
                    FROM employee_metrics_hourly
                    WHERE employee_id = $1
                      AND hour BETWEEN $2 AND $3
                    ORDER BY hour ASC
                """, employee_id, start_date, end_date)
                
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error fetching employee hourly trend: {e}")
            return []
    
    async def get_team_trend(
        self,
        team_name: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        days: int = 90
    ) -> List[Dict[str, Any]]:
        """
        Get aggregated trend data for all employees in a team.
        
        Args:
            team_name: Team name
            start_date: Start of time range (optional)
            end_date: End of time range (optional)
            days: Number of days to look back if start_date not provided
        
        Returns:
            List of aggregated metric records by timestamp
        """
        if end_date is None:
            end_date = datetime.utcnow()
        
        if start_date is None:
            start_date = end_date - timedelta(days=days)
        
        try:
            async with self.pool.acquire() as conn:
                # Join with Neo4j data would be needed for team filtering
                # For now, this is a placeholder that would need integration
                rows = await conn.fetch("""
                    SELECT 
                        time_bucket('1 day', timestamp) as day,
                        AVG(degree_centrality) as avg_degree_centrality,
                        AVG(betweenness_centrality) as avg_betweenness_centrality,
                        AVG(clustering_coeff) as avg_clustering_coeff,
                        AVG(burnout_score) as avg_burnout_score,
                        MAX(burnout_score) as max_burnout_score,
                        COUNT(*) as employee_count
                    FROM employee_metrics
                    WHERE timestamp BETWEEN $1 AND $2
                    GROUP BY day
                    ORDER BY day ASC
                """, start_date, end_date)
                
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error fetching team trend: {e}")
            return []
    
    async def get_burnout_alerts(
        self,
        threshold: float = 70.0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Get employees with burnout scores above threshold in time range.
        
        Args:
            threshold: Burnout score threshold
            start_date: Start of time range (optional)
            end_date: End of time range (optional)
            days: Number of days to look back if start_date not provided
        
        Returns:
            List of employees with high burnout scores
        """
        if end_date is None:
            end_date = datetime.utcnow()
        
        if start_date is None:
            start_date = end_date - timedelta(days=days)
        
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT DISTINCT ON (employee_id)
                        employee_id,
                        timestamp,
                        burnout_score,
                        degree_centrality,
                        betweenness_centrality,
                        clustering_coeff
                    FROM employee_metrics
                    WHERE timestamp BETWEEN $1 AND $2
                      AND burnout_score >= $3
                    ORDER BY employee_id, timestamp DESC
                """, start_date, end_date, threshold)
                
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error fetching burnout alerts: {e}")
            return []
    
    async def get_metric_statistics(
        self,
        metric_name: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        days: int = 30
    ) -> Dict[str, float]:
        """
        Get statistical summary for a specific metric over time range.
        
        Args:
            metric_name: Name of metric (degree_centrality, betweenness_centrality,
                        clustering_coeff, burnout_score)
            start_date: Start of time range (optional)
            end_date: End of time range (optional)
            days: Number of days to look back if start_date not provided
        
        Returns:
            Dictionary with min, max, avg, stddev statistics
        """
        if end_date is None:
            end_date = datetime.utcnow()
        
        if start_date is None:
            start_date = end_date - timedelta(days=days)
        
        # Validate metric name to prevent SQL injection
        valid_metrics = [
            'degree_centrality', 'betweenness_centrality',
            'clustering_coeff', 'burnout_score'
        ]
        if metric_name not in valid_metrics:
            return {}
        
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(f"""
                    SELECT 
                        MIN({metric_name}) as min_value,
                        MAX({metric_name}) as max_value,
                        AVG({metric_name}) as avg_value,
                        STDDEV({metric_name}) as stddev_value,
                        COUNT(*) as sample_count
                    FROM employee_metrics
                    WHERE timestamp BETWEEN $1 AND $2
                      AND {metric_name} IS NOT NULL
                """, start_date, end_date)
                
                if row:
                    return dict(row)
                return {}
        except Exception as e:
            print(f"Error fetching metric statistics: {e}")
            return {}
    
    async def get_recent_metrics_count(
        self,
        hours: int = 24
    ) -> int:
        """
        Get count of metrics records in recent time window.
        
        Useful for monitoring data ingestion.
        
        Args:
            hours: Number of hours to look back
        
        Returns:
            Count of records
        """
        try:
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            async with self.pool.acquire() as conn:
                count = await conn.fetchval("""
                    SELECT COUNT(*) 
                    FROM employee_metrics
                    WHERE timestamp >= $1
                """, cutoff)
                return count or 0
        except Exception as e:
            print(f"Error fetching recent metrics count: {e}")
            return 0
