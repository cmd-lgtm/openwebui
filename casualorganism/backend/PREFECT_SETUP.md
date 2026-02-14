# Prefect Workflow Orchestration Setup

This document describes the Prefect workflow orchestration setup for the Causal Organism platform.

## Overview

Prefect orchestrates two main workflows:

1. **Incremental Update Pipeline** - Runs every 5 minutes
   - Fetches new interactions from Redis stream
   - Applies incremental graph updates
   
2. **Full Analysis Pipeline** - Runs every 6 hours
   - Refreshes materialized views (expensive metrics)
   - Runs causal analysis
   - Stores results in TimescaleDB
   - Evaluates and proposes interventions

## Requirements

- Python 3.11+
- Prefect 2.14.0+
- PostgreSQL 14+ (for Prefect metadata)
- Docker and Docker Compose (for containerized deployment)

## Installation

### Option 1: Local Development

1. Install Prefect:
```bash
pip install prefect>=2.14.0
```

2. Start Prefect server:
```bash
prefect server start
```

3. In a new terminal, set up work queue and deploy flows:
```bash
python backend/prefect_config.py setup
```

4. Start Prefect agent:
```bash
prefect agent start -q default
```

### Option 2: Docker Deployment

1. Start Prefect services:
```bash
docker-compose -f docker-compose.prefect.yml up -d
```

2. Wait for services to be healthy:
```bash
docker-compose -f docker-compose.prefect.yml ps
```

3. Deploy flows:
```bash
docker-compose -f docker-compose.prefect.yml exec prefect-server \
  python /app/backend/prefect_config.py deploy
```

## Configuration

### Environment Variables

- `PREFECT_API_URL` - Prefect server API URL (default: `http://localhost:4200/api`)
- `PREFECT_WORK_QUEUE` - Work queue name (default: `default`)

### Flow Schedules

Schedules are defined in `backend/core/prefect_workflows.py`:

- **Incremental updates**: `*/5 * * * *` (every 5 minutes)
- **Full analysis**: `0 */6 * * *` (every 6 hours at :00)

To modify schedules, edit the `CronSchedule` parameters in `create_deployments()`.

## Usage

### View Prefect UI

Open http://localhost:4200 in your browser to:
- Monitor flow runs
- View logs
- Trigger manual runs
- Manage deployments

### Manual Flow Execution

Run a flow manually via CLI:

```bash
# Run incremental update flow
python backend/core/prefect_workflows.py incremental

# Run full analysis flow
python backend/core/prefect_workflows.py full
```

Or via Prefect CLI:

```bash
# Trigger incremental update
prefect deployment run incremental-update-pipeline/incremental-updates

# Trigger full analysis
prefect deployment run full-analysis-pipeline/full-analysis
```

### Check Deployment Status

```bash
python backend/prefect_config.py list
```

### Check Server Connection

```bash
python backend/prefect_config.py check
```

## Retry Logic and Error Handling

All tasks are configured with retry logic (Requirements 15.4, 15.5):

- **Fetch/Update tasks**: 3 retries with 60-second delay
- **Expensive operations** (materialized views): 2 retries with 300-second delay
- **Flows**: 1 retry with 120-300 second delay

On permanent failure:
- Error is logged to Prefect
- Alert notification should be configured (see Monitoring section)

## Monitoring

### Flow Run Status

Monitor flow runs in the Prefect UI:
- Success/failure status
- Execution time
- Task-level logs
- Retry attempts

### Alerts

Configure alerts for flow failures:

```python
from prefect.blocks.notifications.slack import SlackWebhook

slack_webhook = SlackWebhook(url="YOUR_SLACK_WEBHOOK_URL")
slack_webhook.save("slack-alerts")
```

Then add to flow definition:

```python
@flow(
    name="incremental-update-pipeline",
    on_failure=[slack_webhook]
)
async def incremental_update_flow():
    ...
```

## Architecture

### Task Dependencies

**Incremental Update Flow:**
```
fetch_interactions → update_graph_incremental
```

**Full Analysis Flow:**
```
refresh_materialized_views
    ↓
run_causal_analysis
    ↓
store_metrics
    ↓
evaluate_interventions
```

### Work Queues

All flows use the `default` work queue. For production, consider:
- Separate queues for different priorities
- Dedicated agents for resource-intensive tasks

## Troubleshooting

### Prefect server not starting

Check PostgreSQL connection:
```bash
docker-compose -f docker-compose.prefect.yml logs prefect-db
```

### Agent not picking up work

1. Check agent is running:
```bash
docker-compose -f docker-compose.prefect.yml logs prefect-agent
```

2. Verify work queue exists:
```bash
python backend/prefect_config.py list
```

3. Check agent is subscribed to correct queue:
```bash
prefect agent start -q default
```

### Flow failures

1. View logs in Prefect UI
2. Check task retry attempts
3. Verify database connections
4. Check external service availability

## Production Deployment

For production deployment:

1. Use external PostgreSQL for Prefect metadata
2. Configure high availability for Prefect server
3. Run multiple agents for redundancy
4. Set up monitoring and alerting
5. Configure secrets management for credentials
6. Enable authentication for Prefect UI

See Kubernetes deployment manifests in `k8s/prefect/` (to be created in task 27).

## References

- Prefect Documentation: https://docs.prefect.io/
- Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7, 15.8
- Design Document: `.kiro/specs/architecture-scalability-audit/design.md`
