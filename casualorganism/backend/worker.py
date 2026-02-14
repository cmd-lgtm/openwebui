import os
import asyncio
import tempfile
import boto3
import time
from celery import Celery
from backend.core.neo4j_adapter import Neo4jAdapter
from backend.core.causal import CausalEngine
from backend.core.spark_engine import IntelligentCausalEngine, DistributedCausalEngine
from backend.core.graph import OrganizationalGraph
from backend.core.tracing import setup_worker_tracing
from backend.core.sentry_config import setup_sentry
from backend.core.prometheus_metrics import PrometheusMetrics, get_metrics
from prometheus_client import start_http_server, REGISTRY
import json
import pandas as pd
from datetime import datetime

# Setup Sentry error tracking for workers
setup_sentry()

# Initialize Prometheus metrics for workers
worker_metrics = PrometheusMetrics(registry=REGISTRY)

# Start Prometheus metrics HTTP server on port 9090
# Requirements: 18.2 - Expose /metrics endpoint for workers
try:
    start_http_server(9090)
    print("Worker Prometheus metrics server started on port 9090")
except Exception as e:
    print(f"Warning: Could not start Prometheus metrics server: {e}")

# Env Config
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
NEO4J_URL = os.getenv("GRAPH_DB_URL")
NEO4J_USER = os.getenv("GRAPH_DB_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("GRAPH_DB_PASSWORD", "causal_organism")

# S3 Config for exports
S3_ENDPOINT = os.getenv("S3_ENDPOINT")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
S3_BUCKET = os.getenv("S3_BUCKET", "causal-organism-exports")
S3_REGION = os.getenv("S3_REGION", "us-east-1")

celery_app = Celery('worker', broker=REDIS_URL, backend=REDIS_URL)

# Configure Celery Beat for scheduled tasks
from backend.celerybeat_config import beat_config
celery_app.conf.update(beat_config)

# Setup distributed tracing for workers
# This instruments Celery tasks with OpenTelemetry
tracing_config = setup_worker_tracing(service_name="worker-service")

@celery_app.task(bind=True)
def run_causal_analysis(self):
    """
    Run causal analysis using IntelligentCausalEngine.
    The engine automatically selects Pandas (<100K rows) or Spark (>=100K rows).
    """
    print("Task Started: Causal Analysis with IntelligentCausalEngine")
    
    # Record task start
    start_time = time.time()
    worker_metrics.record_queue_dequeue("celery", "causal_analysis")
    
    # Create IntelligentCausalEngine instance
    engine = IntelligentCausalEngine()
    
    # Prepare parameters for data source
    params = {
        "neo4j_uri": NEO4J_URL,
        "neo4j_user": NEO4J_USER,
        "neo4j_password": NEO4J_PASSWORD
    }
    
    try:
        # Use IntelligentCausalEngine to analyze
        # It will automatically determine data size and select appropriate engine
        if NEO4J_URL:
            print(f"Worker: Using IntelligentCausalEngine with Neo4j data source: {NEO4J_URL}")
            # Run async analysis in sync context
            results = asyncio.run(engine.analyze("neo4j", params))
        else:
            # Fallback to local data for development
            print("Worker: Neo4j not found, using local JSON mock with Pandas engine.")
            with open("data/digital_footprint.json", 'r') as f:
                data = json.load(f)
            graph = OrganizationalGraph()
            graph.build(data)
            df = graph.enrich_and_export(output_file=None)
            
            # Use Pandas engine directly for small local data
            pandas_engine = CausalEngine()
            results = pandas_engine.analyze(df)
        
        # Record successful completion
        duration = time.time() - start_time
        worker_metrics.record_worker_task_completion(
            worker_type="celery",
            task_type="causal_analysis",
            status="success",
            duration_seconds=duration
        )
        
        print(f"Task Complete. Results: {results}")
        return results
        
    except Exception as e:
        # Record failure
        duration = time.time() - start_time
        worker_metrics.record_worker_task_completion(
            worker_type="celery",
            task_type="causal_analysis",
            status="failure",
            duration_seconds=duration
        )
        
        print(f"Task Failed: {str(e)}")
        raise
    finally:
        # Clean up Spark session if it was initialized
        if engine.spark_engine:
            engine.spark_engine.stop()


@celery_app.task(bind=True)
def export_employee_metrics(self, export_type: str, params: dict, user_id: str):
    """
    Background task for data export.
    
    Requirements:
    - 11.3: Implement CSV generation
    - 11.4: Add progress updates
    - 11.5: Upload to S3-compatible storage
    - 11.7: Generate signed download URLs (handled by AsyncExportService)
    
    Args:
        export_type: Type of export (e.g., "employee_metrics", "graph_data")
        params: Export parameters
        user_id: User requesting the export
    
    Returns:
        Dict with s3_key, file_size, and row_count
    """
    print(f"Task Started: Export {export_type} for user {user_id}")
    
    # Record task start
    start_time = time.time()
    worker_metrics.record_queue_dequeue("celery", "export")
    worker_metrics.record_export_request(export_type, "started")
    
    try:
        # Update progress: Starting
        self.update_state(state='PROGRESS', meta={'progress': 10, 'status': 'Fetching data'})
        
        # Fetch data based on export type
        if export_type == "employee_metrics":
            df = _fetch_employee_metrics_data(params)
        elif export_type == "graph_data":
            df = _fetch_graph_data(params)
        elif export_type == "interaction_history":
            df = _fetch_interaction_history(params)
        else:
            raise ValueError(f"Unknown export type: {export_type}")
        
        if df.empty:
            raise ValueError("No data found for export")
        
        # Update progress: Data fetched
        self.update_state(state='PROGRESS', meta={'progress': 40, 'status': 'Generating CSV'})
        
        # Add metadata columns
        df['export_timestamp'] = datetime.utcnow().isoformat()
        df['export_type'] = export_type
        df['exported_by'] = user_id
        
        # Write to temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        temp_file_path = temp_file.name
        temp_file.close()
        
        df.to_csv(temp_file_path, index=False)
        file_size = os.path.getsize(temp_file_path)
        row_count = len(df)
        
        # Update progress: CSV generated
        self.update_state(state='PROGRESS', meta={'progress': 70, 'status': 'Uploading to storage'})
        
        # Initialize S3 client
        s3_config = {
            'region_name': S3_REGION
        }
        
        if S3_ENDPOINT:
            s3_config['endpoint_url'] = S3_ENDPOINT
        
        if S3_ACCESS_KEY and S3_SECRET_KEY:
            s3_config['aws_access_key_id'] = S3_ACCESS_KEY
            s3_config['aws_secret_access_key'] = S3_SECRET_KEY
        
        s3_client = boto3.client('s3', **s3_config)
        
        # Upload to S3
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        s3_key = f"exports/{user_id}/{export_type}_{timestamp}_{self.request.id}.csv"
        
        s3_client.upload_file(temp_file_path, S3_BUCKET, s3_key)
        
        # Clean up temp file
        os.remove(temp_file_path)
        
        # Update progress: Complete
        self.update_state(state='PROGRESS', meta={'progress': 100, 'status': 'Complete'})
        
        # Record successful completion
        duration = time.time() - start_time
        worker_metrics.record_worker_task_completion(
            worker_type="celery",
            task_type="export",
            status="success",
            duration_seconds=duration
        )
        worker_metrics.record_export_completion(
            export_type=export_type,
            duration_seconds=duration,
            size_bytes=file_size
        )
        worker_metrics.record_export_request(export_type, "completed")
        
        print(f"Task Complete: Exported {row_count} rows to {s3_key}")
        
        return {
            "s3_key": s3_key,
            "file_size": file_size,
            "row_count": row_count,
            "export_type": export_type
        }
        
    except Exception as e:
        # Record failure
        duration = time.time() - start_time
        worker_metrics.record_worker_task_completion(
            worker_type="celery",
            task_type="export",
            status="failure",
            duration_seconds=duration
        )
        worker_metrics.record_export_request(export_type, "failed")
        
        print(f"Task Failed: {str(e)}")
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise


def _fetch_employee_metrics_data(params: dict) -> pd.DataFrame:
    """
    Fetch employee metrics data from Neo4j.
    
    Args:
        params: Query parameters (filters, date ranges, etc.)
    
    Returns:
        DataFrame with employee metrics
    """
    try:
        if NEO4J_URL:
            # Connect to Neo4j and fetch data
            adapter = Neo4jAdapter(NEO4J_URL, NEO4J_USER, NEO4J_PASSWORD)
            
            # Fetch employee metrics from materialized views
            df = adapter.enrich_and_export(output_file=None)
            
            # Apply filters if provided
            if params.get('team'):
                df = df[df['team'] == params['team']]
            
            if params.get('min_burnout_score'):
                df = df[df.get('burnout_score', 0) >= params['min_burnout_score']]
            
            return df
        else:
            # Fallback to local data for development
            with open("data/digital_footprint.json", 'r') as f:
                data = json.load(f)
            
            graph = OrganizationalGraph()
            graph.build(data)
            df = graph.enrich_and_export(output_file=None)
            
            return df
            
    except Exception as e:
        print(f"Error fetching employee metrics: {e}")
        return pd.DataFrame()


def _fetch_graph_data(params: dict) -> pd.DataFrame:
    """
    Fetch graph structure data from Neo4j.
    
    Args:
        params: Query parameters
    
    Returns:
        DataFrame with graph edges
    """
    try:
        if NEO4J_URL:
            adapter = Neo4jAdapter(NEO4J_URL, NEO4J_USER, NEO4J_PASSWORD)
            
            # Fetch all edges
            query = """
            MATCH (source:Employee)-[r:INTERACTS]->(target:Employee)
            RETURN 
                source.id as source_id,
                source.name as source_name,
                target.id as target_id,
                target.name as target_name,
                r.weight as weight,
                r.last_updated as last_updated
            """
            
            # Execute query and convert to DataFrame
            # Note: This is a simplified version, actual implementation would use the adapter
            edges = []
            # edges = adapter.execute_query(query)
            
            df = pd.DataFrame(edges)
            return df
        else:
            return pd.DataFrame()
            
    except Exception as e:
        print(f"Error fetching graph data: {e}")
        return pd.DataFrame()


def _fetch_interaction_history(params: dict) -> pd.DataFrame:
    """
    Fetch interaction history from TimescaleDB.
    
    Args:
        params: Query parameters (date range, employee filters, etc.)
    
    Returns:
        DataFrame with interaction history
    """
    try:
        # This would query TimescaleDB for historical interaction data
        # For now, return empty DataFrame as TimescaleDB integration is pending
        return pd.DataFrame()
        
    except Exception as e:
        print(f"Error fetching interaction history: {e}")
        return pd.DataFrame()


@celery_app.task
def cleanup_old_exports():
    """
    Scheduled task to delete exports older than 7 days.
    
    Requirements:
    - 11.8: Delete exports older than 7 days
    
    This task should be scheduled with Celery Beat to run daily.
    """
    print("Task Started: Cleanup old exports")
    
    try:
        from datetime import timedelta
        
        # Initialize S3 client
        s3_config = {
            'region_name': S3_REGION
        }
        
        if S3_ENDPOINT:
            s3_config['endpoint_url'] = S3_ENDPOINT
        
        if S3_ACCESS_KEY and S3_SECRET_KEY:
            s3_config['aws_access_key_id'] = S3_ACCESS_KEY
            s3_config['aws_secret_access_key'] = S3_SECRET_KEY
        
        s3_client = boto3.client('s3', **s3_config)
        
        # Calculate cutoff date (7 days ago)
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        
        # List all objects in exports folder
        response = s3_client.list_objects_v2(
            Bucket=S3_BUCKET,
            Prefix="exports/"
        )
        
        deleted_count = 0
        if 'Contents' in response:
            for obj in response['Contents']:
                # Check if object is older than cutoff date
                if obj['LastModified'].replace(tzinfo=None) < cutoff_date:
                    s3_client.delete_object(
                        Bucket=S3_BUCKET,
                        Key=obj['Key']
                    )
                    deleted_count += 1
                    print(f"Deleted old export: {obj['Key']}")
        
        print(f"Task Complete: Deleted {deleted_count} old exports")
        return {"deleted_count": deleted_count}
        
    except Exception as e:
        print(f"Task Failed: {str(e)}")
        raise


@celery_app.task
def timeout_expired_intervention_approvals():
    """
    Scheduled task to timeout pending approvals that exceed 24 hours.
    
    Requirements:
    - 14.7: Timeout pending approvals after 24 hours
    
    This task should be scheduled with Celery Beat to run hourly.
    """
    print("Task Started: Timeout expired intervention approvals")
    
    try:
        from backend.core.connection_pool import (
            TimescaleConnectionPool,
            Neo4jConnectionPool,
            CircuitBreakerRegistry
        )
        from backend.core.safe_action_orchestrator import SafeActionOrchestrator
        
        # Initialize connection pools
        timescale_host = os.getenv("TIMESCALE_HOST", "timescale")
        timescale_port = int(os.getenv("TIMESCALE_PORT", "5432"))
        timescale_db = os.getenv("TIMESCALE_DB", "postgres")
        timescale_user = os.getenv("TIMESCALE_USER", "postgres")
        timescale_password = os.getenv("TIMESCALE_PASSWORD", "password")
        
        timescale_pool = TimescaleConnectionPool(
            host=timescale_host,
            port=timescale_port,
            database=timescale_db,
            user=timescale_user,
            password=timescale_password
        )
        
        neo4j_pool = Neo4jConnectionPool(
            uri=NEO4J_URL,
            user=NEO4J_USER,
            password=NEO4J_PASSWORD,
            pool_size=20
        )
        
        circuit_breaker = CircuitBreakerRegistry()
        
        # Initialize pools
        async def run_timeout():
            await timescale_pool.initialize()
            await neo4j_pool.initialize()
            
            # Create orchestrator
            orchestrator = SafeActionOrchestrator(
                neo4j_pool=neo4j_pool,
                timescale_pool=timescale_pool,
                circuit_breaker=circuit_breaker
            )
            
            # Timeout expired approvals
            count = await orchestrator.timeout_expired_approvals()
            
            # Cleanup
            await timescale_pool.close()
            await neo4j_pool.close()
            
            return count
        
        # Run async function
        count = asyncio.run(run_timeout())
        
        print(f"Task Complete: Timed out {count} expired approvals")
        return {"timed_out_count": count}
        
    except Exception as e:
        print(f"Task Failed: {str(e)}")
        raise


@celery_app.task
def monitor_intervention_outcome(intervention_id: str):
    """
    Monitor the outcome of an executed intervention and trigger automatic rollback if negative.
    
    Requirements:
    - 14.5: Schedule outcome checks after intervention
    - 14.5: Detect negative outcomes
    - 14.5: Trigger automatic rollback
    
    This task is scheduled automatically after intervention execution (typically 7 days later).
    
    Args:
        intervention_id: UUID of the intervention to monitor
    """
    print(f"Task Started: Monitor intervention outcome for {intervention_id}")
    
    try:
        from backend.core.connection_pool import (
            TimescaleConnectionPool,
            Neo4jConnectionPool,
            CircuitBreakerRegistry
        )
        from backend.core.safe_action_orchestrator import SafeActionOrchestrator
        
        # Initialize connection pools
        timescale_host = os.getenv("TIMESCALE_HOST", "timescale")
        timescale_port = int(os.getenv("TIMESCALE_PORT", "5432"))
        timescale_db = os.getenv("TIMESCALE_DB", "postgres")
        timescale_user = os.getenv("TIMESCALE_USER", "postgres")
        timescale_password = os.getenv("TIMESCALE_PASSWORD", "password")
        
        timescale_pool = TimescaleConnectionPool(
            host=timescale_host,
            port=timescale_port,
            database=timescale_db,
            user=timescale_user,
            password=timescale_password
        )
        
        neo4j_pool = Neo4jConnectionPool(
            uri=NEO4J_URL,
            user=NEO4J_USER,
            password=NEO4J_PASSWORD,
            pool_size=20
        )
        
        circuit_breaker = CircuitBreakerRegistry()
        
        # Initialize pools and check outcome
        async def run_outcome_check():
            await timescale_pool.initialize()
            await neo4j_pool.initialize()
            
            # Create orchestrator
            orchestrator = SafeActionOrchestrator(
                neo4j_pool=neo4j_pool,
                timescale_pool=timescale_pool,
                circuit_breaker=circuit_breaker
            )
            
            # Check intervention outcome
            outcome = await orchestrator.check_intervention_outcome(intervention_id)
            
            # Cleanup
            await timescale_pool.close()
            await neo4j_pool.close()
            
            return outcome
        
        # Run async function
        outcome = asyncio.run(run_outcome_check())
        
        if outcome.get("auto_rollback_triggered"):
            print(f"Task Complete: Negative outcome detected, automatic rollback triggered for {intervention_id}")
        else:
            print(f"Task Complete: Outcome check completed for {intervention_id}, no rollback needed")
        
        return outcome
        
    except Exception as e:
        print(f"Task Failed: {str(e)}")
        raise
