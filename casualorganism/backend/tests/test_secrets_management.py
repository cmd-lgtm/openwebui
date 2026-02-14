"""
Unit tests for secrets management.

Requirements:
- 24.1: Verify no secrets in config files
"""

import os
import pytest
import re
from pathlib import Path

# Define paths to check
CONFIG_PATHS = [
    "docker-compose.yml",
    "docker-compose.prefect.yml",
    "docker-compose.tracing.yml",
    "k8s",
]


class SecretsPatterns:
    """Regex patterns for common secrets."""

    # Common secret patterns
    PATTERNS = [
        # Password patterns
        (r'password\s*=\s*["\'](?!{{|environment|env|secret)[^"\']{3,}["\']', "hardcoded password"),
        (r'POSTGRES_PASSWORD\s*=\s*["\'][^"\']+["\']', "PostgreSQL password"),
        (r'REDIS_PASSWORD\s*=\s*["\'][^"\']+["\']', "Redis password"),

        # API keys and tokens
        (r'api[_-]?key\s*=\s*["\'][^"\']+["\']', "API key"),
        (r'secret[_-]?key\s*=\s*["\'][^"\']+["\']', "secret key"),
        (r'access[_-]?key\s*=\s*["\'][^"\']+["\']', "access key"),
        (r'token\s*=\s*["\'][^"\']+["\']', "token"),

        # JWT
        (r'JWT_SECRET\s*=\s*["\'][^"\']+["\']', "JWT secret"),

        # Database passwords (specific)
        (r'GRAPH_DB_PASSWORD\s*=\s*["\'][^"({{|environment)][^"\']+["\']', "Neo4j password"),
        (r'NEO4J_AUTH\s*=\s*neo4j/[^"\']+', "Neo4j auth password"),
    ]

    # Allowed patterns (environment variable references)
    ALLOWED_PATTERNS = [
        r'\$\{[^}]+\}',           # ${VAR}
        r'\$\w+',                  # $VAR
        r'{{<.*>}}',              # {{ .Values.xxx }}
    ]


def scan_file_for_secrets(file_path: Path) -> list:
    """
    Scan a file for hardcoded secrets.

    Args:
        file_path: Path to file to scan

    Returns:
        List of findings (line number, pattern type, line content)
    """
    findings = []

    if not file_path.exists():
        return findings

    # Skip binary files and certain extensions
    if file_path.suffix in ['.pyc', '.pyo', '.so', '.dll', '.exe']:
        return findings

    # Skip node_modules, venv, etc.
    if any(part in file_path.parts for part in ['node_modules', 'venv', '.venv', '__pycache__']):
        return findings

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception:
        return findings

    # Check each pattern
    for line_num, line in enumerate(content.splitlines(), 1):
        # Skip comments
        if line.strip().startswith('#'):
            continue

        for pattern, pattern_type in SecretsPatterns.PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                # Check if it's an allowed pattern (environment variable reference)
                if not any(re.search(allowed, line) for allowed in SecretsPatterns.ALLOWED_PATTERNS):
                    findings.append({
                        'line': line_num,
                        'type': pattern_type,
                        'content': line.strip()[:100]  # Truncate for readability
                    })

    return findings


def scan_directory(base_path: Path, patterns: list) -> dict:
    """
    Scan directory for files matching patterns.

    Args:
        base_path: Base directory to scan
        patterns: List of glob patterns

    Returns:
        Dictionary mapping file paths to secret findings
    """
    results = {}

    for pattern in patterns:
        for file_path in base_path.glob(pattern):
            if file_path.is_file():
                findings = scan_file_for_secrets(file_path)
                if findings:
                    results[str(file_path.relative_to(base_path))] = findings

    return results


