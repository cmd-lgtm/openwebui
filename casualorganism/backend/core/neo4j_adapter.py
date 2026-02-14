from neo4j import GraphDatabase
import pandas as pd
import numpy as np
import os

class Neo4jAdapter:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        print(f"Connected to Neo4j at {uri}")

    def close(self):
        self.driver.close()

    def build(self, data):
        """
        Bulk ingestion of employees and interactions using Cypher UNWIND.
        """
        employees = data.get('employees', [])
        interactions = data.get('interactions', [])
        
        print("Building Graph in Neo4j...")
        
        with self.driver.session() as session:
            # 1. Create Constraints (Idempotency)
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (e:Employee) REQUIRE e.id IS UNIQUE")
            
            # 2. Ingest Employees
            print(f"Ingesting {len(employees)} employees...")
            session.run("""
                UNWIND $batch AS row
                MERGE (e:Employee {id: row.id})
                SET e.name = row.name, 
                    e.team = row.team, 
                    e.role = row.role,
                    e.is_manager = CASE WHEN row.role = 'Manager' THEN 1 ELSE 0 END
            """, batch=employees)
            
            # 3. Ingest Interactions (Edges)
            # Pre-process interactions to flatten list targets and map types to weights
            edge_list = []
            for interaction in interactions:
                src = interaction['source']
                targets = interaction['target']
                if not isinstance(targets, list): targets = [targets]
                
                weight = 1
                if interaction['type'] == 'calendar_event': weight = 5
                elif interaction['type'] == 'jira_action': weight = 3
                
                if src == "SYSTEM": continue
                
                for target in targets:
                    if src == target: continue
                    edge_list.append({
                        "src": src, 
                        "dst": target, 
                        "weight": weight
                    })

            print(f"Ingesting {len(edge_list)} interactions...")
            # We use MERGE to accumulate weights if multiple interactions exist
            # Note: This is a simplified version. For true high-performance, we might sum in Python first.
            session.run("""
                UNWIND $batch AS row
                MATCH (source:Employee {id: row.src})
                MATCH (target:Employee {id: row.dst})
                MERGE (source)-[r:INTERACTS]->(target)
                ON CREATE SET r.weight = row.weight
                ON MATCH SET r.weight = r.weight + row.weight
            """, batch=edge_list)
            
        print("Graph Build Complete in Neo4j.")

    def get_stats(self):
        with self.driver.session() as session:
            res = session.run("""
                MATCH (n:Employee)
                OPTIONAL MATCH (n)-[r:INTERACTS]->()
                RETURN count(DISTINCT n) as node_count, count(r) as edge_count
            """).single()
            
            # Density approximation (E / N*(N-1))
            n = res['node_count']
            e = res['edge_count']
            density = 0
            if n > 1:
                density = e / (n * (n - 1))
                
            return {
                "node_count": n,
                "edge_count": e,
                "density": density
            }

    def enrich_and_export(self, output_file=None) -> pd.DataFrame:
        """
        Reads Centrality from materialized views (node properties) in Neo4j
        and simulates Burnout. No on-demand centrality calculations.
        """
        print("\n--- Enriching Data with Graph Metrics from Materialized Views ---")
        
        with self.driver.session() as session:
            # Read metrics from materialized views (node properties)
            # These are pre-computed by MaterializedViewManager
            query = """
                MATCH (e:Employee)
                RETURN 
                    e.id as employee_id,
                    e.name as name,
                    e.team as team,
                    e.role as role,
                    e.is_manager as is_manager,
                    e.degree_centrality as degree_centrality,
                    e.betweenness_centrality as betweenness_centrality,
                    e.clustering_coeff as clustering_coeff
            """
            result = session.run(query)
            data = [record.data() for record in result]
            
        # Simulation Logic (Same as POC, but applied to DB results)
        np.random.seed(42)
        enriched_data = []
        
        for row in data:
            d_cent = row['degree_centrality'] if row['degree_centrality'] else 0
            is_manager = row['is_manager']
            
            # CAUSAL SIMULATION
            base_burnout = 10
            stress_from_comms = 60 * d_cent 
            resilience = 30 * is_manager 
            
            burnout_score = base_burnout + stress_from_comms - resilience + np.random.normal(0, 5)
            burnout_score = max(0, min(100, burnout_score)) 
            
            row['burnout_score'] = round(burnout_score, 1)
            # Metrics are already rounded from materialized views
            enriched_data.append(row)
            
        df = pd.DataFrame(enriched_data)
        if output_file:
            df.to_csv(output_file, index=False)
        return df
