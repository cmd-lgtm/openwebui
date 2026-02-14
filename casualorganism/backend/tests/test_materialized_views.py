"""
Property tests for MaterializedViewManager.
Validates: Requirements 8.5
"""
import pytest
from backend.core.materialized_views import MaterializedViewManager


class MockNeo4jPool:
    """Mock Neo4j connection pool for testing"""
    
    def __init__(self):
        self.queries = []
        self.results = []
    
    async def execute_read(self, query: str, params: dict) -> list:
        self.queries.append((query, params))
        return self.results
    
    async def execute_write(self, query: str, params: dict) -> list:
        self.queries.append((query, params))
        return []
    
    async def health_check(self) -> bool:
        return True


@pytest.fixture
def mock_pool():
    return MockNeo4jPool()


@pytest.fixture
def manager(mock_pool):
    return MaterializedViewManager(mock_pool)


class TestMaterializedViewUsage:
    """Property tests for materialized view usage"""
    
    @pytest.mark.asyncio
    async def test_get_employee_metrics_queries_materialized_view(self, manager, mock_pool):
        """
        Property: Materialized View Usage
        When querying employee metrics, the system should read from 
        pre-computed node properties in Neo4j, not calculate on-demand.
        """
        # Setup mock data matching materialized view structure
        mock_pool.results = [{
            'employee_id': 'emp_1',
            'name': 'John Doe',
            'team': 'Engineering',
            'role': 'Developer',
            'is_manager': 0,
            'degree_centrality': 0.25,
            'betweenness_centrality': 0.1,
            'clustering_coeff': 0.5
        }]
        
        # Execute query
        result = await manager.get_employee_metrics('emp_1')
        
        # Verify the query reads from node properties (not calculating)
        assert len(mock_pool.queries) == 1
        query, params = mock_pool.queries[0]
        
        # Check that query reads pre-computed properties
        assert 'degree_centrality' in query
        assert 'betweenness_centrality' in query
        assert 'clustering_coeff' in query
        assert 'RETURN' in query.upper()
        assert params['employee_id'] == 'emp_1'
        
        # Verify result structure
        assert result is not None
        assert result['employee_id'] == 'emp_1'
        assert result['degree_centrality'] == 0.25
        assert result['betweenness_centrality'] == 0.1
        assert result['clustering_coeff'] == 0.5
    
    @pytest.mark.asyncio
    async def test_get_all_employee_metrics_returns_all_from_view(self, manager, mock_pool):
        """
        Property: Materialized View Usage for Bulk Query
        When querying all employee metrics, should return all from 
        materialized view in single query.
        """
        mock_pool.results = [
            {
                'employee_id': 'emp_1',
                'name': 'John Doe',
                'team': 'Engineering',
                'role': 'Developer',
                'is_manager': 0,
                'degree_centrality': 0.25,
                'betweenness_centrality': 0.1,
                'clustering_coeff': 0.5
            },
            {
                'employee_id': 'emp_2',
                'name': 'Jane Smith',
                'team': 'Sales',
                'role': 'Manager',
                'is_manager': 1,
                'degree_centrality': 0.3,
                'betweenness_centrality': 0.15,
                'clustering_coeff': 0.6
            }
        ]
        
        result = await manager.get_all_employee_metrics()
        
        assert len(result) == 2
        assert result[0]['employee_id'] == 'emp_1'
        assert result[1]['employee_id'] == 'emp_2'
        
        # Verify single query for all employees
        assert len(mock_pool.queries) == 1
        query = mock_pool.queries[0][0]
        assert 'ORDER BY' in query.upper() or 'RETURN' in query.upper()
    
    @pytest.mark.asyncio
    async def test_get_employee_metrics_returns_none_for_missing(self, manager, mock_pool):
        """
        Property: Materialized View Usage - Missing Employee
        When querying for non-existent employee, should return None.
        """
        mock_pool.results = []
        
        result = await manager.get_employee_metrics('nonexistent')
        
        assert result is None
        assert len(mock_pool.queries) == 1
    
    @pytest.mark.asyncio
    async def test_materialized_view_contains_all_required_metrics(self, manager, mock_pool):
        """
        Property: Complete Materialized View Schema
        Materialized view should include all required metrics as node properties.
        """
        mock_pool.results = [{
            'employee_id': 'emp_1',
            'name': 'John Doe',
            'team': 'Engineering',
            'role': 'Developer',
            'is_manager': 0,
            'degree_centrality': 0.25,
            'betweenness_centrality': 0.1,
            'clustering_coeff': 0.5
        }]
        
        result = await manager.get_employee_metrics('emp_1')
        
        # Verify all required metrics are present
        required_metrics = [
            'employee_id', 'name', 'team', 'role', 'is_manager',
            'degree_centrality', 'betweenness_centrality', 'clustering_coeff'
        ]
        
        for metric in required_metrics:
            assert metric in result, f"Missing metric: {metric}"
    
    @pytest.mark.asyncio
    async def test_materialized_view_query_uses_parameterized_statement(self, manager, mock_pool):
        """
        Property: Secure Materialized View Query
        Queries should use parameterized statements to prevent injection.
        """
        mock_pool.results = []
        
        await manager.get_employee_metrics('emp_1')
        
        query, params = mock_pool.queries[0]
        
        # Verify parameterized query (uses $employee_id)
        assert '$employee_id' in query
        assert params['employee_id'] == 'emp_1'
