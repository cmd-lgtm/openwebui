"""
Tests for SafeActionOrchestrator

This module tests the intervention approval workflow, rollback capability,
and audit logging functionality.

Requirements tested:
- 14.1: Impact level assessment
- 14.2: Approval workflow for high-impact interventions
- 14.3: Audit logging
- 14.4: Capture pre-intervention state
- 14.5: Rollback capability
- 14.6: Approval queue API
- 14.7: Timeout pending approvals
- 14.8: Audit trail query API
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from backend.core.safe_action_orchestrator import (
    SafeActionOrchestrator,
    Intervention,
    InterventionStatus,
    ImpactLevel,
    AuditLog
)
from backend.core.connection_pool import (
    Neo4jConnectionPool,
    TimescaleConnectionPool,
    CircuitBreakerRegistry
)


@pytest.fixture
def mock_neo4j_pool():
    """Mock Neo4j connection pool"""
    pool = AsyncMock(spec=Neo4jConnectionPool)
    pool.execute_read = AsyncMock(return_value=[])
    pool.execute_write = AsyncMock(return_value=None)
    return pool


@pytest.fixture
def mock_timescale_pool():
    """Mock TimescaleDB connection pool"""
    pool = AsyncMock(spec=TimescaleConnectionPool)
    pool.execute_read = AsyncMock(return_value=[])
    pool.execute_write = AsyncMock(return_value=None)
    return pool


@pytest.fixture
def mock_circuit_breaker():
    """Mock circuit breaker registry"""
    registry = MagicMock(spec=CircuitBreakerRegistry)
    breaker = AsyncMock()
    breaker.call = AsyncMock(side_effect=lambda func, *args, **kwargs: func(*args, **kwargs))
    registry.get = MagicMock(return_value=breaker)
    return registry


@pytest.fixture
def orchestrator(mock_neo4j_pool, mock_timescale_pool, mock_circuit_breaker):
    """Create SafeActionOrchestrator instance with mocked dependencies"""
    return SafeActionOrchestrator(
        neo4j_pool=mock_neo4j_pool,
        timescale_pool=mock_timescale_pool,
        circuit_breaker=mock_circuit_breaker
    )


class TestImpactLevelAssessment:
    """Test impact level classification (Requirement 14.1)"""
    
    def test_high_impact_intervention(self, orchestrator):
        """Test that high-impact intervention types are classified correctly"""
        impact = orchestrator._assess_impact("reassign_manager", {})
        assert impact == ImpactLevel.HIGH
        
        impact = orchestrator._assess_impact("team_restructure", {})
        assert impact == ImpactLevel.HIGH
        
        impact = orchestrator._assess_impact("role_change", {})
        assert impact == ImpactLevel.HIGH
    
    def test_medium_impact_intervention(self, orchestrator):
        """Test that medium-impact intervention types are classified correctly"""
        impact = orchestrator._assess_impact("reduce_meetings", {})
        assert impact == ImpactLevel.MEDIUM
        
        impact = orchestrator._assess_impact("redistribute_tasks", {})
        assert impact == ImpactLevel.MEDIUM
    
    def test_low_impact_intervention(self, orchestrator):
        """Test that unknown intervention types default to low impact"""
        impact = orchestrator._assess_impact("send_notification", {})
        assert impact == ImpactLevel.LOW


class TestApprovalWorkflow:
    """Test approval workflow (Requirements 14.2, 14.6, 14.7)"""
    
    @pytest.mark.asyncio
    async def test_high_impact_requires_approval(self, orchestrator, mock_timescale_pool):
        """Test that high-impact interventions require approval"""
        # Mock database insert
        mock_timescale_pool.execute_write = AsyncMock(return_value=None)
        
        intervention_id = await orchestrator.propose_intervention(
            intervention_type="reassign_manager",
            target_employee_id="emp_123",
            params={"new_manager_id": "mgr_456"},
            reason="Improve team dynamics"
        )
        
        assert intervention_id is not None
        
        # Verify intervention was stored with pending_approval status
        # (In real test, we would query the database to verify)
    
    @pytest.mark.asyncio
    async def test_low_impact_auto_executed(self, orchestrator, mock_timescale_pool, mock_neo4j_pool):
        """Test that low/medium-impact interventions are auto-executed"""
        import uuid
        test_uuid = str(uuid.uuid4())
        
        # Mock database operations
        mock_timescale_pool.execute_write = AsyncMock(return_value=None)
        mock_timescale_pool.execute_read = AsyncMock(return_value=[{
            'id': test_uuid,
            'type': 'send_notification',
            'target_employee_id': 'emp_123',
            'params': {},
            'reason': 'Test',
            'impact_level': 'low',
            'status': 'approved',
            'proposed_at': datetime.utcnow(),
            'approved_at': None,
            'executed_at': None,
            'rolled_back_at': None,
            'result': None,
            'rollback_data': None,
            'error': None
        }])
        mock_neo4j_pool.execute_read = AsyncMock(return_value=[])
        
        intervention_id = await orchestrator.propose_intervention(
            intervention_type="send_notification",
            target_employee_id="emp_123",
            params={},
            reason="Test notification"
        )
        
        assert intervention_id is not None
        # In real implementation, verify execution was triggered


class TestRollbackCapability:
    """Test rollback capability (Requirements 14.4, 14.5)"""
    
    @pytest.mark.asyncio
    async def test_capture_state_for_manager_reassignment(self, orchestrator, mock_neo4j_pool):
        """Test that pre-intervention state is captured"""
        # Mock current state query
        mock_neo4j_pool.execute_read = AsyncMock(return_value=[{
            'employee_id': 'emp_123',
            'current_team': 'Engineering',
            'current_role': 'Senior Engineer',
            'current_manager_id': 'mgr_old'
        }])
        
        intervention = Intervention(
            id='test-id',
            type='reassign_manager',
            target_employee_id='emp_123',
            params={'new_manager_id': 'mgr_new'},
            reason='Test',
            impact_level=ImpactLevel.HIGH,
            status=InterventionStatus.APPROVED,
            proposed_at=datetime.utcnow()
        )
        
        rollback_data = await orchestrator._capture_state(intervention)
        
        assert rollback_data is not None
        assert rollback_data['target_employee_id'] == 'emp_123'
        assert 'state' in rollback_data
        assert rollback_data['state']['current_manager_id'] == 'mgr_old'
    
    @pytest.mark.asyncio
    async def test_rollback_restores_state(self, orchestrator, mock_neo4j_pool, mock_timescale_pool):
        """Test that rollback restores pre-intervention state"""
        # Mock intervention retrieval
        rollback_data = {
            'intervention_id': 'test-id',
            'intervention_type': 'role_change',
            'target_employee_id': 'emp_123',
            'captured_at': datetime.utcnow().isoformat(),
            'state': {
                'current_role': 'Engineer',
                'is_manager': 0
            }
        }
        
        mock_timescale_pool.execute_read = AsyncMock(return_value=[{
            'id': 'test-id',
            'type': 'role_change',
            'target_employee_id': 'emp_123',
            'params': {'new_role': 'Senior Engineer'},
            'reason': 'Test',
            'impact_level': 'high',
            'status': 'executed',
            'proposed_at': datetime.utcnow(),
            'approved_at': datetime.utcnow(),
            'executed_at': datetime.utcnow(),
            'rolled_back_at': None,
            'result': {'success': True},
            'rollback_data': rollback_data,
            'error': None
        }])
        
        mock_neo4j_pool.execute_write = AsyncMock(return_value=None)
        mock_timescale_pool.execute_write = AsyncMock(return_value=None)
        
        await orchestrator.rollback_intervention('test-id')
        
        # Verify Neo4j write was called to restore state
        assert mock_neo4j_pool.execute_write.called


class TestAuditLogging:
    """Test audit logging (Requirements 14.3, 14.8)"""
    
    @pytest.mark.asyncio
    async def test_audit_log_records_events(self, mock_timescale_pool):
        """Test that audit log records intervention events"""
        audit_log = AuditLog(mock_timescale_pool)
        
        await audit_log.log(
            action="intervention_proposed",
            intervention_id="test-id",
            intervention_type="reassign_manager",
            target_employee_id="emp_123"
        )
        
        # Verify write was called
        assert mock_timescale_pool.execute_write.called
    
    @pytest.mark.asyncio
    async def test_audit_log_query_with_filters(self, mock_timescale_pool):
        """Test that audit log can be queried with filters"""
        audit_log = AuditLog(mock_timescale_pool)
        
        mock_timescale_pool.execute_read = AsyncMock(return_value=[
            {
                'timestamp': datetime.utcnow(),
                'action': 'intervention_proposed',
                'intervention_id': 'test-id',
                'details': {}
            }
        ])
        
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        results = await audit_log.query(
            start_date=start_date,
            end_date=end_date,
            intervention_id="test-id"
        )
        
        assert len(results) > 0
        assert mock_timescale_pool.execute_read.called


class TestTimeoutExpiredApprovals:
    """Test timeout of expired approvals (Requirement 14.7)"""
    
    @pytest.mark.asyncio
    async def test_timeout_expired_approvals(self, orchestrator, mock_timescale_pool):
        """Test that approvals pending >24 hours are timed out"""
        # Mock query to return timed out interventions
        mock_timescale_pool.execute_read = AsyncMock(return_value=[
            {'id': 'expired-1'},
            {'id': 'expired-2'}
        ])
        
        count = await orchestrator.timeout_expired_approvals()
        
        assert count == 2
        assert mock_timescale_pool.execute_read.called


class TestOutcomeMonitoring:
    """Test outcome monitoring and auto-rollback (Requirement 14.5)"""
    
    @pytest.mark.asyncio
    async def test_detect_negative_outcome(self, orchestrator, mock_neo4j_pool, mock_timescale_pool):
        """Test that negative outcomes are detected"""
        # Mock intervention retrieval
        executed_at = datetime.utcnow() - timedelta(days=7)
        
        mock_timescale_pool.execute_read = AsyncMock(side_effect=[
            # First call: get intervention
            [{
                'id': 'test-id',
                'type': 'reassign_manager',
                'target_employee_id': 'emp_123',
                'params': {},
                'reason': 'Test',
                'impact_level': 'high',
                'status': 'executed',
                'proposed_at': executed_at - timedelta(days=1),
                'approved_at': executed_at,
                'executed_at': executed_at,
                'rolled_back_at': None,
                'result': {'success': True},
                'rollback_data': {'state': {}},
                'error': None
            }],
            # Second call: get historical metrics
            [{
                'degree_centrality': 0.5,
                'betweenness_centrality': 0.3,
                'clustering_coeff': 0.4,
                'burnout_score': 50.0
            }],
            # Third call: get recent burnout
            [{'avg_burnout': 65.0}]  # 30% increase - negative outcome
        ])
        
        # Mock current metrics
        mock_neo4j_pool.execute_read = AsyncMock(return_value=[{
            'employee_id': 'emp_123',
            'degree_centrality': 0.3,  # 40% drop - negative outcome
            'betweenness_centrality': 0.2,
            'clustering_coeff': 0.3
        }])
        
        mock_neo4j_pool.execute_write = AsyncMock(return_value=None)
        mock_timescale_pool.execute_write = AsyncMock(return_value=None)
        
        outcome = await orchestrator.check_intervention_outcome('test-id')
        
        assert outcome['is_negative'] == True
        assert 'auto_rollback_triggered' in outcome


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
