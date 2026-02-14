# Causal Organism Migration Guide and Operational Runbook

## Table of Contents
1. [Migration Guide](#migration-guide)
2. [Operational Runbooks](#operational-runbooks)
3. [Monitoring and Alerting Guide](#monitoring-and-alerting-guide)

---

## Migration Guide

### Migrating from POC to Production

#### Phase 1: Infrastructure Preparation

1. **Database Setup**
   ```bash
   # Deploy Neo4j
   kubectl apply -f k8s/neo4j.yaml

   # Deploy TimescaleDB
   kubectl apply -f k8s/timescale.yaml

   # Verify connections
   kubectl exec -it <pod> -- python -c "from neo4j import GraphDatabase; ..."
   ```

2. **Secrets Configuration**
   ```bash
   # Create Kubernetes secrets
   kubectl create secret generic neo4j-secret --from-literal=password=<password> -n causal-organism
   kubectl create secret generic timescale-secret --from-literal=password=<password> -n causal-organism
   kubectl create secret generic jwt-secret --from-literal=secret-key=<key> -n causal-organism

   # Or use Vault
   kubectl apply -f k8s/vault-secret.yaml
   ```

3. **Enable Monitoring**
   ```bash
   # Deploy Prometheus
   kubectl apply -f k8s/prometheus.yaml

   # Deploy Grafana
   kubectl apply -f k8s/grafana.yaml

   # Deploy Jaeger
   kubectl apply -f k8s/jaeger.yaml
   ```

#### Phase 2: Application Deployment

1. **Deploy API Service**
   ```bash
   kubectl apply -f k8s/deployment.yaml
   ```

2. **Deploy Workers**
   ```bash
   kubectl apply -f k8s/worker-deployment.yaml
   ```

3. **Configure Auto-scaling**
   ```bash
   kubectl apply -f k8s/hpa.yaml
   ```

4. **Verify Deployment**
   ```bash
   # Check pod status
   kubectl get pods -n causal-organism

   # Check health endpoints
   kubectl exec -it <api-pod> -- curl http://localhost:8000/health/live
   kubectl exec -it <api-pod> -- curl http://localhost:8000/health/ready
   ```

#### Phase 3: Data Migration

1. **Export Data from POC**
   ```bash
   # Export from Neo4j
   docker exec neo4j-container neo4j-admin database dump

   # Export from TimescaleDB
   pg_dump -h timescale-host -U postgres -d postgres > backup.sql
   ```

2. **Import Data to Production**
   ```bash
   # Import to Neo4j
   docker exec neo4j-container neo4j-admin database load

   # Import to TimescaleDB
   psql -h timescale-host -U postgres -d postgres < backup.sql
   ```

#### Phase 4: DNS and Traffic

1. **Update DNS**
   ```bash
   # Point domain to load balancer
   kubectl get svc -n causal-organism
   ```

2. **Enable TLS**
   ```bash
   # Deploy Ingress with TLS
   kubectl apply -f k8s/ingress.yaml
   ```

---

## Operational Runbooks

### Incident Response Procedures

#### High CPU Usage

**Symptoms:**
- API responses slow (>2s)
- P99 latency increases
- HPA scaling up

**Resolution:**
```bash
# 1. Identify affected pods
kubectl top pods -n causal-organism

# 2. Check for runaway queries
kubectl exec -it <pod> -- curl http://localhost:8000/api/graph/stats

# 3. Check database connections
kubectl exec -it <pod> -- curl http://localhost:8000/health/ready

# 4. Scale manually if needed
kubectl scale deployment causal-organism-api --replicas=5 -n causal-organism
```

#### Database Connection Failures

**Symptoms:**
- 503 errors on API
- Readiness probe fails

**Resolution:**
```bash
# 1. Check database pods
kubectl get pods -n causal-organism -l component=database

# 2. Check connection pool
kubectl logs <api-pod> | grep "connection pool"

# 3. Restart API pods
kubectl rollout restart deployment causal-organism-api -n causal-organism
```

#### Celery Worker Failures

**Symptoms:**
- Tasks stuck in pending
- Queue depth increasing

**Resolution:**
```bash
# 1. Check worker logs
kubectl logs -l app=worker -n causal-organism --tail=100

# 2. Check queue length
kubectl exec -it <worker-pod> -- celery -A backend.worker.celery_app inspect active

# 3. Restart workers
kubectl rollout restart deployment causal-organism-worker -n causal-organism
```

### Scaling Procedures

#### Scale API Service

```bash
# Manual scale
kubectl scale deployment causal-organism-api --replicas=5 -n causal-organism

# Or use HPA (automatic)
# HPA already configured - will scale based on CPU/queue
```

#### Scale Workers

```bash
# Manual scale
kubectl scale deployment causal-organism-worker --replicas=10 -n causal-organism

# Check queue before scaling
kubectl exec -it <worker-pod> -- celery -A backend.worker.celery_app inspect stats
```

### Backup and Recovery

#### Backup Neo4j

```bash
# Daily backup (cron job)
kubectl create job neo4j-backup-daily --schedule="0 2 * * *" \
  --from=cronjob/neo4j-backup -n causal-organism

# Verify backup
kubectl logs job/neo4j-backup-daily -n causal-organism
```

#### Backup TimescaleDB

```bash
# Daily backup
kubectl create job timescale-backup-daily --schedule="0 2 * * *" \
  --from=cronjob/timescale-backup -n causal-organism

# Point-in-time recovery (if enabled)
# Use TimescaleDB's recovery features
```

#### Restore from Backup

```bash
# Stop API
kubectl scale deployment causal-organism-api --replicas=0 -n causal-organism

# Restore Neo4j
kubectl exec -it neo4j-0 -n causal-organism -- \
  neo4j-admin database load

# Restore TimescaleDB
psql -h timescale-host -U postgres -d postgres < backup.sql

# Start API
kubectl scale deployment causal-organism-api --replicas=2 -n causal-organism
```

### Secret Rotation

#### Rotate Database Passwords

```bash
# Run rotation script
python -m backend.core.rotate_secrets --secret neo4j

# Update Kubernetes secret
kubectl create secret generic neo4j-secret \
  --from-literal=password=<new-password> \
  -n causal-organism --dry-run=client -o yaml | kubectl apply -f -

# Restart pods to pick up new secret
kubectl rollout restart deployment causal-organism-api -n causal-organism
kubectl rollout restart deployment causal-organism-worker -n causal-organism
```

#### Rotate JWT Secret

```bash
# Generate new key
openssl rand -hex 32

# Update secret
kubectl create secret generic jwt-secret \
  --from-literal=secret-key=<new-key> \
  -n causal-organism --dry-run=client -o yaml | kubectl apply -f -

# Restart API
kubectl rollout restart deployment causal-organism-api -n causal-organism
```

---

## Monitoring and Alerting Guide

### Key Metrics to Watch

#### API Metrics
- **Request Rate**: Target >100 rps
- **Error Rate**: Alert if >5%
- **P95 Latency**: Alert if >1000ms
- **P99 Latency**: Alert if >2000ms

#### Worker Metrics
- **Queue Depth**: Alert if >1000
- **Task Rate**: Target matches request rate
- **Failed Tasks**: Alert if >10

#### Infrastructure
- **CPU Utilization**: Target 50-70%
- **Memory Utilization**: Target <80%
- **Database Connections**: Alert if >80% of max

### Alert Response Procedures

#### High Error Rate Alert

1. Check error details
   ```bash
   kubectl logs -l app=api -n causal-organism | grep ERROR
   ```

2. Check Sentry
   ```bash
   kubectl exec -it <pod> -- curl http://localhost:8000/api/errors/recent
   ```

3. Check database health
   ```bash
   kubectl exec -it <pod> -- curl http://localhost:8000/health/ready
   ```

#### High Latency Alert

1. Check database performance
   ```bash
   # Check slow queries
   kubectl exec -it timescale-0 -n causal-organism -- \
     psql -U postgres -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
   ```

2. Check connection pool
   ```bash
   kubectl exec -it <pod> -- curl http://localhost:8000/metrics | grep pool
   ```

3. Scale if needed
   ```bash
   kubectl scale deployment causal-organism-api --replicas=5 -n causal-organism
   ```

### Dashboard Usage

#### Grafana Dashboards

1. **API Dashboard** (`/d/api-overview`)
   - Request rate by endpoint
   - Response latency percentiles
   - Error rate by type
   - CPU/Memory usage

2. **Worker Dashboard** (`/d/worker-overview`)
   - Queue depth
   - Task throughput
   - Failed tasks
   - Worker count

3. **Database Dashboard** (`/d/db-overview`)
   - Query performance
   - Connection pool
   - Replication lag (if applicable)
   - Storage usage

---

## Contact Information

- **On-Call**: [Phone/Email]
- **SRE Team**: [Email]
- **Development Team**: [Email]
- **Emergency Escalation**: [Phone]

---

## Appendix: Quick Reference Commands

```bash
# Get pod status
kubectl get pods -n causal-organism

# Get logs
kubectl logs -f deployment/causal-organism-api -n causal-organism

# Restart deployment
kubectl rollout restart deployment/causal-organism-api -n causal-organism

# Scale deployment
kubectl scale deployment/causal-organism-api --replicas=3 -n causal-organism

# Port forward to pod
kubectl port-forward svc/api-service 8000:80 -n causal-organism

# Exec into pod
kubectl exec -it <pod-name> -n causal-organism -- /bin/bash

# Check HPA
kubectl get hpa -n causal-organism

# View events
kubectl get events -n causal-organism --sort-by='.lastTimestamp'
```
