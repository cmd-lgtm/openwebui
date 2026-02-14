#!/bin/bash
# Start Celery Beat scheduler for periodic tasks
#
# Requirements:
# - 11.8: Schedule export cleanup with Celery beat
#
# Usage:
#   ./scripts/start_celery_beat.sh

echo "Starting Celery Beat scheduler..."

# Set environment variables if needed
export REDIS_URL=${REDIS_URL:-redis://localhost:6379/0}

# Start Celery Beat
celery -A backend.worker beat \
    --loglevel=info \
    --pidfile=/tmp/celerybeat.pid \
    --schedule=/tmp/celerybeat-schedule

# Note: In production, use a persistent schedule file location
# and consider running as a systemd service or in a container
