import networkx as nx
import matplotlib.pyplot as plt
from typing import Dict, Any
import random 
import numpy as np
import pandas as pd

class OrganizationalGraph:
    def __init__(self):
        self.graph = nx.DiGraph() # Directed graph since A -> B matters (e.g. manager -> report)

    def build(self, data: Dict[str, Any]):
        """
        Builds the NetworkX graph from ingested data.
        """
        employees = data.get('employees', [])
        interactions = data.get('interactions', [])
        
        print("Building Graph...")
        
        # 1. Add Nodes (Employees)
        for emp in employees:
            self.graph.add_node(
                emp['id'], 
                label=emp['name'], 
                team=emp['team'], 
                role=emp['role']
            )
            
        # 2. Add Edges (Interactions)
        # We aggregate interactions into weighted edges
        edge_weights = {} # (source, target) -> weight
        
        for interaction in interactions:
            src = interaction['source']
            targets = interaction['target']
            
            # Handle list targets (like calendar invites)
            if not isinstance(targets, list):
                targets = [targets]
                
            ints_type = interaction['type']
            weight = 0
            
            if ints_type == 'slack_message':
                weight = 1
            elif ints_type == 'calendar_event':
                weight = 5 # Meetings are stronger connections
            elif ints_type == 'jira_action':
                weight = 3
                
            if src == "SYSTEM": # Ignore system events for social graph
                continue
                
            for target in targets:
                if src == target: continue
                
                key = (src, target)
                if key not in edge_weights:
                    edge_weights[key] = 0
                edge_weights[key] += weight
                
        # 3. Commit Edges to Graph
        for (src, target), weight in edge_weights.items():
            if self.graph.has_node(src) and self.graph.has_node(target):
                self.graph.add_edge(src, target, weight=weight)
                
        print(f"Graph Built: {self.graph.number_of_nodes()} Nodes, {self.graph.number_of_edges()} Edges")

    def get_stats(self):
        """Returns basic graph stats"""
        return {
            "node_count": self.graph.number_of_nodes(),
            "edge_count": self.graph.number_of_edges(),
            "density": nx.density(self.graph)
        }

    def enrich_and_export(self, output_file='data/employee_metrics.csv') -> pd.DataFrame:
        """
        Calculates graph metrics (Centrality) and merges with employee metadata.
        Simulates 'Burnout' as a causal outcome of Centrality.
        Returns the DataFrame.
        """
        print("\n--- Enriching Data with Graph Metrics ---")
        
        # 1. Calculate Metrics
        degree_centrality = nx.degree_centrality(self.graph)
        betweenness_centrality = nx.betweenness_centrality(self.graph)
        clustering = nx.clustering(self.graph)
        
        data = []
        
        np.random.seed(42) # For reproducibility
        
        for node_id in self.graph.nodes:
            node_attrs = self.graph.nodes[node_id]
            
            # Metrics
            d_cent = degree_centrality[node_id]
            b_cent = betweenness_centrality[node_id]
            clust = clustering[node_id]
            
            # CAUSAL SIMULATION
            role = node_attrs['role']
            is_manager = 1 if role == 'Manager' else 0
            
            base_burnout = 10
            stress_from_comms = 60 * d_cent 
            resilience = 30 * is_manager 
            
            burnout_score = base_burnout + stress_from_comms - resilience + np.random.normal(0, 5)
            burnout_score = max(0, min(100, burnout_score)) 
            
            data.append({
                'employee_id': node_id,
                'name': node_attrs['label'],
                'team': node_attrs['team'],
                'role': role,
                'is_manager': is_manager,
                'degree_centrality': round(d_cent, 4),
                'betweenness_centrality': round(b_cent, 4),
                'clustering_coeff': round(clust, 4),
                'burnout_score': round(burnout_score, 1)
            })
            
        df = pd.DataFrame(data)
        if output_file:
            df.to_csv(output_file, index=False)
        return df

    def export(self, filepath='data/org_graph.gml'):
        nx.write_gml(self.graph, filepath)
