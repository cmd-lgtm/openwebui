# Asynchronous Export Service

## Overview

The Asynchronous Export Service enables large data exports without blocking API requests. Exports are queued as background tasks, processed by Celery workers, and stored in S3-compatible storage with signed download URLs.

## Architecture

```
Client Request → API Endpoint → Celery Queue → Worker Process → S3 Storage
                      ↓
                 Task ID (immediate response)
                      ↓
                 Status Polling → Download URL (when complete)
```

## Requirements Implemented

- **11.1**: Export task queueing - Tasks are queued to Celery worker pool
- **11.2**: Task status tracking - API returns task ID within 500ms, status endpoint available
- **11.3**: CSV generation - Workers generate CSV files from database queries
- **11.4**: Progress updates - Workers report progress (10%, 40%, 70%, 100%)
- **11.5**: S3 upload - Exports stored in S3-compatible storage
- **11.6**: Immediate response - API returns task ID immediately
- **11.7**: Signed URLs - Download URLs valid for 24 hours
- **11.8**: Automatic cleanup - Celery Beat deletes exports older than 7 days

## API Endpoints

### 1. Request Export

```http
POST /api/exports/request
Content-Type: application/json

{
  "export_type": "employee_metrics",
  "params": {
    "team": "Engineering",
    "min_burnout_score": 60
  },
  "user_id": "user_123"
}
```

**Response (< 500ms):**
```json
{
  "task_id": "abc-123-def-456",
  "status_url": "/api/exports/abc-123-def-456/status",
  "status": "queued"
}
```

### 2. Check Export Status

```http
GET /api/exports/{task_id}/status
```

**Response (Processing):**
```json
{
  "status": "processing",
  "progress": 70
}
```

**Response (Completed):**
```json
{
  "status": "completed",
  "download_url": "https://s3.amazonaws.com/bucket/exports/user_123/...",
  "expires_at": "2024-01-02T12:00:00",
  "file_size": 1048576,
  "row_count": 2000
}
```

**Response (Failed):**
```json
{
  "status": "failed",
  "error": "Database connection timeout"
}
```

### 3. List User Exports

```http
GET /api/exports/user/{user_id}?limit=10
```

**Response:**
```json
{
  "exports": [
    {
      "key": "exports/user_123/employee_metrics_20240101_120000_abc123.csv",
      "size": 1048576,
      "last_modified": "2024-01-01T12:00:00",
      "download_url": "https://..."
    }
  ]
}
```

### 4. Delete Export

```http
DELETE /api/exports/{s3_key}
```

**Response:**
```json
{
  "status": "deleted",
  "key": "exports/user_123/..."
}
```

## Export Types

### 1. Employee Metrics
- **Type**: `employee_metrics`
- **Data Source**: Neo4j materialized views
- **Columns**: employee_id, name, team, role, degree_centrality, betweenness_centrality, clustering_coeff, burnout_score
- **Filters**: team, min_burnout_score

### 2. Graph Data
- **Type**: `graph_data`
- **Data Source**: Neo4j edges
- **Columns**: source_id, source_name, target_id, target_name, weight, last_updated

### 3. Interaction History
- **Type**: `interaction_history`
- **Data Source**: TimescaleDB (when implemented)
- **Columns**: timestamp, source, target, type, weight

## Configuration

### Environment Variables

```bash
# Redis (required)
REDIS_URL=redis://localhost:6379/0

# S3 Configuration (required)
S3_BUCKET=causal-organism-exports
S3_REGION=us-east-1

# For AWS S3
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# For S3-compatible storage (MinIO, etc.)
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin

# Neo4j (required)
GRAPH_DB_URL=bolt://localhost:7687
GRAPH_DB_USER=neo4j
GRAPH_DB_PASSWORD=password
```

## Running the Service

### 1. Start Celery Worker

```bash
celery -A backend.worker worker --loglevel=info
```

### 2. Start Celery Beat (for scheduled cleanup)

```bash
celery -A backend.worker beat --loglevel=info
```

Or use the provided script:
```bash
./scripts/start_celery_beat.sh
```

