"""
Celery Beat configuration for scheduled tasks.

This module configures periodic tasks including:
- Export cleanup (daily at 2 AM UTC)
- Materialized view refresh (hourly)
- Other scheduled maintenance tasks
"""
from celery.schedules import crontab

# Celery Beat schedule configuration
beat_schedule = {
    # Cleanup old exports daily at 2 AM UTC
    'cleanup-old-exports': {
        'task': 'backend.worker.cleanup_old_exports',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM UTC
        'options': {
            'expires': 3600,  # Task expires after 1 hour if not executed
        }
    },
    
    # Timeout expired intervention approvals hourly
    'timeout-expired-approvals': {
        'task': 'backend.worker.timeout_expired_intervention_approvals',
        'schedule': crontab(minute=0),  # Every hour at minute 0
        'options': {
            'expires': 3600,  # Task expires after 1 hour if not executed
        }
    },
    
    # Example: Refresh materialized views hourly
    # 'refresh-materialized-views': {
    #     'task': 'backend.worker.refresh_materialized_views',
    #     'schedule': crontab(minute=0),  # Every hour at minute 0
    # },
    
    # Example: Incremental graph updates every 5 minutes
    # 'incremental-graph-update': {
    #     'task': 'backend.worker.process_interaction_stream',
    #     'schedule': crontab(minute='*/5'),  # Every 5 minutes
    # },
}

# Celery Beat configuration
beat_config = {
    'beat_schedule': beat_schedule,
    'timezone': 'UTC',
}
