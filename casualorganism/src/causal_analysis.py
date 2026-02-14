import pandas as pd
import numpy as np
import dowhy
from dowhy import CausalModel
import warnings

# Suppress warnings for cleaner output in the CLI
warnings.filterwarnings("ignore")

def analyze_causality(input_file='data/employee_metrics.csv'):
    print(f"Loading data from {input_file}...")
    try:
        data = pd.read_csv(input_file)
    except FileNotFoundError:
        print("Error: Data file not found. Run graph_builder.py first.")
        return

    import statsmodels.api as sm
    
    # HYPOTHESIS: Does "Being a Hub" (Centrality) cause "Burnout"?
    print("\n--- Causal Discovery: The Cost of Collaboration ---")
    
    # 1. Naive Analysis
    # Regress Burnout ~ Centrality
    # We expect this to be NOISY or BIASED if we don't control for Role.
    # (Managers might have high centrality but LOW burnout, masking the effect for ICs)
    
    X_naive = data[['degree_centrality']]
    X_naive = sm.add_constant(X_naive)
    y = data['burnout_score']
    
    model_naive = sm.OLS(y, X_naive).fit()
    naive_effect = model_naive.params['degree_centrality']
    
    print(f"\n[Naive Model] Burnout ~ Centrality")
    print(f"Effect: {naive_effect:.2f} points of burnout per unit of centrality")
    print(f"p-value: {model_naive.pvalues['degree_centrality']:.4f}")
    print(f"Note: This mixes Managers (Resilient) and ICs (Vulnerable).")
    
    # 2. Causal Analysis (Controlling for Role)
    # Burnout ~ Centrality + Is_Manager
    
    X_causal = data[['degree_centrality', 'is_manager']]
    X_causal = sm.add_constant(X_causal)
    
    model_causal = sm.OLS(y, X_causal).fit()
    causal_effect = model_causal.params['degree_centrality']
    manager_effect = model_causal.params['is_manager']
    
    print(f"\n[Causal Model] Burnout ~ Centrality + Manager_Status")
    print(f"Direct Effect of Centrality: {causal_effect:.2f} (True Stress Cost)")
    print(f"Effect of Being Manager: {manager_effect:.2f} (Resilience/Buffer)")
    
    # 3. Validation
    # We programmed the 'Simulation' in graph_builder.py as:
    # Stress = 60 * Centrality
    # Resilience = -30 * Manager
    
    print(f"\n[Validation against Simulation Truth]")
    print(f"Target Centrality Effect: 60.0")
    print(f"Target Manager Effect: -30.0")
    print(f"Recovered Centrality: {causal_effect:.2f}")
    print(f"Recovered Manager: {manager_effect:.2f}")
    
    if abs(causal_effect - 60) < 10:
         print("\nSUCCESS: The AI successfully disentangled the structural stress from role resilience.")
    else:
         print("\nWARNING: Model fit is poor.")

if __name__ == "__main__":
    analyze_causality()