### 3. Start API Server

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

## Celery Beat Schedule

The cleanup job runs daily at 2 AM UTC:

```python
'cleanup-old-exports': {
    'task': 'backend.worker.cleanup_old_exports',
    'schedule': crontab(hour=2, minute=0),
}
```

## Testing

### Manual Test

```bash
# 1. Request export
curl -X POST http://localhost:8000/api/exports/request \
  -H "Content-Type: application/json" \
  -d '{"export_type": "employee_metrics", "user_id": "test_user"}'

# Response: {"task_id": "abc-123", "status_url": "/api/exports/abc-123/status"}

# 2. Check status
curl http://localhost:8000/api/exports/abc-123/status

# 3. Download when complete
curl -o export.csv "https://s3.amazonaws.com/bucket/exports/..."
```

### Unit Tests

```python
import pytest
from backend.core.async_export import AsyncExportService

@pytest.mark.asyncio
async def test_request_export():
    service = AsyncExportService(celery_app, ...)
    result = await service.request_export("employee_metrics", {}, "user_123")
    
    assert "task_id" in result
    assert "status_url" in result
    assert result["status"] == "queued"

@pytest.mark.asyncio
async def test_cleanup_old_exports():
    service = AsyncExportService(celery_app, ...)
    deleted = await service.cleanup_old_exports(days=7)
    
    assert deleted >= 0
```

## Performance Characteristics

- **API Response Time**: < 500ms (requirement 11.2)
- **Export Generation**: Varies by data size
  - Small (< 1000 rows): 1-5 seconds
  - Medium (1000-10000 rows): 5-30 seconds
  - Large (> 10000 rows): 30-120 seconds
- **Download URL Expiration**: 24 hours
- **Cleanup Frequency**: Daily at 2 AM UTC
- **Retention Period**: 7 days

## Error Handling

### Common Errors

1. **S3 Connection Failed**
   - Check S3_ENDPOINT, S3_ACCESS_KEY, S3_SECRET_KEY
   - Verify bucket exists and is accessible

2. **Database Connection Failed**
   - Check GRAPH_DB_URL, GRAPH_DB_USER, GRAPH_DB_PASSWORD
   - Verify Neo4j is running

3. **Celery Worker Not Running**
   - Start worker: `celery -A backend.worker worker`
   - Check REDIS_URL is correct

4. **Export Task Failed**
   - Check worker logs for detailed error
   - Verify data exists for requested filters

## Security Considerations

1. **Signed URLs**: Download URLs expire after 24 hours
2. **User Isolation**: Exports stored in user-specific folders
3. **Access Control**: Add authentication/authorization to endpoints
4. **Data Sanitization**: Validate and sanitize all input parameters
5. **Rate Limiting**: Consider adding rate limits to prevent abuse

## Future Enhancements

1. **Compression**: Gzip CSV files before upload
2. **Multiple Formats**: Support JSON, Parquet, Excel
3. **Email Notifications**: Send email when export completes
4. **Streaming Exports**: Stream large exports directly to client
5. **Incremental Exports**: Export only changed data since last export
6. **Export Templates**: Save and reuse export configurations
7. **Scheduled Exports**: Recurring exports on schedule

## Monitoring

### Metrics to Track

- Export request rate
- Export success/failure rate
- Average export generation time
- S3 upload success rate
- Storage usage
- Cleanup job execution

### Logs to Monitor

- Export task start/complete
- S3 upload success/failure
- Cleanup job execution
- Error details for failed exports

## Troubleshooting

### Export Stuck in "Processing"

1. Check Celery worker is running
2. Check worker logs for errors
3. Verify database connectivity
4. Check task status in Redis: `redis-cli GET celery-task-meta-{task_id}`

### Download URL Not Working

1. Verify URL hasn't expired (24 hour limit)
2. Check S3 bucket permissions
3. Verify file exists in S3: `aws s3 ls s3://bucket/exports/`

### Cleanup Job Not Running

1. Verify Celery Beat is running
2. Check beat schedule: `celery -A backend.worker inspect scheduled`
3. Check beat logs for errors
