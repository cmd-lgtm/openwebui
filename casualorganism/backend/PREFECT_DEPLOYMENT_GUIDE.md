# Prefect Deployment Guide

This guide covers deploying Prefect workflows with schedules for the Causal Organism platform.

## Overview

Two workflows are deployed:

1. **Incremental Update Pipeline** - Runs every 5 minutes
   - Fetches new interactions from Redis stream
   - Applies incremental graph updates
   - Updates materialized views for affected nodes

2. **Full Analysis Pipeline** - Runs every 6 hours
   - Refreshes expensive materialized views (betweenness, clustering)
   - Runs causal analysis on all employees
   - Stores results in TimescaleDB
   - Evaluates and proposes interventions

## Prerequisites

- Python 3.11+
- Prefect 2.14.0+ installed
- Prefect server running (local or Docker)
- Access to Neo4j, Redis, and TimescaleDB

## Quick Start

### Option 1: Automated Deployment Script

**Linux/Mac:**
```bash
chmod +x scripts/deploy_prefect.sh
./scripts/deploy_prefect.sh
```

**Windows:**
```cmd
scripts\deploy_prefect.bat
```

### Option 2: Manual Deployment

1. **Start Prefect Server**

   Local:
   ```bash
   prefect server start
   ```

   Docker:
   ```bash
   docker-compose -f docker-compose.prefect.yml up -d
   ```

2. **Deploy Workflows**

   ```bash
   python backend/prefect_config.py setup
   ```

3. **Start Prefect Agent**

   ```bash
   prefect agent start -q default
   ```

4. **Verify Deployment**

   ```bash
   prefect deployment ls
   ```

## Deployment Configuration

### Schedules

Schedules are defined in `backend/core/prefect_workflows.py`:

```python
# Incremental updates: every 5 minutes
schedule=CronSchedule(cron="*/5 * * * *")

# Full analysis: every 6 hours at :00
schedule=CronSchedule(cron="0 */6 * * *")
```

### Retry Configuration

All tasks have retry logic configured (Requirements 15.4):

- **Fetch/Update tasks**: 3 retries, 60-second delay
- **Expensive operations**: 2 retries, 300-second delay
- **Flows**: 1 retry, 120-300 second delay

### Error Handling

On permanent failure (Requirements 15.5):
- Error logged to Prefect
- Alert sent via configured channels (Slack, Sentry, Email)
- Flow marked as failed for manual intervention

## Monitoring

### Prefect UI

Access at http://localhost:4200

Features:
- View flow run history
- Monitor task execution
- View logs in real-time
- Trigger manual runs
- Manage deployments

### CLI Monitoring

```bash
# List all deployments
prefect deployment ls

# List recent flow runs
prefect flow-run ls --limit 10

# View specific flow run
prefect flow-run inspect <flow-run-id>

# View flow run logs
prefect flow-run logs <flow-run-id>
```

### Metrics

Monitor these metrics:
- Flow run success rate
- Task retry frequency
- Execution duration
- Queue depth

## Manual Execution

### Trigger Flow via CLI

```bash
# Incremental update
prefect deployment run incremental-update-pipeline/incremental-updates

# Full analysis
prefect deployment run full-analysis-pipeline/full-analysis
```

### Trigger Flow via Python

```python
from backend.core.prefect_workflows import run_flow_once
import asyncio

# Run incremental update
result = asyncio.run(run_flow_once("incremental"))

# Run full analysis
result = asyncio.run(run_flow_once("full"))
```

### Trigger Flow via API

```bash
# Get deployment ID
DEPLOYMENT_ID=$(prefect deployment ls --json | jq -r '.[0].id')

# Trigger flow run
curl -X POST http://localhost:4200/api/deployments/$DEPLOYMENT_ID/create_flow_run
```

## Alert Configuration

### Setup Alerts

```bash
# Configure all alert integrations
python backend/prefect_alerts.py test
```

### Environment Variables

```bash
# Slack
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# Sentry
export SENTRY_DSN="https://YOUR_SENTRY_DSN"
export ENVIRONMENT="production"

# Email
export ALERT_EMAIL="alerts@example.com"
```

### Add Alerts to Flows

Edit `backend/core/prefect_workflows.py`:

```python
from prefect.blocks.notifications.slack import SlackWebhook

@flow(
    name="incremental-update-pipeline",
    on_failure=[SlackWebhook.load("slack-alerts")]
)
async def incremental_update_flow():
    ...
```

## Production Deployment

### Kubernetes Deployment

For production, deploy Prefect components to Kubernetes:

1. **Deploy Prefect Server**
   ```bash
   kubectl apply -f k8s/prefect/server.yaml
   ```

2. **Deploy Prefect Agent**
   ```bash
   kubectl apply -f k8s/prefect/agent.yaml
   ```

3. **Configure Secrets**
   ```bash
   kubectl create secret generic prefect-secrets \
     --from-literal=slack-webhook-url=$SLACK_WEBHOOK_URL \
     --from-literal=sentry-dsn=$SENTRY_DSN
   ```

### High Availability

For HA deployment:
- Run multiple Prefect agents
- Use external PostgreSQL for Prefect metadata
- Configure load balancer for Prefect UI
- Set up monitoring and alerting

### Scaling

Scale agents based on workload:

```bash
# Scale up agents
kubectl scale deployment prefect-agent --replicas=5

# Scale down agents
kubectl scale deployment prefect-agent --replicas=2
```

## Troubleshooting

### Flow Not Running

1. Check agent is running:
   ```bash
   prefect agent ls
   ```

2. Check work queue:
   ```bash
   prefect work-queue ls
   ```

3. Check deployment schedule:
   ```bash
   prefect deployment inspect incremental-update-pipeline/incremental-updates
   ```

### Task Failures

1. View logs:
   ```bash
   prefect flow-run logs <flow-run-id>
   ```

2. Check database connections:
   ```bash
   python backend/prefect_config.py check
   ```

3. Verify environment variables are set

### Agent Not Picking Up Work

1. Verify agent is subscribed to correct queue:
   ```bash
   prefect agent start -q default
   ```

2. Check deployment work queue matches agent queue

3. Restart agent:
   ```bash
   # Stop agent (Ctrl+C)
   # Start agent
   prefect agent start -q default
   ```

## Updating Deployments

### Update Flow Code

1. Modify flow in `backend/core/prefect_workflows.py`

2. Redeploy:
   ```bash
   python backend/prefect_config.py deploy
   ```

### Update Schedule

1. Modify schedule in `create_deployments()` function

2. Redeploy:
   ```bash
   python backend/prefect_config.py deploy
   ```

### Update Retry Configuration

1. Modify task decorators in `backend/core/prefect_workflows.py`

2. Redeploy:
   ```bash
   python backend/prefect_config.py deploy
   ```

## Best Practices

1. **Monitor Flow Runs**: Check Prefect UI daily for failures
2. **Set Up Alerts**: Configure Slack/email alerts for failures
3. **Test Locally**: Test flows locally before deploying
4. **Version Control**: Keep deployment configurations in git
5. **Document Changes**: Update this guide when making changes
6. **Regular Maintenance**: Review and optimize flows monthly

## References

- Prefect Documentation: https://docs.prefect.io/
- Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7, 15.8
- Design Document: `.kiro/specs/architecture-scalability-audit/design.md`
- Setup Guide: `backend/PREFECT_SETUP.md`