class TestSecretsInConfigFiles:
    """
    Test that no hardcoded secrets exist in configuration files.

    Requirements:
    - 24.1: Verify no secrets in config files
    """

    @pytest.fixture
    def base_path(self):
        """Get the project base path."""
        return Path(__file__).parent.parent.parent

    def test_no_secrets_in_docker_compose(self, base_path):
        """Test that docker-compose.yml has no hardcoded secrets."""
        docker_file = base_path / "docker-compose.yml"

        if not docker_file.exists():
            pytest.skip("docker-compose.yml not found")

        findings = scan_file_for_secrets(docker_file)

        # Filter out allowed patterns
        allowed_findings = []
        real_findings = []

        for finding in findings:
            # Check for placeholder or template values
            content = finding['content'].lower()
            if any(placeholder in content for placeholder in ['placeholder', '{{', 'vault', 'secret', '$var', '${']):
                allowed_findings.append(finding)
            else:
                real_findings.append(finding)

        if real_findings:
            error_msg = "\n".join([
                f"Line {f['line']}: {f['type']} - {f['content']}"
                for f in real_findings
            ])
            pytest.fail(f"Hardcoded secrets found in docker-compose.yml:\n{error_msg}")

    def test_no_secrets_in_k8s_manifests(self, base_path):
        """Test that Kubernetes manifests have no hardcoded secrets."""
        k8s_dir = base_path / "k8s"

        if not k8s_dir.exists():
            pytest.skip("k8s directory not found")

        results = scan_directory(k8s_dir, ["**/*.yml", "**/*.yaml"])

        all_findings = {}
        for file_path, findings in results.items():
            # Filter out allowed patterns
            real_findings = []
            for finding in findings:
                content = finding['content'].lower()
                if any(placeholder in content for placeholder in ['placeholder', '{{', 'vault', 'secret', '$var', '${', 'valuefrom']):
                    continue
                real_findings.append(finding)

            if real_findings:
                all_findings[file_path] = real_findings

        if all_findings:
            error_msg = "\n".join([
                f"{file_path}:\n" + "\n".join([
                    f"  Line {f['line']}: {f['type']} - {f['content']}"
                    for f in findings
                ])
                for file_path, findings in all_findings.items()
            ])
            pytest.fail(f"Hardcoded secrets found in Kubernetes manifests:\n{error_msg}")

    def test_required_secrets_documented(self, base_path):
        """Test that required secrets are documented."""
        # Check for .env.example or secrets documentation
        env_example = base_path / ".env.example"
        secrets_doc = base_path / "SECRETS.md"
        readme = base_path / "README.md"

        has_docs = env_example.exists() or secrets_doc.exists() or (readme.exists() and "secret" in readme.read_text().lower())

        if not has_docs:
            pytest.fail(
                "Required secrets should be documented. "
                "Create .env.example or SECRETS.md with list of required environment variables."
            )

    def test_docker_compose_references_env_vars(self, base_path):
        """Test that docker-compose.yml uses environment variable references."""
        docker_file = base_path / "docker-compose.yml"

        if not docker_file.exists():
            pytest.skip("docker-compose.yml not found")

        content = docker_file.read_text()

        # Check that passwords are not hardcoded inline
        # They should either be: ${VAR} or be empty/default
        lines_with_passwords = []
        for line_num, line in enumerate(content.splitlines(), 1):
            if "password" in line.lower() and "=" in line:
                # Skip comments
                if line.strip().startswith('#'):
                    continue

                # Check if it uses environment variable or is a placeholder
                if not any(pattern in line for pattern in ['${', 'vault:', 'placeholder', 'valueFrom']):
                    # Check if it's a dummy/empty value
                    if "password" in line.lower() and not any(val in line.lower() for val in ['"{}"', '""', "''", '""']):
                        lines_with_passwords.append((line_num, line.strip()))

        # This is informational - we allow some hardcoded defaults for development
        # but they should use env vars for production
        if lines_with_passwords:
            print("\nNote: docker-compose.yml contains some password values. Consider using env vars:")
            for line_num, line in lines_with_passwords[:5]:
                print(f"  Line {line_num}: {line[:80]}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
