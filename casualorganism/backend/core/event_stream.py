"""
Event-Driven Graph Builder using Redis Streams.
Processes incremental graph updates without full rebuilds.
"""
from typing import Dict, Any, Optional
import asyncio
import time
import json
import os
import uuid
from backend.core.connection_pool import RedisConnectionPool, CacheLayer


class EventDrivenGraphBuilder:
    """
    Processes incremental graph updates via event streaming.
    Uses Redis Streams for reliable event delivery.
    """
    
    def __init__(
        self,
        redis_pool: RedisConnectionPool,
        cache: CacheLayer,
        neo4j_pool: Optional = None,
        graph: Optional = None
    ):
        self.redis_pool = redis_pool
        self.cache = cache
        self.neo4j_pool = neo4j_pool
        self.graph = graph
        self._running = False
        self._consumer_id = f"builder_{os.getpid()}_{uuid.uuid4().hex[:8]}"
    
    async def initialize(self) -> bool:
        """Initialize the event stream builder."""
        if not await self.redis_pool.initialize():
            return False
        return True
    
    async def publish_interaction(self, interaction: Dict[str, Any]) -> bool:
        """Publish interaction event to stream."""
        try:
            client = await self.redis_pool.get_client()
            event = {
                "id": str(uuid.uuid4()),
                "source": interaction["source"],
                "target": interaction["target"],
                "type": interaction["type"],
                "weight": interaction.get("weight", 1),
                "timestamp": str(time.time()),
                "event_type": "interaction"
            }
            await client.xadd("interactions", event)
            return True
        except Exception as e:
            print(f"Failed to publish interaction: {e}")
            return False
    
    async def consume_interactions(self, batch_size: int = 100, block_time: int = 5000):
        """
        Consumer loop for incremental graph updates.
        Runs until stopped.
        """
        self._running = True
        
        try:
            client = await self.redis_pool.get_client()
            
            # Create consumer group if not exists
            try:
                await client.xgroup_create(
                    "interactions", 
                    "graph_builder", 
                    id="0",
                    mkstream=True
                )
            except Exception:
                # Group already exists
                pass
            
            while self._running:
                # Read batch of events
                events = await client.xreadgroup(
                    "graph_builder",
                    self._consumer_id,
                    {"interactions": ">"},
                    count=batch_size,
                    block=block_time
                )
                
                for stream_name, messages in events:
                    for message_id, data in messages:
                        await self._process_interaction(data)
                        await client.xack("interactions", "graph_builder", message_id)
                        
        except asyncio.CancelledError:
            self._running = False
        except Exception as e:
            print(f"Error in consume loop: {e}")
            self._running = False
    
    async def stop(self):
        """Stop the consumer loop."""
        self._running = False
    
    async def _process_interaction(self, data: Dict[str, Any]):
        """Apply incremental update to graph."""
        source = data.get("source")
        target = data.get("target")
        interaction_type = data.get("type")
        weight = int(data.get("weight", 1))
        
        if not source or not target:
            return
        
        # Update Neo4j if available
        if self.neo4j_pool:
            await self._update_neo4j(source, target, interaction_type, weight)
        
        # Update in-memory graph if available
        if self.graph:
            self._update_graph(source, target, interaction_type, weight)
        
        # Invalidate cache for affected employees
        await self.cache.invalidate(f"metrics:employee:{source}")
        await self.cache.invalidate(f"metrics:employee:{target}")
        await self.cache.invalidate("graph:stats")
    
    async def _update_neo4j(self, source: str, target: str, interaction_type: str, weight: int):
        """Update Neo4j with incremental edge update."""
        if not self.neo4j_pool:
            return
        
        # Map interaction types to weights
        type_weights = {
            "slack_message": 1,
            "calendar_event": 5,
            "jira_action": 3
        }
        effective_weight = type_weights.get(interaction_type, weight)
        
        query = """
        MATCH (source:Employee {id: $source})
        MATCH (target:Employee {id: $target})
        MERGE (source)-[r:INTERACTS]->(target)
        ON CREATE SET r.weight = $weight, r.last_updated = timestamp()
        ON MATCH SET r.weight = r.weight + $weight, r.last_updated = timestamp()
        
        // Incrementally update degree centrality for affected nodes
        WITH source, target
        CALL {
            WITH source
            MATCH (source)-[r]-()
            WITH source, count(r) as degree
            MATCH (all:Employee)
            WITH source, degree, count(all) as total
            SET source.degree_centrality = toFloat(degree) / (total - 1)
        }
        CALL {
            WITH target
            MATCH (target)-[r]-()
            WITH target, count(r) as degree
            MATCH (all:Employee)
            WITH target, degree, count(all) as total
            SET target.degree_centrality = toFloat(degree) / (total - 1)
        }
        """
        
        try:
            await self.neo4j_pool.execute_write(query, {
                "source": source,
                "target": target,
                "weight": effective_weight
            })
        except Exception as e:
            print(f"Failed to update Neo4j: {e}")
    
    def _update_graph(self, source: str, target: str, interaction_type: str, weight: int):
        """Update in-memory graph with incremental edge update."""
        if not self.graph:
            return
        
        type_weights = {
            "slack_message": 1,
            "calendar_event": 5,
            "jira_action": 3
        }
        effective_weight = type_weights.get(interaction_type, weight)
        
        # Update edge weight
        if self.graph.graph.has_edge(source, target):
            self.graph.graph[source][target]["weight"] += effective_weight
        else:
            self.graph.graph.add_edge(source, target, weight=effective_weight)
        
        # Update centrality for affected nodes
        self.graph.graph.nodes[source]["degree_centrality"] = self._calculate_degree_centrality(source)
        self.graph.graph.nodes[target]["degree_centrality"] = self._calculate_degree_centrality(target)
    
    def _calculate_degree_centrality(self, node: str) -> float:
        """Calculate degree centrality for a node."""
        if not self.graph:
            return 0.0
        
        total_nodes = self.graph.graph.number_of_nodes()
        if total_nodes <= 1:
            return 0.0
        
        degree = self.graph.graph.degree(node)
        return degree / (total_nodes - 1)
