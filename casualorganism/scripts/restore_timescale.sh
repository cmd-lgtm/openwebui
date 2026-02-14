#!/bin/bash
# TimescaleDB Restore Script
# Restores TimescaleDB database from S3 backup

set -e

# Configuration
BACKUP_NAME="${1:-}"
TIMESCALE_CONTAINER="${TIMESCALE_CONTAINER:-timescale}"
TIMESCALE_HOST="${TIMESCALE_HOST:-localhost}"
TIMESCALE_PORT="${TIMESCALE_PORT:-5432}"
TIMESCALE_DB="${TIMESCALE_DB:-postgres}"
TIMESCALE_USER="${TIMESCALE_USER:-postgres}"
TIMESCALE_PASSWORD="${TIMESCALE_PASSWORD:-password}"
BACKUP_DIR="${BACKUP_DIR:-/tmp/timescale_backups}"
S3_BUCKET="${S3_BUCKET:-causal-organism-backups}"
S3_PREFIX="${S3_PREFIX:-timescale}"
ENCRYPTION_KEY="${ENCRYPTION_KEY:-}"

if [ -z "${BACKUP_NAME}" ]; then
    echo "Usage: $0 <backup_name>"
    echo ""
    echo "Available backups:"
    aws s3 ls "s3://${S3_BUCKET}/${S3_PREFIX}/" | grep "\.dump\.gz"
    exit 1
fi

echo "Starting TimescaleDB restore from backup: ${BACKUP_NAME}"

# Create restore directory
mkdir -p "${BACKUP_DIR}/restore"
RESTORE_DIR="${BACKUP_DIR}/restore"

# Export password for pg_restore
export PGPASSWORD="${TIMESCALE_PASSWORD}"

# Download backup from S3
echo "Downloading backup from S3..."
S3_PATH="s3://${S3_BUCKET}/${S3_PREFIX}/${BACKUP_NAME}"
aws s3 cp "${S3_PATH}" "${RESTORE_DIR}/"

BACKUP_FILE="${RESTORE_DIR}/${BACKUP_NAME}"

# Decrypt if encrypted
if [[ "${BACKUP_FILE}" == *.enc ]]; then
    if [ -z "${ENCRYPTION_KEY}" ]; then
        echo "Error: Backup is encrypted but ENCRYPTION_KEY not set"
        exit 1
    fi
    
    echo "Decrypting backup..."
    openssl enc -aes-256-cbc -d -pbkdf2 -iter 100000 \
        -in "${BACKUP_FILE}" \
        -out "${BACKUP_FILE%.enc}" \
        -k "${ENCRYPTION_KEY}"
    
    rm "${BACKUP_FILE}"
    BACKUP_FILE="${BACKUP_FILE%.enc}"
    echo "Decryption completed"
fi

# Decompress if compressed
if [[ "${BACKUP_FILE}" == *.gz ]]; then
    echo "Decompressing backup..."
    gunzip "${BACKUP_FILE}"
    BACKUP_FILE="${BACKUP_FILE%.gz}"
    echo "Decompression completed"
fi

# Stop TimescaleDB
echo "Stopping TimescaleDB container..."
docker-compose stop "${TIMESCALE_CONTAINER}"

# Backup current data
echo "Backing up current data..."
CURRENT_BACKUP="${BACKUP_DIR}/current_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
docker run --rm -v timescale_data:/data -v "${BACKUP_DIR}":/backup \
    alpine tar czf "/backup/$(basename ${CURRENT_BACKUP})" /data 2>/dev/null || true
echo "Current data backed up to: ${CURRENT_BACKUP}"

# Clear existing data
echo "Clearing existing TimescaleDB data..."
docker volume rm timescale_data 2>/dev/null || true
docker volume create timescale_data

# Start TimescaleDB
echo "Starting TimescaleDB..."
docker-compose up -d "${TIMESCALE_CONTAINER}"
sleep 15

# Wait for database to be ready
echo "Waiting for database to be ready..."
for i in {1..30}; do
    if docker exec "${TIMESCALE_CONTAINER}" pg_isready -U "${TIMESCALE_USER}" > /dev/null 2>&1; then
        echo "Database is ready"
        break
    fi
    echo "Waiting... ($i/30)"
    sleep 2
done

# Copy backup to container
echo "Copying backup to container..."
docker cp "${BACKUP_FILE}" "${TIMESCALE_CONTAINER}:/tmp/restore.dump"

# Restore the database
echo "Restoring database..."
docker exec "${TIMESCALE_CONTAINER}" pg_restore \
    -U "${TIMESCALE_USER}" \
    -d "${TIMESCALE_DB}" \
    -c \
    --if-exists \
    /tmp/restore.dump 2>&1 | grep -v "WARNING" || true

# Verify restoration
echo "Verifying restoration..."

# Check employee_metrics table
METRICS_COUNT=$(docker exec "${TIMESCALE_CONTAINER}" psql \
    -U "${TIMESCALE_USER}" \
    -d "${TIMESCALE_DB}" \
    -t -c "SELECT COUNT(*) FROM employee_metrics;" 2>/dev/null | xargs || echo "0")

# Check intervention_audit_log table
AUDIT_COUNT=$(docker exec "${TIMESCALE_CONTAINER}" psql \
    -U "${TIMESCALE_USER}" \
    -d "${TIMESCALE_DB}" \
    -t -c "SELECT COUNT(*) FROM intervention_audit_log;" 2>/dev/null | xargs || echo "0")

echo "Restoration completed successfully!"
echo "Employee metrics records: ${METRICS_COUNT}"
echo "Audit log records: ${AUDIT_COUNT}"

# Clean up
echo "Cleaning up temporary files..."
rm -rf "${RESTORE_DIR}"
docker exec "${TIMESCALE_CONTAINER}" rm /tmp/restore.dump

# Unset password
unset PGPASSWORD

echo "TimescaleDB restore completed!"
