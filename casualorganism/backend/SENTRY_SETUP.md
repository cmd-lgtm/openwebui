# Sentry Error Aggregation Setup Guide

This guide explains how to configure Sentry for error tracking and alerting in the Causal Organism platform.

## Overview

Sentry provides:
- Automatic error capture and aggregation
- Error grouping and deduplication
- Real-time alerting on error rate spikes
- Detailed error context with stack traces
- Performance monitoring integration

## Requirements

**Requirement 17: Error Aggregation and Alerting**
- 17.1: Send all unhandled exceptions to error tracking service
- 17.2: Enable automatic error capture
- 17.3: Group similar errors automatically
- 17.4: Include request context, user context, and stack traces
- 17.5: Alert when error rate exceeds 10 errors/minute
- 17.6: Alert on new error types
- 17.7: Retain error data for 90 days
- 17.8: Provide API for querying error statistics

## Configuration

### 1. Environment Variables

Set the following environment variables:

```bash
# Required: Sentry DSN (Data Source Name)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id

# Optional: Environment name (dev, staging, prod)
SENTRY_ENVIRONMENT=production

# Optional: Release version for tracking
SENTRY_RELEASE=1.0.0

# Optional: Enable debug mode
SENTRY_DEBUG=false
```

### 2. Docker Compose Configuration

Add to `docker-compose.yml`:

```yaml
services:
  api:
    environment:
      - SENTRY_DSN=${SENTRY_DSN}
      - SENTRY_ENVIRONMENT=${SENTRY_ENVIRONMENT:-production}
      - SENTRY_RELEASE=${SENTRY_RELEASE:-latest}
  
  worker:
    environment:
      - SENTRY_DSN=${SENTRY_DSN}
      - SENTRY_ENVIRONMENT=${SENTRY_ENVIRONMENT:-production}
      - SENTRY_RELEASE=${SENTRY_RELEASE:-latest}
```

### 3. Kubernetes Configuration

Create a Kubernetes Secret for Sentry DSN:

```bash
kubectl create secret generic sentry-config \
  --from-literal=dsn='https://your-sentry-dsn@sentry.io/project-id' \
  --from-literal=environment='production'
```

Update deployment manifests:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-service
spec:
  template:
    spec:
      containers:
      - name: api
        env:
        - name: SENTRY_DSN
          valueFrom:
            secretKeyRef:
              name: sentry-config
              key: dsn
        - name: SENTRY_ENVIRONMENT
          valueFrom:
            secretKeyRef:
              name: sentry-config
              key: environment
```

## Alert Configuration

### Requirement 17.5: Error Rate Alerting (>10 errors/minute)

Configure in Sentry UI:

1. Navigate to **Alerts** → **Create Alert Rule**
2. Select **Issues** alert type
3. Configure conditions:
   - **When**: The issue is seen
   - **If**: more than **600** times in **1 hour** (10 errors/min × 60 min)
   - **Then**: Send notification to **#alerts** channel

Alternative configuration for more immediate alerting:

- **When**: The issue is seen
- **If**: more than **50** times in **5 minutes** (10 errors/min × 5 min)
- **Then**: Send notification to **#alerts** channel

### Requirement 17.6: New Error Type Alerting

Configure in Sentry UI:

1. Navigate to **Alerts** → **Create Alert Rule**
2. Select **Issues** alert type
3. Configure conditions:
   - **When**: A new issue is created
   - **If**: The issue's level is **error** or **fatal**
   - **Then**: Send notification to **#alerts** channel

### Alert Channels

Configure notification channels:

1. **Slack Integration**:
   - Navigate to **Settings** → **Integrations** → **Slack**
   - Connect workspace and select channel (e.g., `#alerts`)

2. **Email Notifications**:
   - Navigate to **Settings** → **Notifications**
   - Configure email recipients

3. **PagerDuty** (for critical alerts):
   - Navigate to **Settings** → **Integrations** → **PagerDuty**
   - Configure service integration

4. **Webhook** (for custom integrations):
   - Navigate to **Settings** → **Integrations** → **Webhooks**
   - Configure webhook URL

## Error Grouping

### Automatic Grouping

Sentry automatically groups similar errors based on:
- Exception type
- Stack trace similarity
- Error message patterns

### Custom Fingerprinting

The application uses custom fingerprinting for better grouping:

```python
# Export errors grouped by exception type
event['fingerprint'] = ['export-error', exception_type]

# Database connection errors grouped by database type
event['fingerprint'] = ['database-connection-error', db_type, exception_type]

# Validation errors grouped by endpoint
event['fingerprint'] = ['validation-error', endpoint]
```

## Error Context

### Request Context

Automatically captured:
- URL and endpoint path
- HTTP method
- Request headers
- Query parameters
- Request body (sanitized)

### User Context

Captured from request headers:
- User ID (from `X-User-Id` header)
- IP address
- User agent

### Custom Context

Add custom context in code:

