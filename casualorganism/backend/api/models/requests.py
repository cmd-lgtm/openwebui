"""
Request validation models for the Causal Organism API.

This module defines Pydantic models for all API request bodies to ensure
type safety and validation before processing.

Requirements:
- 21.1: Define Pydantic models for all request bodies
- 21.5: Enforce required fields, type constraints, and value ranges
- 21.6: Sanitize string inputs to prevent injection attacks
"""

from pydantic import BaseModel, Field, validator, constr, conint
from typing import Optional, Dict, Any, List
from datetime import datetime
import re


# String sanitization helper
def sanitize_string(value: str) -> str:
    """
    Sanitize string inputs to prevent injection attacks.
    
    Requirements:
    - 21.6: Sanitize string inputs to prevent injection attacks
    """
    if not value:
        return value
    
    # Remove potential SQL injection patterns
    dangerous_patterns = [
        r"(\bDROP\b|\bDELETE\b|\bINSERT\b|\bUPDATE\b|\bEXEC\b|\bEXECUTE\b)",
        r"(--|;|\/\*|\*\/|xp_|sp_)",
        r"(\bUNION\b.*\bSELECT\b)",
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, value, re.IGNORECASE):
            # Replace dangerous patterns with empty string
            value = re.sub(pattern, "", value, flags=re.IGNORECASE)
    
    # Remove control characters except newlines and tabs
    value = "".join(char for char in value if ord(char) >= 32 or char in ['\n', '\t'])
    
    return value.strip()


# Interaction creation models
class InteractionCreate(BaseModel):
    """
    Model for creating a new interaction between employees.
    
    Requirements:
    - 21.1: Define Pydantic models for all request bodies
    - 21.5: Enforce required fields, type constraints, and value ranges
    """
    source: constr(min_length=1, max_length=100) = Field(
        ...,
        description="Source employee ID",
        example="emp_001"
    )
    target: constr(min_length=1, max_length=100) = Field(
        ...,
        description="Target employee ID",
        example="emp_002"
    )
    interaction_type: constr(min_length=1, max_length=50) = Field(
        ...,
        description="Type of interaction (email, meeting, chat, etc.)",
        example="email"
    )
    weight: float = Field(
        default=1.0,
        ge=0.0,
        le=100.0,
        description="Interaction weight/strength"
    )
    timestamp: Optional[datetime] = Field(
        default=None,
        description="Interaction timestamp (defaults to current time)"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional interaction metadata"
    )
    
    @validator('source', 'target', 'interaction_type')
    def sanitize_strings(cls, v):
        """Sanitize string fields to prevent injection attacks."""
        return sanitize_string(v)
    
    class Config:
        json_schema_extra = {
            "example": {
                "source": "emp_001",
                "target": "emp_002",
                "interaction_type": "email",
                "weight": 1.5,
                "timestamp": "2024-01-15T10:30:00Z",
                "metadata": {"subject": "Project update"}
            }
        }


class InteractionBatchCreate(BaseModel):
    """
    Model for creating multiple interactions in a batch.
    
    Requirements:
    - 21.1: Define Pydantic models for all request bodies
    - 21.5: Enforce required fields, type constraints, and value ranges
    """
    interactions: List[InteractionCreate] = Field(
        ...,
        min_items=1,
        max_items=1000,
        description="List of interactions to create (max 1000 per batch)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "interactions": [
                    {
                        "source": "emp_001",
                        "target": "emp_002",
                        "interaction_type": "email",
                        "weight": 1.0
                    }
                ]
            }
        }


