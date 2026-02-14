"""
Async graph construction module.

Moves graph building to background tasks for faster startup.
Tracks graph readiness status in Redis.
Provides progress updates during build.

Requirements:
- 2.2: Move graph building to background task
- 2.5: Store readiness state in Redis
- 2.7: Expose status in health endpoint
- 2.4: Return 503 with Retry-After when graph not ready
- 2.6: Publish progress to Redis for client polling
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

import redis
from celery import Celery

logger = logging.getLogger(__name__)


class GraphBuildStatus(Enum):
    """Graph build status states."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    READY = "ready"
    FAILED = "failed"


class GraphBuildProgress:
    """Tracks graph build progress."""

    # Redis keys
    STATUS_KEY = "causal_organism:graph:status"
    PROGRESS_KEY = "causal_organism:graph:progress"
    LAST_UPDATE_KEY = "causal_organism:graph:last_update"
    ERROR_KEY = "causal_organism:graph:error"

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self._client: Optional[redis.Redis] = None

    def _get_client(self) -> redis.Redis:
        """Get or create Redis client."""
        if self._client is None:
            self._client = redis.from_url(self.redis_url, decode_responses=True)
        return self._client

    async def set_status(self, status: GraphBuildStatus, error: Optional[str] = None) -> None:
        """Set the current build status."""
        client = self._get_client()
        client.set(self.STATUS_KEY, status.value)
        client.set(self.LAST_UPDATE_KEY, datetime.utcnow().isoformat())
        if error:
            client.set(self.ERROR_KEY, error)

    async def get_status(self) -> Dict[str, Any]:
        """Get current build status."""
        client = self._get_client()

        status = client.get(self.STATUS_KEY) or GraphBuildStatus.NOT_STARTED.value
        progress_raw = client.get(self.PROGRESS_KEY)
        progress = json.loads(progress_raw) if progress_raw else {}
        last_update = client.get(self.LAST_UPDATE_KEY)
        error = client.get(self.ERROR_KEY)

        return {
            "status": status,
            "progress": progress,
            "last_update": last_update,
            "error": error
        }

    async def update_progress(
        self,
        phase: str,
        completed: int,
        total: int,
        message: str = ""
    ) -> None:
        """Update build progress."""
        client = self._get_client()

        progress = {
            "phase": phase,
            "completed": completed,
            "total": total,
            "percent": round((completed / total) * 100, 2) if total > 0 else 0,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }

        client.set(self.PROGRESS_KEY, json.dumps(progress))
        client.set(self.LAST_UPDATE_KEY, datetime.utcnow().isoformat())

        # Publish update for subscribers
        client.publish("graph_build_progress", json.dumps(progress))

    async def mark_ready(self) -> None:
        """Mark graph as ready."""
        await self.set_status(GraphBuildStatus.READY)

    async def mark_failed(self, error: str) -> None:
        """Mark graph build as failed."""
        await self.set_status(GraphBuildStatus.FAILED, error)

    async def reset(self) -> None:
        """Reset build status."""
        client = self._get_client()
        client.delete(self.STATUS_KEY)
        client.delete(self.PROGRESS_KEY)
        client.delete(self.ERROR_KEY)


