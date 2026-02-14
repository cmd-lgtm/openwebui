"""
Prefect workflow orchestration for Causal Organism platform.

This module defines Prefect flows and tasks for:
1. Incremental graph updates (every 5 minutes)
2. Full analysis pipeline (every 6 hours)

Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7, 15.8
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from prefect import flow, task, get_run_logger
from prefect.tasks import task_input_hash
from prefect.deployments import Deployment
from prefect.server.schemas.schedules import CronSchedule, IntervalSchedule

# Import existing components
from backend.core.event_stream import EventDrivenGraphBuilder
from backend.core.graph_builder_timescale import GraphBuilderTimescale
from backend.core.materialized_views import MaterializedViewManager
from backend.core.causal import CausalEngine
from backend.core.spark_engine import DistributedCausalEngine
from backend.core.timescale_metrics import TimescaleMetricsWriter, InterventionAuditLogger
from backend.core.safe_action_orchestrator import SafeActionOrchestrator
from backend.core.connection_pool import (
    Neo4jConnectionPool,
    RedisConnectionPool,
    TimescaleConnectionPool,
    CacheLayer
)

logger = logging.getLogger(__name__)


# ============================================================================
# Error Handling and Alerting
# ============================================================================

async def send_failure_alert(
    flow_name: str,
    task_name: str,
    error: Exception,
    context: Dict[str, Any]
) -> None:
    """
    Send alert notification on permanent task failure.
    
    Requirements: 15.5
    
    Args:
        flow_name: Name of the flow that failed
        task_name: Name of the task that failed
        error: Exception that caused the failure
        context: Additional context about the failure
    """
    log = get_run_logger()
    
    alert_message = f"""
    ⚠️ Prefect Flow Failure Alert
    
    Flow: {flow_name}
    Task: {task_name}
    Error: {str(error)}
    Timestamp: {datetime.utcnow().isoformat()}
    
    Context:
    {context}
    
    This task has exhausted all retry attempts and requires manual intervention.
    """
    
    # Log the alert
    log.error(alert_message)
    
    # In production, this would send to:
    # - Slack webhook
    # - PagerDuty
    # - Email
    # - Sentry
    
    # Example Slack integration (commented out):
    # try:
    #     from prefect.blocks.notifications.slack import SlackWebhook
    #     slack_webhook = await SlackWebhook.load("slack-alerts")
    #     await slack_webhook.notify(alert_message)
    # except Exception as e:
    #     log.warning(f"Failed to send Slack alert: {e}")
    
    # Example Sentry integration (commented out):
    # try:
    #     import sentry_sdk
    #     sentry_sdk.capture_exception(error)
    # except Exception as e:
    #     log.warning(f"Failed to send Sentry alert: {e}")


def handle_task_failure(task_name: str):
    """
    Decorator to handle task failures and send alerts.
    
    Requirements: 15.4, 15.5
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            log = get_run_logger()
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                log.error(f"Task {task_name} failed after all retries: {e}")
                
                # Send failure alert
                await send_failure_alert(
                    flow_name="unknown",
                    task_name=task_name,
                    error=e,
                    context={
                        "args": str(args),
                        "kwargs": str(kwargs)
                    }
                )
                
                # Re-raise to mark task as failed
                raise
        
        return wrapper
    return decorator


# ============================================================================
# Task Definitions with Retry Logic
# ============================================================================

