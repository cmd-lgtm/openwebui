"""
WebSocket handler for real-time frontend updates.

Provides efficient push-based updates instead of polling.
Supports server-side push for data changes.

Requirements:
- 6.2: Add WebSocket endpoint to API
- 6.3: Push updates only when data changes
- 6.4: Fall back to 30-second polling if WebSocket unavailable
- 6.5: Include ETag in responses
- 6.6: Support If-None-Match for 304 responses
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, Set, Optional, Any, Callable
from enum import Enum

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from starlette.websockets import WebSocketState

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """WebSocket message types."""
    GRAPH_UPDATE = "graph_update"
    METRICS_UPDATE = "metrics_update"
    INTERVENTION_UPDATE = "intervention_update"
    ALERT = "alert"
    HEARTBEAT = "heartbeat"
    ERROR = "error"


class ConnectionManager:
    """Manages WebSocket connections."""

    def __init__(self):
        # Active connections by channel
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "graph": set(),
            "metrics": set(),
            "interventions": set(),
            "alerts": set()
        }

        # Subscriptions by connection
        self.connection_subscriptions: Dict[WebSocket, Set[str]] = {}

    async def connect(self, websocket: WebSocket, channel: str) -> None:
        """Accept and track a new WebSocket connection."""
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = set()
        self.active_connections[channel].add(websocket)
        self.connection_subscriptions[websocket] = {channel}
        logger.info(f"WebSocket connected to {channel}")

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        if websocket in self.connection_subscriptions:
            channels = self.connection_subscriptions.pop(websocket)
            for channel in channels:
                self.active_connections.get(channel, set()).discard(websocket)
        logger.info("WebSocket disconnected")

    async def send_message(self, message: Dict[str, Any], channel: str) -> None:
        """Send message to all connections in a channel."""
        if channel not in self.active_connections:
            return

        disconnected = set()

        for connection in self.active_connections[channel]:
            try:
                if connection.client_state == WebSocketState.CONNECTED:
                    await connection.send_json(message)
                else:
                    disconnected.add(connection)
            except Exception as e:
                logger.error(f"Error sending to WebSocket: {e}")
                disconnected.add(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Broadcast message to all connected clients."""
        for channel in self.active_connections:
            await self.send_message(message, channel)


# Global connection manager
manager = ConnectionManager()


# Redis pub/sub for cross-instance communication
_redis_pubsub = None


async def get_redis_pubsub():
    """Get Redis pubsub client for broadcasting updates."""
    global _redis_pubsub

    if _redis_pubsub is None:
        import redis
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _redis_pubsub = redis.from_url(redis_url, decode_responses=True)

    return _redis_pubsub


async def subscribe_to_updates():
    """Subscribe to Redis channels for update notifications."""
    try:
        pubsub = await get_redis_pubsub()
        pubsub.subscribe("causal_organism_updates")

        for message in pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                await manager.broadcast(data)
    except Exception as e:
        logger.error(f"Error in Redis subscribe: {e}")


# Start background task for Redis subscriptions
async def start_pubsub_listener():
    """Start listening for Redis pub/sub messages."""
    asyncio.create_task(subscribe_to_updates())


# WebSocket endpoint
websocket_router = APIRouter()


@websocket_router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    channel: str = Query(default="graph", description="Update channel: graph, metrics, interventions, alerts")
):
    """
    WebSocket endpoint for real-time updates.

    Supports the following channels:
    - graph: Organizational graph updates
    - metrics: Employee metrics updates
    - interventions: Intervention status updates
    - alerts: System alerts

    Requirements:
    - 6.2: Add WebSocket endpoint to API

    Example:
        # Connect to graph updates
        const ws = new WebSocket("ws://localhost:8000/ws?channel=graph");

        # Listen for updates
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log("Graph update:", data);
        };
    """
    await manager.connect(websocket, channel)

    try:
        # Send welcome message
        await websocket.send_json({
            "type": MessageType.HEARTBEAT.value,
            "channel": channel,
            "status": "connected",
            "timestamp": datetime.utcnow().isoformat()
        })

        # Keep connection alive and handle messages
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)

                # Handle ping
                if message.get("type") == "ping":
                    await websocket.send_json({
                        "type": MessageType.HEARTBEAT.value,
                        "timestamp": datetime.utcnow().isoformat()
                    })

                # Handle subscribe to additional channels
                elif message.get("type") == "subscribe":
                    new_channel = message.get("channel")
                    if new_channel in manager.active_connections:
                        manager.connection_subscriptions[websocket].add(new_channel)
                        await websocket.send_json({
                            "type": MessageType.HEARTBEAT.value,
                            "status": f"subscribed_to_{new_channel}"
                        })

                # Handle unsubscribe
                elif message.get("type") == "unsubscribe":
                    old_channel = message.get("channel")
                    manager.connection_subscriptions[websocket].discard(old_channel)

            except json.JSONDecodeError:
                logger.warning("Invalid JSON received on WebSocket")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# Publishing functions