# Analysis request models
class CausalAnalysisRequest(BaseModel):
    """
    Model for requesting causal analysis.
    
    Requirements:
    - 21.1: Define Pydantic models for all request bodies
    - 21.5: Enforce required fields, type constraints, and value ranges
    """
    target_metric: constr(min_length=1, max_length=100) = Field(
        ...,
        description="Target metric to analyze (e.g., burnout_score, productivity)",
        example="burnout_score"
    )
    treatment_variable: Optional[constr(min_length=1, max_length=100)] = Field(
        default=None,
        description="Treatment variable for causal analysis",
        example="meeting_hours"
    )
    control_variables: Optional[List[constr(min_length=1, max_length=100)]] = Field(
        default=None,
        description="Control variables to include in analysis",
        example=["team_size", "role_level"]
    )
    employee_filter: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Filter criteria for employees to include"
    )
    date_range: Optional[Dict[str, str]] = Field(
        default=None,
        description="Date range for analysis (start_date, end_date)"
    )
    use_spark: Optional[bool] = Field(
        default=None,
        description="Force use of Spark engine (auto-detected if not specified)"
    )
    
    @validator('target_metric', 'treatment_variable')
    def sanitize_metric_names(cls, v):
        """Sanitize metric names."""
        if v:
            return sanitize_string(v)
        return v
    
    @validator('control_variables')
    def sanitize_control_variables(cls, v):
        """Sanitize control variable names."""
        if v:
            return [sanitize_string(var) for var in v]
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "target_metric": "burnout_score",
                "treatment_variable": "meeting_hours",
                "control_variables": ["team_size", "role_level"],
                "date_range": {
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31"
                }
            }
        }


# Export request models
class ExportRequest(BaseModel):
    """
    Model for requesting data export.
    
    Requirements:
    - 21.1: Define Pydantic models for all request bodies
    - 21.5: Enforce required fields, type constraints, and value ranges
    """
    export_type: constr(min_length=1, max_length=50) = Field(
        ...,
        description="Type of export (employee_metrics, graph_data, interaction_history)",
        example="employee_metrics"
    )
    format: constr(min_length=1, max_length=20) = Field(
        default="csv",
        description="Export format (csv, json, parquet)",
        example="csv"
    )
    filters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Filter criteria for export"
    )
    date_range: Optional[Dict[str, str]] = Field(
        default=None,
        description="Date range for export (start_date, end_date)"
    )
    include_fields: Optional[List[constr(min_length=1, max_length=100)]] = Field(
        default=None,
        description="Specific fields to include in export"
    )
    
    @validator('export_type', 'format')
    def sanitize_export_fields(cls, v):
        """Sanitize export field names."""
        return sanitize_string(v)
    
    @validator('export_type')
    def validate_export_type(cls, v):
        """Validate export type is one of allowed values."""
        allowed_types = [
            "employee_metrics",
            "graph_data",
            "interaction_history",
            "causal_analysis_results",
            "intervention_audit_log"
        ]
        if v not in allowed_types:
            raise ValueError(f"export_type must be one of: {', '.join(allowed_types)}")
        return v
    
    @validator('format')
    def validate_format(cls, v):
        """Validate format is one of allowed values."""
        allowed_formats = ["csv", "json", "parquet"]
        if v not in allowed_formats:
            raise ValueError(f"format must be one of: {', '.join(allowed_formats)}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "export_type": "employee_metrics",
                "format": "csv",
                "date_range": {
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31"
                },
                "include_fields": ["employee_id", "burnout_score", "productivity"]
            }
        }


