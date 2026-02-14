# Health Checks Implementation Summary

## Overview

This document describes the implementation of Kubernetes health checks (liveness and readiness probes) for the Causal Organism platform. Health checks enable Kubernetes to automatically detect and recover from failures, ensuring high availability.

## Requirements Addressed

### Requirement 23: Health Checks and Readiness Probes

- **23.1**: Liveness probe endpoint exposed
- **23.2**: Readiness probe endpoint exposed
- **23.3**: Liveness probe returns 200 when process is running
- **23.4**: Readiness probe returns 200 if ready, 503 if not
- **23.5**: Readiness probe returns 503 when dependencies unavailable
- **23.6**: Readiness probe checks Neo4j connectivity
- **23.7**: Readiness probe checks Redis connectivity
- **23.8**: Readiness probe checks TimescaleDB connectivity
- **23.9**: Kubernetes restarts pod after 3 consecutive liveness failures
- **23.10**: Kubernetes removes pod from load balancer when readiness fails

## Implementation Details

### 1. API Service Health Endpoints

#### Liveness Probe: `/health/live`

**Purpose**: Checks if the API process is alive and responding to requests.

**Response**:
```json
{
  "status": "alive",
  "service": "api-service",
  "timestamp": "2024-02-14T10:30:00.000Z"
}
```

**HTTP Status**: Always returns 200 if the process is running.

**Use Case**: Kubernetes uses this to detect if the container needs to be restarted (e.g., deadlock, crash).

#### Readiness Probe: `/health/ready`

**Purpose**: Checks if the API service can handle requests by verifying connectivity to all critical dependencies.

**Checks Performed**:
1. **Neo4j** - Graph database connectivity
2. **Redis** - Cache and message queue connectivity
3. **TimescaleDB** - Time-series metrics database connectivity

**Response (Healthy)**:
```json
{
  "status": "ready",
  "service": "api-service",
  "timestamp": "2024-02-14T10:30:00.000Z",
  "checks": {
    "neo4j": {
      "status": "healthy",
      "healthy": true
    },
    "redis": {
      "status": "healthy",
      "healthy": true
    },
    "timescale": {
      "status": "healthy",
      "healthy": true
    }
  }
}
```

**Response (Unhealthy)**:
```json
{
  "status": "not_ready",
  "service": "api-service",
  "timestamp": "2024-02-14T10:30:00.000Z",
  "checks": {
    "neo4j": {
      "status": "error: connection refused",
      "healthy": false
    },
    "redis": {
      "status": "healthy",
      "healthy": true
    },
    "timescale": {
      "status": "healthy",
      "healthy": true
    }
  }
}
```

**HTTP Status**: 
- 200 if all dependencies are healthy
- 503 if any dependency is unhealthy

**Use Case**: Kubernetes uses this to determine if the pod should receive traffic from the load balancer.

### 2. Kubernetes Probe Configuration

#### API Service Probes

**Liveness Probe**:
```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 30      # Wait 30s after container starts
  periodSeconds: 10             # Check every 10 seconds
  timeoutSeconds: 5             # Timeout after 5 seconds
  failureThreshold: 3           # Restart after 3 consecutive failures
  successThreshold: 1           # Consider healthy after 1 success
```

**Readiness Probe**:
```yaml
readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 10       # Wait 10s after container starts
  periodSeconds: 5              # Check every 5 seconds
  timeoutSeconds: 3             # Timeout after 3 seconds
  failureThreshold: 2           # Remove from load balancer after 2 failures
  successThreshold: 1           # Add to load balancer after 1 success
```

#### Worker Service Probes

**Liveness Probe** (Celery inspect):
```yaml
livenessProbe:
  exec:
    command:
    - celery
    - -A
    - backend.worker.celery_app
    - inspect
    - ping
    - -d
    - celery@$HOSTNAME
  initialDelaySeconds: 60      # Wait 60s for worker to start
  periodSeconds: 30             # Check every 30 seconds
  timeoutSeconds: 10            # Timeout after 10 seconds
  failureThreshold: 3           # Restart after 3 consecutive failures
  successThreshold: 1           # Consider healthy after 1 success
```

**Readiness Probe** (Prometheus metrics):
```yaml
readinessProbe:
  httpGet:
    path: /metrics
    port: 9090
  initialDelaySeconds: 30       # Wait 30s after container starts
  periodSeconds: 10             # Check every 10 seconds
  timeoutSeconds: 5             # Timeout after 5 seconds
  failureThreshold: 2           # Mark not ready after 2 failures
  successThreshold: 1           # Mark ready after 1 success
```

## Probe Timing Rationale

### API Service

**Liveness Probe**:
- `initialDelaySeconds: 30` - Allows time for Python imports and initialization
- `periodSeconds: 10` - Frequent checks to detect failures quickly
- `failureThreshold: 3` - Requires 30 seconds of consecutive failures before restart (avoids flapping)

**Readiness Probe**:
- `initialDelaySeconds: 10` - Shorter delay since basic startup is fast
- `periodSeconds: 5` - Very frequent checks for quick traffic routing decisions
- `failureThreshold: 2` - Removes from load balancer after 10 seconds of failures

### Worker Service

