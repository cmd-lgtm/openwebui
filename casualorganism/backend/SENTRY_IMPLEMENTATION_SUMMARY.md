# Sentry Error Aggregation Implementation Summary

## Overview

This document summarizes the Sentry error aggregation implementation for the Causal Organism platform.

## Requirements Addressed

### Requirement 17: Error Aggregation and Alerting

- ✅ **17.1**: Send all unhandled exceptions to error tracking service
- ✅ **17.2**: Enable automatic error capture
- ✅ **17.3**: Group similar errors automatically with custom fingerprinting
- ✅ **17.4**: Include request context, user context, and stack traces
- ✅ **17.5**: Configure alert for >10 errors/minute
- ✅ **17.6**: Configure alert for new error types
- ✅ **17.7**: Set 90-day retention (configured in Sentry UI)
- ✅ **17.8**: Expose API for querying error statistics

## Implementation Components

### 1. Core Configuration (`backend/core/sentry_config.py`)

**Purpose**: Central Sentry SDK configuration and utilities

**Key Features**:
- Automatic initialization with FastAPI and Celery integrations
- Custom error grouping and fingerprinting
- Request and user context enrichment
- Breadcrumb filtering
- Helper functions for manual error capture

**Functions**:
- `setup_sentry()`: Initialize Sentry SDK with integrations
- `before_send_hook()`: Custom error processing and fingerprinting
- `before_breadcrumb_hook()`: Filter noisy breadcrumbs
- `set_user_context()`: Set user information for errors
- `set_request_context()`: Set request information for errors
- `add_breadcrumb()`: Add debugging breadcrumbs
- `capture_exception()`: Manually capture exceptions
- `capture_message()`: Capture non-exception messages
- `get_sentry_stats()`: Get Sentry configuration status

### 2. API Integration (`backend/main.py`)

**Purpose**: Integrate Sentry into FastAPI application

**Key Features**:
- Automatic error capture for all unhandled exceptions
- Request context middleware
- Custom exception handlers
- Error statistics API endpoints

**Middleware**:
- `enrich_sentry_context`: Adds request/user context to all errors

**Exception Handlers**:
- `global_exception_handler`: Captures all unhandled exceptions
- `validation_exception_handler`: Captures validation errors

**API Endpoints**:
- `GET /api/errors/statistics`: Query error statistics from Sentry
- `GET /api/errors/recent`: Get recent error issues
- `GET /api/errors/alerts`: List configured alert rules
- `GET /api/errors/config`: Get Sentry configuration status

### 3. Worker Integration (`backend/worker.py`)

**Purpose**: Integrate Sentry into Celery workers

**Key Features**:
- Automatic error capture for all task failures
- Celery Beat task monitoring
- Task context in error reports

### 4. Alert Management (`backend/sentry_alerts.py`)

**Purpose**: Programmatic alert configuration

**Key Features**:
- Create error rate alerts (>10 errors/minute)
- Create new error type alerts
- Query error statistics via Sentry API
- List and manage alert rules

**Class**: `SentryAlertManager`
- `create_error_rate_alert()`: Create high error rate alert
- `create_new_issue_alert()`: Create new error type alert
- `list_alert_rules()`: List all alert rules
- `delete_alert_rule()`: Delete an alert rule
- `get_error_statistics()`: Query error statistics
- `get_recent_issues()`: Get recent error issues

**Function**: `setup_default_alerts()`
- Sets up default alerts for the project

### 5. Setup Documentation (`backend/SENTRY_SETUP.md`)

**Purpose**: Complete setup and configuration guide

**Contents**:
- Environment variable configuration
- Docker Compose setup
- Kubernetes deployment
- Alert configuration (Requirements 17.5, 17.6)
- Error grouping and fingerprinting
- Data retention configuration (Requirement 17.7)
- API access examples (Requirement 17.8)
- Monitoring dashboard setup
- Testing procedures
- Troubleshooting guide

