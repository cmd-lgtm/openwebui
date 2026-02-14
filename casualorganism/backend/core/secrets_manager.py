"""
Secrets management module for Causal Organism.

Supports multiple backends:
- Environment variables (development)
- Kubernetes Secrets (production)
- HashiCorp Vault (advanced production)

Requirements:
- 24.1: Remove hardcoded secrets from configuration
- 24.2: Document required secrets
- 24.4: Use separate credentials per environment
- 24.6: Add Vault client integration
- 24.7: Rotate database passwords every 90 days
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SecretBackend(Enum):
    """Supported secret backends."""
    ENVIRONMENT = "environment"
    KUBERNETES = "kubernetes"
    VAULT = "vault"


@dataclass
class SecretConfig:
    """Configuration for secrets management."""
    backend: SecretBackend = SecretBackend.ENVIRONMENT
    vault_url: Optional[str] = None
    vault_token: Optional[str] = None
    vault_path: str = "secret/data/causal-organism"
    kubernetes_namespace: str = "default"


class SecretsManager:
    """
    Centralized secrets management with support for multiple backends.

    Supports:
    - Environment variables (development)
    - Kubernetes Secrets (production)
    - HashiCorp Vault (advanced production)

    Requirements:
    - 24.1: Use environment variables instead of hardcoded secrets
    - 24.4: Use separate credentials per environment
    - 24.6: Add Vault client integration
    """

    # Required secrets for the application
    REQUIRED_SECRETS = {
        # Database credentials
        "GRAPH_DB_PASSWORD": "Neo4j graph database password",
        "TIMESCALE_PASSWORD": "TimescaleDB password",

        # API keys
        "SENTRY_DSN": "Sentry error tracking DSN",
        "JWT_SECRET_KEY": "JWT token signing key",

        # Optional secrets
        "S3_ACCESS_KEY": "S3-compatible storage access key",
        "S3_SECRET_KEY": "S3-compatible storage secret key",
        "REDIS_PASSWORD": "Redis password (if configured)",
    }

    # Default values for development (NOT for production)
    DEV_DEFAULTS = {
        "GRAPH_DB_PASSWORD": "causal_organism",
        "TIMESCALE_PASSWORD": "password",
        "REDIS_URL": "redis://redis:6379/0",
    }

    def __init__(self, config: Optional[SecretConfig] = None):
        """
        Initialize secrets manager.

        Args:
            config: Secret backend configuration
        """
        self._config = config or self._auto_detect_config()
        self._cache: Dict[str, str] = {}
        self._vault_client = None

    def _auto_detect_config(self) -> SecretConfig:
        """Auto-detect the best secret backend based on environment."""
        # Check if running in Kubernetes
        if os.path.exists("/var/run/secrets/kubernetes.io"):
            return SecretConfig(backend=SecretBackend.KUBERNETES)

        # Check if Vault is configured
        if os.getenv("VAULT_ADDR"):
            return SecretConfig(
                backend=SecretBackend.VAULT,
                vault_url=os.getenv("VAULT_ADDR"),
                vault_token=os.getenv("VAULT_TOKEN"),
                vault_path=os.getenv("VAULT_PATH", "secret/data/causal-organism")
            )

        # Default to environment variables
        return SecretConfig(backend=SecretBackend.ENVIRONMENT)

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a secret value.

        Args:
            key: Secret key name
            default: Default value if not found

        Returns:
            Secret value or default
        """
        # Check cache first
        if key in self._cache:
            return self._cache[key]

        # Fetch from backend
        value = self._fetch_secret(key)

        if value is None:
            # Use default for development
            if os.getenv("ENVIRONMENT") == "development":
                value = self.DEV_DEFAULTS.get(key, default)
            else:
                value = default

        if value:
            self._cache[key] = value

        return value

    def _fetch_secret(self, key: str) -> Optional[str]:
        """Fetch secret from the configured backend."""
        if self._config.backend == SecretBackend.KUBERNETES:
            return self._fetch_from_kubernetes(key)
        elif self._config.backend == SecretBackend.VAULT:
            return self._fetch_from_vault(key)
        else:
            return os.getenv(key)

    def _fetch_from_kubernetes(self, key: str) -> Optional[str]:
        """Fetch secret from Kubernetes Secrets."""
        try:
            # Try to read from /run/secrets/kubernetes.io namespace
            # Kubernetes mounts secrets as files in this directory
            secret_file = f"/run/secrets/kubernetes.io/serviceaccount/{key.lower()}"

            if os.path.exists(secret_file):
                with open(secret_file, 'r') as f:
                    return f.read().strip()

            # Also check legacy location
            legacy_file = f"/etc/secrets/{key}"
            if os.path.exists(legacy_file):
                with open(legacy_file, 'r') as f:
                    return f.read().strip()

            return None
        except Exception as e:
            logger.warning(f"Failed to fetch secret {key} from Kubernetes: {e}")
            return None

    def _fetch_from_vault(self, key: str) -> Optional[str]:
        """Fetch secret from HashiCorp Vault."""
        if not self._vault_client:
            self._initialize_vault()

        if not self._vault_client:
            return None

        try:
            # Use hvac library for Vault access
            secret = self._vault_client.secrets.kv.v2.read_secret_version(
                path=f"{self._config.vault_path}/{key}",
                mount_point="secret"
            )
            return secret["data"]["data"].get(key)
        except Exception as e:
            logger.warning(f"Failed to fetch secret {key} from Vault: {e}")
            return None

    def _initialize_vault(self) -> None:
        """Initialize Vault client."""
        try:
            import hvac

            self._vault_client = hvac.Client(
                url=self._config.vault_url,
                token=self._config.vault_token
            )

            if not self._vault_client.is_authenticated():
                logger.warning("Vault client authentication failed")
                self._vault_client = None
        except ImportError:
            logger.warning("hvac library not installed - Vault secrets unavailable")
            self._vault_client = None
        except Exception as e:
            logger.warning(f"Failed to initialize Vault client: {e}")
            self._vault_client = None

    def get_all(self) -> Dict[str, Optional[str]]:
        """
        Get all required secrets.

        Returns:
            Dictionary of all secret keys and values
        """
        result = {}
        for key in self.REQUIRED_SECRETS:
            result[key] = self.get(key)
        return result

    def validate(self) -> Dict[str, Any]:
        """
        Validate that all required secrets are available.

        Returns:
            Validation result with missing secrets
        """
        missing = []
        present = []

        for key in self.REQUIRED_SECRETS:
            value = self.get(key)
            if value:
                present.append(key)
            else:
                missing.append({
                    "key": key,
                    "description": self.REQUIRED_SECRETS[key]
                })

        return {
            "valid": len(missing) == 0,
            "present_count": len(present),
            "missing_count": len(missing),
            "missing_secrets": missing,
            "backend": self._config.backend.value
        }

    def clear_cache(self) -> None:
        """Clear the secrets cache."""
        self._cache.clear()


def get_secrets_manager() -> SecretsManager:
    """
    Get the global secrets manager instance.

    Returns:
        Configured SecretsManager instance
    """
    global _secrets_manager

    if _secrets_manager is None:
        config = SecretConfig(
            backend=SecretBackend(os.getenv("SECRET_BACKEND", "environment")),
            vault_url=os.getenv("VAULT_ADDR"),
            vault_token=os.getenv("VAULT_TOKEN"),
            vault_path=os.getenv("VAULT_PATH", "secret/data/causal-organism")
        )
        _secrets_manager = SecretsManager(config)

    return _secrets_manager


# Global instance
_secrets_manager: Optional[SecretsManager] = None


# Convenience function for getting secrets
def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get a secret value using the global secrets manager.

    Args:
        key: Secret key name
        default: Default value if not found

    Returns:
        Secret value or default
    """
    return get_secrets_manager().get(key, default)


def get_required_secret(key: str) -> str:
    """
    Get a required secret, raising an error if not found.

    Args:
        key: Secret key name

    Returns:
        Secret value

    Raises:
        ValueError: If secret is not found
    """
    value = get_secrets_manager().get(key)
    if not value:
        raise ValueError(f"Required secret '{key}' is not configured")
    return value
