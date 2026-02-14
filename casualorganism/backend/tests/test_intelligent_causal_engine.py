"""
Tests for IntelligentCausalEngine - intelligent engine selection based on data size.
"""
import pytest
import pandas as pd
from unittest.mock import Mock, AsyncMock, patch
from backend.core.spark_engine import IntelligentCausalEngine


class TestIntelligentEngineSelection:
    """Test intelligent engine selection based on data size."""
    
    @pytest.mark.asyncio
    async def test_uses_pandas_for_small_datasets(self):
        """
        Test that IntelligentCausalEngine uses Pandas for datasets < 100K rows.
        Validates: Requirements 9.1
        """
        engine = IntelligentCausalEngine()
        
        # Mock _get_row_count to return small dataset size
        with patch.object(engine, '_get_row_count', return_value=50000):
            # Mock _fetch_pandas to return test data
            test_df = pd.DataFrame({
                'degree_centrality': [0.5, 0.6, 0.7],
                'is_manager': [0, 1, 0],
                'burnout_score': [60, 70, 65]
            })
            with patch.object(engine, '_fetch_pandas', return_value=test_df):
                # Mock pandas engine analyze
                with patch.object(engine.pandas_engine, 'analyze', return_value={'engine': 'pandas'}):
                    result = await engine.analyze("neo4j", {})
                    
                    # Verify Pandas engine was used
                    assert result['engine'] == 'pandas'
                    assert engine.spark_engine is None  # Spark should not be initialized
    
    @pytest.mark.asyncio
    async def test_uses_spark_for_large_datasets(self):
        """
        Test that IntelligentCausalEngine uses Spark for datasets >= 100K rows.
        Validates: Requirements 9.1
        """
        engine = IntelligentCausalEngine()
        
        # Mock _get_row_count to return large dataset size
        with patch.object(engine, '_get_row_count', return_value=150000):
            # Mock _fetch_spark to return mock Spark DataFrame
            mock_spark_df = Mock()
            with patch.object(engine, '_fetch_spark', return_value=mock_spark_df):
                # Mock DistributedCausalEngine
                mock_spark_engine = Mock()
                mock_spark_engine.analyze_spark_df.return_value = {'engine': 'spark'}
                
                with patch('backend.core.spark_engine.DistributedCausalEngine', return_value=mock_spark_engine):
                    result = await engine.analyze("neo4j", {})
                    
                    # Verify Spark engine was used
                    assert result['engine'] == 'spark'
                    assert engine.spark_engine is not None  # Spark should be initialized
    
    @pytest.mark.asyncio
    async def test_threshold_boundary_at_100k(self):
        """
        Test that the threshold is exactly 100,000 rows.
        99,999 rows should use Pandas, 100,000 should use Spark.
        Validates: Requirements 9.1, 9.3
        """
        # Test just below threshold
        engine1 = IntelligentCausalEngine()
        with patch.object(engine1, '_get_row_count', return_value=99999):
            test_df = pd.DataFrame({
                'degree_centrality': [0.5],
                'is_manager': [0],
                'burnout_score': [60]
            })
            with patch.object(engine1, '_fetch_pandas', return_value=test_df):
                with patch.object(engine1.pandas_engine, 'analyze', return_value={'engine': 'pandas'}):
                    result = await engine1.analyze("neo4j", {})
                    assert result['engine'] == 'pandas'
        
        # Test at threshold
        engine2 = IntelligentCausalEngine()
        with patch.object(engine2, '_get_row_count', return_value=100000):
            mock_spark_df = Mock()
            with patch.object(engine2, '_fetch_spark', return_value=mock_spark_df):
                mock_spark_engine = Mock()
                mock_spark_engine.analyze_spark_df.return_value = {'engine': 'spark'}
                with patch('backend.core.spark_engine.DistributedCausalEngine', return_value=mock_spark_engine):
                    result = await engine2.analyze("neo4j", {})
                    assert result['engine'] == 'spark'
    
    @pytest.mark.asyncio
    async def test_avoids_pandas_conversion_for_large_datasets(self):
        """
        Test that Spark engine reads directly from database without Pandas conversion.
        Validates: Requirements 9.2, 9.5
        """
        engine = IntelligentCausalEngine()
        
        # Mock large dataset
        with patch.object(engine, '_get_row_count', return_value=200000):
            mock_spark_df = Mock()
            
            # Verify _fetch_spark is called (not _fetch_pandas)
            with patch.object(engine, '_fetch_spark', return_value=mock_spark_df) as mock_fetch_spark:
                with patch.object(engine, '_fetch_pandas') as mock_fetch_pandas:
                    mock_spark_engine = Mock()
                    mock_spark_engine.analyze_spark_df.return_value = {'engine': 'spark'}
                    
                    with patch('backend.core.spark_engine.DistributedCausalEngine', return_value=mock_spark_engine):
                        await engine.analyze("neo4j", {})
                        
                        # Verify Spark fetch was called, not Pandas fetch
                        mock_fetch_spark.assert_called_once()
                        mock_fetch_pandas.assert_not_called()


class TestEngineDataSourceIntegration:
    """Test that engine correctly passes data source information."""
    
    @pytest.mark.asyncio
    async def test_passes_neo4j_params_correctly(self):
        """
        Test that Neo4j connection parameters are passed correctly.
        Validates: Requirements 9.4
        """
        engine = IntelligentCausalEngine()
        
        params = {
            "neo4j_uri": "bolt://test:7687",
            "neo4j_user": "test_user",
            "neo4j_password": "test_pass"
        }
        
        with patch.object(engine, '_get_row_count', return_value=50000):
            test_df = pd.DataFrame({
                'degree_centrality': [0.5],
                'is_manager': [0],
                'burnout_score': [60]
            })
            with patch.object(engine, '_fetch_pandas', return_value=test_df) as mock_fetch:
                with patch.object(engine.pandas_engine, 'analyze', return_value={}):
                    await engine.analyze("neo4j", params)
                    
                    # Verify params were passed to fetch method
                    mock_fetch.assert_called_once_with("neo4j", params)
    
    @pytest.mark.asyncio
    async def test_passes_timescale_params_correctly(self):
        """
        Test that TimescaleDB connection parameters are passed correctly.
        Validates: Requirements 9.4
        """
        engine = IntelligentCausalEngine()
        
        mock_pool = Mock()
        params = {
            "timescale_pool": mock_pool,
            "timescale_host": "localhost",
            "timescale_port": 5432
        }
        
        with patch.object(engine, '_get_row_count', return_value=50000):
            test_df = pd.DataFrame({
                'degree_centrality': [0.5],
                'is_manager': [0],
                'burnout_score': [60]
            })
            with patch.object(engine, '_fetch_pandas', return_value=test_df) as mock_fetch:
                with patch.object(engine.pandas_engine, 'analyze', return_value={}):
                    await engine.analyze("timescale", params)
                    
                    # Verify params were passed to fetch method
                    mock_fetch.assert_called_once_with("timescale", params)
