"""
Tests for request validation with Pydantic models.

Requirements:
- 21.1: Define Pydantic models for all request bodies
- 21.2: Validate request bodies against Pydantic models
- 21.3: Return HTTP 422 with detailed error messages
- 21.5: Enforce required fields, type constraints, and value ranges
- 21.6: Sanitize string inputs to prevent injection attacks
- 21.7: Limit request body size to 10MB
- 21.8: Return validation errors in consistent JSON format
"""

import pytest
from pydantic import ValidationError
from backend.api.models.requests import (
    InteractionCreate,
    InteractionBatchCreate,
    CausalAnalysisRequest,
    ExportRequest,
    TrendQueryRequest,
    AlertQueryRequest,
    StatisticsQueryRequest,
    sanitize_string,
)


class TestInputSanitization:
    """Test input sanitization functions."""
    
    def test_sanitize_removes_sql_injection_patterns(self):
        """Test that SQL injection patterns are removed."""
        dangerous_input = "emp_001; DROP TABLE employees--"
        sanitized = sanitize_string(dangerous_input)
        
        assert "DROP" not in sanitized.upper()
        assert "--" not in sanitized
        assert ";" not in sanitized
    
    def test_sanitize_removes_union_select(self):
        """Test that UNION SELECT patterns are removed."""
        dangerous_input = "emp_001 UNION SELECT * FROM users"
        sanitized = sanitize_string(dangerous_input)
        
        assert "UNION" not in sanitized.upper()
        assert "SELECT" not in sanitized.upper()
    
    def test_sanitize_removes_control_characters(self):
        """Test that control characters are removed."""
        input_with_control = "emp_001\x00\x01\x02"
        sanitized = sanitize_string(input_with_control)
        
        assert "\x00" not in sanitized
        assert "\x01" not in sanitized
        assert "\x02" not in sanitized
    
    def test_sanitize_preserves_valid_input(self):
        """Test that valid input is preserved."""
        valid_input = "emp_001"
        sanitized = sanitize_string(valid_input)
        
        assert sanitized == valid_input


class TestInteractionCreateValidation:
    """Test InteractionCreate model validation."""
    
    def test_valid_interaction_create(self):
        """Test that valid interaction data passes validation."""
        data = {
            "source": "emp_001",
            "target": "emp_002",
            "interaction_type": "email",
            "weight": 1.5
        }
        
        interaction = InteractionCreate(**data)
        
        assert interaction.source == "emp_001"
        assert interaction.target == "emp_002"
        assert interaction.interaction_type == "email"
        assert interaction.weight == 1.5
    
    def test_missing_required_fields(self):
        """Test that missing required fields raise validation error."""
        data = {
            "source": "emp_001"
            # Missing target and interaction_type
        }
        
        with pytest.raises(ValidationError) as exc_info:
            InteractionCreate(**data)
        
        errors = exc_info.value.errors()
        assert len(errors) >= 2
        assert any(e["loc"] == ("target",) for e in errors)
        assert any(e["loc"] == ("interaction_type",) for e in errors)
    
    def test_weight_range_validation(self):
        """Test that weight is validated within range."""
        data = {
            "source": "emp_001",
            "target": "emp_002",
            "interaction_type": "email",
            "weight": 150.0  # Exceeds max of 100.0
        }
        
        with pytest.raises(ValidationError) as exc_info:
            InteractionCreate(**data)
        
        errors = exc_info.value.errors()
        assert any("weight" in str(e["loc"]) for e in errors)
    
    def test_string_sanitization_in_validator(self):
        """Test that string fields are sanitized."""
        data = {
            "source": "emp_001; DROP TABLE--",
            "target": "emp_002",
            "interaction_type": "email"
        }
        
        interaction = InteractionCreate(**data)
        
        # Sanitization should remove dangerous patterns
        assert "DROP" not in interaction.source.upper()
        assert "--" not in interaction.source


class TestInteractionBatchCreateValidation:
    """Test InteractionBatchCreate model validation."""
    
    def test_valid_batch_create(self):
        """Test that valid batch data passes validation."""
        data = {
            "interactions": [
                {
                    "source": "emp_001",
                    "target": "emp_002",
                    "interaction_type": "email"
                },
                {
                    "source": "emp_002",
                    "target": "emp_003",
                    "interaction_type": "meeting"
                }
            ]
        }
        
        batch = InteractionBatchCreate(**data)
        
        assert len(batch.interactions) == 2
    
    def test_empty_batch_fails(self):
        """Test that empty batch fails validation."""
        data = {"interactions": []}
        
        with pytest.raises(ValidationError) as exc_info:
            InteractionBatchCreate(**data)
        
        errors = exc_info.value.errors()
        assert any("interactions" in str(e["loc"]) for e in errors)
    
    def test_batch_size_limit(self):
        """Test that batch size is limited to 1000."""
        data = {
            "interactions": [
                {
                    "source": f"emp_{i:04d}",
                    "target": f"emp_{i+1:04d}",
                    "interaction_type": "email"
                }
                for i in range(1001)  # Exceeds max of 1000
            ]
        }
        
        with pytest.raises(ValidationError) as exc_info:
            InteractionBatchCreate(**data)
        
        errors = exc_info.value.errors()
        assert any("interactions" in str(e["loc"]) for e in errors)


