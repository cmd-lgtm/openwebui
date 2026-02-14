# Causal Organism: The Autonomous Enterprise

**Technical Pitch Deck & Due Diligence Brief**

---

## 1. The Problem: "The Visibility Gap"
Modern enterprises run on **Dark Matter**.
- **90% of work** happens in unstructured channels (Slack, decisions in hallways, calendar blocks).
- **Process Mining (Celonis)** only sees structured ERP logs.
- **Management Consulting (McKinsey)** relies on flawed human interviews.
- **Result**: Companies optimization is based on *correlation* and *opinion*, not *causality*.

---

## 2. The Solution: Causal Organism
An AI that treats the organization as a verifiable, causal graph.
- **SENSE**: Ingests the "Digital Footprint" (Slack, Calendar, Jira).
- **MODEL**: Distinguishes "Hubs" from "Bottle-necks" using **Causal Inference** (not just correlation).
- **ACT**: Autonomously intervenes (schedules Deep Work, suggests org changes) to optimize flow.

---

## 3. Technical Moat (Defensibility)
Why this is hard to copy:

### A. The Causal Advantage
- **Competitors (Copilot/Insight Tools)**: "You have a lot of meetings." (Descriptive)
- **Causal Organism**: "Reducing your meetings by 20% will save 15% burnout, **unless** you are a Manager." (Prescriptive & Counterfactual).
- *Implemented using structural causal models (DoWhy) that control for hidden confounders like Role and Seniority.*

### B. The Action Loop
- We don't just generate reports. We **write back** to the OS.
- Capabilities: Auto-scheduling focus time, re-routing tickets, flagging burnout risks to HR APIs.
- *Safety Layer*: "Constitutional AI" guardrails prevent high-risk actions without human approval.

---

## 4. Architecture (POC Complete)
We have a working End-to-End MVP:

1.  **Ingestion Layer**: `src/ingestion.py` - Parses unstructured interaction logs.
2.  **Graph Layer**: `src/graph_builder.py` - Builds a NetworkX/Neo4j graph of true working relationships.
3.  **Causal Engine**: `src/causal_analysis.py` - Regresses outcomes (Delay/Burnout) against structural features (Centrality), controlling for confounders.
4.  **Autonomous Agent**: `src/intervention.py` - Orchestrator that detects risks and executes API calls to fix them.

---

## 5. The "Why Now"
- **LLMs**: Finally allow us to extract structured "Events" from unstructured Slack/Email (The "Sensor").
- **Causal Libraries (DoWhy/PyMC)**: Finally matured to move beyond academic use (The "Brain").
- **API Economy**: Every enterprise tool (Slack, Zoom, Jira) is now fully programmable (The "Hands").

---

## 6. Ask & Roadmap
**Asking**: $3M Seed to move from "Shadow Mode" to "Live Production".

**12-Month Plan**:
- **Q1**: Pilot with 3 Mid-Market SaaS companies (Engineering Vertical).
- **Q2**: Replace NetworkX with Neo4j + GraphRAG for identifying "Knowledge Silos".
- **Q3**: Launch "Causal Manager" (Slack Bot that coaches managers based on team telemetry).
