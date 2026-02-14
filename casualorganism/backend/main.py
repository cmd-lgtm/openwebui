from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi import Request, status, HTTPException
from fastapi.exceptions import RequestValidationError
from backend.core.graph import OrganizationalGraph
from backend.core.neo4j_adapter import Neo4jAdapter
from backend.core.causal import CausalEngine
from backend.core.materialized_views import MaterializedViewManager
from backend.core.async_export import AsyncExportService
from backend.core.connection_pool import (
    TimescaleConnectionPool,
    Neo4jConnectionPool,
    CircuitBreakerRegistry
)
from backend.core.timescale_queries import TimescaleQueryService
from backend.core.safe_action_orchestrator import SafeActionOrchestrator
from backend.core.tracing import setup_api_tracing
from backend.core.sentry_config import setup_sentry, set_request_context, add_breadcrumb
from backend.core.prometheus_metrics import setup_api_metrics, get_metrics, initialize_metrics
from backend.core.rate_limiter import RateLimiter
from backend.core.rate_limit_middleware import RateLimitMiddleware
from backend.core.request_validation import RequestValidationMiddleware, sanitize_path_parameter
from backend.api.endpoints import interventions, auth
from backend.core.websocket_handler import websocket_router, http_router, start_pubsub_listener
from backend.core.auth import get_current_user, require_permission, TokenData
from backend.api.models.requests import (
    CausalAnalysisRequest,
    ExportRequest,
    TrendQueryRequest,
    AlertQueryRequest,
    StatisticsQueryRequest,
)
from backend.worker import celery_app
import json
import os
from datetime import datetime, timedelta
from typing import Optional
import sentry_sdk

app = FastAPI(title="Causal Organism API", version="1.0")

# Setup Sentry error tracking BEFORE including routers
# This ensures all errors are captured
setup_sentry()

# Include authentication endpoints (no auth required for these)
app.include_router(auth.router)

# Include intervention endpoints
app.include_router(interventions.router)