**Liveness Probe**:
- `initialDelaySeconds: 60` - Celery workers take longer to initialize
- `periodSeconds: 30` - Less frequent checks (workers don't handle user traffic)
- `failureThreshold: 3` - Requires 90 seconds of consecutive failures before restart

**Readiness Probe**:
- `initialDelaySeconds: 30` - Wait for Prometheus metrics server to start
- `periodSeconds: 10` - Moderate frequency for worker readiness
- `failureThreshold: 2` - Mark not ready after 20 seconds of failures

## Failure Scenarios and Recovery

### Scenario 1: Database Connection Lost

**Symptom**: Readiness probe returns 503
**Kubernetes Action**: Removes pod from load balancer
**Recovery**: When database connection is restored, readiness probe returns 200 and pod is added back to load balancer
**User Impact**: No failed requests (traffic routed to healthy pods)

### Scenario 2: API Process Deadlock

**Symptom**: Liveness probe times out (no response)
**Kubernetes Action**: After 3 consecutive failures (30 seconds), restarts the pod
**Recovery**: New pod starts and passes health checks
**User Impact**: Brief service degradation if all pods fail simultaneously

### Scenario 3: Worker Process Crash

**Symptom**: Celery inspect ping command fails
**Kubernetes Action**: After 3 consecutive failures (90 seconds), restarts the pod
**Recovery**: New worker starts and begins processing tasks
**User Impact**: Tasks may be delayed but will be processed by other workers

### Scenario 4: Slow Startup

**Symptom**: Readiness probe fails during initialization
**Kubernetes Action**: Pod not added to load balancer until ready
**Recovery**: Once initialization completes, pod receives traffic
**User Impact**: No impact (pod doesn't receive traffic until ready)

## Testing Health Checks

### Manual Testing

**Test Liveness Probe**:
```bash
# Port-forward to pod
kubectl port-forward deployment/causal-organism-backend 8000:8000

# Test liveness endpoint
curl http://localhost:8000/health/live
```

**Test Readiness Probe**:
```bash
# Test readiness endpoint
curl http://localhost:8000/health/ready

# Simulate database failure (stop Neo4j)
kubectl scale deployment neo4j --replicas=0

# Verify readiness returns 503
curl -i http://localhost:8000/health/ready

# Restore database
kubectl scale deployment neo4j --replicas=1

# Verify readiness returns 200
curl http://localhost:8000/health/ready
```

### Automated Testing

**Test Pod Restart on Liveness Failure**:
```bash
# Get pod name
POD=$(kubectl get pod -l app=backend -o jsonpath='{.items[0].metadata.name}')

# Simulate deadlock (kill process without stopping container)
kubectl exec $POD -- kill -STOP 1

# Watch pod status (should restart after ~30 seconds)
kubectl get pod $POD -w
```

**Test Traffic Removal on Readiness Failure**:
```bash
# Monitor endpoints
kubectl get endpoints backend-service -w

# Stop database
kubectl scale deployment neo4j --replicas=0

# Verify pod removed from endpoints after ~10 seconds
# Restore database
kubectl scale deployment neo4j --replicas=1

# Verify pod added back to endpoints after ~5 seconds
```

## Monitoring and Alerting

### Metrics to Monitor

1. **Liveness Probe Failures**: Alert if any pod has >1 liveness failure in 5 minutes
2. **Readiness Probe Failures**: Alert if >50% of pods are not ready
3. **Pod Restart Rate**: Alert if >2 restarts per hour per pod
4. **Endpoint Count**: Alert if backend-service has 0 endpoints

### Prometheus Queries

**Liveness Failures**:
```promql
rate(kube_pod_container_status_restarts_total{container="api"}[5m]) > 0
```

**Readiness Failures**:
```promql
(kube_pod_status_ready{condition="false", pod=~"causal-organism-backend.*"} / 
 kube_pod_status_ready{pod=~"causal-organism-backend.*"}) > 0.5
```

## Files Modified

1. **backend/main.py**
   - Added `/health/live` endpoint
   - Added `/health/ready` endpoint with dependency checks
   - Replaced simple `health_check()` function

2. **k8s/deployment.yaml**
   - Added liveness and readiness probes to API container
   - Added liveness and readiness probes to worker container
   - Added resource requests and limits
   - Added environment variables for database credentials from secrets

3. **k8s/secrets.yaml** (NEW)
   - Created Kubernetes Secrets for database passwords
   - Created secrets for JWT and S3 credentials
   - Added documentation for production secret management

## Best Practices Implemented

1. **Separate Liveness and Readiness**: Liveness checks process health, readiness checks dependency health
2. **Appropriate Timeouts**: Longer timeouts for liveness (avoid unnecessary restarts)
3. **Failure Thresholds**: Multiple failures required before action (avoid flapping)
4. **Initial Delays**: Allow time for startup before first check
5. **Detailed Readiness Response**: Include status of each dependency for debugging
6. **Resource Limits**: Prevent resource exhaustion that could cause health check failures

## Production Considerations

1. **Secret Management**: Replace example secrets with actual secrets using:
   - `kubectl create secret` commands
   - External secret managers (Vault, AWS Secrets Manager)
   - Never commit secrets to version control

2. **Monitoring**: Set up alerts for:
   - High pod restart rates
   - Persistent readiness failures
   - Zero healthy endpoints

3. **Capacity Planning**: Ensure enough healthy pods to handle traffic when some are not ready

4. **Database Maintenance**: During maintenance, scale up extra pods before taking databases offline

5. **Graceful Shutdown**: Implement proper shutdown handlers to finish in-flight requests before termination

## Next Steps

1. Test health checks in staging environment
2. Set up Prometheus alerts for health check failures
3. Document runbook for common health check failure scenarios
4. Implement graceful shutdown handlers
5. Add health check metrics to Grafana dashboards