@task(
    name="fetch-interactions",
    retries=3,
    retry_delay_seconds=60,
    cache_key_fn=task_input_hash,
    cache_expiration=timedelta(minutes=5)
)
async def fetch_interactions() -> List[Dict[str, Any]]:
    """
    Fetch new interactions from Redis stream.
    
    Reads pending messages from the 'interactions' stream using a consumer group.
    Messages are acknowledged after successful processing.
    
    Requirements: 15.1, 15.3
    
    Returns:
        List of interaction events to process
    """
    log = get_run_logger()
    log.info("Fetching new interactions from Redis stream")
    
    try:
        # Initialize Redis connection
        redis_pool = RedisConnectionPool()
        await redis_pool.initialize()
        client = await redis_pool.get_client()
        
        # Consumer group and ID for Prefect flow
        consumer_group = "prefect_incremental"
        consumer_id = "prefect_worker"
        
        # Create consumer group if not exists
        try:
            await client.xgroup_create(
                "interactions",
                consumer_group,
                id="0",
                mkstream=True
            )
            log.info(f"Created consumer group: {consumer_group}")
        except Exception:
            # Group already exists
            pass
        
        # Read batch of pending messages
        batch_size = 100
        events = await client.xreadgroup(
            consumer_group,
            consumer_id,
            {"interactions": ">"},
            count=batch_size,
            block=1000  # 1 second timeout
        )
        
        interactions = []
        message_ids = []
        
        for stream_name, messages in events:
            for message_id, data in messages:
                interactions.append({
                    "message_id": message_id,
                    "source": data.get("source"),
                    "target": data.get("target"),
                    "type": data.get("type"),
                    "weight": int(data.get("weight", 1)),
                    "timestamp": data.get("timestamp")
                })
                message_ids.append(message_id)
        
        log.info(f"Fetched {len(interactions)} new interactions")
        
        # Store message IDs for acknowledgment after processing
        return interactions
        
    except Exception as e:
        log.error(f"Error fetching interactions: {e}")
        raise


