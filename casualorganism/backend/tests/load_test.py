"""
Load test suite for Causal Organism API.

Simulates realistic usage patterns to validate performance
and scalability under load.

Requirements:
- 25.1: Simulate 100 concurrent users
- 25.2: Mix of read and write operations
- 25.3: Measure P95 and P99 latency
- 25.4: Measure error rate
- 25.5: Run on every release candidate
- 25.6: Block release if tests fail
- 25.7: Generate performance reports

Usage:
    # Run locally
    locust -f backend/tests/load_test.py --host=http://localhost:8000

    # Run with UI
    locust -f backend/tests/load_test.py --host=http://localhost:8000 --web-port=8089

    # Run headless with specific users
    locust -f backend/tests/load_test.py --host=http://localhost:8000 \
        --users 100 --spawn-rate 10 --run-time 5m --headless \
        --html report.html
"""

import random
import time
from typing import Dict, Any, Optional

from locust import (
    HttpUser,
    task,
    between,
    events,
    stats as locust_stats,
    TaskSet
)
from locust.contrib.fasthttp import FastHttpUser


# Configure Locust
locust_stats.STATS_PERCENTILE_NUMERIC = 2  # P50, P95, P99


class CausalOrganismUser(HttpUser):
    """
    Simulates a typical user of the Causal Organism platform.

    User behavior:
    - 60% read operations (graph stats, metrics)
    - 20% trend queries
    - 10% write operations (trigger analysis)
    - 10% export operations
    """

    # Wait time between tasks: 1-3 seconds
    wait_time = between(1, 3)

    # Authentication token (would be set on login)
    token: Optional[str] = None

    def on_start(self):
        """Called when a user starts. Authenticate first."""
        # For testing, use a test token or skip auth
        self.token = "test-token"

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with auth."""
        headers = {
            "Content-Type": "application/json"
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    @task(60)
    def get_graph_stats(self):
        """Get graph statistics - most common operation."""
        self.client.get(
            "/api/graph/stats",
            headers=self._get_headers(),
            name="/api/graph/stats"
        )

    @task(40)
    def get_employee_metrics(self):
        """Get employee metrics."""
        self.client.get(
            "/api/graph/employee_metrics",
            headers=self._get_headers(),
            name="/api/graph/employee_metrics"
        )

    @task(20)
    def get_employee_metrics_by_id(self):
        """Get specific employee metrics."""
        # Random employee ID
        employee_id = f"emp_{random.randint(1, 1000)}"
        self.client.get(
            f"/api/graph/employee_metrics/{employee_id}",
            headers=self._get_headers(),
            name="/api/graph/employee_metrics/[id]"
        )

    @task(15)
    def get_employee_trend(self):
        """Get historical trend for an employee."""
        employee_id = f"emp_{random.randint(1, 1000)}"
        days = random.choice([7, 30, 90])
        self.client.get(
            f"/api/trends/employee/{employee_id}?days={days}",
            headers=self._get_headers(),
            name="/api/trends/employee/[id]"
        )

    @task(10)
    def trigger_analysis(self):
        """Trigger a causal analysis - write operation."""
        self.client.post(
            "/api/causal/analyze",
            json={
                "analysis_type": "causal",
                "target_metric": "burnout_score"
            },
            headers=self._get_headers(),
            name="/api/causal/analyze"
        )

    @task(10)
    def request_export(self):
        """Request a data export."""
        self.client.post(
            "/api/exports/request",
            json={
                "export_type": "employee_metrics",
                "format": "csv",
                "date_range": {
                    "start": "2024-01-01",
                    "end": "2024-12-31"
                }
            },
            headers=self._get_headers(),
            name="/api/exports/request"
        )

    @task(5)
    def get_health(self):
        """Check service health."""
        self.client.get("/health/live", name="/health/live")

    @task(5)
    def get_readiness(self):
        """Check service readiness."""
        self.client.get("/health/ready", name="/health/ready")


class ReadHeavyUser(HttpUser):
    """
    Simulates a user that primarily reads data.
    Useful for testing read-heavy scenarios.
    """

    wait_time = between(0.5, 1.5)

    @task
    def get_all_stats(self):
        """Get multiple stats in sequence."""
        self.client.get("/api/graph/stats")
        self.client.get("/api/graph/employee_metrics")

    @task
    def poll_metrics(self):
        """Simulate polling for metrics."""
        for _ in range(5):
            self.client.get("/api/graph/employee_metrics")
            time.sleep(1)


class BurstUser(HttpUser):
    """
    Simulates burst traffic patterns.
    Useful for testing auto-scaling triggers.
    """

    wait_time = between(0.1, 0.5)

    @task
    def burst_reads(self):
        """Burst of read requests."""
        for _ in range(10):
            self.client.get("/api/graph/stats")


# Test configuration for CI/CD
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Log test start."""
    print(f"Starting load test with {environment.runner.user_count} users")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Log test results summary."""
    print("\n=== Load Test Summary ===")
    print(f"Total requests: {environment.stats.total.num_requests}")
    print(f"Total failures: {environment.stats.total.num_failures}")

    if environment.stats.total.num_requests > 0:
        error_rate = (
            environment.stats.total.num_failures /
            environment.stats.total.num_requests * 100
        )
        print(f"Error rate: {error_rate:.2f}%")

    print(f"\nResponse times (ms):")
    print(f"  Median: {environment.stats.total.median_response_time}")
    print(f"  P95: {environment.stats.total.get_response_time_percentile(0.95)}")
    print(f"  P99: {environment.stats.total.get_response_time_percentile(0.99)}")

    # Check against thresholds
    if environment.stats.total.num_failures > 0:
        error_rate = (
            environment.stats.total.num_failures /
            environment.stats.total.num_requests * 100
        )
        if error_rate > 5:
            print(f"\nERROR: Error rate {error_rate:.2f}% exceeds 5% threshold")
            environment.process_exit_code = 1

    p99 = environment.stats.total.get_response_time_percentile(0.99)
    if p99 and p99 > 2000:
        print(f"\nERROR: P99 latency {p99}ms exceeds 2000ms threshold")
        environment.process_exit_code = 1


# Custom thresholds for pass/fail
class TestThresholds:
    """Performance thresholds for load tests."""

    # Maximum error rate (percentage)
    MAX_ERROR_RATE = 5.0

    # Maximum P95 latency (ms)
    MAX_P95_LATENCY = 1000

    # Maximum P99 latency (ms)
    MAX_P99_LATENCY = 2000

    # Minimum requests per second
    MIN_RPS = 10


def check_thresholds(environment) -> bool:
    """
    Check if test results meet performance thresholds.

    Args:
        environment: Locust environment

    Returns:
        True if all thresholds pass
    """
    stats = environment.stats.total

    if stats.num_requests == 0:
        print("No requests recorded")
        return False

    # Check error rate
    error_rate = (stats.num_failures / stats.num_requests) * 100
    if error_rate > TestThresholds.MAX_ERROR_RATE:
        print(f"Error rate {error_rate:.2f}% exceeds {TestThresholds.MAX_ERROR_RATE}%")
        return False

    # Check P95 latency
    p95 = stats.get_response_time_percentile(0.95)
    if p95 and p95 > TestThresholds.MAX_P95_LATENCY:
        print(f"P95 latency {p95}ms exceeds {TestThresholds.MAX_P95_LATENCY}ms")
        return False

    # Check P99 latency
    p99 = stats.get_response_time_percentile(0.99)
    if p99 and p99 > TestThresholds.MAX_P99_LATENCY:
        print(f"P99 latency {p99}ms exceeds {TestThresholds.MAX_P99_LATENCY}ms")
        return False

    return True


# Performance test scenarios
class PerformanceTestScenario:
    """Define different performance test scenarios."""

    # Target scale from requirements
    TARGET_SCALE = {
        "employees": 2000,
        "interactions_per_day": 1_500_000,
        "concurrent_users": 100
    }

    @staticmethod
    def get_scenario(name: str) -> Dict[str, Any]:
        """Get test scenario configuration."""
        scenarios = {
            "smoke": {
                "users": 10,
                "spawn_rate": 5,
                "duration": "1m",
                "description": "Quick smoke test"
            },
            "load": {
                "users": 100,
                "spawn_rate": 10,
                "duration": "5m",
                "description": "Normal load test"
            },
            "stress": {
                "users": 500,
                "spawn_rate": 20,
                "duration": "10m",
                "description": "Stress test"
            },
            "spike": {
                "users": 200,
                "spawn_rate": 50,
                "duration": "2m",
                "description": "Spike test"
            }
        }
        return scenarios.get(name, scenarios["load"])


# Export for direct usage
__all__ = [
    "CausalOrganismUser",
    "ReadHeavyUser",
    "BurstUser",
    "TestThresholds",
    "PerformanceTestScenario",
    "check_thresholds"
]
