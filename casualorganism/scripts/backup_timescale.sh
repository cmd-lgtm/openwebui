#!/bin/bash
# TimescaleDB Backup Script
# Performs full and incremental backups and uploads to S3-compatible storage

set -e

# Configuration
BACKUP_TYPE="${1:-incremental}"  # full or incremental
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
RETENTION_DAYS="${RETENTION_DAYS:-30}"
WAL_ARCHIVE_DIR="${WAL_ARCHIVE_DIR:-/tmp/timescale_wal}"

# Timestamp for backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="timescale_${BACKUP_TYPE}_${TIMESTAMP}"
LOCAL_BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

echo "Starting TimescaleDB ${BACKUP_TYPE} backup at ${TIMESTAMP}"

# Create backup directory
mkdir -p "${BACKUP_DIR}"
mkdir -p "${WAL_ARCHIVE_DIR}"

# Export password for pg_dump
export PGPASSWORD="${TIMESCALE_PASSWORD}"

# Perform backup based on type
if [ "${BACKUP_TYPE}" = "full" ]; then
    echo "Performing full backup..."
    
    # Use pg_dump for full backup
    docker exec "${TIMESCALE_CONTAINER}" pg_dump \
        -h localhost \
        -p 5432 \
        -U "${TIMESCALE_USER}" \
        -d "${TIMESCALE_DB}" \
        -F c \
        -f "/tmp/${BACKUP_NAME}.dump"
    
    # Copy backup from container
    docker cp "${TIMESCALE_CONTAINER}:/tmp/${BACKUP_NAME}.dump" "${LOCAL_BACKUP_PATH}.dump"
    
    # Clean up container backup
    docker exec "${TIMESCALE_CONTAINER}" rm "/tmp/${BACKUP_NAME}.dump"
    
    echo "Full backup completed: ${LOCAL_BACKUP_PATH}.dump"
    
elif [ "${BACKUP_TYPE}" = "incremental" ]; then
    echo "Performing incremental backup (WAL archiving)..."
    
    # For incremental backups, we use WAL (Write-Ahead Log) archiving
    # First, ensure WAL archiving is enabled in PostgreSQL
    
    # Get the latest WAL files
    docker exec "${TIMESCALE_CONTAINER}" psql \
        -U "${TIMESCALE_USER}" \
        -d "${TIMESCALE_DB}" \
        -c "SELECT pg_switch_wal();" > /dev/null 2>&1 || true
    
    # Archive WAL files
    WAL_FILES=$(docker exec "${TIMESCALE_CONTAINER}" ls /var/lib/postgresql/data/pg_wal/ 2>/dev/null || echo "")
    
    if [ -n "${WAL_FILES}" ]; then
        # Create incremental backup directory
        INCREMENTAL_DIR="${LOCAL_BACKUP_PATH}_wal"
        mkdir -p "${INCREMENTAL_DIR}"
        
        # Copy WAL files
        docker exec "${TIMESCALE_CONTAINER}" tar -czf "/tmp/wal_${TIMESTAMP}.tar.gz" \
            -C /var/lib/postgresql/data/pg_wal . 2>/dev/null || true
        
        docker cp "${TIMESCALE_CONTAINER}:/tmp/wal_${TIMESTAMP}.tar.gz" \
            "${INCREMENTAL_DIR}/wal_${TIMESTAMP}.tar.gz" 2>/dev/null || true
        
        docker exec "${TIMESCALE_CONTAINER}" rm "/tmp/wal_${TIMESTAMP}.tar.gz" 2>/dev/null || true
        
        echo "Incremental backup (WAL) completed: ${INCREMENTAL_DIR}"
        
        # For simplicity, also create a full dump for incremental
        # In production, use pg_basebackup with WAL archiving
        docker exec "${TIMESCALE_CONTAINER}" pg_dump \
            -h localhost \
            -p 5432 \
            -U "${TIMESCALE_USER}" \
            -d "${TIMESCALE_DB}" \
            -F c \
            -f "/tmp/${BACKUP_NAME}.dump"
        
        docker cp "${TIMESCALE_CONTAINER}:/tmp/${BACKUP_NAME}.dump" "${LOCAL_BACKUP_PATH}.dump"
        docker exec "${TIMESCALE_CONTAINER}" rm "/tmp/${BACKUP_NAME}.dump"
    else
        echo "Warning: Could not access WAL files. Performing full dump instead."
        docker exec "${TIMESCALE_CONTAINER}" pg_dump \
            -h localhost \
            -p 5432 \
            -U "${TIMESCALE_USER}" \
            -d "${TIMESCALE_DB}" \
            -F c \
            -f "/tmp/${BACKUP_NAME}.dump"
        
        docker cp "${TIMESCALE_CONTAINER}:/tmp/${BACKUP_NAME}.dump" "${LOCAL_BACKUP_PATH}.dump"
        docker exec "${TIMESCALE_CONTAINER}" rm "/tmp/${BACKUP_NAME}.dump"
    fi
    
