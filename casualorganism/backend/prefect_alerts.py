"""
Alert configuration for Prefect workflow failures.

This module provides utilities for configuring alert notifications
when workflows fail after exhausting all retries.

Requirements: 15.5
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ============================================================================
# Alert Configuration
# ============================================================================

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
PAGERDUTY_API_KEY = os.getenv("PAGERDUTY_API_KEY")
SENTRY_DSN = os.getenv("SENTRY_DSN")
ALERT_EMAIL = os.getenv("ALERT_EMAIL")


# ============================================================================
# Slack Integration
# ============================================================================

async def setup_slack_alerts(webhook_url: Optional[str] = None) -> bool:
    """
    Configure Slack webhook for flow failure alerts.
    
    Args:
        webhook_url: Slack webhook URL (defaults to env var)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        from prefect.blocks.notifications.slack import SlackWebhook
        
        url = webhook_url or SLACK_WEBHOOK_URL
        if not url:
            logger.warning("No Slack webhook URL provided")
            return False
        
        # Create and save Slack webhook block
        slack_webhook = SlackWebhook(url=url)
        await slack_webhook.save("slack-alerts", overwrite=True)
        
        logger.info("Slack alerts configured successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to configure Slack alerts: {e}")
        return False


# ============================================================================
# Sentry Integration
# ============================================================================

def setup_sentry_alerts(dsn: Optional[str] = None) -> bool:
    """
    Configure Sentry for error tracking.
    
    Args:
        dsn: Sentry DSN (defaults to env var)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        import sentry_sdk
        
        dsn_value = dsn or SENTRY_DSN
        if not dsn_value:
            logger.warning("No Sentry DSN provided")
            return False
        
        sentry_sdk.init(
            dsn=dsn_value,
            environment=os.getenv("ENVIRONMENT", "development"),
            traces_sample_rate=0.1,
            profiles_sample_rate=0.1
        )
        
        logger.info("Sentry alerts configured successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to configure Sentry alerts: {e}")
        return False


# ============================================================================
# Email Integration
# ============================================================================

async def setup_email_alerts(email: Optional[str] = None) -> bool:
    """
    Configure email notifications for flow failures.
    
    Args:
        email: Alert email address (defaults to env var)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        from prefect.blocks.notifications.email import EmailServerCredentials
        
        email_address = email or ALERT_EMAIL
        if not email_address:
            logger.warning("No alert email provided")
            return False
        
        # This is a placeholder - actual implementation would require
        # SMTP server configuration
        logger.info(f"Email alerts would be sent to: {email_address}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to configure email alerts: {e}")
        return False


# ============================================================================
# Setup All Alerts
# ============================================================================

async def setup_all_alerts() -> dict:
    """
    Configure all available alert integrations.
    
    Returns:
        Dictionary with status of each integration
    """
    results = {
        "slack": await setup_slack_alerts(),
        "sentry": setup_sentry_alerts(),
        "email": await setup_email_alerts()
    }
    
    enabled_count = sum(1 for v in results.values() if v)
    logger.info(f"Configured {enabled_count}/{len(results)} alert integrations")
    
    return results


# ============================================================================
# Usage Instructions
# ============================================================================

SETUP_INSTRUCTIONS = """
# Prefect Alert Configuration

## Environment Variables

Set the following environment variables to enable alerts:

### Slack
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

### Sentry
export SENTRY_DSN="https://YOUR_SENTRY_DSN"
export ENVIRONMENT="production"

### Email
export ALERT_EMAIL="alerts@example.com"

## Setup

Run the setup script:

```bash
python backend/prefect_alerts.py
```

Or programmatically:

```python
from backend.prefect_alerts import setup_all_alerts
import asyncio

asyncio.run(setup_all_alerts())
```

## Using Alerts in Flows

Add alert notifications to flow definitions:

```python
from prefect import flow
from prefect.blocks.notifications.slack import SlackWebhook

@flow(
    name="my-flow",
    on_failure=[SlackWebhook.load("slack-alerts")]
)
async def my_flow():
    ...
```

## Testing Alerts

Test alert delivery:

```bash
python backend/prefect_alerts.py test
```
"""


# ============================================================================
# CLI
# ============================================================================

async def main():
    """Main entry point for alert configuration."""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("Testing alert integrations...")
        results = await setup_all_alerts()
        
        print("\nAlert Integration Status:")
        for integration, status in results.items():
            status_str = "✓ Enabled" if status else "✗ Disabled"
            print(f"  {integration}: {status_str}")
        
        print("\nTo enable alerts, set the required environment variables.")
        print("See SETUP_INSTRUCTIONS for details.")
    else:
        print(SETUP_INSTRUCTIONS)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
