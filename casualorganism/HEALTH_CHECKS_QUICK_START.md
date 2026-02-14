# Health Checks Quick Start Guide

## Overview

The Causal Organism platform now includes Kubernetes-ready health check endpoints for liveness and readiness probes. This guide shows you how to use and test them.

## Endpoints

### Liveness Probe: `/health/live`

**Purpose**: Checks if the API process is alive and responding.

**Usage**:
```bash
curl http://localhost:8000/health/live
```

**Response**:
```json
{
  "status": "alive",
  "service": "api-service",
  "timestamp": "2024-02-14T10:30:00.000Z"
}
```

**HTTP Status**: Always 200 if process is running

### Readiness Probe: `/health/ready`

**Purpose**: Checks if the API can handle requests by verifying all dependencies are healthy.

**Usage**:
```bash
curl http://localhost:8000/health/ready
```

**Response (Healthy)**:
```json
{
  "status": "ready",
  "service": "api-service",
  "timestamp": "2024-02-14T10:30:00.000Z",
  "checks": {
    "neo4j": {"status": "healthy", "healthy": true},
    "redis": {"status": "healthy", "healthy": true},
    "timescale": {"status": "healthy", "healthy": true}
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
    "neo4j": {"status": "error: connection refused", "healthy": false},
    "redis": {"status": "healthy", "healthy": true},
    "timescale": {"status": "healthy", "healthy": true}
  }
}
```

**HTTP Status**: 
- 200 if all dependencies healthy
- 503 if any dependency unhealthy

## Testing Locally

### 1. Start Services

```bash
docker-compose up -d
```

### 2. Test Liveness

```bash
curl http://localhost:8000/health/live
```

### 3. Test Readiness

```bash
# Should return 200 when all services are up
curl -i http://localhost:8000/health/ready

# Stop Neo4j to simulate failure
docker-compose stop neo4j

# Should return 503
curl -i http://localhost:8000/health/ready

# Restart Neo4j
docker-compose start neo4j

# Should return 200 again
curl -i http://localhost:8000/health/ready
```

## Kubernetes Deployment

### 1. Create Secrets

Before deploying, create the required secrets:

```bash
# TimescaleDB password
kubectl create secret generic timescale-secret \
  --from-literal=password=your-secure-password

# Neo4j password
kubectl create secret generic neo4j-secret \
  --from-literal=password=your-secure-password

# JWT secret key
kubectl create secret generic jwt-secret \
  --from-literal=secret-key=$(openssl rand -hex 32)

# S3 credentials (optional)
kubectl create secret generic s3-secret \
  --from-literal=access-key=your-access-key \
  --from-literal=secret-key=your-secret-key
```

### 2. Deploy Application

```bash
kubectl apply -f k8s/deployment.yaml
```

### 3. Verify Health Checks

```bash
# Check pod status
kubectl get pods -l app=backend

# Check pod events (shows probe failures)
kubectl describe pod <pod-name>

# Check endpoints (shows which pods are ready)
kubectl get endpoints backend-service

# Port-forward and test directly
kubectl port-forward deployment/causal-organism-backend 8000:8000
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
```

## Monitoring Health Checks

### View Probe Status

```bash
# Watch pod status in real-time
kubectl get pods -l app=backend -w

# View detailed probe information
kubectl describe pod <pod-name> | grep -A 10 "Liveness\|Readiness"
```

### Common Probe Failures

**Liveness Probe Failure**:
- Pod will be restarted after 3 consecutive failures (30 seconds)
- Check logs: `kubectl logs <pod-name> --previous`

**Readiness Probe Failure**:
- Pod removed from load balancer after 2 consecutive failures (10 seconds)
- Check which dependency failed: `curl http://<pod-ip>:8000/health/ready`

## Troubleshooting

### Pod Keeps Restarting

```bash
# Check liveness probe status
kubectl describe pod <pod-name> | grep Liveness

# Check logs from previous container
kubectl logs <pod-name> --previous

# Common causes:
# - Application crash on startup
# - Deadlock or infinite loop
# - Out of memory
```

### Pod Not Receiving Traffic

```bash
# Check readiness probe status
kubectl describe pod <pod-name> | grep Readiness

# Check which dependency is failing
kubectl port-forward <pod-name> 8000:8000
curl http://localhost:8000/health/ready

# Common causes:
# - Database connection failure
# - Redis connection failure
# - Slow startup (increase initialDelaySeconds)
```

### All Pods Failing

```bash
# Check if databases are running
kubectl get pods

# Check database services
kubectl get svc

# Check database connectivity from pod
kubectl exec <pod-name> -- nc -zv neo4j-service 7687
kubectl exec <pod-name> -- nc -zv redis-service 6379
kubectl exec <pod-name> -- nc -zv timescale-service 5432
```

## Probe Configuration

### API Service

```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 2
```

### Worker Service

```yaml
livenessProbe:
  exec:
    command:
    - celery
    - -A
    - backend.worker.celery_app
    - inspect
    - ping
  initialDelaySeconds: 60
  periodSeconds: 30
  timeoutSeconds: 10
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /metrics
    port: 9090
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 2
```

## Running Tests

```bash
# Run health check tests
python -m pytest backend/tests/test_health_checks.py -v

# Run all tests
python -m pytest backend/tests/ -v
```

## Next Steps

1. Set up Prometheus alerts for probe failures
2. Add health check metrics to Grafana dashboards
3. Document runbooks for common failure scenarios
4. Test failover scenarios in staging environment

## References

- [Kubernetes Liveness and Readiness Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [HEALTH_CHECKS_IMPLEMENTATION_SUMMARY.md](./HEALTH_CHECKS_IMPLEMENTATION_SUMMARY.md) - Detailed implementation documentation
