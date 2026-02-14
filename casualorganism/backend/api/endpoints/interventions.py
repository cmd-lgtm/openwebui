"""
Intervention API Endpoints

This module provides REST API endpoints for the intervention approval workflow.

Requirements:
- 14.2: Approval workflow for high-impact interventions
- 14.6: Expose approval queue API
- 14.7: Timeout pending approvals (24 hours)
- 19.1: Require valid JWT token
- 19.4: Enforce role-based access control
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from backend.core.safe_action_orchestrator import (
    SafeActionOrchestrator,
    Intervention,
    InterventionStatus,
    ImpactLevel
)
from backend.core.auth import require_permission, require_role, TokenData, Roles


router = APIRouter(prefix="/api/interventions", tags=["interventions"])


# Request/Response Models
class ProposeInterventionRequest(BaseModel):
    """Request model for proposing an intervention"""
    intervention_type: str = Field(..., description="Type of intervention")
    target_employee_id: str = Field(..., description="Target employee ID")
    params: dict = Field(default_factory=dict, description="Intervention parameters")
    reason: str = Field(..., description="Reason for intervention")


class ProposeInterventionResponse(BaseModel):
    """Response model for intervention proposal"""
    intervention_id: str
    status: str
    impact_level: str
    message: str


class ApproveInterventionRequest(BaseModel):
    """Request model for approving an intervention"""
    intervention_id: str


class RejectInterventionRequest(BaseModel):
    """Request model for rejecting an intervention"""
    intervention_id: str
    reason: str


class InterventionResponse(BaseModel):
    """Response model for intervention details"""
    id: str
    type: str
    target_employee_id: str
    params: dict
    reason: str
    impact_level: str
    status: str
    proposed_at: str
    approved_at: Optional[str] = None
    executed_at: Optional[str] = None
    rolled_back_at: Optional[str] = None
    result: Optional[dict] = None
    error: Optional[str] = None


class TimeoutExpiredApprovalsResponse(BaseModel):
    """Response model for timeout operation"""
    timed_out_count: int
    message: str


# Global orchestrator instance (will be initialized in main.py)
orchestrator: Optional[SafeActionOrchestrator] = None


def set_orchestrator(orch: SafeActionOrchestrator):
    """Set the global orchestrator instance"""
    global orchestrator
    orchestrator = orch


def get_orchestrator() -> SafeActionOrchestrator:
    """Get the orchestrator instance"""
    if orchestrator is None:
        raise HTTPException(
            status_code=503,
            detail="Action orchestrator not initialized"
        )
    return orchestrator


@router.post("/propose", response_model=ProposeInterventionResponse)
async def propose_intervention(
    request: ProposeInterventionRequest,
    current_user: TokenData = Depends(require_permission("write:interventions"))
):
    """
    Propose a new intervention.
    
    Requirements:
    - 14.1: Assess impact level
    - 14.2: Require approval for high-impact interventions
    - 14.7: Auto-execute low/medium impact interventions
    - 19.1: Require valid JWT token
    - 19.4: Enforce role-based access control
    
    High-impact interventions require approval before execution.
    Low and medium-impact interventions are auto-executed.
    """
    orch = get_orchestrator()
    
    try:
        intervention_id = await orch.propose_intervention(
            intervention_type=request.intervention_type,
            target_employee_id=request.target_employee_id,
            params=request.params,
            reason=request.reason
        )
        
        # Get the intervention to check its status
        intervention = await orch._get_intervention(intervention_id)
        
        if intervention.status == InterventionStatus.PENDING_APPROVAL:
            message = "Intervention proposed and pending approval (high impact)"
        else:
            message = "Intervention proposed and auto-executed (low/medium impact)"
        
        return ProposeInterventionResponse(
            intervention_id=intervention_id,
            status=intervention.status.value,
            impact_level=intervention.impact_level.value,
            message=message
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/approve")
async def approve_intervention(
    request: ApproveInterventionRequest,
    current_user: TokenData = Depends(require_permission("approve:interventions"))
):
    """
    Approve a pending intervention.
    
    Requirements:
    - 14.2: Approval workflow for high-impact interventions
    - 19.1: Require valid JWT token
    - 19.4: Enforce role-based access control (only admins can approve)
    
    Only interventions with status "pending_approval" can be approved.
    """
    orch = get_orchestrator()
    
    try:
        await orch.approve_intervention(request.intervention_id)
        return {
            "intervention_id": request.intervention_id,
            "status": "approved",
            "message": "Intervention approved and execution initiated"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reject")
async def reject_intervention(request: RejectInterventionRequest):
    """
    Reject a pending intervention.
    
    Requirement 14.2: Approval workflow for high-impact interventions
    """
    orch = get_orchestrator()
    
    try:
        await orch.reject_intervention(
            request.intervention_id,
            request.reason
        )
        return {
            "intervention_id": request.intervention_id,
            "status": "rejected",
            "message": "Intervention rejected"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pending", response_model=List[InterventionResponse])
async def get_pending_approvals(
    current_user: TokenData = Depends(require_permission("read:interventions"))
):
    """
    Get all interventions pending approval.
    
    Requirements:
    - 14.6: Expose approval queue API
    - 19.1: Require valid JWT token
    - 19.4: Enforce role-based access control
    
    Returns list of interventions with status "pending_approval",
    ordered by proposal time (oldest first).
    """
    orch = get_orchestrator()
    
    try:
        interventions = await orch.get_pending_approvals()
        return [
            InterventionResponse(
                id=i.id,
                type=i.type,
                target_employee_id=i.target_employee_id,
                params=i.params,
                reason=i.reason,
                impact_level=i.impact_level.value,
                status=i.status.value,
                proposed_at=i.proposed_at.isoformat(),
                approved_at=i.approved_at.isoformat() if i.approved_at else None,
                executed_at=i.executed_at.isoformat() if i.executed_at else None,
                rolled_back_at=i.rolled_back_at.isoformat() if i.rolled_back_at else None,
                result=i.result,
                error=i.error
            )
            for i in interventions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{intervention_id}", response_model=InterventionResponse)
async def get_intervention(intervention_id: str):
    """
    Get details of a specific intervention.
    """
    orch = get_orchestrator()
    
    try:
        intervention = await orch._get_intervention(intervention_id)
        return InterventionResponse(
            id=intervention.id,
            type=intervention.type,
            target_employee_id=intervention.target_employee_id,
            params=intervention.params,
            reason=intervention.reason,
            impact_level=intervention.impact_level.value,
            status=intervention.status.value,
            proposed_at=intervention.proposed_at.isoformat(),
            approved_at=intervention.approved_at.isoformat() if intervention.approved_at else None,
            executed_at=intervention.executed_at.isoformat() if intervention.executed_at else None,
            rolled_back_at=intervention.rolled_back_at.isoformat() if intervention.rolled_back_at else None,
            result=intervention.result,
            error=intervention.error
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/timeout-expired", response_model=TimeoutExpiredApprovalsResponse)
async def timeout_expired_approvals():
    """
    Timeout pending approvals that exceed 24 hours.
    
    Requirement 14.7: Timeout pending approvals after 24 hours
    
    This endpoint should be called periodically (e.g., via scheduled task)
    to automatically timeout interventions that have been pending approval
    for more than 24 hours.
    """
    orch = get_orchestrator()
    
    try:
        count = await orch.timeout_expired_approvals()
        return TimeoutExpiredApprovalsResponse(
            timed_out_count=count,
            message=f"Timed out {count} expired approval(s)"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{intervention_id}/rollback")
async def rollback_intervention(intervention_id: str):
    """
    Rollback an executed intervention.
    
    Requirement 14.5: Rollback capability
    
    This endpoint will be fully implemented in task 11.3.
    """
    orch = get_orchestrator()
    
    try:
        await orch.rollback_intervention(intervention_id)
        return {
            "intervention_id": intervention_id,
            "status": "rolled_back",
            "message": "Intervention rolled back successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit/query")
async def query_audit_log(
    start_date: datetime = Query(..., description="Start of time range"),
    end_date: datetime = Query(..., description="End of time range"),
    intervention_id: Optional[str] = Query(None, description="Filter by intervention ID"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    employee_id: Optional[str] = Query(None, description="Filter by employee ID")
):
    """
    Query intervention audit log.
    
    Requirement 14.8: Provide audit trail query API
    
    Returns audit log entries matching the specified filters.
    """
    orch = get_orchestrator()
    
    try:
        entries = await orch.audit_log.query(
            start_date=start_date,
            end_date=end_date,
            intervention_id=intervention_id,
            action=action,
            employee_id=employee_id
        )
        return {
            "count": len(entries),
            "entries": entries
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