# Include WebSocket endpoints
app.include_router(websocket_router)
app.include_router(ws_http_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request validation middleware
# Requirements:
# - 21.7: Limit request body size to 10MB
app.add_middleware(RequestValidationMiddleware)

class AppState:
    """State container with dependency injection - no global state in process memory"""
    
    def __init__(self):
        self.graph = None
        self.metrics_df = None
        self.causal_weights = None
        self.graph_ready = False
        self.materialized_view_manager = None
        self.export_service = None
        self.timescale_pool = None
        self.timescale_query_service = None
        self.neo4j_pool = None
        self.circuit_breaker = None
        self.action_orchestrator = None
        self.tracing_config = None
        self.prometheus_metrics = None
        self.instrumentator = None
        self.rate_limiter = None


state = AppState()

# Initialize Prometheus metrics
# This must be done before setting up tracing and instrumenting the app
state.prometheus_metrics = initialize_metrics()

# Setup distributed tracing
# This must be done before any requests are handled
state.tracing_config = setup_api_tracing(app, service_name="api-service")

# Setup Prometheus instrumentation
# This must be done after app is created but before routes are added
state.instrumentator = setup_api_metrics(app, state.prometheus_metrics)

# Initialize rate limiter
# This will be initialized in startup_event after Redis is available
# Middleware will be added after initialization


# Exception handlers for enriched error reporting
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handler for HTTP exceptions including authentication and authorization errors.
    
    Requirements:
    - 19.5: Return HTTP 403 when user lacks required role
    - 19.6: Return HTTP 401 when authentication fails
    - 19.8: Log all authentication and authorization failures
    """
    # Log authentication and authorization failures
    if exc.status_code == 401:
        with sentry_sdk.push_scope() as scope:
            scope.set_context("auth_error", {
                "type": "authentication_failure",
                "endpoint": request.url.path,
                "method": request.method,
                "detail": exc.detail
            })
            scope.set_tag("error_type", "authentication")
            
            sentry_sdk.capture_message(
                f"Authentication failed: {request.method} {request.url.path} - {exc.detail}",
                level="warning"
            )
    
    elif exc.status_code == 403:
        with sentry_sdk.push_scope() as scope:
            scope.set_context("auth_error", {
                "type": "authorization_failure",
                "endpoint": request.url.path,
                "method": request.method,
                "detail": exc.detail
            })
            scope.set_tag("error_type", "authorization")
            
            sentry_sdk.capture_message(
                f"Authorization failed: {request.method} {request.url.path} - {exc.detail}",
                level="warning"
            )
    
    # Return appropriate error response
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler that captures all unhandled exceptions.
    
    Requirements:
    - 17.1: Send all unhandled exceptions to error tracking service
    - 17.4: Include stack traces
    """
    # Sentry will automatically capture this exception due to FastAPI integration
    # But we add extra context here
    with sentry_sdk.push_scope() as scope:
        scope.set_context("error_details", {
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "endpoint": request.url.path,
            "method": request.method
        })
        
        # Capture the exception
        sentry_sdk.capture_exception(exc)
    
    # Return error response
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "type": type(exc).__name__
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handler for request validation errors.
    
    Requirements:
    - 17.4: Include request context in errors
    - 21.3: Return HTTP 422 with detailed error messages
    - 21.8: Return validation errors in consistent JSON format
    """
    # Log validation errors to Sentry as messages (not exceptions)
    with sentry_sdk.push_scope() as scope:
        scope.set_context("validation_error", {
            "errors": exc.errors(),
            "body": str(exc.body) if hasattr(exc, 'body') else None
        })
        scope.set_tag("error_type", "validation")
        
        sentry_sdk.capture_message(
            f"Request validation failed: {request.url.path}",
            level="warning"
        )
    
    # Format errors in a consistent, user-friendly way
    errors = []
    for error in exc.errors():
        error_detail = {
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        }
        
        # Add input value if available (for debugging)
        if "input" in error:
            error_detail["input"] = str(error["input"])[:100]  # Limit to 100 chars
        
        errors.append(error_detail)
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "message": "Request validation failed. Please check the errors below.",
            "errors": errors,
            "path": str(request.url.path)
        }
    )

@app.get("/")
def health_check():
    """Legacy health check endpoint - redirects to liveness probe"""
    return {"status": "ok", "system": "Causal Organism"}


@app.get("/health/live")
def liveness_probe():
    """
    Liveness probe endpoint for Kubernetes.
    
    Simple check that the process is running and responding to requests.
    Returns 200 if the process is alive.
    
    Requirements:
    - 23.1: Liveness probe endpoint
    - 23.3: Return 200 if alive
    """
    return {
        "status": "alive",
        "service": "api-service",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health/ready")
async def readiness_probe():
    """
    Readiness probe endpoint for Kubernetes.
    
    Checks connectivity to all critical dependencies:
    - Neo4j (Graph Store)
    - Redis (Cache and Queue)
    - TimescaleDB (Metrics Store)
    
    Returns 200 if ready to handle requests, 503 if not ready.
    
    Requirements:
    - 23.2: Readiness probe endpoint
    - 23.4: Return 200 if ready, 503 if not
    - 23.5: Return 503 when dependencies unavailable
    - 23.6: Check Neo4j connectivity
    - 23.7: Check Redis connectivity
    - 23.8: Check TimescaleDB connectivity
    """
    checks = {
        "neo4j": {"status": "unknown", "healthy": False},
        "redis": {"status": "unknown", "healthy": False},
        "timescale": {"status": "unknown", "healthy": False}
    }
    
    all_healthy = True
    
    # Check Neo4j connectivity
    if state.neo4j_pool:
        try:
            neo4j_healthy = await state.neo4j_pool.health_check()
            checks["neo4j"]["healthy"] = neo4j_healthy
            checks["neo4j"]["status"] = "healthy" if neo4j_healthy else "unhealthy"
            if not neo4j_healthy:
                all_healthy = False
        except Exception as e:
            checks["neo4j"]["status"] = f"error: {str(e)}"
            checks["neo4j"]["healthy"] = False
            all_healthy = False
    else:
        checks["neo4j"]["status"] = "not_initialized"
        checks["neo4j"]["healthy"] = False
        all_healthy = False
    
    # Check Redis connectivity (via rate limiter)
    if state.rate_limiter and state.rate_limiter.client:
        try:
            # Use sync ping since redis-py client is synchronous
            redis_healthy = state.rate_limiter.client.ping()
            checks["redis"]["healthy"] = redis_healthy
            checks["redis"]["status"] = "healthy" if redis_healthy else "unhealthy"
            if not redis_healthy:
                all_healthy = False
        except Exception as e:
            checks["redis"]["status"] = f"error: {str(e)}"
            checks["redis"]["healthy"] = False
            all_healthy = False
    else:
        checks["redis"]["status"] = "not_initialized"
        checks["redis"]["healthy"] = False
        all_healthy = False
    
    # Check TimescaleDB connectivity
    if state.timescale_pool:
        try:
            timescale_healthy = await state.timescale_pool.health_check()
            checks["timescale"]["healthy"] = timescale_healthy
            checks["timescale"]["status"] = "healthy" if timescale_healthy else "unhealthy"
            if not timescale_healthy:
                all_healthy = False
        except Exception as e:
            checks["timescale"]["status"] = f"error: {str(e)}"
            checks["timescale"]["healthy"] = False
            all_healthy = False
    else:
        checks["timescale"]["status"] = "not_initialized"
        checks["timescale"]["healthy"] = False
        all_healthy = False
    
    response_data = {
        "status": "ready" if all_healthy else "not_ready",
        "service": "api-service",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks
    }
    
    if all_healthy:
        return response_data
    else:
        return JSONResponse(
            status_code=503,
            content=response_data
        )

# Middleware to add trace ID to response headers
@app.middleware("http")
async def add_trace_id_header(request, call_next):
    """
    Add trace ID to response headers for request correlation.
    
    Requirements:
    - 16.3: Add trace ID to response headers
    """
    response = await call_next(request)
    
    if state.tracing_config:
        trace_id = state.tracing_config.get_current_trace_id()
        if trace_id:
            response.headers["X-Trace-Id"] = trace_id
    
    return response


# Middleware to enrich Sentry context with request information
@app.middleware("http")
async def enrich_sentry_context(request, call_next):
    """
    Enrich Sentry error context with request information.
    
    Requirements:
    - 17.4: Include request context in errors
    - 17.4: Include user context in errors
    - 19.8: Log all authentication and authorization failures
    """
    # Set request context for Sentry
    with sentry_sdk.push_scope() as scope:
        # Add request information
        scope.set_context("request", {
            "url": str(request.url),
            "method": request.method,
            "headers": dict(request.headers),
            "query_params": dict(request.query_params)
        })
        
        # Add user context if available (from auth headers)
        user_id = request.headers.get("X-User-Id")
        if user_id:
            scope.set_user({
                "id": user_id,
                "ip_address": request.client.host if request.client else None
            })
        
        # Add tags for better grouping
        scope.set_tag("endpoint", request.url.path)
        scope.set_tag("method", request.method)
        
        # Add breadcrumb for request
        add_breadcrumb(
            message=f"{request.method} {request.url.path}",
            category="request",
            level="info",
            data={
                "url": str(request.url),
                "method": request.method
            }
        )
        
        try:
            response = await call_next(request)
            
            # Add response status to context
            scope.set_context("response", {
                "status_code": response.status_code
            })
            
            # Log authentication and authorization failures to Sentry
            if response.status_code == 401:
                sentry_sdk.capture_message(
                    f"Authentication failed: {request.method} {request.url.path}",
                    level="warning"
                )
            elif response.status_code == 403:
                sentry_sdk.capture_message(
                    f"Authorization failed: {request.method} {request.url.path}",
                    level="warning"
                )
            
            return response
        except Exception as e:
            # Capture exception
            sentry_sdk.capture_exception(e)
            raise

@app.on_event("startup")
async def startup_event():
    # Initialize rate limiter
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    state.rate_limiter = RateLimiter(redis_url=redis_url)
    
    if await state.rate_limiter.initialize():
        print("Rate limiter initialized")
        
        # Add rate limiting middleware
        app.add_middleware(
            RateLimitMiddleware,
            rate_limiter=state.rate_limiter,
            prometheus_metrics=state.prometheus_metrics
        )
        print("Rate limiting middleware added")
    else:
        print("Warning: Rate limiter initialization failed - rate limiting disabled")
    
    # Initialize TimescaleDB connection pool
    timescale_host = os.getenv("TIMESCALE_HOST", "timescale")
    timescale_port = int(os.getenv("TIMESCALE_PORT", "5432"))
    timescale_db = os.getenv("TIMESCALE_DB", "postgres")
    timescale_user = os.getenv("TIMESCALE_USER", "postgres")
    timescale_password = os.getenv("TIMESCALE_PASSWORD", "password")
    
    state.timescale_pool = TimescaleConnectionPool(
        host=timescale_host,
        port=timescale_port,
        database=timescale_db,
        user=timescale_user,
        password=timescale_password
    )
    
    if await state.timescale_pool.initialize():
        print("TimescaleDB connection pool initialized")
        
        # Initialize schema
        from backend.core.timescale_schema import TimescaleSchemaManager
        schema_manager = TimescaleSchemaManager(state.timescale_pool.pool)
        await schema_manager.create_schema()
        print("TimescaleDB schema initialized")
        
        # Initialize query service
        state.timescale_query_service = TimescaleQueryService(state.timescale_pool.pool)
        
        # Update Prometheus metrics for TimescaleDB pool
        if state.prometheus_metrics:
            pool_stats = state.timescale_pool.get_pool_stats()
            state.prometheus_metrics.update_connection_pool_metrics(
                pool_name="timescale",
                database_type="postgresql",
                active=pool_stats.get("active", 0),
                idle=pool_stats.get("idle", 0),
                waiting=pool_stats.get("waiting", 0),
                max_connections=pool_stats.get("max_size", 20)
            )
    else:
        print("Warning: TimescaleDB connection pool initialization failed")
    
    # Initialize Neo4j connection pool (for orchestrator)
    neo4j_url = os.getenv("GRAPH_DB_URL")
    if neo4j_url:
        neo4j_user = os.getenv("GRAPH_DB_USER", "neo4j")
        neo4j_password = os.getenv("GRAPH_DB_PASSWORD", "causal_organism")
        
        state.neo4j_pool = Neo4jConnectionPool(
            uri=neo4j_url,
            user=neo4j_user,
            password=neo4j_password,
            pool_size=20
        )
        
        if await state.neo4j_pool.initialize():
            print("Neo4j connection pool initialized")
            
            # Update Prometheus metrics for Neo4j pool
            if state.prometheus_metrics:
                pool_stats = state.neo4j_pool.get_pool_stats()
                state.prometheus_metrics.update_connection_pool_metrics(
                    pool_name="neo4j",
                    database_type="neo4j",
                    active=pool_stats.get("active", 0),
                    idle=pool_stats.get("idle", 0),
                    waiting=pool_stats.get("waiting", 0),
                    max_connections=pool_stats.get("max_size", 20)
                )
        else:
            print("Warning: Neo4j connection pool initialization failed")
    
    # Initialize circuit breaker registry
    state.circuit_breaker = CircuitBreakerRegistry()
    
    # Initialize SafeActionOrchestrator
    if state.neo4j_pool and state.timescale_pool and state.circuit_breaker:
        state.action_orchestrator = SafeActionOrchestrator(
            neo4j_pool=state.neo4j_pool,
            timescale_pool=state.timescale_pool,
            circuit_breaker=state.circuit_breaker
        )
        # Set the orchestrator in the interventions module
        interventions.set_orchestrator(state.action_orchestrator)
        print("SafeActionOrchestrator initialized")
    else:
        print("Warning: SafeActionOrchestrator not initialized - missing dependencies")
    
    # Initialize AsyncExportService
    state.export_service = AsyncExportService(
        celery_app=celery_app,
        s3_endpoint=os.getenv("S3_ENDPOINT"),
        s3_access_key=os.getenv("S3_ACCESS_KEY"),
        s3_secret_key=os.getenv("S3_SECRET_KEY"),
        s3_bucket=os.getenv("S3_BUCKET", "causal-organism-exports"),
        s3_region=os.getenv("S3_REGION", "us-east-1")
    )
    
    # Load initial mock data if available
    try:
        with open("data/digital_footprint.json", 'r') as f:
            data = json.load(f)
            
        neo4j_url = os.getenv("GRAPH_DB_URL")
        if neo4j_url:
            print(f"Connecting to Neo4j at {neo4j_url}...")
            user = os.getenv("GRAPH_DB_USER", "neo4j")
            pw = os.getenv("GRAPH_DB_PASSWORD", "causal_organism")
            state.graph = Neo4jAdapter(neo4j_url, user, pw)
            # In production, we might skip full build on restart, but for POC we build on start
            state.graph.build(data) 
            
            # Initialize materialized view manager for graph metrics
            state.materialized_view_manager = MaterializedViewManager(state.graph)
            await state.materialized_view_manager.initialize()
            
            # Create materialized views if not exist
            await state.materialized_view_manager.create_degree_centrality_view()
            await state.materialized_view_manager.create_betweenness_centrality_view()
            await state.materialized_view_manager.create_clustering_coefficient_view()
        else:
            print("Using In-Memory NetworkX Graph (POC Mode)")
            state.graph = OrganizationalGraph()
            state.graph.build(data)
            
        state.metrics_df = state.graph.enrich_and_export(output_file=None)
        state.graph_ready = True
        print("Initial graph loaded.")
        
        # Update graph metrics
        if state.prometheus_metrics and state.graph:
            stats = state.graph.get_stats()
            if stats:
                state.prometheus_metrics.update_graph_metrics(
                    node_count=stats.get("nodes", 0),
                    edge_count=stats.get("edges", 0)
                )
    except Exception as e:
        print(f"Startup warning: {e}")
    
    # Start background task to update metrics periodically
    import asyncio
    asyncio.create_task(update_metrics_periodically())


@app.on_event("shutdown")
async def shutdown_event():
    """
    Shutdown event handler to clean up resources.
    
    Requirements:
    - 16.6: Properly flush traces before shutdown
    """
    # Shutdown tracing
    if state.tracing_config:
        state.tracing_config.shutdown()
        print("Tracing shutdown complete")
    
    # Close rate limiter
    if state.rate_limiter:
        await state.rate_limiter.close()
        print("Rate limiter closed")
    
    # Close connection pools
    if state.timescale_pool:
        await state.timescale_pool.close()
        print("TimescaleDB connection pool closed")
    
    if state.neo4j_pool:
        await state.neo4j_pool.close()
        print("Neo4j connection pool closed")


async def update_metrics_periodically():
    """
    Background task to update Prometheus metrics periodically.
    
    Requirements:
    - 18.4: Collect metrics for database connection pool utilization
    - 18.5: Collect metrics for cache hit rate
    - 18.6: Collect metrics for queue depth
    """
    import asyncio
    
    while True:
        try:
            # Update connection pool metrics
            if state.prometheus_metrics:
                if state.timescale_pool:
                    pool_stats = state.timescale_pool.get_pool_stats()
                    state.prometheus_metrics.update_connection_pool_metrics(
                        pool_name="timescale",
                        database_type="postgresql",
                        active=pool_stats.get("active", 0),
                        idle=pool_stats.get("idle", 0),
                        waiting=pool_stats.get("waiting", 0),
                        max_connections=pool_stats.get("max_size", 20)
                    )
                
                if state.neo4j_pool:
                    pool_stats = state.neo4j_pool.get_pool_stats()
                    state.prometheus_metrics.update_connection_pool_metrics(
                        pool_name="neo4j",
                        database_type="neo4j",
                        active=pool_stats.get("active", 0),
                        idle=pool_stats.get("idle", 0),
                        waiting=pool_stats.get("waiting", 0),
                        max_connections=pool_stats.get("max_size", 20)
                    )
                
                # Update circuit breaker metrics
                if state.circuit_breaker:
                    for service_name, breaker in state.circuit_breaker.breakers.items():
                        state.prometheus_metrics.update_circuit_breaker_state(
                            service_name=service_name,
                            state=breaker.state
                        )
        except Exception as e:
            print(f"Error updating metrics: {e}")
        
        # Update every 15 seconds
        await asyncio.sleep(15)

@app.get("/api/graph/stats")
def get_graph_stats(current_user: TokenData = Depends(require_permission("read:graph"))):
    """
    Get graph statistics.
    
    Requirements:
    - 19.1: Require valid JWT token
    - 19.4: Enforce role-based access control
    
    Args:
        current_user: Authenticated user with read:graph permission
    
    Returns:
        Graph statistics
    """
    if not state.graph:
        return {"error": "Graph not loaded"}
    
    stats = state.graph.get_stats()
    
    # Update Prometheus metrics
    if state.prometheus_metrics and stats:
        state.prometheus_metrics.update_graph_metrics(
            node_count=stats.get("nodes", 0),
            edge_count=stats.get("edges", 0)
        )
    
    return stats

@app.get("/api/graph/employee_metrics")
def get_employee_metrics(current_user: TokenData = Depends(require_permission("read:metrics"))):
    """
    Fetch all employee metrics from materialized views.
    No on-demand centrality calculations - reads pre-computed values.
    
    Requirements:
    - 19.1: Require valid JWT token
    - 19.4: Enforce role-based access control
    
    Args:
        current_user: Authenticated user with read:metrics permission
    
    Returns:
        List of employee metrics
    """
    if not state.graph:
        return {"error": "Graph not loaded"}
    
    try:
        # Use Neo4jAdapter's enrich_and_export which reads from materialized views
        df = state.graph.enrich_and_export(output_file=None)
        return df.to_dict(orient="records")
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/graph/employee_metrics/{employee_id}")
async def get_employee_metrics_by_id(
    employee_id: str,
    current_user: TokenData = Depends(require_permission("read:metrics"))
):
    """
    Fetch metrics for a specific employee from materialized views.
    No on-demand centrality calculations - reads pre-computed values.
    
    Requirements:
    - 19.1: Require valid JWT token
    - 19.4: Enforce role-based access control
    - 21.6: Sanitize string inputs to prevent injection attacks
    
    Args:
        employee_id: Employee identifier
        current_user: Authenticated user with read:metrics permission
    
    Returns:
        Employee metrics
    """
    # Sanitize path parameter
    employee_id = sanitize_path_parameter(employee_id)
    
    if not state.graph:
        return {"error": "Graph not loaded"}
    
    if not state.materialized_view_manager:
        return {"error": "Materialized view manager not initialized"}
    
    try:
        metrics = await state.materialized_view_manager.get_employee_metrics(employee_id)
        if metrics:
            return metrics
        return {"error": "Employee not found"}
    except Exception as e:
        return {"error": str(e)}

from backend.worker import run_causal_analysis
from celery.result import AsyncResult

@app.post("/api/causal/analyze")
def trigger_causal_analysis(
    request: CausalAnalysisRequest,
    current_user: TokenData = Depends(require_permission("write:metrics"))
):
    """
    Triggers the analysis asynchronously. Returns a Task ID.
    
    Requirements:
    - 19.1: Require valid JWT token
    - 19.4: Enforce role-based access control
    - 21.1: Define Pydantic models for all request bodies
    - 21.2: Validate request bodies against Pydantic models
    
    Args:
        request: Validated causal analysis request
        current_user: Authenticated user with write:metrics permission
    
    Returns:
        Task ID and status
    """
    task = run_causal_analysis.delay()
    return {"task_id": task.id, "status": "Processing involved..."}

@app.get("/api/tasks/{task_id}")
def get_task_status(task_id: str, current_user: TokenData = Depends(get_current_user)):
    """
    Get status of an asynchronous task.
    
    Requirements:
    - 19.1: Require valid JWT token
    
    Args:
        task_id: Celery task ID
        current_user: Authenticated user
    
    Returns:
        Task status and result
    """
    task_result = AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result if task_result.ready() else None
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


# Export Service Endpoints

@app.post("/api/exports/request")
async def request_export(
    request: ExportRequest,
    current_user: TokenData = Depends(require_permission("write:exports"))
):
    """
    Request an asynchronous data export.
    
    Requirements:
    - 11.1: Queue export task to Worker_Pool
    - 11.2: Return task ID and status URL within 500ms
    - 19.1: Require valid JWT token
    - 19.4: Enforce role-based access control
    - 21.1: Define Pydantic models for all request bodies
    - 21.2: Validate request bodies against Pydantic models
    
    Args:
        request: Validated export request
        current_user: Authenticated user with write:exports permission
    
    Returns:
        Dict with task_id, status_url, and status
    """
    if not state.export_service:
        return {"error": "Export service not initialized"}
    
    try:
        # Use authenticated user's ID
        actual_user_id = current_user.user_id or "default_user"
        
        result = await state.export_service.request_export(
            export_type=request.export_type,
            params={
                "format": request.format,
                "filters": request.filters or {},
                "date_range": request.date_range,
                "include_fields": request.include_fields,
            },
            user_id=actual_user_id
        )
        return result
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/exports/{task_id}/status")
async def get_export_status(
    task_id: str,
    current_user: TokenData = Depends(require_permission("read:exports"))
):
    """
    Check the status of an export task.
    
    Requirements:
    - 11.2: Provide endpoint to check export task status
    - 11.7: Generate signed URL valid for 24 hours
    - 19.1: Require valid JWT token
    - 19.4: Enforce role-based access control
    
    Args:
        task_id: Celery task ID
        current_user: Authenticated user with read:exports permission
    
    Returns:
        Dict with status, progress, download_url (if completed), error (if failed)
    """
    if not state.export_service:
        return {"error": "Export service not initialized"}
    
    try:
        result = await state.export_service.get_export_status(task_id)
        return result
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/exports/user/{user_id}")
async def list_user_exports(user_id: str, limit: int = 10):
    """
    List recent exports for a user.
    
    Args:
        user_id: User ID
        limit: Maximum number of exports to return
    
    Returns:
        List of export metadata with download URLs
    """
    if not state.export_service:
        return {"error": "Export service not initialized"}
    
    try:
        exports = await state.export_service.list_user_exports(user_id, limit)
        return {"exports": exports}
    except Exception as e:
        return {"error": str(e)}


@app.delete("/api/exports/{s3_key:path}")
async def delete_export(s3_key: str):
    """
    Delete an export file.
    
    Args:
        s3_key: S3 object key (path parameter)
    
    Returns:
        Success status
    """
    if not state.export_service:
        return {"error": "Export service not initialized"}
    
    try:
        success = await state.export_service.delete_export(s3_key)
        if success:
            return {"status": "deleted", "key": s3_key}
        else:
            return {"error": "Failed to delete export"}
    except Exception as e:
        return {"error": str(e)}


# Historical Trend Query Endpoints

@app.get("/api/trends/employee/{employee_id}")
async def get_employee_trend(
    employee_id: str,
    days: int = Query(default=90, ge=1, le=730),
    use_hourly: bool = Query(default=False),
    current_user: TokenData = Depends(require_permission("read:trends"))
):
    """
    Get historical trend data for a specific employee.
    
    Requirements:
    - 12.6: Query TimescaleDB for time-series data with date range filtering
    - 12.7: Return 90-day trend data within 1 second
    - 19.1: Require valid JWT token
    - 19.4: Enforce role-based access control
    - 21.6: Sanitize string inputs to prevent injection attacks
    
    Args:
        employee_id: Employee identifier
        days: Number of days to look back (1-730)
        use_hourly: Use hourly aggregates for faster queries on long ranges
        current_user: Authenticated user with read:trends permission
    
    Returns:
        List of metric records with timestamps
    """
    # Sanitize path parameter
    employee_id = sanitize_path_parameter(employee_id)
    
    if not state.timescale_query_service:
        return {"error": "TimescaleDB query service not initialized"}
    
    try:
        if use_hourly:
            data = await state.timescale_query_service.get_employee_hourly_trend(
                employee_id=employee_id,
                days=days
            )
        else:
            data = await state.timescale_query_service.get_employee_trend(
                employee_id=employee_id,
                days=days
            )
        
        return {
            "employee_id": employee_id,
            "days": days,
            "data_points": len(data),
            "data": data
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/trends/employee/{employee_id}/range")
async def get_employee_trend_range(
    employee_id: str,
    start_date: str = Query(..., description="Start date in ISO format (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date in ISO format (YYYY-MM-DD)"),
    use_hourly: bool = Query(default=False)
):
    """
    Get historical trend data for a specific employee with custom date range.
    
    Requirements:
    - 12.6: Query TimescaleDB for time-series data with date range filtering
    
    Args:
        employee_id: Employee identifier
        start_date: Start date in ISO format
        end_date: End date in ISO format
        use_hourly: Use hourly aggregates for faster queries
    
    Returns:
        List of metric records with timestamps
    """
    if not state.timescale_query_service:
        return {"error": "TimescaleDB query service not initialized"}
    
    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        
        if use_hourly:
            data = await state.timescale_query_service.get_employee_hourly_trend(
                employee_id=employee_id,
                start_date=start,
                end_date=end
            )
        else:
            data = await state.timescale_query_service.get_employee_trend(
                employee_id=employee_id,
                start_date=start,
                end_date=end
            )
        
        return {
            "employee_id": employee_id,
            "start_date": start_date,
            "end_date": end_date,
            "data_points": len(data),
            "data": data
        }
    except ValueError as e:
        return {"error": f"Invalid date format: {e}"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/trends/team/{team_name}")
async def get_team_trend(
    team_name: str,
    days: int = Query(default=90, ge=1, le=730)
):
    """
    Get aggregated trend data for all employees in a team.
    
    Requirements:
    - 12.6: Query TimescaleDB for time-series data
    
    Args:
        team_name: Team name
        days: Number of days to look back (1-730)
    
    Returns:
        List of aggregated metric records by day
    """
    if not state.timescale_query_service:
        return {"error": "TimescaleDB query service not initialized"}
    
    try:
        data = await state.timescale_query_service.get_team_trend(
            team_name=team_name,
            days=days
        )
        
        return {
            "team": team_name,
            "days": days,
            "data_points": len(data),
            "data": data
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/trends/burnout-alerts")
async def get_burnout_alerts(
    threshold: float = Query(default=70.0, ge=0.0, le=100.0),
    days: int = Query(default=7, ge=1, le=90)
):
    """
    Get employees with burnout scores above threshold.
    
    Requirements:
    - 12.6: Query TimescaleDB for time-series data
    
    Args:
        threshold: Burnout score threshold (0-100)
        days: Number of days to look back (1-90)
    
    Returns:
        List of employees with high burnout scores
    """
    if not state.timescale_query_service:
        return {"error": "TimescaleDB query service not initialized"}
    
    try:
        data = await state.timescale_query_service.get_burnout_alerts(
            threshold=threshold,
            days=days
        )
        
        return {
            "threshold": threshold,
            "days": days,
            "alert_count": len(data),
            "alerts": data
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/trends/statistics/{metric_name}")
async def get_metric_statistics(
    metric_name: str,
    days: int = Query(default=30, ge=1, le=365)
):
    """
    Get statistical summary for a specific metric.
    
    Requirements:
    - 12.6: Query TimescaleDB for time-series data
    - 21.6: Sanitize string inputs to prevent injection attacks
    
    Args:
        metric_name: Metric name (degree_centrality, betweenness_centrality,
                    clustering_coeff, burnout_score)
        days: Number of days to look back (1-365)
    
    Returns:
        Dictionary with min, max, avg, stddev statistics
    """
    # Sanitize path parameter
    metric_name = sanitize_path_parameter(metric_name)
    
    if not state.timescale_query_service:
        return {"error": "TimescaleDB query service not initialized"}
    
    try:
        stats = await state.timescale_query_service.get_metric_statistics(
            metric_name=metric_name,
            days=days
        )
        
        if not stats:
            return {"error": f"Invalid metric name or no data available"}
        
        return {
            "metric": metric_name,
            "days": days,
            "statistics": stats
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/trends/health")
async def get_trends_health():
    """
    Get health status of TimescaleDB metrics storage.
    
    Returns:
        Health status and recent metrics count
    """
    if not state.timescale_query_service:
        return {"error": "TimescaleDB query service not initialized"}
    
    try:
        recent_count = await state.timescale_query_service.get_recent_metrics_count(hours=24)
        
        return {
            "status": "healthy",
            "timescale_connected": state.timescale_pool is not None,
            "recent_metrics_24h": recent_count
        }
    except Exception as e:
        return {"error": str(e)}


# Sentry Error Statistics Endpoints

@app.get("/api/errors/statistics")
async def get_error_statistics(
    stat: str = Query(default="received", description="Statistic type (received, rejected)"),
    since: str = Query(default="1d", description="Time range (1h, 1d, 1w, 30d)"),
    resolution: str = Query(default="1h", description="Data resolution (1h, 1d)")
):
    """
    Get error statistics from Sentry.
    
    Requirements:
    - 17.8: Expose API for querying error statistics
    
    Args:
        stat: Statistic type (received, rejected, blacklisted)
        since: Time range (1h, 1d, 1w, 30d)
        resolution: Data resolution (1h, 1d)
    
    Returns:
        Error statistics over time
    """
    from backend.sentry_alerts import SentryAlertManager
    
    try:
        manager = SentryAlertManager()
        stats = manager.get_error_statistics(stat=stat, since=since, resolution=resolution)
        
        if stats is None:
            return {
                "error": "Failed to fetch error statistics",
                "message": "Check SENTRY_AUTH_TOKEN, SENTRY_ORG, and SENTRY_PROJECT configuration"
            }
        
        return {
            "stat": stat,
            "since": since,
            "resolution": resolution,
            "data": stats
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/errors/recent")
async def get_recent_errors(
    limit: int = Query(default=25, ge=1, le=100, description="Maximum number of issues"),
    query: Optional[str] = Query(default=None, description="Search query (e.g., 'is:unresolved')")
):
    """
    Get recent error issues from Sentry.
    
    Requirements:
    - 17.8: Expose API for querying error statistics
    
    Args:
        limit: Maximum number of issues to return (1-100)
        query: Search query (e.g., "is:unresolved", "is:unresolved level:error")
    
    Returns:
        List of recent error issues
    """
    from backend.sentry_alerts import SentryAlertManager
    
    try:
        manager = SentryAlertManager()
        issues = manager.get_recent_issues(limit=limit, query=query)
        
        if issues is None:
            return {
                "error": "Failed to fetch recent issues",
                "message": "Check SENTRY_AUTH_TOKEN, SENTRY_ORG, and SENTRY_PROJECT configuration"
            }
        
        return {
            "count": len(issues),
            "limit": limit,
            "query": query,
            "issues": issues
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/errors/alerts")
async def get_alert_rules():
    """
    Get configured Sentry alert rules.
    
    Requirements:
    - 17.8: Expose API for querying error statistics
    
    Returns:
        List of configured alert rules
    """
    from backend.sentry_alerts import SentryAlertManager
    
    try:
        manager = SentryAlertManager()
        rules = manager.list_alert_rules()
        
        if rules is None:
            return {
                "error": "Failed to fetch alert rules",
                "message": "Check SENTRY_AUTH_TOKEN, SENTRY_ORG, and SENTRY_PROJECT configuration"
            }
        
        return {
            "count": len(rules),
            "rules": rules
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/errors/config")
async def get_sentry_config():
    """
    Get Sentry configuration status.
    
    Requirements:
    - 17.8: Expose API for querying error statistics
    
    Returns:
        Sentry configuration status
    """
    from backend.core.sentry_config import get_sentry_stats
    
    try:
        stats = get_sentry_stats()
        return stats
    except Exception as e:
        return {"error": str(e)}