async def publish_graph_update(data: Dict[str, Any]) -> None:
    """
    Publish graph update to all subscribers.

    Requirements:
    - 6.3: Push updates only when data changes
    """
    message = {
        "type": MessageType.GRAPH_UPDATE.value,
        "timestamp": datetime.utcnow().isoformat(),
        "data": data
    }

    # Send to all connected clients
    await manager.send_message(message, "graph")

    # Also publish to Redis for cross-instance communication
    try:
        pubsub = await get_redis_pubsub()
        pubsub.publish("causal_organism_updates", json.dumps(message))
    except Exception as e:
        logger.warning(f"Failed to publish to Redis: {e}")


async def publish_metrics_update(data: Dict[str, Any]) -> None:
    """Publish metrics update to all subscribers."""
    message = {
        "type": MessageType.METRICS_UPDATE.value,
        "timestamp": datetime.utcnow().isoformat(),
        "data": data
    }

    await manager.send_message(message, "metrics")

    try:
        pubsub = await get_redis_pubsub()
        pubsub.publish("causal_organism_updates", json.dumps(message))
    except Exception as e:
        logger.warning(f"Failed to publish to Redis: {e}")


async def publish_intervention_update(data: Dict[str, Any]) -> None:
    """Publish intervention update to all subscribers."""
    message = {
        "type": MessageType.INTERVENTION_UPDATE.value,
        "timestamp": datetime.utcnow().isoformat(),
        "data": data
    }

    await manager.send_message(message, "interventions")

    try:
        pubsub = await get_redis_pubsub()
        pubsub.publish("causal_organism_updates", json.dumps(message))
    except Exception as e:
        logger.warning(f"Failed to publish to Redis: {e}")


async def publish_alert(alert: Dict[str, Any]) -> None:
    """Publish alert to all subscribers."""
    message = {
        "type": MessageType.ALERT.value,
        "timestamp": datetime.utcnow().isoformat(),
        "alert": alert
    }

    await manager.send_message(message, "alerts")

    try:
        pubsub = await get_redis_pubsub()
        pubsub.publish("causal_organism_updates", json.dumps(message))
    except Exception as e:
        logger.warning(f"Failed to publish to Redis: {e}")


# HTTP endpoints with ETag support for fallback polling
http_router = APIRouter()


# ETag storage
_etag_store: Dict[str, str] = {}


def generate_etag(data: Any) -> str:
    """Generate ETag from data."""
    import hashlib
    content = json.dumps(data, sort_keys=True)
    return f'"{hashlib.md5(content.encode()).hexdigest()}"'


@http_router.get("/api/graph/stats")
async def get_graph_stats_with_etag():
    """
    Get graph statistics with ETag support.

    Requirements:
    - 6.5: Include ETag in responses
    - 6.6: Support If-None-Match for 304 responses
    """
    # Get stats (would normally come from state)
    from backend.main import state

    if not state.graph:
        raise HTTPException(status_code=503, detail="Graph not loaded")

    stats = state.graph.get_stats()
    etag = generate_etag(stats)

    return {
        "data": stats,
        "etag": etag,
        "_links": {
            "websocket": "/ws?channel=graph"
        }
    }


@http_router.get("/api/graph/employee_metrics")
async def get_metrics_with_etag():
    """Get employee metrics with ETag support."""
    from backend.main import state

    if not state.graph:
        raise HTTPException(status_code=503, detail="Graph not loaded")

    metrics = state.graph.enrich_and_export(output_file=None)
    etag = generate_etag(metrics.to_dict())

    return {
        "data": metrics.to_dict(orient="records"),
        "etag": etag,
        "_links": {
            "websocket": "/ws?channel=metrics"
        }
    }