```python
from backend.core.sentry_config import add_breadcrumb, capture_exception

# Add breadcrumb for debugging
add_breadcrumb(
    message="Processing export request",
    category="export",
    level="info",
    data={"export_type": "employee_metrics", "user_id": "user123"}
)

# Capture exception with custom context
try:
    process_export()
except Exception as e:
    capture_exception(
        e,
        tags={"export_type": "employee_metrics"},
        extra={"user_id": "user123", "params": params}
    )
```

## Data Retention

### Requirement 17.7: 90-Day Retention

Configure in Sentry UI:

1. Navigate to **Settings** → **Data Management**
2. Set **Event Retention** to **90 days**
3. Configure **Data Scrubbing** rules to remove sensitive data

### Data Scrubbing

Configure automatic PII removal:

1. Navigate to **Settings** → **Security & Privacy**
2. Enable **Data Scrubbing**
3. Add custom scrubbing rules:
   - Remove credit card numbers
   - Remove social security numbers
   - Remove API keys and tokens
   - Remove passwords

## API Access

### Requirement 17.8: Query Error Statistics

Use Sentry API to query error statistics:

```python
import requests

SENTRY_AUTH_TOKEN = "your-auth-token"
SENTRY_ORG = "your-org"
SENTRY_PROJECT = "causal-organism"

# Get error statistics for last 24 hours
response = requests.get(
    f"https://sentry.io/api/0/projects/{SENTRY_ORG}/{SENTRY_PROJECT}/stats/",
    headers={"Authorization": f"Bearer {SENTRY_AUTH_TOKEN}"},
    params={
        "stat": "received",
        "since": "1d",
        "resolution": "1h"
    }
)

stats = response.json()
```

### API Endpoints

Available Sentry API endpoints:

- **Project Stats**: `/api/0/projects/{org}/{project}/stats/`
- **Issues List**: `/api/0/projects/{org}/{project}/issues/`
- **Issue Details**: `/api/0/issues/{issue_id}/`
- **Events**: `/api/0/issues/{issue_id}/events/`

## Monitoring Dashboard

### Key Metrics

Monitor these metrics in Sentry:

1. **Error Rate**: Errors per minute/hour
2. **Error Types**: Distribution of error types
3. **Affected Users**: Number of users experiencing errors
4. **Error Trends**: Error rate over time
5. **Resolution Time**: Time to resolve issues

### Custom Dashboard

Create custom dashboard in Sentry UI:

1. Navigate to **Dashboards** → **Create Dashboard**
2. Add widgets:
   - **Error Rate**: Line chart of errors over time
   - **Top Issues**: Table of most frequent errors
   - **Error Distribution**: Pie chart by error type
   - **Affected Users**: Count of unique users with errors
   - **Response Time**: P95 latency correlation with errors

## Testing

### Test Error Capture

Test Sentry integration:

```python
# In Python shell or test script
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
   - Environment information
   - Custom tags

## Troubleshooting

### Errors Not Appearing in Sentry

1. **Check DSN Configuration**:
   ```bash
   echo $SENTRY_DSN
   ```

2. **Check Sentry Initialization**:
   Look for log message: `Sentry initialized for environment: production`

3. **Enable Debug Mode**:
   ```bash
   export SENTRY_DEBUG=true
   ```

4. **Check Network Connectivity**:
   ```bash
   curl -I https://sentry.io
   ```

### High Error Volume

If error rate is too high:

1. **Add Sampling**:
   ```python
   setup_sentry(sample_rate=0.5)  # Capture 50% of errors
   ```

2. **Filter Noisy Errors**:
   Update `before_send_hook` to filter specific errors

3. **Increase Rate Limits**:
   Configure in Sentry UI: **Settings** → **Rate Limits**

## Best Practices

1. **Use Environments**: Separate dev, staging, and prod environments
2. **Tag Releases**: Use `SENTRY_RELEASE` to track errors by version
3. **Add Context**: Use breadcrumbs and custom context for debugging
4. **Monitor Alerts**: Respond to alerts promptly
5. **Review Regularly**: Review error trends weekly
6. **Clean Up**: Resolve or ignore old/irrelevant errors
7. **Document Fixes**: Add comments to resolved issues

## Integration with Other Tools

### OpenTelemetry Integration

Sentry integrates with OpenTelemetry for distributed tracing:

```python
from opentelemetry import trace
from sentry_sdk import start_transaction

# Sentry transaction linked to OpenTelemetry trace
with start_transaction(op="task", name="process_export"):
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("export_data"):
        # Your code here
        pass
```

### Prometheus Integration

Export Sentry metrics to Prometheus:

```python
from prometheus_client import Counter

sentry_errors = Counter('sentry_errors_total', 'Total errors sent to Sentry')

# Increment counter when capturing error
capture_exception(error)
sentry_errors.inc()
```

## Support

For issues or questions:
- Sentry Documentation: https://docs.sentry.io/
- Sentry Support: support@sentry.io
- Internal Slack: #sentry-support
