import pandas as pd
from backend.core.causal import CausalEngine

def test_causal_analysis_logic():
    # Mock Data
    data = {
        'degree_centrality': [0.1, 0.5, 0.9, 0.2, 0.8],
        'is_manager':        [0,   0,   0,   1,   1],
        # Synthetic Truth: Burnout = 10 + 60*Centrality - 30*Manager
        'burnout_score':     [16,  40,  64,  -8,  28] 
    }
    df = pd.DataFrame(data)
    
    engine = CausalEngine()
    results = engine.analyze(df)
    
    coeffs = results['coefficients']
    
    # Check if directionality is correct
    assert coeffs['degree_centrality'] > 0  # Should be positive stress
    assert coeffs['is_manager'] < 0         # Should be negative buffer