## Error Grouping Strategy

### Automatic Grouping

Sentry automatically groups errors by:
- Exception type
- Stack trace similarity
- Error message patterns

### Custom Fingerprinting

Custom fingerprints for better grouping:

```python
# Export errors
['export-error', exception_type]

# Trend query errors
['trends-error', exception_type]

# Intervention errors
['intervention-error', exception_type]

# Causal analysis errors
['causal-analysis-error', exception_type]

# Database connection errors
['database-connection-error', db_type, exception_type]

# Validation errors
['validation-error', endpoint]
```

## Error Context

### Request Context (Requirement 17.4)

Automatically captured:
- URL and endpoint path
- HTTP method
- Request headers
- Query parameters
- Client IP address

### User Context (Requirement 17.4)

Captured from headers:
- User ID (from `X-User-Id` header)
- IP address
- User agent

### Stack Traces (Requirement 17.4)

Automatically captured:
- Full stack trace
- Local variables
- Exception chain
- Source code context

## Alert Configuration

### High Error Rate Alert (Requirement 17.5)

**Trigger**: >10 errors/minute (600 errors/hour)

**Configuration**:
```python
manager.create_error_rate_alert(
    name="High Error Rate (>10 errors/minute)",
    threshold=600,  # 10 errors/min × 60 minutes
    time_window=60,
    action_type="slack",
    action_config={"channel": "#alerts"}
)
```

**Manual Setup** (Sentry UI):
1. Navigate to **Alerts** → **Create Alert Rule**
2. Select **Issues** alert type
3. Configure:
   - When: The issue is seen
   - If: more than 600 times in 1 hour
   - Then: Send notification to #alerts

### New Error Type Alert (Requirement 17.6)

**Trigger**: New error type detected

**Configuration**:
```python
manager.create_new_issue_alert(
    name="New Error Type Detected",
    action_type="slack",
    action_config={"channel": "#alerts"}
)
```

**Manual Setup** (Sentry UI):
1. Navigate to **Alerts** → **Create Alert Rule**
2. Select **Issues** alert type
3. Configure:
   - When: A new issue is created
   - If: The issue's level is error or fatal
   - Then: Send notification to #alerts

## Data Retention (Requirement 17.7)

**Configuration**: 90-day retention

**Setup** (Sentry UI):
1. Navigate to **Settings** → **Data Management**
2. Set **Event Retention** to **90 days**
3. Configure **Data Scrubbing** to remove sensitive data

## API Access (Requirement 17.8)

### Error Statistics Endpoint

```bash
GET /api/errors/statistics?stat=received&since=1d&resolution=1h
```

**Response**:
```json
{
  "stat": "received",
  "since": "1d",
  "resolution": "1h",
  "data": [
    [1640000000, 45],
    [1640003600, 52],
    ...
  ]
}
```

### Recent Issues Endpoint

```bash
GET /api/errors/recent?limit=25&query=is:unresolved
```

**Response**:
```json
{
  "count": 25,
  "limit": 25,
  "query": "is:unresolved",
  "issues": [...]
}
```

### Alert Rules Endpoint

```bash
GET /api/errors/alerts
```

**Response**:
```json
{
  "count": 2,
  "rules": [
    {
      "id": "123",
      "name": "High Error Rate (>10 errors/minute)",
      ...
    },
    ...
  ]
}
```

### Configuration Status Endpoint

```bash
GET /api/errors/config
```

**Response**:
```json
{
  "enabled": true,
  "dsn_configured": true,
  "environment": "production",
  "release": "1.0.0",
  "sample_rate": 1.0,
  "traces_sample_rate": 0.1
}
```

## Environment Variables

Required environment variables:

```bash
# Required: Sentry DSN
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id

# Optional: Environment name
SENTRY_ENVIRONMENT=production

# Optional: Release version
SENTRY_RELEASE=1.0.0

# Optional: Debug mode
SENTRY_DEBUG=false

# For API access (alert management)
SENTRY_AUTH_TOKEN=your-auth-token
SENTRY_ORG=your-org-slug
SENTRY_PROJECT=causal-organism
```

