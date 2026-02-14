"""
Materialized View Manager for graph metrics.
Pre-computes expensive graph metrics for fast queries.
"""
from typing import Dict, Any, Optional
import asyncio
import time


class MaterializedViewManager:
    """
    Pre-computes expensive graph metrics for fast queries.
    Stores results as node properties in Neo4j.
    """
    
    def __init__(self, neo4j_pool):
        self.neo4j_pool = neo4j_pool
        self._initialized = False
    
    async def initialize(self) -> bool:
        """Initialize the materialized view manager."""
        if not self.neo4j_pool:
            return False
        return await self.neo4j_pool.health_check()
    
    async def create_degree_centrality_view(self) -> bool:
        """
        Create degree centrality materialized view.
        Updates incrementally on edge changes.
        """
        if not self.neo4j_pool:
            return False
        
        query = """
        MATCH (e:Employee)
        OPTIONAL MATCH (e)-[r]-()
        WITH e, count(r) as degree
        MATCH (all:Employee)
        WITH e, degree, count(all) as total_nodes
        SET e.degree_centrality = toFloat(degree) / (total_nodes - 1)
        RETURN count(e) as updated_count
        """
        
        try:
            result = await self.neo4j_pool.execute_write(query, {})
            return True
        except Exception as e:
            print(f"Failed to create degree centrality view: {e}")
            return False
    
    async def create_betweenness_centrality_view(self) -> bool:
        """
        Create betweenness centrality materialized view.
        Expensive operation, should be scheduled refresh.
        """
        if not self.neo4j_pool:
            return False
        
        # Check if GDS is available
        try:
            # Try to create graph projection
            await self.neo4j_pool.execute_write("""
                CALL gds.graph.project(
                    'org_graph',
                    'Employee',
                    'INTERACTS',
                    {relationshipProperties: 'weight'}
                )
            """, {})
            
            # Calculate betweenness centrality
            await self.neo4j_pool.execute_write("""
                CALL gds.betweenness.write('org_graph', {
                    writeProperty: 'betweenness_centrality'
                })
            """, {})
            
            # Drop graph projection
            await self.neo4j_pool.execute_write("CALL gds.graph.drop('org_graph', false)", {})
            
            return True
        except Exception as e:
            print(f"Failed to create betweenness centrality view: {e}")
            return False
    
    async def create_clustering_coefficient_view(self) -> bool:
        """
        Create clustering coefficient materialized view.
        Expensive operation, should be scheduled refresh.
        """
        if not self.neo4j_pool:
            return False
        
        try:
            # Try to create graph projection
            await self.neo4j_pool.execute_write("""
                CALL gds.graph.project(
                    'org_graph',
                    'Employee',
                    'INTERACTS',
                    {relationshipProperties: 'weight'}
                )
            """, {})
            
            # Calculate clustering coefficient
            await self.neo4j_pool.execute_write("""
                CALL gds.localClusteringCoefficient.write('org_graph', {
                    writeProperty: 'clustering_coeff'
                })
            """, {})
            
            # Drop graph projection
            await self.neo4j_pool.execute_write("CALL gds.graph.drop('org_graph', false)", {})
            
            return True
        except Exception as e:
            print(f"Failed to create clustering coefficient view: {e}")
            return False
    
    async def refresh_expensive_metrics(self) -> bool:
        """
        Scheduled refresh of expensive metrics (betweenness, clustering).
        Should be run hourly or on demand.
        """
        if not self.neo4j_pool:
            return False
        
        try:
            # Drop existing graph projection if exists
            try:
                await self.neo4j_pool.execute_write("CALL gds.graph.drop('org_graph', false)", {})
            except Exception:
                pass
            
            # Create graph projection
            await self.neo4j_pool.execute_write("""
                CALL gds.graph.project(
                    'org_graph',
                    'Employee',
                    'INTERACTS',
                    {relationshipProperties: 'weight'}
                )
            """, {})
            
            # Calculate betweenness centrality
            await self.neo4j_pool.execute_write("""
                CALL gds.betweenness.write('org_graph', {
                    writeProperty: 'betweenness_centrality'
                })
            """, {})
            
            # Calculate clustering coefficient
            await self.neo4j_pool.execute_write("""
                CALL gds.localClusteringCoefficient.write('org_graph', {
                    writeProperty: 'clustering_coeff'
                })
            """, {})
            
            # Drop graph projection
            await self.neo4j_pool.execute_write("CALL gds.graph.drop('org_graph', false)", {})
            
            return True
        except Exception as e:
            print(f"Failed to refresh expensive metrics: {e}")
            return False
    
    async def get_employee_metrics(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """
        Fast query from materialized views.
        Returns all metrics for an employee.
        """
        if not self.neo4j_pool:
            return None
        
        query = """
        MATCH (e:Employee {id: $employee_id})
        RETURN 
            e.id as employee_id,
            e.name as name,
            e.team as team,
            e.role as role,
            e.is_manager as is_manager,
            e.degree_centrality as degree_centrality,
            e.betweenness_centrality as betweenness_centrality,
            e.clustering_coeff as clustering_coeff
        """
        
        try:
            result = await self.neo4j_pool.execute_read(query, {"employee_id": employee_id})
            return result[0] if result else None
        except Exception as e:
            print(f"Failed to get employee metrics: {e}")
            return None
    
    async def get_all_employee_metrics(self) -> list:
        """
        Get all employee metrics from materialized views.
        """
        if not self.neo4j_pool:
            return []
        
        query = """
        MATCH (e:Employee)
        RETURN 
            e.id as employee_id,
            e.name as name,
            e.team as team,
            e.role as role,
            e.is_manager as is_manager,
            e.degree_centrality as degree_centrality,
            e.betweenness_centrality as betweenness_centrality,
            e.clustering_coeff as clustering_coeff
        ORDER BY e.name
        """
        
        try:
            result = await self.neo4j_pool.execute_read(query, {})
            return result
        except Exception as e:
            print(f"Failed to get all employee metrics: {e}")
            return []
    
    async def close(self):
        """Close the materialized view manager."""
        self._initialized = False
