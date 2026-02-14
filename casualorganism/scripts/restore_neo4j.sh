#!/bin/bash
# Neo4j Restore Script
# Restores Neo4j database from S3 backup

set -e

# Configuration
BACKUP_NAME="${1:-}"
NEO4J_CONTAINER="${NEO4J_CONTAINER:-neo4j}"
NEO4J_USER="${NEO4J_USER:-neo4j}"
NEO4J_PASSWORD="${NEO4J_PASSWORD:-causal_organism}"
BACKUP_DIR="${BACKUP_DIR:-/tmp/neo4j_backups}"
S3_BUCKET="${S3_BUCKET:-causal-organism-backups}"
S3_PREFIX="${S3_PREFIX:-neo4j}"
ENCRYPTION_KEY="${ENCRYPTION_KEY:-}"

if [ -z "${BACKUP_NAME}" ]; then
    echo "Usage: $0 <backup_name>"
    echo ""
    echo "Available backups:"
    aws s3 ls "s3://${S3_BUCKET}/${S3_PREFIX}/" | grep "\.dump\.gz"
    exit 1
fi

echo "Starting Neo4j restore from backup: ${BACKUP_NAME}"

# Create restore directory
mkdir -p "${BACKUP_DIR}/restore"
RESTORE_DIR="${BACKUP_DIR}/restore"

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

# Stop Neo4j
echo "Stopping Neo4j container..."
docker-compose stop "${NEO4J_CONTAINER}"

# Backup current data
echo "Backing up current data..."
CURRENT_BACKUP="${BACKUP_DIR}/current_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
docker run --rm -v neo4j_data:/data -v "${BACKUP_DIR}":/backup \
    alpine tar czf "/backup/$(basename ${CURRENT_BACKUP})" /data 2>/dev/null || true
echo "Current data backed up to: ${CURRENT_BACKUP}"

# Clear existing data
echo "Clearing existing Neo4j data..."
docker volume rm neo4j_data 2>/dev/null || true
docker volume create neo4j_data

# Start Neo4j temporarily
echo "Starting Neo4j for initialization..."
docker-compose up -d "${NEO4J_CONTAINER}"
sleep 15
docker-compose stop "${NEO4J_CONTAINER}"

# Copy backup to container
echo "Copying backup to container..."
docker cp "${BACKUP_FILE}" "${NEO4J_CONTAINER}:/tmp/restore.dump"

# Start Neo4j
echo "Starting Neo4j..."
docker-compose start "${NEO4J_CONTAINER}"
sleep 10

# Load the dump
echo "Loading database dump..."
docker exec "${NEO4J_CONTAINER}" neo4j-admin database load neo4j \
    --from-path=/tmp \
    --overwrite-destination=true

# Restart Neo4j
echo "Restarting Neo4j..."
docker-compose restart "${NEO4J_CONTAINER}"
sleep 10

# Verify restoration
echo "Verifying restoration..."
NODE_COUNT=$(docker exec "${NEO4J_CONTAINER}" cypher-shell \
    -u "${NEO4J_USER}" \
    -p "${NEO4J_PASSWORD}" \
    "MATCH (n) RETURN count(n) as count;" | grep -oP '\d+' | head -1)

echo "Restoration completed successfully!"
echo "Total nodes in database: ${NODE_COUNT}"

# Clean up
echo "Cleaning up temporary files..."
rm -rf "${RESTORE_DIR}"

echo "Neo4j restore completed!"
