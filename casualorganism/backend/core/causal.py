import pandas as pd
import numpy as np
import warnings
import statsmodels.api as sm

# Suppress warnings
warnings.filterwarnings("ignore")

class CausalEngine:
    def __init__(self):
        pass

    def analyze(self, data: pd.DataFrame):
        """
        Runs the causal regression: Burnout ~ Centrality + Role
        Returns the regression summary/coefficients.
        """
        if data.empty:
            return {"error": "No data provided"}

        # HYPOTHESIS: Does "Being a Hub" (Centrality) cause "Burnout"?
        
        # Causal Analysis (Controlling for Role)
        # Burnout ~ Centrality + Is_Manager
        
        X_causal = data[['degree_centrality', 'is_manager']]
        X_causal = sm.add_constant(X_causal)
        y = data['burnout_score']
        
        model_causal = sm.OLS(y, X_causal).fit()
        
        return {
            "coefficients": {
                "intercept": model_causal.params['const'],
                "degree_centrality": model_causal.params['degree_centrality'],
                "is_manager": model_causal.params['is_manager']
            },
            "p_values": {
                "degree_centrality": model_causal.pvalues['degree_centrality'],
                "is_manager": model_causal.pvalues['is_manager']
            },
            "r_squared": model_causal.rsquared
        }
