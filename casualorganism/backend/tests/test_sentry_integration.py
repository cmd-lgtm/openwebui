"""
Tests for Sentry error aggregation integration.

Requirements:
- 17.1: Send all unhandled exceptions to error tracking service
- 17.2: Enable automatic error capture
- 17.3: Group similar errors automatically
- 17.4: Include request context, user context, and stack traces
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.core.sentry_config import (
    setup_sentry,
    before_send_hook,
    before_breadcrumb_hook,
    set_user_context,
    set_request_context,
    add_breadcrumb,
    capture_exception,
    capture_message,
    get_sentry_stats
)


class TestSentrySetup:
    """Test Sentry initialization and configuration."""
    
    def test_setup_sentry_without_dsn(self):
        """Test that setup_sentry returns False when DSN is not provided."""
        with patch.dict('os.environ', {}, clear=True):
            result = setup_sentry()
            assert result is False
    
    def test_setup_sentry_with_dsn(self):
        """Test that setup_sentry initializes when DSN is provided."""
        with patch('backend.core.sentry_config.sentry_sdk.init') as mock_init:
            result = setup_sentry(
                dsn="https://test@sentry.io/123",
                environment="test"
            )
            assert result is True
            assert mock_init.called
    
    def test_setup_sentry_with_environment_variables(self):
        """Test that setup_sentry reads from environment variables."""
        with patch('backend.core.sentry_config.sentry_sdk.init') as mock_init:
            with patch.dict('os.environ', {
                'SENTRY_DSN': 'https://test@sentry.io/123',
                'SENTRY_ENVIRONMENT': 'production'
            }):
                result = setup_sentry()
                assert result is True
                assert mock_init.called


class TestBeforeSendHook:
    """Test error event processing and fingerprinting."""
    
    def test_filter_keyboard_interrupt(self):
        """Test that KeyboardInterrupt is filtered out."""
        event = {}
        hint = {'exc_info': (KeyboardInterrupt, KeyboardInterrupt(), None)}
        
        result = before_send_hook(event, hint)
        assert result is None
    
    def test_filter_system_exit(self):
        """Test that SystemExit is filtered out."""
        event = {}
        hint = {'exc_info': (SystemExit, SystemExit(), None)}
        
        result = before_send_hook(event, hint)
        assert result is None
    
    def test_fingerprint_export_error(self):
        """Test custom fingerprinting for export errors."""
        event = {
            'request': {'url': 'https://api.example.com/api/exports/123'},
            'exception': {
                'values': [{'type': 'ValueError', 'value': 'Invalid export'}]
            }
        }
        hint = {}
        
        result = before_send_hook(event, hint)
        assert result is not None
        assert result['fingerprint'] == ['export-error', 'ValueError']
    
    def test_fingerprint_trends_error(self):
        """Test custom fingerprinting for trends errors."""
        event = {
            'request': {'url': 'https://api.example.com/api/trends/employee/123'},
            'exception': {
                'values': [{'type': 'TimeoutError', 'value': 'Query timeout'}]
            }
        }
        hint = {}
        
        result = before_send_hook(event, hint)
        assert result is not None
        assert result['fingerprint'] == ['trends-error', 'TimeoutError']
    
    def test_fingerprint_intervention_error(self):
        """Test custom fingerprinting for intervention errors."""
        event = {
            'request': {'url': 'https://api.example.com/api/interventions/propose'},
            'exception': {
                'values': [{'type': 'RuntimeError', 'value': 'Intervention failed'}]
            }
        }
        hint = {}
        
        result = before_send_hook(event, hint)
        assert result is not None
        assert result['fingerprint'] == ['intervention-error', 'RuntimeError']
    
    def test_fingerprint_database_connection_error(self):
        """Test custom fingerprinting for database connection errors."""
        event = {
            'request': {'url': 'https://api.example.com/api/graph/stats'},
            'exception': {
                'values': [{
                    'type': 'ConnectionError',
                    'value': 'Failed to connect to neo4j'
                }]
            }
        }
        hint = {}
        
        result = before_send_hook(event, hint)
        assert result is not None
        assert result['fingerprint'] == ['database-connection-error', 'neo4j', 'ConnectionError']
    
    def test_fingerprint_validation_error(self):
        """Test custom fingerprinting for validation errors."""
        event = {
            'request': {'url': 'https://api.example.com/api/graph/stats?param=invalid'},
            'exception': {
                'values': [{'type': 'ValidationError', 'value': 'Invalid parameter'}]
            }
        }
        hint = {}
        
        result = before_send_hook(event, hint)
        assert result is not None
        assert result['fingerprint'] == ['validation-error', 'https://api.example.com/api/graph/stats']
    
    def test_default_fingerprint(self):
        """Test default fingerprinting for unknown errors."""
        event = {
            'request': {'url': 'https://api.example.com/api/unknown'},
            'exception': {
                'values': [{'type': 'UnknownError', 'value': 'Something went wrong'}]
            }
        }
        hint = {}
        
        result = before_send_hook(event, hint)
        assert result is not None
        assert result['fingerprint'] == ['{{ default }}']


class TestBeforeBreadcrumbHook:
    """Test breadcrumb filtering."""
    
    def test_filter_health_check_breadcrumbs(self):
        """Test that health check breadcrumbs are filtered out."""
        crumb = {
            'category': 'httplib',
            'data': {'url': 'https://api.example.com/health'}
        }
        hint = {}
        
        result = before_breadcrumb_hook(crumb, hint)
        assert result is None
    
    def test_keep_non_health_check_breadcrumbs(self):
        """Test that non-health check breadcrumbs are kept."""
        crumb = {
            'category': 'httplib',
            'data': {'url': 'https://api.example.com/api/graph/stats'}
        }
        hint = {}
        
        result = before_breadcrumb_hook(crumb, hint)
        assert result is not None
        assert result == crumb


class TestContextHelpers:
    """Test context helper functions."""
    
    @patch('backend.core.sentry_config.sentry_sdk.set_user')
    def test_set_user_context(self, mock_set_user):
        """Test setting user context."""
        set_user_context(
            user_id="user123",
            email="user@example.com",
            username="testuser"
        )
        
        mock_set_user.assert_called_once_with({
            "id": "user123",
            "email": "user@example.com",
            "username": "testuser"
        })
    
    @patch('backend.core.sentry_config.sentry_sdk.set_context')
    def test_set_request_context(self, mock_set_context):
        """Test setting request context."""
        set_request_context(
            request_id="req123",
            endpoint="/api/graph/stats",
            method="GET"
        )
        
        mock_set_context.assert_called_once_with("request", {
            "request_id": "req123",
            "endpoint": "/api/graph/stats",
            "method": "GET"
        })
    
    @patch('backend.core.sentry_config.sentry_sdk.add_breadcrumb')
    def test_add_breadcrumb(self, mock_add_breadcrumb):
        """Test adding breadcrumb."""
        add_breadcrumb(
            message="Processing export",
            category="export",
            level="info",
            data={"export_type": "employee_metrics"}
        )
        
        mock_add_breadcrumb.assert_called_once_with(
            message="Processing export",
            category="export",
            level="info",
            data={"export_type": "employee_metrics"}
        )


class TestErrorCapture:
    """Test manual error capture functions."""
    
    @patch('backend.core.sentry_config.sentry_sdk.capture_exception')
    @patch('backend.core.sentry_config.sentry_sdk.push_scope')
    def test_capture_exception(self, mock_push_scope, mock_capture_exception):
        """Test capturing exception with context."""
        mock_scope = MagicMock()
        mock_push_scope.return_value.__enter__.return_value = mock_scope
        
        error = ValueError("Test error")
        capture_exception(
            error,
            tags={"test": "true"},
            extra={"detail": "test detail"}
        )
        
        assert mock_capture_exception.called
    
    @patch('backend.core.sentry_config.sentry_sdk.capture_message')
    @patch('backend.core.sentry_config.sentry_sdk.push_scope')
    def test_capture_message(self, mock_push_scope, mock_capture_message):
        """Test capturing message with context."""
        mock_scope = MagicMock()
        mock_push_scope.return_value.__enter__.return_value = mock_scope
        
        capture_message(
            "Test message",
            level="info",
            tags={"test": "true"}
        )
        
        mock_capture_message.assert_called_once_with("Test message", level="info")


class TestSentryStats:
    """Test Sentry statistics function."""
    
    @patch('backend.core.sentry_config.sentry_sdk.Hub')
    def test_get_sentry_stats_disabled(self, mock_hub):
        """Test getting stats when Sentry is disabled."""
        mock_hub.current.client = None
        
        stats = get_sentry_stats()
        
        assert stats['enabled'] is False
        assert stats['dsn_configured'] is False
    
    @patch('backend.core.sentry_config.sentry_sdk.Hub')
    def test_get_sentry_stats_enabled(self, mock_hub):
        """Test getting stats when Sentry is enabled."""
        mock_client = Mock()
        mock_client.options = {
            'environment': 'production',
            'release': '1.0.0',
            'sample_rate': 1.0,
            'traces_sample_rate': 0.1
        }
        mock_hub.current.client = mock_client
        
        stats = get_sentry_stats()
        
        assert stats['enabled'] is True
        assert stats['dsn_configured'] is True
        assert stats['environment'] == 'production'
        assert stats['release'] == '1.0.0'
        assert stats['sample_rate'] == 1.0
        assert stats['traces_sample_rate'] == 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
