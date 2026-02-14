import pandas as pd
import numpy as np

class CounterfactualEngine:
    def __init__(self, causal_weights):
        """
        Initialize with learned Causal Parameters.
        weights: dict with keys 'intercept', 'centrality', 'is_manager' (mapped to coeffs)
        """
        # Map generic keys if needed, assumes direct mapping for now
        self.weights = {
            'intercept': causal_weights.get('intercept', 0),
            'centrality': causal_weights.get('degree_centrality', 0),
            'is_manager': causal_weights.get('is_manager', 0)
        }
        print(f"Engine Initialized with Causal Physics: {self.weights}")

    def predict(self, df):
        preds = self.weights['intercept'] + \
                (self.weights['centrality'] * df['degree_centrality']) + \
                (self.weights['is_manager'] * df['is_manager'])
        return preds.clip(0, 100)

    def simulate_intervention(self, df, intervention_type):
        """
        Runs a specific intervention scenario.
        intervention_type: 'meeting_cap_50' or 'promote_hubs'
        """
        print(f"\n--- Simulating Scenario: {intervention_type} ---")
        
        baseline_burnout = self.predict(df).mean()
        
        df_counterfactual = df.copy()
        
        if intervention_type == 'meeting_cap_50':
            df_counterfactual['degree_centrality'] = df_counterfactual['degree_centrality'] * 0.5
            
        elif intervention_type == 'promote_hubs':
            # Find top 3 central nodes who are NOT managers
            candidates = df_counterfactual[df_counterfactual['is_manager'] == 0].nlargest(3, 'degree_centrality')
            # Apply promotion
            df_counterfactual.loc[candidates.index, 'is_manager'] = 1
            
        else:
            return {"error": "Unknown intervention type"}
            
        new_burnout = self.predict(df_counterfactual).mean()
        delta = new_burnout - baseline_burnout
        
        return {
            "baseline_burnout": baseline_burnout,
            "new_burnout": new_burnout,
            "impact_delta": delta,
            "impact_percent": (delta/baseline_burnout)*100 if baseline_burnout > 0 else 0
        }