class AsyncGraphBuilder:
    """
    Handles asynchronous graph building in background.

    Requirements:
    - 2.2: Remove synchronous build from startup_event
    - 2.5: Store readiness state in Redis
    - 2.6: Publish progress updates to Redis
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        celery_app: Optional[Celery] = None
    ):
        self.redis_url = redis_url
        self.celery_app = celery_app
        self.progress = GraphBuildProgress(redis_url)

    async def start_async_build(self, data_path: str = "data/digital_footprint.json") -> str:
        """
        Start asynchronous graph build.

        Args:
            data_path: Path to data file

        Returns:
            Task ID for tracking
        """
        if self.celery_app:
            # Use Celery task
            task = build_graph_task.delay(data_path)
            return task.id
        else:
            # Run in background thread
            import threading

            thread = threading.Thread(
                target=asyncio.run,
                args=(self._build_graph(data_path),)
            )
            thread.daemon = True
            thread.start()
            return "in_progress"

    async def _build_graph(self, data_path: str) -> None:
        """Build graph in background with progress updates."""
        try:
            await self.progress.set_status(GraphBuildStatus.IN_PROGRESS)

            # Phase 1: Load data
            await self.progress.update_progress(
                phase="loading_data",
                completed=0,
                total=100,
                message="Loading digital footprint data..."
            )

            with open(data_path, 'r') as f:
                data = json.load(f)

            total_items = len(data.get("employees", []))
            await self.progress.update_progress(
                phase="loading_data",
                completed=50,
                total=100,
                message=f"Loaded {total_items} employees"
            )

            # Phase 2: Build graph
            await self.progress.update_progress(
                phase="building_graph",
                completed=50,
                total=100,
                message="Building organizational graph..."
            )

            # Import here to avoid circular imports
            from backend.core.graph import OrganizationalGraph
            from backend.core.neo4j_adapter import Neo4jAdapter

            neo4j_url = os.getenv("GRAPH_DB_URL")
            if neo4j_url:
                graph = Neo4jAdapter(
                    neo4j_url,
                    os.getenv("GRAPH_DB_USER", "neo4j"),
                    os.getenv("GRAPH_DB_PASSWORD", "causal_organism")
                )
            else:
                graph = OrganizationalGraph()

            # Build with progress
            for i, emp in enumerate(data.get("employees", [])):
                graph.add_employee(emp)

                if i % 100 == 0:
                    percent = int((i / total_items) * 50) + 50
                    await self.progress.update_progress(
                        phase="building_graph",
                        completed=percent,
                        total=100,
                        message=f"Processing employee {i}/{total_items}"
                    )

            # Add interactions
            for interaction in data.get("interactions", []):
                graph.add_interaction(interaction)

            await self.progress.update_progress(
                phase="building_graph",
                completed=90,
                total=100,
                message="Finalizing graph..."
            )

            # Phase 3: Compute metrics
            await self.progress.update_progress(
                phase="computing_metrics",
                completed=90,
                total=100,
                message="Computing centrality metrics..."
            )

            # Create materialized views
            from backend.core.materialized_views import MaterializedViewManager
            view_manager = MaterializedViewManager(graph)
            await view_manager.initialize()
            await view_manager.create_degree_centrality_view()
            await view_manager.create_betweenness_centrality_view()
            await view_manager.create_clustering_coefficient_view()

            # Mark as ready
            await self.progress.mark_ready()

            logger.info("Graph build completed successfully")

        except Exception as e:
            logger.error(f"Graph build failed: {e}")
            await self.progress.mark_failed(str(e))
            raise

    def get_readiness_status(self) -> Dict[str, Any]:
        """
        Get current graph readiness status.

        Returns:
            Status dictionary with state and progress

        Requirements:
        - 2.5: Expose status in health endpoint
        """
        import asyncio

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.progress.get_status())

    def is_ready(self) -> bool:
        """Check if graph is ready."""
        status = self.get_readiness_status()
        return status.get("status") == GraphBuildStatus.READY.value


# Celery task for graph building
def build_graph_task(data_path: str = "data/digital_footprint.json") -> Dict[str, Any]:
    """
    Celery task to build graph in background.

    Args:
        data_path: Path to data file

    Returns:
        Build result
    """
    import asyncio

    async def _build():
        builder = AsyncGraphBuilder()
        await builder._build_graph(data_path)

    try:
        asyncio.run(_build())
        return {"status": "success", "message": "Graph built successfully"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}


# Global instance
_graph_builder: Optional[AsyncGraphBuilder] = None


def get_graph_builder() -> AsyncGraphBuilder:
    """Get the global graph builder instance."""
    global _graph_builder

    if _graph_builder is None:
        _graph_builder = AsyncGraphBuilder(
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0")
        )

    return _graph_builder