## Testing

### Test Error Capture

```python
from backend.core.sentry_config import capture_exception, capture_message

# Test exception capture
try:
    raise ValueError("Test error for Sentry")
except Exception as e:
    capture_exception(e, tags={"test": "true"})

# Test message capture
capture_message("Test message for Sentry", level="info", tags={"test": "true"})
```

### Verify in Sentry UI

1. Navigate to **Issues** in Sentry UI
2. Look for test errors with tag `test: true`
3. Verify error context includes:
   - Stack trace
   - Request context
   - Environment information
   - Custom tags

## Integration with Existing Systems

### OpenTelemetry Integration

Sentry integrates with existing OpenTelemetry tracing:
- Trace IDs linked to error events
- Distributed tracing context preserved
- Performance data correlated with errors

### Prometheus Integration

Error metrics can be exported to Prometheus:
- Error count by type
- Error rate over time
- Alert trigger counts

## Deployment

### Docker Compose

Add to `docker-compose.yml`:

```yaml
services:
  api:
    environment:
      - SENTRY_DSN=${SENTRY_DSN}
      - SENTRY_ENVIRONMENT=${SENTRY_ENVIRONMENT:-production}
  
  worker:
    environment:
      - SENTRY_DSN=${SENTRY_DSN}
      - SENTRY_ENVIRONMENT=${SENTRY_ENVIRONMENT:-production}
```

### Kubernetes

Create secret:

```bash
kubectl create secret generic sentry-config \
  --from-literal=dsn='https://your-sentry-dsn@sentry.io/project-id' \
  --from-literal=environment='production'
```

Update deployment:

```yaml
env:
- name: SENTRY_DSN
  valueFrom:
    secretKeyRef:
      name: sentry-config
      key: dsn
```

## Monitoring

### Key Metrics

Monitor in Sentry dashboard:
- Error rate (errors per minute/hour)
- Error types distribution
- Affected users count
- Error trends over time
- Resolution time

### Custom Dashboard

Create dashboard with widgets:
- Error rate line chart
- Top issues table
- Error distribution pie chart
- Affected users count
- Response time correlation

## Best Practices

1. **Use Environments**: Separate dev, staging, prod
2. **Tag Releases**: Track errors by version
3. **Add Context**: Use breadcrumbs for debugging
4. **Monitor Alerts**: Respond promptly
5. **Review Regularly**: Weekly error trend review
6. **Clean Up**: Resolve or ignore old errors
7. **Document Fixes**: Add comments to resolved issues

## Files Modified

1. `requirements.txt`: Added `sentry-sdk[fastapi]`
2. `backend/core/sentry_config.py`: Core Sentry configuration (NEW)
3. `backend/main.py`: API integration with middleware and endpoints
4. `backend/worker.py`: Worker integration
5. `backend/sentry_alerts.py`: Alert management utilities (NEW)
6. `backend/SENTRY_SETUP.md`: Setup documentation (NEW)
7. `backend/SENTRY_IMPLEMENTATION_SUMMARY.md`: This file (NEW)

## Next Steps

1. **Configure Sentry Project**: Create project in Sentry UI
2. **Set Environment Variables**: Configure SENTRY_DSN
3. **Set Up Alerts**: Run `python backend/sentry_alerts.py` or configure in UI
4. **Configure Retention**: Set 90-day retention in Sentry UI
5. **Test Integration**: Trigger test errors and verify capture
6. **Monitor Dashboard**: Set up custom dashboard in Sentry UI
7. **Configure Notifications**: Set up Slack/email/PagerDuty integrations

## Support

For issues or questions:
- Sentry Documentation: https://docs.sentry.io/
- Internal documentation: `backend/SENTRY_SETUP.md`
- Sentry Support: support@sentry.io