# Trend query models
class TrendQueryRequest(BaseModel):
    """
    Model for querying historical trend data.
    
    Requirements:
    - 21.1: Define Pydantic models for all request bodies
    - 21.5: Enforce required fields, type constraints, and value ranges
    """
    employee_id: Optional[constr(min_length=1, max_length=100)] = Field(
        default=None,
        description="Employee ID for individual trend query"
    )
    team_id: Optional[constr(min_length=1, max_length=100)] = Field(
        default=None,
        description="Team ID for team trend query"
    )
    metric_name: constr(min_length=1, max_length=100) = Field(
        ...,
        description="Metric name to query",
        example="burnout_score"
    )
    days: conint(ge=1, le=730) = Field(
        default=90,
        description="Number of days to look back (1-730)"
    )
    use_hourly: bool = Field(
        default=False,
        description="Use hourly aggregates for faster queries"
    )
    aggregation: Optional[constr(min_length=1, max_length=20)] = Field(
        default="avg",
        description="Aggregation function (avg, min, max, sum)"
    )
    
    @validator('employee_id', 'team_id', 'metric_name', 'aggregation')
    def sanitize_query_fields(cls, v):
        """Sanitize query field names."""
        if v:
            return sanitize_string(v)
        return v
    
    @validator('aggregation')
    def validate_aggregation(cls, v):
        """Validate aggregation function."""
        if v:
            allowed_agg = ["avg", "min", "max", "sum", "count"]
            if v not in allowed_agg:
                raise ValueError(f"aggregation must be one of: {', '.join(allowed_agg)}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "employee_id": "emp_001",
                "metric_name": "burnout_score",
                "days": 90,
                "use_hourly": False,
                "aggregation": "avg"
            }
        }


# Alert query models
class AlertQueryRequest(BaseModel):
    """
    Model for querying burnout alerts.
    
    Requirements:
    - 21.1: Define Pydantic models for all request bodies
    - 21.5: Enforce required fields, type constraints, and value ranges
    """
    severity: Optional[constr(min_length=1, max_length=20)] = Field(
        default=None,
        description="Alert severity filter (low, medium, high, critical)"
    )
    status: Optional[constr(min_length=1, max_length=20)] = Field(
        default=None,
        description="Alert status filter (active, acknowledged, resolved)"
    )
    employee_id: Optional[constr(min_length=1, max_length=100)] = Field(
        default=None,
        description="Filter by employee ID"
    )
    team_id: Optional[constr(min_length=1, max_length=100)] = Field(
        default=None,
        description="Filter by team ID"
    )
    days: conint(ge=1, le=365) = Field(
        default=30,
        description="Number of days to look back (1-365)"
    )
    limit: conint(ge=1, le=1000) = Field(
        default=100,
        description="Maximum number of alerts to return (1-1000)"
    )
    
    @validator('severity')
    def validate_severity(cls, v):
        """Validate severity level."""
        if v:
            allowed_severity = ["low", "medium", "high", "critical"]
            if v not in allowed_severity:
                raise ValueError(f"severity must be one of: {', '.join(allowed_severity)}")
        return v
    
    @validator('status')
    def validate_status(cls, v):
        """Validate alert status."""
        if v:
            allowed_status = ["active", "acknowledged", "resolved"]
            if v not in allowed_status:
                raise ValueError(f"status must be one of: {', '.join(allowed_status)}")
        return v
    
    @validator('severity', 'status', 'employee_id', 'team_id')
    def sanitize_alert_fields(cls, v):
        """Sanitize alert query fields."""
        if v:
            return sanitize_string(v)
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "severity": "high",
                "status": "active",
                "days": 30,
                "limit": 100
            }
        }


# Statistics query models
class StatisticsQueryRequest(BaseModel):
    """
    Model for querying metric statistics.
    
    Requirements:
    - 21.1: Define Pydantic models for all request bodies
    - 21.5: Enforce required fields, type constraints, and value ranges
    """
    metric_name: constr(min_length=1, max_length=100) = Field(
        ...,
        description="Metric name to query statistics for",
        example="burnout_score"
    )
    employee_id: Optional[constr(min_length=1, max_length=100)] = Field(
        default=None,
        description="Filter by employee ID"
    )
    team_id: Optional[constr(min_length=1, max_length=100)] = Field(
        default=None,
        description="Filter by team ID"
    )
    days: conint(ge=1, le=730) = Field(
        default=90,
        description="Number of days to look back (1-730)"
    )
    
    @validator('metric_name', 'employee_id', 'team_id')
    def sanitize_stats_fields(cls, v):
        """Sanitize statistics query fields."""
        if v:
            return sanitize_string(v)
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "metric_name": "burnout_score",
                "team_id": "team_engineering",
                "days": 90
            }
        }
