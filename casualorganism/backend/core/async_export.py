"""
Asynchronous Export Service for handling large data exports without blocking API requests.

This module implements:
- Export task queueing
- Task status tracking
- CSV generation
- S3-compatible storage upload
- Signed download URLs
- Automatic cleanup of old exports
"""
from typing import Optional, Dict, Any
import os
import time
import json
from datetime import datetime, timedelta
from celery import Celery
from celery.result import AsyncResult
import pandas as pd
import boto3
from botocore.exceptions import ClientError


class AsyncExportService:
    """
    Handles asynchronous data exports with task queueing and status tracking.
    
    Requirements:
    - 11.1: Implement export task queueing
    - 11.2: Add task status tracking
    - 11.6: Return task ID immediately
    """
    
    def __init__(
        self,
        celery_app: Celery,
        s3_endpoint: Optional[str] = None,
        s3_access_key: Optional[str] = None,
        s3_secret_key: Optional[str] = None,
        s3_bucket: str = "causal-organism-exports",
        s3_region: str = "us-east-1"
    ):
        """
        Initialize AsyncExportService.
        
        Args:
            celery_app: Celery application instance
            s3_endpoint: S3-compatible endpoint URL (None for AWS S3)
            s3_access_key: S3 access key
            s3_secret_key: S3 secret key
            s3_bucket: S3 bucket name for exports
            s3_region: S3 region
        """
        self.celery = celery_app
        self.s3_bucket = s3_bucket
        
        # Initialize S3 client
        s3_config = {
            'region_name': s3_region
        }
        
        if s3_endpoint:
            s3_config['endpoint_url'] = s3_endpoint
        
        if s3_access_key and s3_secret_key:
            s3_config['aws_access_key_id'] = s3_access_key
            s3_config['aws_secret_access_key'] = s3_secret_key
        
        self.s3_client = boto3.client('s3', **s3_config)
        
        # Ensure bucket exists
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Create S3 bucket if it doesn't exist."""
        try:
            self.s3_client.head_bucket(Bucket=self.s3_bucket)
        except ClientError:
            try:
                self.s3_client.create_bucket(Bucket=self.s3_bucket)
                print(f"Created S3 bucket: {self.s3_bucket}")
            except Exception as e:
                print(f"Warning: Could not create S3 bucket: {e}")
    
    async def request_export(
        self,
        export_type: str,
        params: Dict[str, Any],
        user_id: str
    ) -> Dict[str, str]:
        """
        Queue export task and return task ID immediately.
        
        Requirements:
        - 11.1: Queue export task to Worker_Pool
        - 11.2: Return task ID and status URL within 500ms
        
        Args:
            export_type: Type of export (e.g., "employee_metrics", "graph_data")
            params: Export parameters (filters, date ranges, etc.)
            user_id: User requesting the export
        
        Returns:
            Dict with task_id and status_url
        """
        # Import the Celery task (avoid circular import)
        from backend.worker import export_employee_metrics
        
        # Queue the export task
        task = export_employee_metrics.delay(
            export_type=export_type,
            params=params,
            user_id=user_id
        )
        
        return {
            "task_id": task.id,
            "status_url": f"/api/exports/{task.id}/status",
            "status": "queued"
        }
    
    async def get_export_status(self, task_id: str) -> Dict[str, Any]:
        """
        Check export task status.
        
        Requirements:
        - 11.2: Provide endpoint to check export task status
        - 11.7: Generate signed URL valid for 24 hours
        
        Args:
            task_id: Celery task ID
        
        Returns:
            Dict with status, progress, download_url (if completed), error (if failed)
        """
        task = AsyncResult(task_id, app=self.celery)
        
        if task.ready():
            if task.successful():
                # Task completed successfully
                result = task.result
                s3_key = result.get("s3_key")
                
                if s3_key:
                    # Generate signed URL for download
                    download_url = self._generate_signed_url(s3_key)
                    
                    return {
                        "status": "completed",
                        "download_url": download_url,
                        "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
                        "file_size": result.get("file_size"),
                        "row_count": result.get("row_count")
                    }
                else:
                    return {
                        "status": "completed",
                        "error": "Export completed but no file was generated"
                    }
            else:
                # Task failed
                return {
                    "status": "failed",
                    "error": str(task.result) if task.result else "Unknown error"
                }
        else:
            # Task still processing
            progress = 0
            if task.info and isinstance(task.info, dict):
                progress = task.info.get("progress", 0)
            
            return {
                "status": "processing",
                "progress": progress
            }
    
    def _generate_signed_url(self, s3_key: str, expiration: int = 86400) -> str:
        """
        Generate signed URL for S3 object download.
        
        Requirements:
        - 11.7: Generate signed download URLs valid for 24 hours
        
        Args:
            s3_key: S3 object key
            expiration: URL expiration time in seconds (default: 24 hours)
        
        Returns:
            Signed URL string
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.s3_bucket,
                    'Key': s3_key
                },
                ExpiresIn=expiration
            )
            return url
        except Exception as e:
            print(f"Error generating signed URL: {e}")
            return ""
    
    async def list_user_exports(self, user_id: str, limit: int = 10) -> list:
        """
        List recent exports for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of exports to return
        
        Returns:
            List of export metadata
        """
        try:
            # List objects in user's export folder
            prefix = f"exports/{user_id}/"
            response = self.s3_client.list_objects_v2(
                Bucket=self.s3_bucket,
                Prefix=prefix,
                MaxKeys=limit
            )
            
            exports = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    exports.append({
                        "key": obj['Key'],
                        "size": obj['Size'],
                        "last_modified": obj['LastModified'].isoformat(),
                        "download_url": self._generate_signed_url(obj['Key'])
                    })
            
            return exports
        except Exception as e:
            print(f"Error listing exports: {e}")
            return []
    
    async def delete_export(self, s3_key: str) -> bool:
        """
        Delete an export file from S3.
        
        Args:
            s3_key: S3 object key
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.s3_bucket,
                Key=s3_key
            )
            return True
        except Exception as e:
            print(f"Error deleting export: {e}")
            return False
    
    async def cleanup_old_exports(self, days: int = 7) -> int:
        """
        Delete exports older than specified days.
        
        Requirements:
        - 11.8: Delete export files older than 7 days
        
        Args:
            days: Age threshold in days
        
        Returns:
            Number of files deleted
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # List all objects in exports folder
            response = self.s3_client.list_objects_v2(
                Bucket=self.s3_bucket,
                Prefix="exports/"
            )
            
            deleted_count = 0
            if 'Contents' in response:
                for obj in response['Contents']:
                    if obj['LastModified'].replace(tzinfo=None) < cutoff_date:
                        self.s3_client.delete_object(
                            Bucket=self.s3_bucket,
                            Key=obj['Key']
                        )
                        deleted_count += 1
                        print(f"Deleted old export: {obj['Key']}")
            
            return deleted_count
        except Exception as e:
            print(f"Error cleaning up old exports: {e}")
            return 0


class ExportHelper:
    """
    Helper class for export data fetching and formatting.
    """
    
    @staticmethod
    def fetch_employee_metrics(params: Dict[str, Any]) -> pd.DataFrame:
        """
        Fetch employee metrics data based on parameters.
        
        Args:
            params: Query parameters (filters, date ranges, etc.)
        
        Returns:
            DataFrame with employee metrics
        """
        # This will be implemented to fetch from Neo4j/TimescaleDB
        # For now, return empty DataFrame
        return pd.DataFrame()
    
    @staticmethod
    def fetch_graph_data(params: Dict[str, Any]) -> pd.DataFrame:
        """
        Fetch graph data based on parameters.
        
        Args:
            params: Query parameters
        
        Returns:
            DataFrame with graph data
        """
        return pd.DataFrame()
    
    @staticmethod
    def format_csv(df: pd.DataFrame, export_type: str) -> pd.DataFrame:
        """
        Format DataFrame for CSV export.
        
        Args:
            df: Input DataFrame
            export_type: Type of export
        
        Returns:
            Formatted DataFrame
        """
        # Add timestamp column
        df['export_timestamp'] = datetime.utcnow().isoformat()
        return df