class TestCausalAnalysisRequestValidation:
    """Test CausalAnalysisRequest model validation."""
    
    def test_valid_analysis_request(self):
        """Test that valid analysis request passes validation."""
        data = {
            "target_metric": "burnout_score",
            "treatment_variable": "meeting_hours",
            "control_variables": ["team_size", "role_level"]
        }
        
        request = CausalAnalysisRequest(**data)
        
        assert request.target_metric == "burnout_score"
        assert request.treatment_variable == "meeting_hours"
        assert len(request.control_variables) == 2
    
    def test_missing_target_metric_fails(self):
        """Test that missing target_metric fails validation."""
        data = {
            "treatment_variable": "meeting_hours"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            CausalAnalysisRequest(**data)
        
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("target_metric",) for e in errors)
    
    def test_metric_name_sanitization(self):
        """Test that metric names are sanitized."""
        data = {
            "target_metric": "burnout_score; DROP TABLE--",
            "treatment_variable": "meeting_hours"
        }
        
        request = CausalAnalysisRequest(**data)
        
        # Sanitization should remove dangerous patterns
        assert "DROP" not in request.target_metric.upper()
        assert "--" not in request.target_metric


class TestExportRequestValidation:
    """Test ExportRequest model validation."""
    
    def test_valid_export_request(self):
        """Test that valid export request passes validation."""
        data = {
            "export_type": "employee_metrics",
            "format": "csv"
        }
        
        request = ExportRequest(**data)
        
        assert request.export_type == "employee_metrics"
        assert request.format == "csv"
    
    def test_invalid_export_type_fails(self):
        """Test that invalid export_type fails validation."""
        data = {
            "export_type": "invalid_type",
            "format": "csv"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ExportRequest(**data)
        
        errors = exc_info.value.errors()
        assert any("export_type" in str(e["loc"]) for e in errors)
    
    def test_invalid_format_fails(self):
        """Test that invalid format fails validation."""
        data = {
            "export_type": "employee_metrics",
            "format": "xml"  # Not in allowed formats
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ExportRequest(**data)
        
        errors = exc_info.value.errors()
        assert any("format" in str(e["loc"]) for e in errors)


class TestTrendQueryRequestValidation:
    """Test TrendQueryRequest model validation."""
    
    def test_valid_trend_query(self):
        """Test that valid trend query passes validation."""
        data = {
            "employee_id": "emp_001",
            "metric_name": "burnout_score",
            "days": 90
        }
        
        request = TrendQueryRequest(**data)
        
        assert request.employee_id == "emp_001"
        assert request.metric_name == "burnout_score"
        assert request.days == 90
    
    def test_days_range_validation(self):
        """Test that days is validated within range."""
        data = {
            "metric_name": "burnout_score",
            "days": 1000  # Exceeds max of 730
        }
        
        with pytest.raises(ValidationError) as exc_info:
            TrendQueryRequest(**data)
        
        errors = exc_info.value.errors()
        assert any("days" in str(e["loc"]) for e in errors)
    
    def test_invalid_aggregation_fails(self):
        """Test that invalid aggregation fails validation."""
        data = {
            "metric_name": "burnout_score",
            "aggregation": "invalid_agg"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            TrendQueryRequest(**data)
        
        errors = exc_info.value.errors()
        assert any("aggregation" in str(e["loc"]) for e in errors)


class TestAlertQueryRequestValidation:
    """Test AlertQueryRequest model validation."""
    
    def test_valid_alert_query(self):
        """Test that valid alert query passes validation."""
        data = {
            "severity": "high",
            "status": "active",
            "days": 30
        }
        
        request = AlertQueryRequest(**data)
        
        assert request.severity == "high"
        assert request.status == "active"
        assert request.days == 30
    
    def test_invalid_severity_fails(self):
        """Test that invalid severity fails validation."""
        data = {
            "severity": "invalid_severity"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            AlertQueryRequest(**data)
        
        errors = exc_info.value.errors()
        assert any("severity" in str(e["loc"]) for e in errors)
    
    def test_limit_range_validation(self):
        """Test that limit is validated within range."""
        data = {
            "limit": 2000  # Exceeds max of 1000
        }
        
        with pytest.raises(ValidationError) as exc_info:
            AlertQueryRequest(**data)
        
        errors = exc_info.value.errors()
        assert any("limit" in str(e["loc"]) for e in errors)


class TestStatisticsQueryRequestValidation:
    """Test StatisticsQueryRequest model validation."""
    
    def test_valid_statistics_query(self):
        """Test that valid statistics query passes validation."""
        data = {
            "metric_name": "burnout_score",
            "days": 90
        }
        
        request = StatisticsQueryRequest(**data)
        
        assert request.metric_name == "burnout_score"
        assert request.days == 90
    
    def test_missing_metric_name_fails(self):
        """Test that missing metric_name fails validation."""
        data = {
            "days": 90
        }
        
        with pytest.raises(ValidationError) as exc_info:
            StatisticsQueryRequest(**data)
        
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("metric_name",) for e in errors)