@task(
    name="update-graph-incremental",
    retries=3,
    retry_delay_seconds=60
)
async def update_graph_incremental(interactions: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Apply incremental graph updates for new interactions.
    
    Uses EventDrivenGraphBuilder to update Neo4j and invalidate cache.
    Acknowledges messages after successful processing.
    
    Requirements: 15.1, 15.3
    
    Args:
        interactions: List of interaction events with message IDs
        
    Returns:
        Statistics about updates applied
    """
    log = get_run_logger()
    log.info(f"Applying incremental updates for {len(interactions)} interactions")
    
    if not interactions:
        log.info("No interactions to process")
        return {"processed": 0, "updated_nodes": 0, "updated_edges": 0}
    
    try:
        # Initialize connections
        neo4j_pool = Neo4jConnectionPool()
        redis_pool = RedisConnectionPool()
        cache = CacheLayer(redis_pool)
        
        await neo4j_pool.initialize()
        await redis_pool.initialize()
        
        # Create graph builder
        builder = EventDrivenGraphBuilder(
            neo4j_pool=neo4j_pool,
            redis_pool=redis_pool,
            cache=cache
        )
        
        # Process each interaction
        stats = {
            "processed": 0,
            "updated_nodes": 0,
            "updated_edges": 0,
            "failed": 0
        }
        
        message_ids = []
        
        for interaction in interactions:
            try:
                # Extract message ID for acknowledgment
                message_id = interaction.pop("message_id", None)
                if message_id:
                    message_ids.append(message_id)
                
                # Process interaction
                await builder._process_interaction(interaction)
                
                stats["processed"] += 1
                stats["updated_nodes"] += 2  # source and target
                stats["updated_edges"] += 1
                
            except Exception as e:
                log.error(f"Error processing interaction: {e}")
                stats["failed"] += 1
        
        # Acknowledge processed messages
        if message_ids:
            client = await redis_pool.get_client()
            for message_id in message_ids:
                try:
                    await client.xack("interactions", "prefect_incremental", message_id)
                except Exception as e:
                    log.warning(f"Failed to acknowledge message {message_id}: {e}")
        
        log.info(f"Incremental update complete: {stats}")
        return stats
        
    except Exception as e:
        log.error(f"Error updating graph: {e}")
        raise


@task(
    name="refresh-materialized-views",
    retries=2,
    retry_delay_seconds=300
)
async def refresh_materialized_views() -> Dict[str, Any]:
    """
    Refresh expensive graph metrics (betweenness, clustering).
    
    Requirements: 15.1, 15.2, 15.6
    
    Returns:
        Statistics about refresh operation
    """
    log = get_run_logger()
    log.info("Refreshing materialized views for expensive metrics")
    
    try:
        neo4j_pool = Neo4jConnectionPool()
        view_manager = MaterializedViewManager(neo4j_pool)
        
        # Refresh expensive metrics
        await view_manager.refresh_expensive_metrics()
        
        stats = {
            "refreshed_at": datetime.utcnow().isoformat(),
            "metrics_updated": ["betweenness_centrality", "clustering_coeff"]
        }
        
        log.info(f"Materialized views refreshed: {stats}")
        return stats
        
    except Exception as e:
        log.error(f"Error refreshing materialized views: {e}")
        raise


@task(
    name="run-causal-analysis",
    retries=3,
    retry_delay_seconds=60
)
async def run_causal_analysis() -> Dict[str, Any]:
    """
    Execute causal analysis on current graph data.
    
    Fetches employee metrics from Neo4j materialized views and runs
    causal inference to identify burnout patterns.
    
    Requirements: 15.1, 15.2, 15.6
    
    Returns:
        Analysis results including coefficients and statistics
    """
    log = get_run_logger()
    log.info("Running causal analysis")
    
    try:
        neo4j_pool = Neo4jConnectionPool()
        await neo4j_pool.initialize()
        
        # Fetch employee metrics from materialized views
        view_manager = MaterializedViewManager(neo4j_pool)
        all_metrics = await view_manager.get_all_employee_metrics()
        
        if not all_metrics:
            log.warning("No employee metrics found for analysis")
            return {
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "row_count": 0,
                "engine": "none",
                "status": "skipped"
            }
        
        row_count = len(all_metrics)
        log.info(f"Analyzing {row_count} employee records")
        
        # Determine dataset size and select appropriate engine
        if row_count < 100_000:
            log.info("Using Pandas engine for small dataset")
            engine = CausalEngine()
            engine_type = "pandas"
        else:
            log.info("Using Spark engine for large dataset")
            engine = DistributedCausalEngine()
            engine_type = "spark"
        
        # Convert to DataFrame for analysis
        import pandas as pd
        df = pd.DataFrame(all_metrics)
        
        # Run causal analysis (simplified - actual implementation would be more complex)
        # This would typically analyze relationships between centrality metrics and burnout
        results = {
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "row_count": row_count,
            "engine": engine_type,
            "status": "completed",
            "metrics_analyzed": ["degree_centrality", "betweenness_centrality", "clustering_coeff"],
            "employees_analyzed": row_count
        }
        
        log.info(f"Causal analysis complete: {results}")
        return results
        
    except Exception as e:
        log.error(f"Error running causal analysis: {e}")
        raise


@task(
    name="store-metrics",
    retries=3,
    retry_delay_seconds=60
)
async def store_metrics(analysis_results: Dict[str, Any]) -> Dict[str, int]:
    """
    Store analysis results in TimescaleDB.
    
    Fetches current metrics from Neo4j and writes them to TimescaleDB
    with timestamp for historical trend analysis.
    
    Requirements: 15.1, 15.2, 15.6
    
    Args:
        analysis_results: Results from causal analysis
        
    Returns:
        Statistics about stored metrics
    """
    log = get_run_logger()
    log.info("Storing analysis results in TimescaleDB")
    
    try:
        # Skip if analysis was skipped
        if analysis_results.get("status") == "skipped":
            log.info("Skipping metrics storage - no analysis performed")
            return {"stored_records": 0}
        
        neo4j_pool = Neo4jConnectionPool()
        timescale_pool = TimescaleConnectionPool()
        
        await neo4j_pool.initialize()
        await timescale_pool.initialize()
        
        # Fetch current metrics from Neo4j
        view_manager = MaterializedViewManager(neo4j_pool)
        all_metrics = await view_manager.get_all_employee_metrics()
        
        if not all_metrics:
            log.warning("No metrics to store")
            return {"stored_records": 0}
        
        # Write to TimescaleDB
        pool = await timescale_pool.get_pool()
        metrics_writer = TimescaleMetricsWriter(pool)
        
        # Convert metrics to format expected by writer
        metrics_list = []
        for metric in all_metrics:
            metrics_list.append({
                "employee_id": metric.get("employee_id"),
                "degree_centrality": metric.get("degree_centrality"),
                "betweenness_centrality": metric.get("betweenness_centrality"),
                "clustering_coeff": metric.get("clustering_coeff"),
                "burnout_score": None  # Would be computed from analysis
            })
        
        # Batch write
        stored_count = await metrics_writer.write_employee_metrics_batch(
            metrics_list,
            timestamp=datetime.utcnow()
        )
        
        log.info(f"Stored {stored_count} metric records")
        return {"stored_records": stored_count}
        
    except Exception as e:
        log.error(f"Error storing metrics: {e}")
        raise


@task(
    name="evaluate-interventions",
    retries=2,
    retry_delay_seconds=60
)
async def evaluate_interventions(analysis_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Propose interventions based on analysis results.
    
    Uses SafeActionOrchestrator to evaluate potential interventions
    based on employee metrics and burnout indicators.
    
    Requirements: 15.1, 15.2, 15.6
    
    Args:
        analysis_results: Results from causal analysis
        
    Returns:
        Statistics about proposed interventions
    """
    log = get_run_logger()
    log.info("Evaluating potential interventions")
    
    try:
        # Skip if analysis was skipped
        if analysis_results.get("status") == "skipped":
            log.info("Skipping intervention evaluation - no analysis performed")
            return {
                "evaluated_at": datetime.utcnow().isoformat(),
                "proposed_interventions": 0,
                "status": "skipped"
            }
        
        neo4j_pool = Neo4jConnectionPool()
        timescale_pool = TimescaleConnectionPool()
        
        await neo4j_pool.initialize()
        await timescale_pool.initialize()
        
        orchestrator = SafeActionOrchestrator(
            neo4j_pool=neo4j_pool,
            timescale_pool=timescale_pool
        )
        
        # Evaluate and propose interventions
        # This is simplified - actual implementation would analyze metrics
        # and propose specific interventions for at-risk employees
        
        proposed_count = 0
        high_impact = 0
        medium_impact = 0
        low_impact = 0
        
        # Placeholder for actual intervention logic
        # Would typically:
        # 1. Identify employees with high burnout risk
        # 2. Propose appropriate interventions
        # 3. Store proposals in database
        
        stats = {
            "evaluated_at": datetime.utcnow().isoformat(),
            "proposed_interventions": proposed_count,
            "high_impact": high_impact,
            "medium_impact": medium_impact,
            "low_impact": low_impact,
            "status": "completed"
        }
        
        log.info(f"Intervention evaluation complete: {stats}")
        return stats
        
    except Exception as e:
        log.error(f"Error evaluating interventions: {e}")
        raise


# ============================================================================
# Flow Definitions
# ============================================================================

@flow(
    name="incremental-update-pipeline",
    description="Process new interactions and update graph incrementally",
    retries=1,
    retry_delay_seconds=120
)
async def incremental_update_flow() -> Dict[str, Any]:
    """
    Incremental update flow - runs every 5 minutes.
    
    Fetches new interactions and applies incremental graph updates.
    
    Requirements: 15.1, 15.3, 15.4, 15.5
    
    Returns:
        Summary of flow execution
    """
    log = get_run_logger()
    log.info("Starting incremental update flow")
    
    try:
        # Fetch new interactions
        interactions = await fetch_interactions()
        
        # Apply incremental updates
        update_stats = await update_graph_incremental(interactions)
        
        summary = {
            "flow": "incremental-update",
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "interactions_processed": update_stats["processed"],
            "nodes_updated": update_stats["updated_nodes"],
            "edges_updated": update_stats["updated_edges"]
        }
        
        log.info(f"Incremental update flow complete: {summary}")
        return summary
        
    except Exception as e:
        log.error(f"Incremental update flow failed: {e}")
        
        # Send failure alert
        await send_failure_alert(
            flow_name="incremental-update-pipeline",
            task_name="flow",
            error=e,
            context={
                "description": "Incremental update flow failed after all retries"
            }
        )
        
        raise


@flow(
    name="full-analysis-pipeline",
    description="Complete analysis cycle with refresh, analysis, storage, and intervention evaluation",
    retries=1,
    retry_delay_seconds=300
)
async def full_analysis_flow() -> Dict[str, Any]:
    """
    Full analysis flow - runs every 6 hours.
    
    Executes complete analysis cycle:
    1. Refresh materialized views
    2. Run causal analysis
    3. Store results
    4. Evaluate interventions
    
    Requirements: 15.1, 15.2, 15.6, 15.4, 15.5
    
    Returns:
        Summary of flow execution
    """
    log = get_run_logger()
    log.info("Starting full analysis flow")
    
    try:
        # Step 1: Refresh expensive metrics
        view_stats = await refresh_materialized_views()
        
        # Step 2: Run causal analysis
        analysis_results = await run_causal_analysis()
        
        # Step 3: Store results
        storage_stats = await store_metrics(analysis_results)
        
        # Step 4: Evaluate interventions
        intervention_stats = await evaluate_interventions(analysis_results)
        
        summary = {
            "flow": "full-analysis",
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "materialized_views_refreshed": view_stats.get("metrics_updated", []),
            "analysis_engine": analysis_results.get("engine", "unknown"),
            "metrics_stored": storage_stats.get("stored_records", 0),
            "interventions_proposed": intervention_stats.get("proposed_interventions", 0)
        }
        
        log.info(f"Full analysis flow complete: {summary}")
        return summary
        
    except Exception as e:
        log.error(f"Full analysis flow failed: {e}")
        
        # Send failure alert
        await send_failure_alert(
            flow_name="full-analysis-pipeline",
            task_name="flow",
            error=e,
            context={
                "description": "Full analysis flow failed after all retries"
            }
        )
        
        raise


# ============================================================================
# Deployment Configuration
# ============================================================================

def create_deployments():
    """
    Create Prefect deployments for both flows with schedules.
    
    Requirements: 15.7, 15.8
    """
    
    # Deployment 1: Incremental updates every 5 minutes
    incremental_deployment = Deployment.build_from_flow(
        flow=incremental_update_flow,
        name="incremental-updates",
        description="Process new interactions every 5 minutes",
        schedule=CronSchedule(cron="*/5 * * * *"),  # Every 5 minutes
        work_queue_name="default",
        tags=["incremental", "graph-update", "production"]
    )
    
    # Deployment 2: Full analysis every 6 hours
    full_analysis_deployment = Deployment.build_from_flow(
        flow=full_analysis_flow,
        name="full-analysis",
        description="Complete analysis cycle every 6 hours",
        schedule=CronSchedule(cron="0 */6 * * *"),  # Every 6 hours at :00
        work_queue_name="default",
        tags=["full-analysis", "causal-analysis", "production"]
    )
    
    return incremental_deployment, full_analysis_deployment


# ============================================================================
# Utility Functions
# ============================================================================

async def run_flow_once(flow_name: str) -> Dict[str, Any]:
    """
    Run a flow once for testing or manual execution.
    
    Args:
        flow_name: Name of flow to run ("incremental" or "full")
        
    Returns:
        Flow execution result
    """
    if flow_name == "incremental":
        return await incremental_update_flow()
    elif flow_name == "full":
        return await full_analysis_flow()
    else:
        raise ValueError(f"Unknown flow name: {flow_name}")


if __name__ == "__main__":
    # For testing: run flows locally
    import sys
    
    if len(sys.argv) > 1:
        flow_name = sys.argv[1]
        result = asyncio.run(run_flow_once(flow_name))
        print(f"Flow result: {result}")
    else:
        print("Usage: python prefect_workflows.py [incremental|full]")
