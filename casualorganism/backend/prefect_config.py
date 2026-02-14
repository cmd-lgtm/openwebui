"""
Prefect server and agent configuration.

This module provides utilities for:
1. Setting up Prefect server
2. Configuring work queues
3. Deploying flows with schedules

Requirements: 15.1, 15.7, 15.8
"""

import os
import asyncio
import logging
from typing import Optional

from prefect import get_client
from prefect.client.schemas.actions import WorkQueueCreate
from prefect.deployments import Deployment

from backend.core.prefect_workflows import (
    incremental_update_flow,
    full_analysis_flow,
    create_deployments
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

PREFECT_API_URL = os.getenv("PREFECT_API_URL", "http://localhost:4200/api")
PREFECT_WORK_QUEUE = os.getenv("PREFECT_WORK_QUEUE", "default")


# ============================================================================
# Setup Functions
# ============================================================================

async def setup_work_queue(queue_name: str = PREFECT_WORK_QUEUE) -> None:
    """
    Create work queue if it doesn't exist.
    
    Requirements: 15.1
    
    Args:
        queue_name: Name of work queue to create
    """
    logger.info(f"Setting up work queue: {queue_name}")
    
    try:
        async with get_client() as client:
            # Check if work queue exists
            work_queues = await client.read_work_queues()
            existing_queue = next(
                (wq for wq in work_queues if wq.name == queue_name),
                None
            )
            
            if existing_queue:
                logger.info(f"Work queue '{queue_name}' already exists")
            else:
                # Create work queue
                await client.create_work_queue(
                    WorkQueueCreate(name=queue_name)
                )
                logger.info(f"Created work queue: {queue_name}")
                
    except Exception as e:
        logger.error(f"Error setting up work queue: {e}")
        raise


async def deploy_flows() -> None:
    """
    Deploy both flows with schedules.
    
    Requirements: 15.7, 15.8
    """
    logger.info("Deploying Prefect flows")
    
    try:
        # Create deployments
        incremental_deployment, full_analysis_deployment = create_deployments()
        
        # Apply deployments
        logger.info("Deploying incremental update flow...")
        incremental_id = await incremental_deployment.apply()
        logger.info(f"Incremental update flow deployed: {incremental_id}")
        
        logger.info("Deploying full analysis flow...")
        full_analysis_id = await full_analysis_deployment.apply()
        logger.info(f"Full analysis flow deployed: {full_analysis_id}")
        
        logger.info("All flows deployed successfully")
        
    except Exception as e:
        logger.error(f"Error deploying flows: {e}")
        raise


async def list_deployments() -> None:
    """
    List all deployed flows.
    
    Requirements: 15.8
    """
    logger.info("Listing Prefect deployments")
    
    try:
        async with get_client() as client:
            deployments = await client.read_deployments()
            
            if not deployments:
                logger.info("No deployments found")
                return
            
            logger.info(f"Found {len(deployments)} deployment(s):")
            for deployment in deployments:
                logger.info(f"  - {deployment.name} (Flow: {deployment.flow_name})")
                if deployment.schedule:
                    logger.info(f"    Schedule: {deployment.schedule}")
                logger.info(f"    Work Queue: {deployment.work_queue_name}")
                
    except Exception as e:
        logger.error(f"Error listing deployments: {e}")
        raise


async def check_prefect_connection() -> bool:
    """
    Check if Prefect server is accessible.
    
    Returns:
        True if connection successful, False otherwise
    """
    logger.info(f"Checking Prefect server connection: {PREFECT_API_URL}")
    
    try:
        async with get_client() as client:
            # Try to read server version
            await client.hello()
            logger.info("Successfully connected to Prefect server")
            return True
            
    except Exception as e:
        logger.error(f"Failed to connect to Prefect server: {e}")
        return False


# ============================================================================
# Main Setup Function
# ============================================================================

async def setup_prefect() -> None:
    """
    Complete Prefect setup:
    1. Check server connection
    2. Create work queue
    3. Deploy flows
    
    Requirements: 15.1, 15.7, 15.8
    """
    logger.info("Starting Prefect setup")
    
    # Check connection
    if not await check_prefect_connection():
        logger.error("Cannot connect to Prefect server. Please ensure it's running.")
        logger.info("Start Prefect server with: prefect server start")
        return
    
    # Setup work queue
    await setup_work_queue()
    
    # Deploy flows
    await deploy_flows()
    
    # List deployments
    await list_deployments()
    
    logger.info("Prefect setup complete!")
    logger.info("\nNext steps:")
    logger.info("1. Start Prefect agent: prefect agent start -q default")
    logger.info("2. View UI: http://localhost:4200")
    logger.info("3. Monitor flow runs in the UI")


# ============================================================================
# CLI Commands
# ============================================================================

async def main():
    """Main entry point for Prefect configuration."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python prefect_config.py [setup|deploy|list|check]")
        print("\nCommands:")
        print("  setup  - Complete Prefect setup (queue + deployments)")
        print("  deploy - Deploy flows with schedules")
        print("  list   - List all deployments")
        print("  check  - Check Prefect server connection")
        return
    
    command = sys.argv[1]
    
    if command == "setup":
        await setup_prefect()
    elif command == "deploy":
        await deploy_flows()
    elif command == "list":
        await list_deployments()
    elif command == "check":
        await check_prefect_connection()
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    asyncio.run(main())
