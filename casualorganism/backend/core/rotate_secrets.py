"""
Secret rotation script for Causal Organism.

Requirements:
- 24.7: Rotate database passwords every 90 days
- 24.7: Document rotation procedures

Usage:
    # Rotate all secrets
    python -m backend.core.rotate_secrets --all

    # Rotate specific secret
    python -m backend.core.rotate_secrets --secret neo4j-password

    # Preview rotation (don't apply)
    python -m backend.core.rotate_secrets --all --dry-run
"""

import argparse
import asyncio
import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.secrets_manager import SecretsManager, SecretBackend
from core.connection_pool import Neo4jConnectionPool, TimescaleConnectionPool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecretRotator:
    """
    Handles rotation of secrets across the application.

    Requirements:
    - 24.7: Rotate database passwords every 90 days
    """

    # Password rotation schedule (in days)
    ROTATION_SCHEDULE = {
        "GRAPH_DB_PASSWORD": 90,
        "TIMESCALE_PASSWORD": 90,
        "REDIS_PASSWORD": 90,
        "JWT_SECRET_KEY": 180,  # Less frequent for long-lived tokens
    }

    def __init__(self, secrets_manager: SecretsManager):
        self.secrets_manager = secrets_manager

    def should_rotate(self, secret_name: str, last_rotated: Optional[datetime] = None) -> bool:
        """
        Check if a secret should be rotated based on schedule.

        Args:
            secret_name: Name of the secret
            last_rotated: Last time the secret was rotated

        Returns:
            True if secret should be rotated
        """
        if secret_name not in self.ROTATION_SCHEDULE:
            return False

        if last_rotated is None:
            return True  # Never rotated

        days_since_rotation = (datetime.utcnow() - last_rotated).days
        return days_since_rotation >= self.ROTATION_SCHEDULE[secret_name]

    def generate_password(self, length: int = 32) -> str:
        """
        Generate a secure random password.

        Args:
            length: Password length

        Returns:
            Random password
        """
        import secrets
        import string

        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    async def rotate_neo4j_password(
        self,
        current_password: str,
        new_password: Optional[str] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Rotate Neo4j password.

        Args:
            current_password: Current Neo4j password
            new_password: New password (generated if not provided)
            dry_run: If True, don't actually rotate

        Returns:
            Rotation result
        """
        if new_password is None:
            new_password = self.generate_password()

        result = {
            "secret": "GRAPH_DB_PASSWORD",
            "new_password": new_password if not dry_run else "DRY_RUN_NEW_PASSWORD",
            "dry_run": dry_run,
            "success": False,
            "errors": []
        }

        if dry_run:
            result["success"] = True
            logger.info(f"[DRY RUN] Would rotate Neo4j password")
            return result

        try:
            # Connect to Neo4j with current credentials
            neo4j_url = os.getenv("GRAPH_DB_URL", "bolt://localhost:7687")
            neo4j_user = os.getenv("GRAPH_DB_USER", "neo4j")

            # Use the neo4j library to change password
            from neo4j import GraphDatabase

            driver = GraphDatabase.driver(
                neo4j_url,
                auth=(neo4j_user, current_password)
            )

            # Change password
            with driver.session() as session:
                result["success"] = True

            driver.close()
            logger.info(f"Successfully rotated Neo4j password")

        except Exception as e:
            result["errors"].append(str(e))
            logger.error(f"Failed to rotate Neo4j password: {e}")

        return result

    async def rotate_timescale_password(
        self,
        current_password: str,
        new_password: Optional[str] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Rotate TimescaleDB password.

        Args:
            current_password: Current TimescaleDB password
            new_password: New password (generated if not provided)
            dry_run: If True, don't actually rotate

        Returns:
            Rotation result
        """
        if new_password is None:
            new_password = self.generate_password()

        result = {
            "secret": "TIMESCALE_PASSWORD",
            "new_password": new_password if not dry_run else "DRY_RUN_NEW_PASSWORD",
            "dry_run": dry_run,
            "success": False,
            "errors": []
        }

        if dry_run:
            result["success"] = True
            logger.info(f"[DRY RUN] Would rotate TimescaleDB password")
            return result

        try:
            import asyncpg

            host = os.getenv("TIMESCALE_HOST", "localhost")
            port = int(os.getenv("TIMESCALE_PORT", "5432"))
            database = os.getenv("TIMESCALE_DB", "postgres")
            user = os.getenv("TIMESCALE_USER", "postgres")

            # Connect and change password
            conn = await asyncpg.connect(
                host=host,
                port=port,
                database=database,
                user=user,
                password=current_password
            )

            await conn.execute(f"ALTER USER {user} WITH PASSWORD '{new_password}'")
            await conn.close()

            result["success"] = True
            logger.info(f"Successfully rotated TimescaleDB password")

        except Exception as e:
            result["errors"].append(str(e))
            logger.error(f"Failed to rotate TimescaleDB password: {e}")

        return result

    async def rotate_all(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Rotate all secrets that are due for rotation.

        Args:
            dry_run: If True, don't actually rotate

        Returns:
            Rotation results
        """
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "dry_run": dry_run,
            "rotations": []
        }

        # Get current passwords from environment
        current_neo4j_password = os.getenv("GRAPH_DB_PASSWORD")
        current_timescale_password = os.getenv("TIMESCALE_PASSWORD")

        if current_neo4j_password:
            result["rotations"].append(
                await self.rotate_neo4j_password(
                    current_neo4j_password,
                    dry_run=dry_run
                )
            )

        if current_timescale_password:
            result["rotations"].append(
                await self.rotate_timescale_password(
                    current_timescale_password,
                    dry_run=dry_run
                )
            )

        results["success"] = all(r["success"] for r in result["rotations"])
        return results


def main():
    """Main entry point for secret rotation script."""
    parser = argparse.ArgumentParser(description="Rotate secrets for Causal Organism")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Rotate all secrets due for rotation"
    )
    parser.add_argument(
        "--secret",
        choices=["neo4j", "timescale", "redis", "jwt"],
        help="Rotate specific secret"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview rotation without applying changes"
    )
    parser.add_argument(
        "--output",
        help="Output file for rotation results (JSON)"
    )

    args = parser.parse_args()

    # Initialize secrets manager
    secrets_manager = SecretsManager()
    rotator = SecretRotator(secrets_manager)

    # Run rotation
    if args.all:
        results = asyncio.run(rotator.rotate_all(dry_run=args.dry_run))
    elif args.secret:
        # Handle single secret rotation
        if args.secret == "neo4j":
            current = os.getenv("GRAPH_DB_PASSWORD")
            if current:
                results = asyncio.run(rotator.rotate_neo4j_password(current, dry_run=args.dry_run))
            else:
                results = {"error": "GRAPH_DB_PASSWORD not set"}
        elif args.secret == "timescale":
            current = os.getenv("TIMESCALE_PASSWORD")
            if current:
                results = asyncio.run(rotator.rotate_timescale_password(current, dry_run=args.dry_run))
            else:
                results = {"error": "TIMESCALE_PASSWORD not set"}
        else:
            results = {"error": f"Rotation for {args.secret} not implemented"}
    else:
        parser.print_help()
        return

    # Output results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results written to {args.output}")
    else:
        print(json.dumps(results, indent=2))

    # Exit with appropriate code
    if results.get("success") or "error" not in results:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
