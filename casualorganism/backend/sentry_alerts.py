"""
Sentry Alert Configuration

This module provides utilities for configuring Sentry alerts programmatically.

Requirements:
- 17.5: Configure alert for >10 errors/minute
- 17.6: Configure alert for new error types
"""

import os
import requests
from typing import Dict, List, Optional, Any


class SentryAlertManager:
    """
    Manager for Sentry alert rules.
    
    Requirements:
    - 17.5: Alert when error rate exceeds 10 errors/minute
    - 17.6: Alert on new error types
    """
    
    def __init__(
        self,
        auth_token: Optional[str] = None,
        organization: Optional[str] = None,
        project: Optional[str] = None
    ):
        """
        Initialize Sentry alert manager.
        
        Args:
            auth_token: Sentry API auth token (or from SENTRY_AUTH_TOKEN env var)
            organization: Sentry organization slug (or from SENTRY_ORG env var)
            project: Sentry project slug (or from SENTRY_PROJECT env var)
        """
        self.auth_token = auth_token or os.getenv("SENTRY_AUTH_TOKEN")
        self.organization = organization or os.getenv("SENTRY_ORG")
        self.project = project or os.getenv("SENTRY_PROJECT")
        self.base_url = "https://sentry.io/api/0"
        
        if not all([self.auth_token, self.organization, self.project]):
            print("Warning: Sentry alert manager not fully configured")
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Make authenticated request to Sentry API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            data: Request body data
        
        Returns:
            Response JSON or None on error
        """
        if not self.auth_token:
            print("Error: SENTRY_AUTH_TOKEN not configured")
            return None
        
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Sentry API request failed: {e}")
            return None
    
    def create_error_rate_alert(
        self,
        name: str = "High Error Rate Alert",
        threshold: int = 600,
        time_window: int = 60,
        action_type: str = "slack",
        action_config: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Create alert for high error rate.
        
        Requirements:
        - 17.5: Alert when error rate exceeds 10 errors/minute
        
        Args:
            name: Alert rule name
            threshold: Number of errors to trigger alert (default: 600 = 10/min × 60min)
            time_window: Time window in minutes (default: 60)
            action_type: Action type (slack, email, pagerduty, webhook)
            action_config: Action-specific configuration
        
        Returns:
            Created alert rule or None on error
        """
        endpoint = f"/projects/{self.organization}/{self.project}/rules/"
        
        # Default action config
        if action_config is None:
            action_config = {}
        
        # Build action based on type
        actions = []
        if action_type == "slack":
            actions.append({
                "id": "sentry.integrations.slack.notify_action.SlackNotifyServiceAction",
                "workspace": action_config.get("workspace"),
                "channel": action_config.get("channel", "#alerts"),
                "tags": "environment,level"
            })
        elif action_type == "email":
            actions.append({
                "id": "sentry.mail.actions.NotifyEmailAction",
                "targetType": "IssueOwners",
                "targetIdentifier": ""
            })
        
        data = {
            "name": name,
            "environment": None,  # Apply to all environments
            "actionMatch": "all",
            "frequency": time_window,
            "conditions": [
                {
                    "id": "sentry.rules.conditions.event_frequency.EventFrequencyCondition",
                    "value": threshold,
                    "interval": f"{time_window}m"
                }
            ],
            "filters": [
                {
                    "id": "sentry.rules.filters.level.LevelFilter",
                    "match": "gte",
                    "level": "40"  # Error level (40) and above
                }
            ],
            "actions": actions
        }
        
        result = self._make_request("POST", endpoint, data)
        if result:
            print(f"Created error rate alert: {name}")
        return result
    
    def create_new_issue_alert(
        self,
        name: str = "New Error Type Alert",
        action_type: str = "slack",
        action_config: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Create alert for new error types.
        
        Requirements:
        - 17.6: Alert on new error types
        
        Args:
            name: Alert rule name
            action_type: Action type (slack, email, pagerduty, webhook)
            action_config: Action-specific configuration
        
        Returns:
            Created alert rule or None on error
        """
        endpoint = f"/projects/{self.organization}/{self.project}/rules/"
        
        # Default action config
        if action_config is None:
            action_config = {}
        
        # Build action based on type
        actions = []
        if action_type == "slack":
            actions.append({
                "id": "sentry.integrations.slack.notify_action.SlackNotifyServiceAction",
                "workspace": action_config.get("workspace"),
                "channel": action_config.get("channel", "#alerts"),
                "tags": "environment,level"
            })
        elif action_type == "email":
            actions.append({
                "id": "sentry.mail.actions.NotifyEmailAction",
                "targetType": "IssueOwners",
                "targetIdentifier": ""
            })
        
        data = {
            "name": name,
            "environment": None,  # Apply to all environments
            "actionMatch": "all",
            "frequency": 30,  # Check every 30 minutes
            "conditions": [
                {
                    "id": "sentry.rules.conditions.first_seen_event.FirstSeenEventCondition"
                }
            ],
            "filters": [
                {
                    "id": "sentry.rules.filters.level.LevelFilter",
                    "match": "gte",
                    "level": "40"  # Error level (40) and above
                }
            ],
            "actions": actions
        }
        
        result = self._make_request("POST", endpoint, data)
        if result:
            print(f"Created new issue alert: {name}")
        return result
    
    def list_alert_rules(self) -> Optional[List[Dict]]:
        """
        List all alert rules for the project.
        
        Returns:
            List of alert rules or None on error
        """
        endpoint = f"/projects/{self.organization}/{self.project}/rules/"
        return self._make_request("GET", endpoint)
    
    def delete_alert_rule(self, rule_id: str) -> bool:
        """
        Delete an alert rule.
        
        Args:
            rule_id: Alert rule ID
        
        Returns:
            True if deleted successfully, False otherwise
        """
        endpoint = f"/projects/{self.organization}/{self.project}/rules/{rule_id}/"
        result = self._make_request("DELETE", endpoint)
        return result is not None
    
    def get_error_statistics(
        self,
        stat: str = "received",
        since: str = "1d",
        resolution: str = "1h"
    ) -> Optional[List[List]]:
        """
        Get error statistics from Sentry.
        
        Requirements:
        - 17.8: Provide API for querying error statistics
        
        Args:
            stat: Statistic type (received, rejected, blacklisted)
            since: Time range (1h, 1d, 1w, 30d)
            resolution: Data resolution (1h, 1d)
        
        Returns:
            List of [timestamp, count] pairs or None on error
        """
        endpoint = f"/projects/{self.organization}/{self.project}/stats/"
        params = {
            "stat": stat,
            "since": since,
            "resolution": resolution
        }
        
        # Add query params to endpoint
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        endpoint_with_params = f"{endpoint}?{query_string}"
        
        return self._make_request("GET", endpoint_with_params)
    
    def get_recent_issues(
        self,
        limit: int = 25,
        query: Optional[str] = None
    ) -> Optional[List[Dict]]:
        """
        Get recent issues from Sentry.
        
        Args:
            limit: Maximum number of issues to return
            query: Search query (e.g., "is:unresolved")
        
        Returns:
            List of issues or None on error
        """
        endpoint = f"/projects/{self.organization}/{self.project}/issues/"
        params = {"limit": limit}
        if query:
            params["query"] = query
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        endpoint_with_params = f"{endpoint}?{query_string}"
        
        return self._make_request("GET", endpoint_with_params)


def setup_default_alerts():
    """
    Set up default alert rules for the project.
    
    Requirements:
    - 17.5: Configure alert for >10 errors/minute
    - 17.6: Configure alert for new error types
    
    This function should be run once during initial setup.
    """
    manager = SentryAlertManager()
    
    if not all([manager.auth_token, manager.organization, manager.project]):
        print("Sentry alert manager not configured. Skipping alert setup.")
        print("Set SENTRY_AUTH_TOKEN, SENTRY_ORG, and SENTRY_PROJECT environment variables.")
        return
    
    # Create high error rate alert (>10 errors/minute)
    print("Creating high error rate alert...")
    manager.create_error_rate_alert(
        name="High Error Rate (>10 errors/minute)",
        threshold=600,  # 10 errors/min × 60 minutes
        time_window=60,
        action_type="slack",
        action_config={
            "channel": "#alerts"
        }
    )
    
    # Create new error type alert
    print("Creating new error type alert...")
    manager.create_new_issue_alert(
        name="New Error Type Detected",
        action_type="slack",
        action_config={
            "channel": "#alerts"
        }
    )
    
    print("Alert setup complete!")


if __name__ == "__main__":
    # Run setup when executed directly
    setup_default_alerts()