else
    echo "Error: Invalid backup type. Use 'full' or 'incremental'"
    exit 1
fi

# Compress backup
echo "Compressing backup..."
if [ -f "${LOCAL_BACKUP_PATH}.dump" ]; then
    gzip "${LOCAL_BACKUP_PATH}.dump"
    COMPRESSED_BACKUP="${LOCAL_BACKUP_PATH}.dump.gz"
else
    echo "Error: Backup file not found"
    exit 1
fi

# Encrypt backup if encryption key is provided
if [ -n "${ENCRYPTION_KEY}" ]; then
    echo "Encrypting backup with AES-256..."
    openssl enc -aes-256-cbc -salt -pbkdf2 \
        -in "${COMPRESSED_BACKUP}" \
        -out "${COMPRESSED_BACKUP}.enc" \
        -k "${ENCRYPTION_KEY}"
    
    # Remove unencrypted backup
    rm "${COMPRESSED_BACKUP}"
    FINAL_BACKUP="${COMPRESSED_BACKUP}.enc"
    echo "Backup encrypted: ${FINAL_BACKUP}"
else
    FINAL_BACKUP="${COMPRESSED_BACKUP}"
    echo "Warning: Backup not encrypted. Set ENCRYPTION_KEY for encryption."
fi

# Upload to S3
echo "Uploading backup to S3..."
S3_PATH="s3://${S3_BUCKET}/${S3_PREFIX}/${BACKUP_NAME}.dump.gz$([ -n "${ENCRYPTION_KEY}" ] && echo '.enc' || echo '')"

# Use AWS CLI or compatible tool (MinIO, etc.)
if command -v aws &> /dev/null; then
    aws s3 cp "${FINAL_BACKUP}" "${S3_PATH}"
    echo "Backup uploaded to ${S3_PATH}"
    
    # Upload WAL files if they exist
    if [ -d "${LOCAL_BACKUP_PATH}_wal" ]; then
        aws s3 sync "${LOCAL_BACKUP_PATH}_wal" "s3://${S3_BUCKET}/${S3_PREFIX}/wal/"
        echo "WAL files uploaded to s3://${S3_BUCKET}/${S3_PREFIX}/wal/"
    fi
else
    echo "Error: AWS CLI not found. Install aws-cli to upload backups."
    exit 1
fi

# Clean up old local backups
echo "Cleaning up local backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -name "timescale_*" -type f -mtime +${RETENTION_DAYS} -delete
find "${BACKUP_DIR}" -name "timescale_*" -type d -mtime +${RETENTION_DAYS} -exec rm -rf {} + 2>/dev/null || true

# Clean up old S3 backups
echo "Cleaning up S3 backups older than ${RETENTION_DAYS} days..."
CUTOFF_DATE=$(date -d "${RETENTION_DAYS} days ago" +%Y%m%d)
aws s3 ls "s3://${S3_BUCKET}/${S3_PREFIX}/" | while read -r line; do
    BACKUP_FILE=$(echo "$line" | awk '{print $4}')
    BACKUP_DATE=$(echo "$BACKUP_FILE" | grep -oP '\d{8}' | head -1)
    
    if [ -n "${BACKUP_DATE}" ] && [ "${BACKUP_DATE}" -lt "${CUTOFF_DATE}" ]; then
        echo "Deleting old backup: ${BACKUP_FILE}"
        aws s3 rm "s3://${S3_BUCKET}/${S3_PREFIX}/${BACKUP_FILE}"
    fi
done

# Unset password
unset PGPASSWORD

echo "TimescaleDB backup completed successfully!"
echo "Backup location: ${S3_PATH}"
echo "Local backup: ${FINAL_BACKUP}"
