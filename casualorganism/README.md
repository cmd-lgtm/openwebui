# Causal Organism

**The Autonomous Causal Intelligence Platform for Enterprise Self-Optimization**

Causal Organism is an AI system that treats organizations as living organisms. It goes beyond correlation to understand the *cause* of operational inefficiencies and autonomously intervenes to optimize them.

## 🚀 The Core Loop (POC)

We have implemented the full **Sense -> Model -> Act** loop:

1.  **Sense**: Ingests digital footprints (Slack messages, Calendar invites).
2.  **Model**: Builds an Organizational Graph and learns Causal Laws (e.g. "Centrality + Role -> Burnout").
3.  **Simulate**: Runs counterfactuals ("What if we reduce meetings?").
4.  **Act**: Autonomously schedules "Deep Work" blocks to mitigate burnout risks.

## 🛠️ Quick Start

### 1. Installation
```bash
pip install -r requirements.txt
```

### 2. Run the Autonomous Demo
This script runs the entire pipeline: generates synthetic data, trains the causal model, detects bad patterns, and "fixes" them via a Mock API.

```bash
python -m src.demo_full_loop
```

**Expected Output**:
```text
[STEP 4] ACT: Executing Safety-Critical Interventions...
[CALENDAR] Scheduled 'Deep Work (Causal Optimizer)' for ['EMP_002']...
[SUCCESS] Optimization Cycle Complete.
```

## 📂 Project Structure

- `src/generate_data.py`: Creates synthetic "Digital Footprints" (JSON).
- `src/ingestion.py`: Parses raw logs into structured Interactions.
- `src/graph_builder.py`: Constructs the Organizational Graph (NetworkX).
- `src/causal_analysis.py`: The brain. Uses Statsmodels/DoWhy to find ground truth.
- `src/simulation.py`: The Crystal Ball. Predicts "What if" scenarios.
- `src/intervention.py`: The Action Layer. Safely executes API calls.

## 🔮 Roadmap
- **Phase 1**: Digital Twin (Complete)
- **Phase 2**: Causal Discovery (Complete)
- **Phase 3**: Simulation (Complete)
- **Phase 4**: Autonomous Intervention (Complete)
- **Next**: Deployment to real Slack/Neo4j environment.

