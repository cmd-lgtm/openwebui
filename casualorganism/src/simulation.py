import pandas as pd
import numpy as np

class CounterfactualEngine:
    def __init__(self, causal_weights):
        """
        Initialize with learned Causal Parameters (from Phase 2).
        weights: dict with keys 'intercept', 'centrality', 'is_manager'
        """
        self.weights = causal_weights
        print(f"Engine Initialized with Causal Physics: {self.weights}")

    def predict(self, df):
        """
        Predicts outcome (Burnout) based on current state and causal laws.
        Formula: Burnout = Intercept + (W_cent * Centrality) + (W_mgr * Is_Manager)
        """
        # We start with the BASELINE burnout from the data (which includes noise/other factors)
        # But for the simulation delta, we care about the CHANGE in the causal component.
        # Alternatively, we can predict "Predicted Burnout" from scratch.
        # Let's predict from scratch to see the purely causal impact.
        
        preds = self.weights['intercept'] + \
                (self.weights['centrality'] * df['degree_centrality']) + \
                (self.weights['is_manager'] * df['is_manager'])
        
        return preds.clip(0, 100)

    def simulate_intervention(self, df, intervention_name, transformation_func):
        """
        The "Do-Operator".
        - df: Original State
        - intervention_name: Label for the scenario
        - transformation_func: Function to modify the dataframe (e.g. reduce centrality)
        """
        print(f"\n--- Simulating Scenario: {intervention_name} ---")
        
        # 1. Baseline
        baseline_burnout = self.predict(df).mean()
        print(f"Baseline Average Burnout: {baseline_burnout:.2f}")
        
        # 2. Apply Intervention (Counterfactual World)
        df_counterfactual = df.copy()
        df_counterfactual = transformation_func(df_counterfactual)
        
        # 3. Predict New State
        new_burnout = self.predict(df_counterfactual).mean()
        print(f"New Average Burnout: {new_burnout:.2f}")
        
        delta = new_burnout - baseline_burnout
        print(f"Impact: {delta:.2f} points ({ (delta/baseline_burnout)*100 :.1f}%)")
        return df_counterfactual

def run_simulation():
    try:
        df = pd.read_csv('data/employee_metrics.csv')
    except FileNotFoundError:
        print("Error: data/employee_metrics.csv not found.")
        return

    # HARDCODED PARAMETERS (Derived from Phase 2 Analysis)
    # Recovered Centrality Effect: 58.12
    # Recovered Manager Effect: -28.75
    # Intercept (approx): 10
    causal_weights = {
        'intercept': 10.0,
        'centrality': 58.12,
        'is_manager': -28.75
    }
    
    engine = CounterfactualEngine(causal_weights)
    
    # SCENARIO 1: "Meeting Cap" Policy
    # Intervention: Reduce everyone's Centrality by 50% (e.g. by banning half the meetings)
    def reduce_communication(d):
        d['degree_centrality'] = d['degree_centrality'] * 0.5
        return d
        
    engine.simulate_intervention(df, "Meeting Cap (50% reduction)", reduce_communication)
    
    # SCENARIO 2: "Targeted support"
    # Intervention: Promote the top 3 most central ICs to Manager (giving them resilience)
    def promote_top_hubs(d):
        # Find top 3 central nodes who are NOT managers
        candidates = d[d['is_manager'] == 0].nlargest(3, 'degree_centrality')
        print(f"Promoting Candidates: {candidates['name'].tolist()}")
        
        # Apply promotion
        d.loc[candidates.index, 'is_manager'] = 1
        return d
        
    engine.simulate_intervention(df, "Promote Top 3 Hubs", promote_top_hubs)

if __name__ == "__main__":
    run_simulation()
