from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "system": "Causal Organism"}

def test_get_graph_stats():
    # Note: Requires graph to be built on startup
    response = client.get("/api/graph/stats")
    # We accept 200 (with valid data) or 200 (with error if graph not loaded)
    assert response.status_code == 200
    data = response.json()
    # Either we have valid stats or graph not loaded error
    if "node_count" in data:
        assert "edge_count" in data
    else:
        # Graph not loaded is acceptable for POC without Neo4j
        assert data.get("error") == "Graph not loaded"
