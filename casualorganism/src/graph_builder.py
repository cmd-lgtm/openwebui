import networkx as nx
import matplotlib.pyplot as plt
from typing import Dict, Any

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

    def analyze(self):
        """
        Runs basic network analysis algorithms.
        """
        print("\n--- Network Analysis ---")
        
        # 1. Degree Centrality (Who is the hub?)
        # We use weighted degree if possible, but standard degree is a good proxy for "connectedness"
        centrality = nx.degree_centrality(self.graph)
        top_hubs = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:3]
        
        print("Top 3 Central Hubs (Most Connected):")
        for node_id, score in top_hubs:
            node_data = self.graph.nodes[node_id]
            print(f"  - {node_data['label']} ({node_data['team']}): {score:.3f}")
            
        # 2. Silo Detection (Modularity / Communities)
        # Simple proxy: Density of the graph
        density = nx.density(self.graph)
        print(f"Graph Density: {density:.3f} (Lower = More Siloed)")
        
        # 3. Team-to-Team connectivity
        # TODO: Advanced metric for Phase 2
        
    def enrich_and_export(self, output_file='data/employee_metrics.csv'):
        """
        Calculates graph metrics (Centrality) and merges with employee metadata.
        Simulates 'Burnout' as a causal outcome of Centrality.
        """
        print("\n--- Enriching Data with Graph Metrics ---")
        
        # 1. Calculate Metrics
        degree_centrality = nx.degree_centrality(self.graph)
        betweenness_centrality = nx.betweenness_centrality(self.graph)
        clustering = nx.clustering(self.graph)
        
        data = []
        
        import random 
        import numpy as np
        np.random.seed(42) # For reproducibility of the "Bio-Simulation"
        
        for node_id in self.graph.nodes:
            node_attrs = self.graph.nodes[node_id]
            
            # Metrics
            d_cent = degree_centrality[node_id]
            b_cent = betweenness_centrality[node_id]
            clust = clustering[node_id]
            
            # CAUSAL SIMULATION (The "God Mode" part where we define the laws of physics)
            # Hypothesis: High Centrality (Over-communication) -> Burnout
            # Confounder: Role (Managers handle high centrality better)
            
            role = node_attrs['role']
            is_manager = 1 if role == 'Manager' else 0
            
            # True Causal Equation:
            # Burnout = 10 + (50 * Degree_Centrality) - (20 * Is_Manager) + Noise
            # Managers buffer the stress of communication.
            
            base_burnout = 10
            stress_from_comms = 60 * d_cent # d_cent is 0-1, so max ~60 points
            resilience = 30 * is_manager # Managers have -30 burnout points
            
            burnout_score = base_burnout + stress_from_comms - resilience + np.random.normal(0, 5)
            burnout_score = max(0, min(100, burnout_score)) # Clamp 0-100
            
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
            
        import pandas as pd
        df = pd.DataFrame(data)
        df.to_csv(output_file, index=False)
        print(f"Enriched data exported to {output_file}")
        print("Sample with Burnout:")
        print(df[['name', 'role', 'degree_centrality', 'burnout_score']].head())

    def export(self, filepath='data/org_graph.gml'):
        nx.write_gml(self.graph, filepath)
        print(f"Graph exported to {filepath}")

if __name__ == "__main__":
    # Test flow
    import json
    try:
        with open("data/digital_footprint.json", 'r') as f:
            data = json.load(f)
        
        org_graph = OrganizationalGraph()
        org_graph.build(data)
        org_graph.analyze()
        org_graph.enrich_and_export() # New step
        org_graph.export()
    except FileNotFoundError:
        print("Run generate_data.py first!")
