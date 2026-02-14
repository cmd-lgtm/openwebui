# Database Backup and Recovery Runbook

## Overview

This runbook provides procedures for backing up and recovering Neo4j and TimescaleDB databases for the Causal Organism platform. The backup strategy ensures:

- **RPO (Recovery Point Objective)**: <15 minutes
- **RTO (Recovery Time Objective)**: <1 hour
- **Encryption**: AES-256 for all backups at rest
- **Retention**: 30 days for all backups

## Table of Contents

1. [Backup Procedures](#backup-procedures)
2. [Recovery Procedures](#recovery-procedures)
3. [Scheduled Backup Jobs](#scheduled-backup-jobs)
4. [Testing and Validation](#testing-and-validation)
5. [Troubleshooting](#troubleshooting)
6. [Emergency Contacts](#emergency-contacts)

---

## Backup Procedures

### Prerequisites

1. AWS CLI installed and configured
2. OpenSSL installed for encryption
3. Docker access to database containers
4. Backup configuration file set up

### Setup Backup Configuration

```bash
# Copy example configuration
cp config/backup-config.env.example config/backup-config.env

# Edit configuration with your values
nano config/backup-config.env

# Generate encryption key
openssl rand -base64 32

# Add encryption key to config
echo "ENCRYPTION_KEY=<generated_key>" >> config/backup-config.env

# Load configuration
source config/backup-config.env
```

### Neo4j Backup

#### Full Backup (Daily at 2 AM UTC)

```bash
# Load configuration
source config/backup-config.env

# Run full backup
./scripts/backup_neo4j.sh full
```

**Expected Output:**
```
Starting Neo4j full backup at 20240214_020000
Performing full backup...
Full backup completed: /tmp/neo4j_backups/neo4j_full_20240214_020000.dump
Compressing backup...
Encrypting backup with AES-256...
Backup encrypted: /tmp/neo4j_backups/neo4j_full_20240214_020000.dump.gz.enc
Uploading backup to S3...
Backup uploaded to s3://causal-organism-backups/neo4j/neo4j_full_20240214_020000.dump.gz.enc
Neo4j backup completed successfully!
```

#### Incremental Backup (Every 15 minutes)

```bash
# Load configuration
source config/backup-config.env

# Run incremental backup
./scripts/backup_neo4j.sh incremental
```

### TimescaleDB Backup

#### Full Backup (Daily at 2 AM UTC)

```bash
# Load configuration
source config/backup-config.env

# Run full backup
./scripts/backup_timescale.sh full
```

#### Incremental Backup (Every 15 minutes)

```bash
# Load configuration
source config/backup-config.env

# Run incremental backup
./scripts/backup_timescale.sh incremental
```

### Manual Backup Encryption

If you need to encrypt an existing backup file:

```bash
# Load configuration
source config/backup-config.env

# Encrypt file
./scripts/backup_encryption.sh encrypt /path/to/backup.dump.gz
```

---

## Recovery Procedures

### Neo4j Recovery

#### Prerequisites

1. Stop the Neo4j service
2. Backup current data (if any)
3. Download backup from S3
4. Decrypt backup

#### Step-by-Step Recovery

```bash
# 1. Stop Neo4j container
docker-compose stop neo4j

# 2. Backup current data (optional)
docker run --rm -v neo4j_data:/data -v $(pwd):/backup \
    alpine tar czf /backup/neo4j_current_backup.tar.gz /data

# 3. Load configuration
source config/backup-config.env

# 4. List available backups
aws s3 ls s3://${S3_BUCKET}/neo4j/

# 5. Download backup (replace with actual backup name)
BACKUP_NAME="neo4j_full_20240214_020000.dump.gz.enc"
aws s3 cp "s3://${S3_BUCKET}/neo4j/${BACKUP_NAME}" /tmp/

# 6. Decrypt backup
./scripts/backup_encryption.sh decrypt "/tmp/${BACKUP_NAME}"

# 7. Decompress backup
gunzip "/tmp/${BACKUP_NAME%.enc}"

# 8. Remove existing Neo4j data
docker volume rm neo4j_data || true
docker volume create neo4j_data

# 9. Start Neo4j temporarily to initialize
docker-compose up -d neo4j
sleep 10
docker-compose stop neo4j

# 10. Restore backup
DUMP_FILE="/tmp/${BACKUP_NAME%.enc.gz}"
docker cp "${DUMP_FILE}" neo4j:/tmp/restore.dump

docker-compose start neo4j
sleep 5

# 11. Load the dump
docker exec neo4j neo4j-admin database load neo4j \
    --from-path=/tmp \
    --overwrite-destination=true

# 12. Restart Neo4j
docker-compose restart neo4j

# 13. Verify recovery
docker exec neo4j cypher-shell -u neo4j -p causal_organism \
    "MATCH (n) RETURN count(n) as node_count;"
```

**Expected Recovery Time**: 15-30 minutes for typical database size

### TimescaleDB Recovery

#### Prerequisites

1. Stop the TimescaleDB service
2. Backup current data (if any)
3. Download backup from S3
4. Decrypt backup

#### Step-by-Step Recovery

```bash
# 1. Stop TimescaleDB container
docker-compose stop timescale

# 2. Backup current data (optional)
docker run --rm -v timescale_data:/data -v $(pwd):/backup \
    alpine tar czf /backup/timescale_current_backup.tar.gz /data

# 3. Load configuration
source config/backup-config.env

# 4. List available backups
aws s3 ls s3://${S3_BUCKET}/timescale/

# 5. Download backup (replace with actual backup name)
BACKUP_NAME="timescale_full_20240214_020000.dump.gz.enc"
aws s3 cp "s3://${S3_BUCKET}/timescale/${BACKUP_NAME}" /tmp/

# 6. Decrypt backup
./scripts/backup_encryption.sh decrypt "/tmp/${BACKUP_NAME}"

# 7. Decompress backup
gunzip "/tmp/${BACKUP_NAME%.enc}"

# 8. Remove existing TimescaleDB data
docker volume rm timescale_data || true
docker volume create timescale_data

# 9. Start TimescaleDB
docker-compose up -d timescale
sleep 10

# 10. Restore backup
DUMP_FILE="/tmp/${BACKUP_NAME%.enc.gz}"
docker cp "${DUMP_FILE}" timescale:/tmp/restore.dump

# 11. Restore the database
docker exec timescale pg_restore \
    -U postgres \
    -d postgres \
    -c \
    --if-exists \
    /tmp/restore.dump

# 12. Verify recovery
docker exec timescale psql -U postgres -d postgres \
    -c "SELECT COUNT(*) FROM employee_metrics;"

docker exec timescale psql -U postgres -d postgres \
    -c "SELECT COUNT(*) FROM intervention_audit_log;"
```

**Expected Recovery Time**: 10-20 minutes for typical database size

### Point-in-Time Recovery (PITR)

For point-in-time recovery using incremental backups:

```bash
# 1. Restore latest full backup (follow steps above)

# 2. Download and apply incremental backups
aws s3 sync "s3://${S3_BUCKET}/timescale/wal/" /tmp/wal_restore/

# 3. Apply WAL files in order
for wal_file in /tmp/wal_restore/*.tar.gz; do
    echo "Applying WAL: ${wal_file}"
    # Extract and apply WAL files
    # (Implementation depends on PostgreSQL WAL replay mechanism)
done
```

---

## Scheduled Backup Jobs

### Using Cron (Linux/Unix)

Add to crontab (`crontab -e`):

```cron
# Load environment variables
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin

# Neo4j Full Backup - Daily at 2 AM UTC
0 2 * * * cd /path/to/causal-organism && source config/backup-config.env && ./scripts/backup_neo4j.sh full >> /var/log/neo4j_backup.log 2>&1

# Neo4j Incremental Backup - Every 15 minutes
*/15 * * * * cd /path/to/causal-organism && source config/backup-config.env && ./scripts/backup_neo4j.sh incremental >> /var/log/neo4j_backup.log 2>&1

# TimescaleDB Full Backup - Daily at 2 AM UTC
0 2 * * * cd /path/to/causal-organism && source config/backup-config.env && ./scripts/backup_timescale.sh full >> /var/log/timescale_backup.log 2>&1

# TimescaleDB Incremental Backup - Every 15 minutes
*/15 * * * * cd /path/to/causal-organism && source config/backup-config.env && ./scripts/backup_timescale.sh incremental >> /var/log/timescale_backup.log 2>&1
```

### Using Kubernetes CronJob

Create `k8s/backup-cronjob.yaml`:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: neo4j-full-backup
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM UTC
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: causal-organism-backup:latest
            command: ["/scripts/backup_neo4j.sh", "full"]
            envFrom:
            - secretRef:
                name: backup-config
          restartPolicy: OnFailure
---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: neo4j-incremental-backup
spec:
  schedule: "*/15 * * * *"  # Every 15 minutes
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: causal-organism-backup:latest
            command: ["/scripts/backup_neo4j.sh", "incremental"]
            envFrom:
            - secretRef:
                name: backup-config
          restartPolicy: OnFailure
---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: timescale-full-backup
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM UTC
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: causal-organism-backup:latest
            command: ["/scripts/backup_timescale.sh", "full"]
            envFrom:
            - secretRef:
                name: backup-config
          restartPolicy: OnFailure
---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: timescale-incremental-backup
spec:
  schedule: "*/15 * * * *"  # Every 15 minutes
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: causal-organism-backup:latest
            command: ["/scripts/backup_timescale.sh", "incremental"]
            envFrom:
            - secretRef:
                name: backup-config
          restartPolicy: OnFailure
```

Apply the CronJob:

```bash
kubectl apply -f k8s/backup-cronjob.yaml
```

---

## Testing and Validation

### Monthly Recovery Test

**Schedule**: First Sunday of each month at 10 AM

**Procedure**:

1. **Select Test Environment**: Use staging environment, not production
2. **Download Recent Backup**: Get latest full backup from S3
3. **Perform Recovery**: Follow recovery procedures above
4. **Validate Data Integrity**:
   ```bash
   # Neo4j validation
   docker exec neo4j cypher-shell -u neo4j -p causal_organism \
       "MATCH (n) RETURN count(n) as nodes, labels(n) as types;"
   
   # TimescaleDB validation
   docker exec timescale psql -U postgres -d postgres \
       -c "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size FROM pg_tables WHERE schemaname NOT IN ('pg_catalog', 'information_schema') ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
   ```
5. **Measure Recovery Time**: Record actual RTO
6. **Document Results**: Update test log

### Backup Verification

Run weekly to verify backup integrity:

```bash
#!/bin/bash
# Verify latest backups

source config/backup-config.env

# Check Neo4j backup
LATEST_NEO4J=$(aws s3 ls s3://${S3_BUCKET}/neo4j/ | sort | tail -n 1 | awk '{print $4}')
echo "Latest Neo4j backup: ${LATEST_NEO4J}"

# Download and verify checksum
aws s3 cp "s3://${S3_BUCKET}/neo4j/${LATEST_NEO4J}" /tmp/
aws s3 cp "s3://${S3_BUCKET}/neo4j/${LATEST_NEO4J}.sha256" /tmp/

EXPECTED=$(cat "/tmp/${LATEST_NEO4J}.sha256")
ACTUAL=$(sha256sum "/tmp/${LATEST_NEO4J}" | awk '{print $1}')

if [ "${EXPECTED}" = "${ACTUAL}" ]; then
    echo "✓ Neo4j backup checksum verified"
else
    echo "✗ Neo4j backup checksum FAILED"
    exit 1
fi

# Check TimescaleDB backup
LATEST_TIMESCALE=$(aws s3 ls s3://${S3_BUCKET}/timescale/ | sort | tail -n 1 | awk '{print $4}')
echo "Latest TimescaleDB backup: ${LATEST_TIMESCALE}"

# Download and verify checksum
aws s3 cp "s3://${S3_BUCKET}/timescale/${LATEST_TIMESCALE}" /tmp/
aws s3 cp "s3://${S3_BUCKET}/timescale/${LATEST_TIMESCALE}.sha256" /tmp/

EXPECTED=$(cat "/tmp/${LATEST_TIMESCALE}.sha256")
ACTUAL=$(sha256sum "/tmp/${LATEST_TIMESCALE}" | awk '{print $1}')

if [ "${EXPECTED}" = "${ACTUAL}" ]; then
    echo "✓ TimescaleDB backup checksum verified"
else
    echo "✗ TimescaleDB backup checksum FAILED"
    exit 1
fi

echo "All backups verified successfully!"
```

---

## Troubleshooting

### Backup Failures

#### Issue: "AWS CLI not found"

**Solution**:
```bash
# Install AWS CLI
pip install awscli
# Or on Ubuntu/Debian
apt-get install awscli
```

#### Issue: "Encryption key not set"

**Solution**:
```bash
# Generate new encryption key
openssl rand -base64 32

# Add to configuration
echo "ENCRYPTION_KEY=<generated_key>" >> config/backup-config.env

# Reload configuration
source config/backup-config.env
```

#### Issue: "Cannot connect to Docker container"

**Solution**:
```bash
# Check container status
docker ps -a

# Restart container if needed
docker-compose restart neo4j
docker-compose restart timescale

# Check logs
docker logs neo4j
docker logs timescale
```

#### Issue: "S3 upload failed"

**Solution**:
```bash
# Verify AWS credentials
aws sts get-caller-identity

# Check S3 bucket access
aws s3 ls s3://${S3_BUCKET}/

# Verify network connectivity
ping s3.amazonaws.com
```

### Recovery Failures

#### Issue: "Database restore fails with permission error"

**Solution**:
```bash
# Ensure correct ownership
docker exec neo4j chown -R neo4j:neo4j /data
docker exec timescale chown -R postgres:postgres /var/lib/postgresql/data
```

#### Issue: "Decryption fails"

**Solution**:
```bash
# Verify encryption key matches
echo $ENCRYPTION_KEY

# Try manual decryption with verbose output
openssl enc -aes-256-cbc -d -pbkdf2 -iter 100000 \
    -in backup.dump.gz.enc \
    -out backup.dump.gz \
    -k "${ENCRYPTION_KEY}" -v
```

#### Issue: "Recovery takes longer than 1 hour"

**Solution**:
1. Check available disk space: `df -h`
2. Check available memory: `free -h`
3. Increase Docker resource limits
4. Consider using faster storage (SSD)
5. Parallelize recovery if possible

---

## Emergency Contacts

### On-Call Rotation

- **Primary**: ops-primary@example.com
- **Secondary**: ops-secondary@example.com
- **Manager**: ops-manager@example.com

### Escalation Path

1. **Level 1**: On-call engineer (15 min response)
2. **Level 2**: Senior engineer (30 min response)
3. **Level 3**: Engineering manager (1 hour response)

### Communication Channels

- **Slack**: #ops-incidents
- **PagerDuty**: causal-organism-ops
- **Email**: ops@example.com

---

## Appendix

### Backup File Naming Convention

```
<database>_<type>_<timestamp>.<extension>

Examples:
- neo4j_full_20240214_020000.dump.gz.enc
- timescale_incremental_20240214_021500.dump.gz.enc
```

### Encryption Details

- **Algorithm**: AES-256-CBC
- **Key Derivation**: PBKDF2 with 100,000 iterations
- **Salt**: Randomly generated per file
- **Checksum**: SHA-256

### Compliance Notes

- All backups are encrypted at rest (Requirement 22.6)
- Backups are retained for 30 days (Requirement 22.5)
- Recovery procedures target RTO <1 hour (Requirement 22.7)
- Monthly recovery testing validates procedures (Requirement 22.8)
- RPO <15 minutes achieved through incremental backups (Requirement 22.9)

---

**Document Version**: 1.0  
**Last Updated**: 2024-02-14  
**Next Review**: 2024-03-14
