"""
Background job queue using Redis
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Callable, Dict, Optional
from enum import Enum
import uuid

import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Job status enum"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class QueueService:
    """Redis-based background job queue"""

    def __init__(self):
        self._redis: Optional[Redis] = None
        self._enabled = False
        self._worker_tasks: Dict[str, asyncio.Task] = {}

    async def connect(self):
        """Connect to Redis"""
        if not settings.REDIS_ENABLED:
            logger.info("Redis queue disabled")
            return

        try:
            self._redis = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
            await self._redis.ping()
            self._enabled = True
            logger.info("Queue service connected to Redis")
        except Exception as e:
            logger.warning(f"Queue connection failed: {e}. Queue disabled.")
            self._enabled = False
            self._redis = None

    async def disconnect(self):
        """Disconnect from Redis"""
        # Cancel all worker tasks
        for task in self._worker_tasks.values():
            task.cancel()
        self._worker_tasks = {}

        if self._redis:
            await self._redis.close()
            self._redis = None
            self._enabled = False

    @property
    def is_enabled(self) -> bool:
        """Check if queue is enabled"""
        return self._enabled and self._redis is not None

    async def enqueue(
        self,
        job_type: str,
        payload: Dict[str, Any],
        job_id: Optional[str] = None
    ) -> str:
        """
        Add a job to the queue.

        Args:
            job_type: Type of job (e.g., 'code_execution', 'file_indexing')
            payload: Job data
            job_id: Optional custom job ID

        Returns:
            Job ID
        """
        if not self.is_enabled:
            logger.warning("Queue not enabled, job not queued")
            return ""

        job_id = job_id or str(uuid.uuid4())

        job_data = {
            "id": job_id,
            "type": job_type,
            "payload": payload,
            "status": JobStatus.PENDING,
            "created_at": datetime.utcnow().isoformat(),
            "attempts": 0,
        }

        # Add to queue
        queue_key = f"queue:{job_type}"
        await self._redis.rpush(queue_key, json.dumps(job_data))

        # Add to pending set
        await self._redis.sadd(f"jobs:pending", job_id)

        logger.info(f"Job enqueued: {job_type}:{job_id}")

        return job_id

    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job data"""
        if not self.is_enabled:
            return None

        job_data = await self._redis.get(f"job:{job_id}")
        if job_data:
            return json.loads(job_data)
        return None

    async def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        """Update job status and store result"""
        if not self.is_enabled:
            return

        job = await self.get_job(job_id)
        if not job:
            return

        job["status"] = status
        job["updated_at"] = datetime.utcnow().isoformat()

        if result:
            job["result"] = result
        if error:
            job["error"] = error

        # Store job data
        await self._redis.set(f"job:{job_id}", json.dumps(job), ex=86400)  # 24h TTL

        # Update sets based on status
        if status == JobStatus.COMPLETED:
            await self._redis.srem(f"jobs:pending", job_id)
            await self._redis.sadd(f"jobs:completed", job_id)
        elif status == JobStatus.FAILED:
            await self._redis.srem(f"jobs:pending", job_id)
            await self._redis.sadd(f"jobs:failed", job_id)

    async def get_job_status(self, job_id: str) -> Optional[JobStatus]:
        """Get current job status"""
        job = await self.get_job(job_id)
        if job:
            return JobStatus(job.get("status", JobStatus.PENDING))
        return None

    async def process_next(self, job_type: str) -> Optional[Dict[str, Any]]:
        """Process next job in queue (blocking pop)"""
        if not self.is_enabled:
            return None

        queue_key = f"queue:{job_type}"

        # Use BRPOP for blocking pop (wait up to 1 second)
        result = await self._redis.blpop(queue_key, timeout=1)

        if result:
            _, job_data = result
            job = json.loads(job_data)
            job["status"] = JobStatus.PROCESSING
            job["attempts"] = job.get("attempts", 0) + 1

            # Store updated job
            await self._redis.set(
                f"job:{job['id']}",
                json.dumps(job),
                ex=86400
            )

            return job

        return None

    async def get_queue_length(self, job_type: str) -> int:
        """Get number of pending jobs"""
        if not self.is_enabled:
            return 0

        return await self._redis.llen(f"queue:{job_type}")

    async def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        if not self.is_enabled:
            return {"enabled": False}

        pending = await self._redis.scard("jobs:pending")
        completed = await self._redis.scard("jobs:completed")
        failed = await self._redis.scard("jobs:failed")

        return {
            "enabled": True,
            "pending": pending,
            "completed": completed,
            "failed": failed,
        }


# Global queue service
queue_service = QueueService()


async def init_queue():
    """Initialize queue service"""
    await queue_service.connect()


async def close_queue():
    """Close queue service"""
    await queue_service.disconnect()


# ==================== JOB HANDLERS ====================


async def handle_code_execution(job: Dict[str, Any]) -> Dict[str, Any]:
    """Handle code execution job"""
    from app.services.code_executor import CodeExecutor

    payload = job.get("payload", {})
    code = payload.get("code", "")
    language = payload.get("language", "python")

    executor = CodeExecutor()
    result = await executor.execute(code, language)

    return {
        "output": result.get("output"),
        "error": result.get("error"),
        "execution_time": result.get("execution_time"),
    }


async def handle_file_indexing(job: Dict[str, Any]) -> Dict[str, Any]:
    """Handle file indexing job"""
    # Placeholder for file indexing logic
    payload = job.get("payload", {})
    file_path = payload.get("file_path")

    # Index file and generate embeddings
    # This would call your RAG/embedding service

    return {
        "indexed": True,
        "file_path": file_path,
        "tokens": 0,
    }


# Job type to handler mapping
JOB_HANDLERS = {
    "code_execution": handle_code_execution,
    "file_indexing": handle_file_indexing,
}


# ==================== WORKER ====================


async def process_job(job: Dict[str, Any]) -> Dict[str, Any]:
    """Process a single job"""
    job_id = job.get("id")
    job_type = job.get("type")

    logger.info(f"Processing job: {job_type}:{job_id}")

    try:
        handler = JOB_HANDLERS.get(job_type)
        if not handler:
            raise ValueError(f"Unknown job type: {job_type}")

        result = await handler(job)

        await queue_service.update_job_status(
            job_id,
            JobStatus.COMPLETED,
            result=result
        )

        logger.info(f"Job completed: {job_type}:{job_id}")
        return result

    except Exception as e:
        logger.error(f"Job failed: {job_type}:{job_id}: {e}")

        await queue_service.update_job_status(
            job_id,
            JobStatus.FAILED,
            error=str(e)
        )

        raise


class QueueWorker:
    """Background worker that processes jobs"""

    def __init__(self, job_types: list[str]):
        self.job_types = job_types
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the worker"""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info(f"Queue worker started for: {self.job_types}")

    async def stop(self):
        """Stop the worker"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Queue worker stopped")

    async def _run(self):
        """Main worker loop"""
        while self._running:
            for job_type in self.job_types:
                job = await queue_service.process_next(job_type)
                if job:
                    try:
                        await process_job(job)
                    except Exception as e:
                        logger.error(f"Error processing job: {e}")

            # Brief pause to prevent CPU spinning
            await asyncio.sleep(0.1)
