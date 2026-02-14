#!/bin/bash
# Neo4j Backup Script
# Performs full and incremental backups and uploads to S3-compatible storage

set -e

# Configuration
BACKUP_TYPE="${1:-incremental}"  # full or incremental
NEO4J_CONTAINER="${NEO4J_CONTAINER:-neo4j}"
NEO4J_USER="${NEO4J_USER:-neo4j}"
NEO4J_PASSWORD="${NEO4J_PASSWORD:-causal_organism}"
BACKUP_DIR="${BACKUP_DIR:-/tmp/neo4j_backups}"
S3_BUCKET="${S3_BUCKET:-causal-organism-backups}"
S3_PREFIX="${S3_PREFIX:-neo4j}"
ENCRYPTION_KEY="${ENCRYPTION_KEY:-}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

# Timestamp for backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="neo4j_${BACKUP_TYPE}_${TIMESTAMP}"
LOCAL_BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

echo "Starting Neo4j ${BACKUP_TYPE} backup at ${TIMESTAMP}"

# Create backup directory
mkdir -p "${BACKUP_DIR}"

# Perform backup based on type
if [ "${BACKUP_TYPE}" = "full" ]; then
    echo "Performing full backup..."
    
    # Use neo4j-admin dump for full backup
    docker exec "${NEO4J_CONTAINER}" neo4j-admin database dump neo4j \
        --to-path=/tmp/backup \
        --overwrite-destination=true
    
    # Copy backup from container
    docker cp "${NEO4J_CONTAINER}:/tmp/backup/neo4j.dump" "${LOCAL_BACKUP_PATH}.dump"
    
    echo "Full backup completed: ${LOCAL_BACKUP_PATH}.dump"
    
elif [ "${BACKUP_TYPE}" = "incremental" ]; then
    echo "Performing incremental backup..."
    
    # For incremental, we'll use neo4j-admin backup (requires Enterprise)
    # For Community edition, we'll do a full dump but mark it as incremental
    # In production with Enterprise, use: neo4j-admin backup --backup-dir=/backup --name=graph.db-backup
    
    docker exec "${NEO4J_CONTAINER}" neo4j-admin database dump neo4j \
        --to-path=/tmp/backup \
        --overwrite-destination=true
    
    # Copy backup from container
    docker cp "${NEO4J_CONTAINER}:/tmp/backup/neo4j.dump" "${LOCAL_BACKUP_PATH}.dump"
    
    echo "Incremental backup completed: ${LOCAL_BACKUP_PATH}.dump"
else
    echo "Error: Invalid backup type. Use 'full' or 'incremental'"
    exit 1
fi

# Compress backup
echo "Compressing backup..."
gzip "${LOCAL_BACKUP_PATH}.dump"
COMPRESSED_BACKUP="${LOCAL_BACKUP_PATH}.dump.gz"

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
else
    echo "Error: AWS CLI not found. Install aws-cli to upload backups."
    exit 1
fi

# Clean up old local backups
echo "Cleaning up local backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -name "neo4j_*" -type f -mtime +${RETENTION_DAYS} -delete

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

echo "Neo4j backup completed successfully!"
echo "Backup location: ${S3_PATH}"
echo "Local backup: ${FINAL_BACKUP}"
