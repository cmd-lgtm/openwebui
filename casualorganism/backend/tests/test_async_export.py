"""
Tests for Asynchronous Export Service.

This module tests:
- Export task queueing
- Task status tracking
- Export cleanup
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.core.async_export import AsyncExportService
from celery import Celery
from datetime import datetime, timedelta


@pytest.fixture
def mock_celery_app():
    """Create a mock Celery app."""
    app = Mock(spec=Celery)
    return app


@pytest.fixture
def mock_s3_client():
    """Create a mock S3 client."""
    client = MagicMock()
    client.head_bucket.return_value = True
    client.generate_presigned_url.return_value = "https://s3.example.com/signed-url"
    return client


@pytest.fixture
def export_service(mock_celery_app, mock_s3_client):
    """Create AsyncExportService with mocked dependencies."""
    with patch('backend.core.async_export.boto3.client', return_value=mock_s3_client):
        service = AsyncExportService(
            celery_app=mock_celery_app,
            s3_endpoint="http://localhost:9000",
            s3_access_key="test_key",
            s3_secret_key="test_secret",
            s3_bucket="test-bucket"
        )
        service.s3_client = mock_s3_client
        return service


@pytest.mark.asyncio
async def test_request_export_returns_task_id(export_service):
    """
    Test that request_export returns task ID immediately.
    
    Requirements:
    - 11.1: Queue export task to Worker_Pool
    - 11.2: Return task ID and status URL within 500ms
    """
    # Mock the Celery task
    mock_task = Mock()
    mock_task.id = "test-task-123"
    
    with patch('backend.worker.export_employee_metrics') as mock_export:
        mock_export.delay.return_value = mock_task
        
        result = await export_service.request_export(
            export_type="employee_metrics",
            params={"team": "Engineering"},
            user_id="user_123"
        )
    
    # Verify response structure
    assert "task_id" in result
    assert result["task_id"] == "test-task-123"
    assert "status_url" in result
    assert result["status_url"] == "/api/exports/test-task-123/status"
    assert result["status"] == "queued"


@pytest.mark.asyncio
async def test_get_export_status_processing(export_service):
    """
    Test getting status of a processing export.
    
    Requirements:
    - 11.2: Provide endpoint to check export task status
    """
    with patch('backend.core.async_export.AsyncResult') as mock_result:
        # Mock a processing task
        task = Mock()
        task.ready.return_value = False
        task.info = {"progress": 50}
        mock_result.return_value = task
        
        result = await export_service.get_export_status("test-task-123")
    
    assert result["status"] == "processing"
    assert result["progress"] == 50


@pytest.mark.asyncio
async def test_get_export_status_completed(export_service):
    """
    Test getting status of a completed export.
    
    Requirements:
    - 11.2: Provide endpoint to check export task status
    - 11.7: Generate signed URL valid for 24 hours
    """
    with patch('backend.core.async_export.AsyncResult') as mock_result:
        # Mock a completed task
        task = Mock()
        task.ready.return_value = True
        task.successful.return_value = True
        task.result = {
            "s3_key": "exports/user_123/test.csv",
            "file_size": 1024,
            "row_count": 100
        }
        mock_result.return_value = task
        
        result = await export_service.get_export_status("test-task-123")
    
    assert result["status"] == "completed"
    assert "download_url" in result
    assert result["download_url"] == "https://s3.example.com/signed-url"
    assert "expires_at" in result
    assert result["file_size"] == 1024
    assert result["row_count"] == 100


@pytest.mark.asyncio
async def test_get_export_status_failed(export_service):
    """Test getting status of a failed export."""
    with patch('backend.core.async_export.AsyncResult') as mock_result:
        # Mock a failed task
        task = Mock()
        task.ready.return_value = True
        task.successful.return_value = False
        task.result = Exception("Database connection failed")
        mock_result.return_value = task
        
        result = await export_service.get_export_status("test-task-123")
    
    assert result["status"] == "failed"
    assert "error" in result


@pytest.mark.asyncio
async def test_cleanup_old_exports(export_service):
    """
    Test cleanup of old exports.
    
    Requirements:
    - 11.8: Delete export files older than 7 days
    """
    # Mock S3 list_objects_v2 response
    old_date = datetime.utcnow() - timedelta(days=10)
    recent_date = datetime.utcnow() - timedelta(days=3)
    
    export_service.s3_client.list_objects_v2.return_value = {
        'Contents': [
            {'Key': 'exports/user1/old.csv', 'LastModified': old_date},
            {'Key': 'exports/user2/recent.csv', 'LastModified': recent_date},
            {'Key': 'exports/user3/old2.csv', 'LastModified': old_date}
        ]
    }
    
    deleted_count = await export_service.cleanup_old_exports(days=7)
    
    # Should delete 2 old files
    assert deleted_count == 2
    
    # Verify delete_object was called for old files
    assert export_service.s3_client.delete_object.call_count == 2


@pytest.mark.asyncio
async def test_list_user_exports(export_service):
    """Test listing user exports."""
    export_service.s3_client.list_objects_v2.return_value = {
        'Contents': [
            {
                'Key': 'exports/user_123/export1.csv',
                'Size': 1024,
                'LastModified': datetime.utcnow()
            },
            {
                'Key': 'exports/user_123/export2.csv',
                'Size': 2048,
                'LastModified': datetime.utcnow()
            }
        ]
    }
    
    exports = await export_service.list_user_exports("user_123", limit=10)
    
    assert len(exports) == 2
    assert exports[0]['key'] == 'exports/user_123/export1.csv'
    assert exports[0]['size'] == 1024
    assert 'download_url' in exports[0]


@pytest.mark.asyncio
async def test_delete_export(export_service):
    """Test deleting an export."""
    export_service.s3_client.delete_object.return_value = True
    
    result = await export_service.delete_export("exports/user_123/test.csv")
    
    assert result is True
    export_service.s3_client.delete_object.assert_called_once_with(
        Bucket="test-bucket",
        Key="exports/user_123/test.csv"
    )


def test_generate_signed_url(export_service):
    """
    Test signed URL generation.
    
    Requirements:
    - 11.7: Generate signed download URLs valid for 24 hours
    """
    url = export_service._generate_signed_url("exports/user_123/test.csv")
    
    assert url == "https://s3.example.com/signed-url"
    export_service.s3_client.generate_presigned_url.assert_called_once_with(
        'get_object',
        Params={
            'Bucket': 'test-bucket',
            'Key': 'exports/user_123/test.csv'
        },
        ExpiresIn=86400  # 24 hours
    )


@pytest.mark.asyncio
async def test_request_export_with_filters(export_service):
    """Test requesting export with filter parameters."""
    mock_task = Mock()
    mock_task.id = "test-task-456"
    
    with patch('backend.worker.export_employee_metrics') as mock_export:
        mock_export.delay.return_value = mock_task
        
        result = await export_service.request_export(
            export_type="employee_metrics",
            params={
                "team": "Engineering",
                "min_burnout_score": 60
            },
            user_id="user_123"
        )
    
    # Verify task was queued with correct parameters
    mock_export.delay.assert_called_once_with(
        export_type="employee_metrics",
        params={
            "team": "Engineering",
            "min_burnout_score": 60
        },
        user_id="user_123"
    )
    
    assert result["task_id"] == "test-task-456"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
