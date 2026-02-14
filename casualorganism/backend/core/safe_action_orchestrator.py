"""
Safe Action Orchestrator with Safety Rails

This module implements autonomous intervention execution with approval workflow,
rollback capability, and comprehensive audit logging.

Requirements:
- 14.1: Classify interventions by impact level
- 14.2: Require approval for high-impact interventions
- 14.3: Log all intervention events
- 14.4: Store rollback procedures
- 14.5: Automatic rollback on negative outcomes
- 14.6: Expose approval queue API
- 14.7: Timeout pending approvals
- 14.8: Provide audit trail query API
"""
import uuid
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from enum import Enum

from backend.core.connection_pool import (
    Neo4jConnectionPool,
    TimescaleConnectionPool,
    CircuitBreakerRegistry
)


class ImpactLevel(str, Enum):
    """Impact level classification for interventions"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class InterventionStatus(str, Enum):
    """Status of an intervention"""
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    EXECUTED = "executed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    TIMEOUT = "timeout"


class Intervention:
    """
    Represents an intervention with all its metadata.
    """
    def __init__(
        self,
        id: str,
        type: str,
        target_employee_id: str,
        params: dict,
        reason: str,
        impact_level: ImpactLevel,
        status: InterventionStatus,
        proposed_at: datetime,
        approved_at: Optional[datetime] = None,
        executed_at: Optional[datetime] = None,
        rolled_back_at: Optional[datetime] = None,
        result: Optional[dict] = None,
        rollback_data: Optional[dict] = None,
        error: Optional[str] = None
    ):
        self.id = id
        self.type = type
        self.target_employee_id = target_employee_id
        self.params = params
        self.reason = reason
        self.impact_level = impact_level
        self.status = status
        self.proposed_at = proposed_at
        self.approved_at = approved_at
        self.executed_at = executed_at
        self.rolled_back_at = rolled_back_at
        self.result = result
        self.rollback_data = rollback_data
        self.error = error
    
    def to_dict(self) -> dict:
        """Convert intervention to dictionary for storage"""
        return {
            "id": self.id,
            "type": self.type,
            "target_employee_id": self.target_employee_id,
            "params": self.params,
            "reason": self.reason,
            "impact_level": self.impact_level.value,
            "status": self.status.value,
            "proposed_at": self.proposed_at.isoformat(),
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "rolled_back_at": self.rolled_back_at.isoformat() if self.rolled_back_at else None,
            "result": self.result,
            "rollback_data": self.rollback_data,
            "error": self.error
        }
    
    @classmethod
    def from_db_row(cls, row: dict) -> 'Intervention':
        """Create intervention from database row"""
        return cls(
            id=str(row['id']),
            type=row['type'],
            target_employee_id=row['target_employee_id'],
            params=row['params'],
            reason=row['reason'],
            impact_level=ImpactLevel(row['impact_level']),
            status=InterventionStatus(row['status']),
            proposed_at=row['proposed_at'],
            approved_at=row['approved_at'],
            executed_at=row['executed_at'],
            rolled_back_at=row['rolled_back_at'],
            result=row['result'],
            rollback_data=row['rollback_data'],
            error=row['error']
        )


class AuditLog:
    """
    Immutable audit trail for all interventions.
    
    Requirements:
    - 14.3: Log all intervention events to TimescaleDB
    - 14.8: Provide query API for audit trail
    """
    
    def __init__(self, timescale_pool: TimescaleConnectionPool):
        self.db = timescale_pool
    
    async def log(
        self,
        action: str,
        intervention_id: str,
        **kwargs
    ):
        """
        Write audit log entry.
        
        Args:
            action: Type of action (e.g., "intervention_proposed", "intervention_executed")
            intervention_id: UUID of the intervention
            **kwargs: Additional details to store in JSONB
        """
        query = """
        INSERT INTO intervention_audit_log 
        (timestamp, action, intervention_id, details)
        VALUES (NOW(), $1, $2, $3)
        """
        await self.db.execute_write(
            query,
            [action, intervention_id, json.dumps(kwargs)]
        )
    
    async def query(
        self,
        start_date: datetime,
        end_date: datetime,
        intervention_id: Optional[str] = None,
        action: Optional[str] = None,
        employee_id: Optional[str] = None
    ) -> List[dict]:
        """
        Query audit log with filters.
        
        Args:
            start_date: Start of time range
            end_date: End of time range
            intervention_id: Filter by specific intervention
            action: Filter by action type
            employee_id: Filter by target employee
        
        Returns:
            List of audit log entries
        """
        conditions = ["timestamp BETWEEN $1 AND $2"]
        params = [start_date, end_date]
        param_count = 2
        
        if intervention_id:
            param_count += 1
            conditions.append(f"intervention_id = ${param_count}")
            params.append(intervention_id)
        
        if action:
            param_count += 1
            conditions.append(f"action = ${param_count}")
            params.append(action)
        
        if employee_id:
            param_count += 1
            conditions.append(f"details->>'target_employee_id' = ${param_count}")
            params.append(employee_id)
        
        query = f"""
        SELECT * FROM intervention_audit_log
        WHERE {' AND '.join(conditions)}
        ORDER BY timestamp DESC
        LIMIT 1000
        """
        
        return await self.db.execute_read(query, params)


class SafeActionOrchestrator:
    """
    Executes autonomous interventions with approval workflow and rollback capability.
    
    Requirements:
    - 14.1: Classify interventions by impact level
    - 14.2: Require approval for high-impact interventions
    - 14.4: Capture pre-intervention state
    - 14.5: Automatic rollback on negative outcomes
    - 14.6: Expose approval queue API
    - 14.7: Timeout pending approvals (24 hours)
    """
    
    # Impact level classification rules
    HIGH_IMPACT_TYPES = {
        "reassign_manager",
        "team_restructure",
        "role_change",
        "fire_employee",
        "major_schedule_change"
    }
    
    MEDIUM_IMPACT_TYPES = {
        "reduce_meetings",
        "redistribute_tasks",
        "schedule_focus_time",
        "promote_role"
    }
    
    # Approval timeout (24 hours)
    APPROVAL_TIMEOUT = timedelta(hours=24)
    
    def __init__(
        self,
        neo4j_pool: Neo4jConnectionPool,
        timescale_pool: TimescaleConnectionPool,
        circuit_breaker: CircuitBreakerRegistry
    ):
        self.neo4j = neo4j_pool
        self.timescale = timescale_pool
        self.circuit_breaker = circuit_breaker
        self.audit_log = AuditLog(timescale_pool)
    
    def _assess_impact(self, intervention_type: str, params: dict) -> ImpactLevel:
        """
        Classify intervention impact level.
        
        Requirement 14.1: Classify interventions by impact level
        
        Args:
            intervention_type: Type of intervention
            params: Intervention parameters
        
        Returns:
            Impact level (LOW, MEDIUM, or HIGH)
        """
        if intervention_type in self.HIGH_IMPACT_TYPES:
            return ImpactLevel.HIGH
        elif intervention_type in self.MEDIUM_IMPACT_TYPES:
            return ImpactLevel.MEDIUM
        else:
            return ImpactLevel.LOW
    
    async def propose_intervention(
        self,
        intervention_type: str,
        target_employee_id: str,
        params: dict,
        reason: str
    ) -> str:
        """
        Propose intervention and determine if approval needed.
        
        Requirements:
        - 14.1: Assess impact level
        - 14.2: Require approval for high-impact interventions
        - 14.7: Auto-execute low/medium impact interventions
        
        Args:
            intervention_type: Type of intervention
            target_employee_id: Target employee ID
            params: Intervention parameters
            reason: Reason for intervention
        
        Returns:
            Intervention ID
        """
        impact_level = self._assess_impact(intervention_type, params)
        
        # Determine initial status based on impact level
        if impact_level == ImpactLevel.HIGH:
            status = InterventionStatus.PENDING_APPROVAL
        else:
            status = InterventionStatus.APPROVED
        
        intervention = Intervention(
            id=str(uuid.uuid4()),
            type=intervention_type,
            target_employee_id=target_employee_id,
            params=params,
            reason=reason,
            impact_level=impact_level,
            status=status,
            proposed_at=datetime.utcnow()
        )
        
        # Store in database
        await self._store_intervention(intervention)
        
        # Log proposal
        await self.audit_log.log(
            action="intervention_proposed",
            intervention_id=intervention.id,
            intervention_type=intervention_type,
            target_employee_id=target_employee_id,
            impact_level=impact_level.value,
            reason=reason
        )
        
        # Auto-execute low/medium impact
        if impact_level != ImpactLevel.HIGH:
            await self.execute_intervention(intervention.id)
        
        return intervention.id
    
    async def _store_intervention(self, intervention: Intervention):
        """
        Store intervention in database.
        
        Requirement 14.2: Store interventions in database
        """
        query = """
        INSERT INTO interventions 
        (id, type, target_employee_id, params, reason, impact_level, status, 
         proposed_at, approved_at, executed_at, rolled_back_at, result, rollback_data, error)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
        """
        await self.timescale.execute_write(
            query,
            [
                uuid.UUID(intervention.id),
                intervention.type,
                intervention.target_employee_id,
                json.dumps(intervention.params),
                intervention.reason,
                intervention.impact_level.value,
                intervention.status.value,
                intervention.proposed_at,
                intervention.approved_at,
                intervention.executed_at,
                intervention.rolled_back_at,
                json.dumps(intervention.result) if intervention.result else None,
                json.dumps(intervention.rollback_data) if intervention.rollback_data else None,
                intervention.error
            ]
        )
    
    async def _update_intervention(self, intervention: Intervention):
        """Update intervention in database"""
        query = """
        UPDATE interventions 
        SET status = $2, approved_at = $3, executed_at = $4, rolled_back_at = $5,
            result = $6, rollback_data = $7, error = $8
        WHERE id = $1
        """
        await self.timescale.execute_write(
            query,
            [
                uuid.UUID(intervention.id),
                intervention.status.value,
                intervention.approved_at,
                intervention.executed_at,
                intervention.rolled_back_at,
                json.dumps(intervention.result) if intervention.result else None,
                json.dumps(intervention.rollback_data) if intervention.rollback_data else None,
                intervention.error
            ]
        )
    
    async def _get_intervention(self, intervention_id: str) -> Intervention:
        """Retrieve intervention from database"""
        query = """
        SELECT * FROM interventions WHERE id = $1
        """
        rows = await self.timescale.execute_read(query, [uuid.UUID(intervention_id)])
        if not rows:
            raise ValueError(f"Intervention {intervention_id} not found")
        return Intervention.from_db_row(rows[0])
    
    async def approve_intervention(self, intervention_id: str):
        """
        Approve a pending intervention.
        
        Requirement 14.2: Approval workflow for high-impact interventions
        """
        intervention = await self._get_intervention(intervention_id)
        
        if intervention.status != InterventionStatus.PENDING_APPROVAL:
            raise ValueError(f"Intervention {intervention_id} is not pending approval")
        
        intervention.status = InterventionStatus.APPROVED
        intervention.approved_at = datetime.utcnow()
        await self._update_intervention(intervention)
        
        # Log approval
        await self.audit_log.log(
            action="intervention_approved",
            intervention_id=intervention.id
        )
        
        # Execute the intervention
        await self.execute_intervention(intervention_id)
    
    async def reject_intervention(self, intervention_id: str, reason: str):
        """
        Reject a pending intervention.
        """
        intervention = await self._get_intervention(intervention_id)
        
        if intervention.status != InterventionStatus.PENDING_APPROVAL:
            raise ValueError(f"Intervention {intervention_id} is not pending approval")
        
        intervention.status = InterventionStatus.FAILED
        intervention.error = f"Rejected: {reason}"
        await self._update_intervention(intervention)
        
        # Log rejection
        await self.audit_log.log(
            action="intervention_rejected",
            intervention_id=intervention.id,
            reason=reason
        )
    
    async def get_pending_approvals(self) -> List[Intervention]:
        """
        Get all interventions pending approval.
        
        Requirement 14.6: Expose approval queue API
        """
        query = """
        SELECT * FROM interventions 
        WHERE status = $1
        ORDER BY proposed_at ASC
        """
        rows = await self.timescale.execute_read(
            query,
            [InterventionStatus.PENDING_APPROVAL.value]
        )
        return [Intervention.from_db_row(row) for row in rows]
    
    async def timeout_expired_approvals(self):
        """
        Timeout pending approvals that exceed 24 hours.
        
        Requirement 14.7: Timeout pending approvals after 24 hours
        """
        timeout_threshold = datetime.utcnow() - self.APPROVAL_TIMEOUT
        
        query = """
        UPDATE interventions 
        SET status = $1, error = $2
        WHERE status = $3 AND proposed_at < $4
        RETURNING id
        """
        rows = await self.timescale.execute_read(
            query,
            [
                InterventionStatus.TIMEOUT.value,
                "Approval timeout exceeded (24 hours)",
                InterventionStatus.PENDING_APPROVAL.value,
                timeout_threshold
            ]
        )
        
        # Log timeouts
        for row in rows:
            await self.audit_log.log(
                action="intervention_timeout",
                intervention_id=str(row['id'])
            )
        
        return len(rows)
    
    async def execute_intervention(self, intervention_id: str):
        """
        Execute approved intervention with rollback capability.
        
        Requirements:
        - 14.4: Capture pre-intervention state
        - 14.5: Store rollback procedures
        
        Args:
            intervention_id: UUID of the intervention to execute
        """
        intervention = await self._get_intervention(intervention_id)
        
        if intervention.status != InterventionStatus.APPROVED:
            raise ValueError(f"Intervention {intervention_id} is not approved for execution")
        
        # Capture pre-intervention state for rollback
        rollback_data = await self._capture_state(intervention)
        intervention.rollback_data = rollback_data
        
        try:
            # Execute the intervention action
            result = await self._execute_action(intervention)
            
            # Update status to executed
            intervention.status = InterventionStatus.EXECUTED
            intervention.executed_at = datetime.utcnow()
            intervention.result = result
            await self._update_intervention(intervention)
            
            # Log execution
            await self.audit_log.log(
                action="intervention_executed",
                intervention_id=intervention.id,
                intervention_type=intervention.type,
                target_employee_id=intervention.target_employee_id,
                result=result
            )
            
            # Schedule outcome monitoring
            await self._schedule_outcome_monitoring(intervention, rollback_data)
            
        except Exception as e:
            # Log failure
            await self.audit_log.log(
                action="intervention_failed",
                intervention_id=intervention.id,
                error=str(e)
            )
            
            intervention.status = InterventionStatus.FAILED
            intervention.error = str(e)
            await self._update_intervention(intervention)
            raise
    
    async def _capture_state(self, intervention: Intervention) -> dict:
        """
        Capture pre-intervention state for rollback.
        
        Requirement 14.4: Capture pre-intervention state
        
        Args:
            intervention: The intervention to capture state for
        
        Returns:
            Dictionary containing state information needed for rollback
        """
        rollback_data = {
            "intervention_id": intervention.id,
            "intervention_type": intervention.type,
            "target_employee_id": intervention.target_employee_id,
            "captured_at": datetime.utcnow().isoformat(),
            "state": {}
        }
        
        # Capture state based on intervention type
        if intervention.type in ["reassign_manager", "team_restructure"]:
            # Capture current manager and team assignments
            query = """
            MATCH (e:Employee {id: $employee_id})
            OPTIONAL MATCH (e)-[:REPORTS_TO]->(manager:Employee)
            RETURN 
                e.id as employee_id,
                e.team as current_team,
                e.role as current_role,
                manager.id as current_manager_id
            """
            result = await self.neo4j.execute_read(
                query,
                {"employee_id": intervention.target_employee_id}
            )
            
            if result:
                rollback_data["state"] = {
                    "current_team": result[0].get("current_team"),
                    "current_role": result[0].get("current_role"),
                    "current_manager_id": result[0].get("current_manager_id")
                }
        
        elif intervention.type == "role_change":
            # Capture current role
            query = """
            MATCH (e:Employee {id: $employee_id})
            RETURN e.role as current_role, e.is_manager as is_manager
            """
            result = await self.neo4j.execute_read(
                query,
                {"employee_id": intervention.target_employee_id}
            )
            
            if result:
                rollback_data["state"] = {
                    "current_role": result[0].get("current_role"),
                    "is_manager": result[0].get("is_manager")
                }
        
        elif intervention.type in ["schedule_focus_time", "reduce_meetings"]:
            # For calendar-based interventions, store the action details
            # In a real system, this would query the calendar API
            rollback_data["state"] = {
                "calendar_events": intervention.params.get("affected_events", [])
            }
        
        elif intervention.type == "redistribute_tasks":
            # Store current task assignments
            rollback_data["state"] = {
                "original_assignments": intervention.params.get("original_assignments", {})
            }
        
        return rollback_data
    
    async def _execute_action(self, intervention: Intervention) -> dict:
        """
        Execute the actual intervention action.
        
        Args:
            intervention: The intervention to execute
        
        Returns:
            Dictionary containing execution results
        """
        result = {
            "executed_at": datetime.utcnow().isoformat(),
            "intervention_type": intervention.type,
            "target_employee_id": intervention.target_employee_id,
            "success": False,
            "details": {}
        }
        
        try:
            if intervention.type == "reassign_manager":
                # Update manager relationship in Neo4j
                new_manager_id = intervention.params.get("new_manager_id")
                
                query = """
                MATCH (e:Employee {id: $employee_id})
                OPTIONAL MATCH (e)-[old_rel:REPORTS_TO]->()
                DELETE old_rel
                WITH e
                MATCH (new_manager:Employee {id: $new_manager_id})
                CREATE (e)-[:REPORTS_TO]->(new_manager)
                RETURN e.id as employee_id, new_manager.id as new_manager_id
                """
                
                await self.neo4j.execute_write(
                    query,
                    {
                        "employee_id": intervention.target_employee_id,
                        "new_manager_id": new_manager_id
                    }
                )
                
                result["success"] = True
                result["details"] = {"new_manager_id": new_manager_id}
            
            elif intervention.type == "team_restructure":
                # Update team assignment in Neo4j
                new_team = intervention.params.get("new_team")
                
                query = """
                MATCH (e:Employee {id: $employee_id})
                SET e.team = $new_team
                RETURN e.id as employee_id, e.team as new_team
                """
                
                await self.neo4j.execute_write(
                    query,
                    {
                        "employee_id": intervention.target_employee_id,
                        "new_team": new_team
                    }
                )
                
                result["success"] = True
                result["details"] = {"new_team": new_team}
            
            elif intervention.type == "role_change":
                # Update role in Neo4j
                new_role = intervention.params.get("new_role")
                is_manager = intervention.params.get("is_manager", False)
                
                query = """
                MATCH (e:Employee {id: $employee_id})
                SET e.role = $new_role, e.is_manager = $is_manager
                RETURN e.id as employee_id, e.role as new_role
                """
                
                await self.neo4j.execute_write(
                    query,
                    {
                        "employee_id": intervention.target_employee_id,
                        "new_role": new_role,
                        "is_manager": 1 if is_manager else 0
                    }
                )
                
                result["success"] = True
                result["details"] = {"new_role": new_role, "is_manager": is_manager}
            
            elif intervention.type == "schedule_focus_time":
                # In a real system, this would call calendar API via circuit breaker
                # For now, we'll simulate the action
                duration = intervention.params.get("duration", 120)
                
                # Use circuit breaker for external API call
                breaker = self.circuit_breaker.get("calendar_api")
                
                # Simulated calendar API call
                async def schedule_event():
                    # This would be replaced with actual calendar API call
                    return {
                        "event_id": f"focus_time_{intervention.id}",
                        "duration": duration,
                        "scheduled": True
                    }
                
                event_result = await breaker.call(schedule_event)
                
                result["success"] = True
                result["details"] = event_result
            
            elif intervention.type == "reduce_meetings":
                # Simulate meeting reduction
                meetings_to_cancel = intervention.params.get("meeting_ids", [])
                
                result["success"] = True
                result["details"] = {
                    "cancelled_meetings": len(meetings_to_cancel),
                    "meeting_ids": meetings_to_cancel
                }
            
            elif intervention.type == "redistribute_tasks":
                # Simulate task redistribution
                task_assignments = intervention.params.get("new_assignments", {})
                
                result["success"] = True
                result["details"] = {
                    "reassigned_tasks": len(task_assignments),
                    "assignments": task_assignments
                }
            
            else:
                # Unknown intervention type
                result["success"] = False
                result["details"] = {"error": f"Unknown intervention type: {intervention.type}"}
        
        except Exception as e:
            result["success"] = False
            result["details"] = {"error": str(e)}
            raise
        
        return result
    
    async def rollback_intervention(self, intervention_id: str):
        """
        Rollback intervention to pre-execution state.
        
        Requirement 14.5: Rollback capability
        
        Args:
            intervention_id: UUID of the intervention to rollback
        """
        intervention = await self._get_intervention(intervention_id)
        
        if intervention.status != InterventionStatus.EXECUTED:
            raise ValueError(f"Intervention {intervention_id} is not in executed state")
        
        if not intervention.rollback_data:
            raise ValueError(f"No rollback data available for intervention {intervention_id}")
        
        try:
            # Execute rollback based on intervention type
            await self._restore_state(intervention.rollback_data)
            
            # Update status
            intervention.status = InterventionStatus.ROLLED_BACK
            intervention.rolled_back_at = datetime.utcnow()
            await self._update_intervention(intervention)
            
            # Log rollback
            await self.audit_log.log(
                action="intervention_rolled_back",
                intervention_id=intervention.id,
                intervention_type=intervention.type,
                target_employee_id=intervention.target_employee_id
            )
            
        except Exception as e:
            # Log rollback failure
            await self.audit_log.log(
                action="rollback_failed",
                intervention_id=intervention.id,
                error=str(e)
            )
            raise
    
    async def _restore_state(self, rollback_data: dict):
        """
        Restore system state from rollback data.
        
        Requirement 14.5: Execute rollback procedures
        
        Args:
            rollback_data: State information captured before intervention
        """
        intervention_type = rollback_data["intervention_type"]
        target_employee_id = rollback_data["target_employee_id"]
        state = rollback_data["state"]
        
        if intervention_type in ["reassign_manager", "team_restructure"]:
            # Restore manager and team assignments
            query = """
            MATCH (e:Employee {id: $employee_id})
            SET e.team = $team, e.role = $role
            WITH e
            OPTIONAL MATCH (e)-[old_rel:REPORTS_TO]->()
            DELETE old_rel
            WITH e
            MATCH (manager:Employee {id: $manager_id})
            CREATE (e)-[:REPORTS_TO]->(manager)
            RETURN e.id as employee_id
            """
            
            await self.neo4j.execute_write(
                query,
                {
                    "employee_id": target_employee_id,
                    "team": state.get("current_team"),
                    "role": state.get("current_role"),
                    "manager_id": state.get("current_manager_id")
                }
            )
        
        elif intervention_type == "role_change":
            # Restore role
            query = """
            MATCH (e:Employee {id: $employee_id})
            SET e.role = $role, e.is_manager = $is_manager
            RETURN e.id as employee_id
            """
            
            await self.neo4j.execute_write(
                query,
                {
                    "employee_id": target_employee_id,
                    "role": state.get("current_role"),
                    "is_manager": state.get("is_manager", 0)
                }
            )
        
        elif intervention_type in ["schedule_focus_time", "reduce_meetings"]:
            # Restore calendar events
            # In a real system, this would call calendar API to restore events
            calendar_events = state.get("calendar_events", [])
            
            # Use circuit breaker for external API call
            breaker = self.circuit_breaker.get("calendar_api")
            
            async def restore_events():
                # This would be replaced with actual calendar API call
                return {"restored_events": len(calendar_events)}
            
            await breaker.call(restore_events)
        
        elif intervention_type == "redistribute_tasks":
            # Restore task assignments
            # In a real system, this would call task management API
            original_assignments = state.get("original_assignments", {})
            
            # Simulated restoration
            pass
    
    async def _schedule_outcome_monitoring(
        self,
        intervention: Intervention,
        rollback_data: dict
    ):
        """
        Schedule outcome monitoring for executed intervention.
        
        Requirement 14.5: Monitor outcomes and trigger automatic rollback
        
        Args:
            intervention: The executed intervention
            rollback_data: Rollback data for potential automatic rollback
        """
        # Import here to avoid circular dependency
        from backend.worker import monitor_intervention_outcome
        
        # Schedule task to check outcomes after 7 days
        # In production, this would be configurable based on intervention type
        monitoring_delay = 7 * 86400  # 7 days in seconds
        
        monitor_intervention_outcome.apply_async(
            args=[intervention.id],
            countdown=monitoring_delay
        )
        
        # Log monitoring scheduled
        await self.audit_log.log(
            action="outcome_monitoring_scheduled",
            intervention_id=intervention.id,
            monitoring_delay_days=7
        )
    
    async def check_intervention_outcome(self, intervention_id: str) -> dict:
        """
        Check the outcome of an executed intervention.
        
        Requirement 14.5: Detect negative outcomes
        
        Args:
            intervention_id: UUID of the intervention to check
        
        Returns:
            Dictionary with outcome assessment
        """
        intervention = await self._get_intervention(intervention_id)
        
        if intervention.status != InterventionStatus.EXECUTED:
            return {
                "intervention_id": intervention_id,
                "outcome": "not_applicable",
                "reason": f"Intervention status is {intervention.status.value}, not executed"
            }
        
        # Assess outcome based on intervention type and target metrics
        outcome = await self._assess_outcome(intervention)
        
        # Log outcome check
        await self.audit_log.log(
            action="outcome_checked",
            intervention_id=intervention.id,
            outcome=outcome
        )
        
        # Trigger automatic rollback if outcome is negative
        if outcome["is_negative"]:
            await self.audit_log.log(
                action="negative_outcome_detected",
                intervention_id=intervention.id,
                details=outcome
            )
            
            # Automatically rollback
            await self.rollback_intervention(intervention_id)
            
            outcome["auto_rollback_triggered"] = True
        
        return outcome
    
    async def _assess_outcome(self, intervention: Intervention) -> dict:
        """
        Assess the outcome of an intervention.
        
        Requirement 14.5: Detect negative outcomes
        
        Args:
            intervention: The intervention to assess
        
        Returns:
            Dictionary with outcome assessment including is_negative flag
        """
        outcome = {
            "intervention_id": intervention.id,
            "intervention_type": intervention.type,
            "target_employee_id": intervention.target_employee_id,
            "is_negative": False,
            "metrics": {},
            "reason": ""
        }
        
        try:
            # Query current metrics for target employee
            query = """
            MATCH (e:Employee {id: $employee_id})
            RETURN 
                e.id as employee_id,
                e.degree_centrality as degree_centrality,
                e.betweenness_centrality as betweenness_centrality,
                e.clustering_coeff as clustering_coeff
            """
            
            current_metrics = await self.neo4j.execute_read(
                query,
                {"employee_id": intervention.target_employee_id}
            )
            
            if not current_metrics:
                outcome["reason"] = "Employee not found in graph"
                return outcome
            
            metrics = current_metrics[0]
            outcome["metrics"] = {
                "degree_centrality": metrics.get("degree_centrality"),
                "betweenness_centrality": metrics.get("betweenness_centrality"),
                "clustering_coeff": metrics.get("clustering_coeff")
            }
            
            # Query historical metrics from TimescaleDB to compare
            # Get metrics from before intervention execution
            if intervention.executed_at:
                historical_query = """
                SELECT 
                    degree_centrality,
                    betweenness_centrality,
                    clustering_coeff,
                    burnout_score
                FROM employee_metrics
                WHERE employee_id = $1
                AND timestamp < $2
                ORDER BY timestamp DESC
                LIMIT 1
                """
                
                historical_metrics = await self.timescale.execute_read(
                    historical_query,
                    [intervention.target_employee_id, intervention.executed_at]
                )
                
                if historical_metrics:
                    hist = historical_metrics[0]
                    
                    # Compare metrics to detect negative outcomes
                    # Negative outcome indicators:
                    # 1. Significant drop in centrality (isolation)
                    # 2. Significant increase in burnout score
                    
                    current_degree = metrics.get("degree_centrality", 0)
                    hist_degree = hist.get("degree_centrality", 0)
                    
                    # Check for isolation (>30% drop in degree centrality)
                    if hist_degree > 0 and current_degree < hist_degree * 0.7:
                        outcome["is_negative"] = True
                        outcome["reason"] = f"Significant drop in degree centrality: {hist_degree:.3f} -> {current_degree:.3f}"
                    
                    # Check for increased burnout (if available)
                    # This would require querying recent burnout scores
                    recent_burnout_query = """
                    SELECT AVG(burnout_score) as avg_burnout
                    FROM employee_metrics
                    WHERE employee_id = $1
                    AND timestamp > $2
                    """
                    
                    recent_burnout = await self.timescale.execute_read(
                        recent_burnout_query,
                        [intervention.target_employee_id, intervention.executed_at]
                    )
                    
                    if recent_burnout and recent_burnout[0].get("avg_burnout"):
                        current_burnout = recent_burnout[0]["avg_burnout"]
                        hist_burnout = hist.get("burnout_score", 0)
                        
                        # Check for significant burnout increase (>20% increase)
                        if hist_burnout > 0 and current_burnout > hist_burnout * 1.2:
                            outcome["is_negative"] = True
                            outcome["reason"] = f"Significant increase in burnout: {hist_burnout:.1f} -> {current_burnout:.1f}"
                            outcome["metrics"]["burnout_score"] = current_burnout
            
            if not outcome["is_negative"]:
                outcome["reason"] = "No negative outcomes detected"
        
        except Exception as e:
            outcome["reason"] = f"Error assessing outcome: {str(e)}"
        
        return outcome
