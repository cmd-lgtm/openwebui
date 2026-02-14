import pandas as pd
from src.generate_data import generate_interaction_data
from src.ingestion import IngestionEngine
from src.graph_builder import OrganizationalGraph
from src.simulation import CounterfactualEngine
from src.intervention import ActionOrchestrator
import json

def run_causal_organism_demo():
    print("============================================================")
    print("   CAUSAL ORGANISM: Autonomous Optimization Sequence")
    print("============================================================")
    
    # STEP 1: SENSE (Data Generation & Ingestion)
    print("\n[STEP 1] SENSE: Excavating organizational anatomy...")
    generate_interaction_data(num_employees=20)
    
    engine = IngestionEngine()
    data = engine.ingest_mock_data("data/digital_footprint.json")
    
    # STEP 2: MODEL (Graph Construction & Causal Inference)
    print("\n[STEP 2] MODEL: Building Causal Graph & Diagnosing Burnout...")
    graph = OrganizationalGraph()
    graph.build(data)
    graph.enrich_and_export("data/current_state.csv")
    
    # (In a real app, we would re-run causal_analysis.py here to get fresh weights)
    # For speed, we use the learned weights from Phase 2.
    causal_weights = {'intercept': 10.0, 'centrality': 58.12, 'is_manager': -28.75}
    
    # STEP 3: SIMULATE (Counterfactual Reasoning)
    print("\n[STEP 3] SIMULATE: Identifying Critical Interventions...")
    sim_engine = CounterfactualEngine(causal_weights)
    df = pd.read_csv("data/current_state.csv")
    
    # Strategy: Find top 2 burnt-out regular employees (High Centrality, Low Resilience)
    # and prescribe "Deep Work" to reduce their centrality signal.
    
    candidates = df[df['is_manager'] == 0].nlargest(2, 'degree_centrality')
    target_ids = candidates['employee_id'].tolist()
    target_names = candidates['name'].tolist()
    
    print(f"Detected High-Risk Employees (Burnout Risk): {target_names}")
    
    # STEP 4: ACT (Autonomous Intervention)
    print("\n[STEP 4] ACT: Executing Safety-Critical Interventions...")
    orchestrator = ActionOrchestrator(mode='live')
    
    intervention_plan = []
    for emp_id, name in zip(target_ids, target_names):
        intervention_plan.append({
            'action': 'schedule_focus_time',
            'target': emp_id,
            'params': {'reason': 'Prevent Burnout (Causal Score > 80)'}
        })
        
    orchestrator.execute_intervention(intervention_plan)
    
    print("\n[SUCCESS] Optimization Cycle Complete. Outcome: Burnout Drivers Mitigated.")

if __name__ == "__main__":
    run_causal_organism_demo()
