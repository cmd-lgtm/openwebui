# Database Backup Quick Start Guide

## Initial Setup (5 minutes)

### 1. Configure Backup Settings

```bash
# Copy configuration template
cp config/backup-config.env.example config/backup-config.env

# Generate encryption key
openssl rand -base64 32

# Edit configuration file
nano config/backup-config.env
```

**Required settings:**
- `S3_BUCKET`: Your S3 bucket name
- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `ENCRYPTION_KEY`: Generated encryption key (paste from above)

### 2. Make Scripts Executable (Linux/Mac)

```bash
chmod +x scripts/backup_neo4j.sh
chmod +x scripts/backup_timescale.sh
chmod +x scripts/backup_encryption.sh
chmod +x scripts/restore_neo4j.sh
chmod +x scripts/restore_timescale.sh
chmod +x scripts/test_backup_recovery.sh
```

### 3. Test Backup

```bash
# Load configuration
source config/backup-config.env

# Test Neo4j backup
./scripts/backup_neo4j.sh full

# Test TimescaleDB backup
./scripts/backup_timescale.sh full

# Verify uploads
aws s3 ls s3://${S3_BUCKET}/neo4j/
aws s3 ls s3://${S3_BUCKET}/timescale/
```

## Daily Usage

### Create Manual Backup

```bash
# Load configuration
source config/backup-config.env

# Full backup
./scripts/backup_neo4j.sh full
./scripts/backup_timescale.sh full

# Incremental backup
./scripts/backup_neo4j.sh incremental
./scripts/backup_timescale.sh incremental
```

### List Available Backups

```bash
# Neo4j backups
aws s3 ls s3://${S3_BUCKET}/neo4j/

# TimescaleDB backups
aws s3 ls s3://${S3_BUCKET}/timescale/
```

### Restore from Backup

```bash
# Load configuration
source config/backup-config.env

# List available backups
aws s3 ls s3://${S3_BUCKET}/neo4j/

# Restore Neo4j (replace with actual backup name)
./scripts/restore_neo4j.sh neo4j_full_20240214_020000.dump.gz.enc

# Restore TimescaleDB (replace with actual backup name)
./scripts/restore_timescale.sh timescale_full_20240214_020000.dump.gz.enc
```

## Automated Backups

### Setup Cron Jobs (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Add these lines (adjust path to your installation):
0 2 * * * cd /path/to/causal-organism && source config/backup-config.env && ./scripts/backup_neo4j.sh full >> /var/log/neo4j_backup.log 2>&1
*/15 * * * * cd /path/to/causal-organism && source config/backup-config.env && ./scripts/backup_neo4j.sh incremental >> /var/log/neo4j_backup.log 2>&1
0 2 * * * cd /path/to/causal-organism && source config/backup-config.env && ./scripts/backup_timescale.sh full >> /var/log/timescale_backup.log 2>&1
*/15 * * * * cd /path/to/causal-organism && source config/backup-config.env && ./scripts/backup_timescale.sh incremental >> /var/log/timescale_backup.log 2>&1
```

### Setup Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Daily at 2:00 AM
4. Action: Start a program
5. Program: `bash` (requires WSL or Git Bash)
6. Arguments: `-c "cd /path/to/causal-organism && source config/backup-config.env && ./scripts/backup_neo4j.sh full"`

Repeat for other backup scripts.

## Monitoring

### Check Backup Status

```bash
# View backup logs
tail -f /var/log/neo4j_backup.log
tail -f /var/log/timescale_backup.log

# Check S3 storage usage
aws s3 ls s3://${S3_BUCKET}/ --recursive --human-readable --summarize
```

### Run Test Suite

```bash
# Run automated tests
TEST_ENV=staging ./scripts/test_backup_recovery.sh

# View test results
cat /var/log/backup_recovery_test_*.log
```

## Troubleshooting

### "AWS CLI not found"

```bash
# Install AWS CLI
pip install awscli
# Or on Ubuntu/Debian
sudo apt-get install awscli
```

### "Encryption key not set"

```bash
# Generate new key
openssl rand -base64 32

# Add to config
echo "ENCRYPTION_KEY=<paste_key_here>" >> config/backup-config.env
```

### "Cannot connect to Docker container"

```bash
# Check containers
docker ps -a

# Restart if needed
docker-compose restart neo4j timescale
```

### "S3 upload failed"

```bash
# Test AWS credentials
aws sts get-caller-identity

# Test S3 access
aws s3 ls s3://${S3_BUCKET}/
```

## Important Notes

⚠️ **Security**:
- Never commit `config/backup-config.env` to version control
- Store encryption keys securely (use secret manager in production)
- Restrict S3 bucket access with IAM policies

⚠️ **Testing**:
- Test restore procedures monthly
- Use staging environment for restore tests
- Verify data integrity after restore

⚠️ **Monitoring**:
- Set up alerts for backup failures
- Monitor S3 storage costs
- Track backup duration trends

## Quick Reference

| Task | Command |
|------|---------|
| Full backup (Neo4j) | `./scripts/backup_neo4j.sh full` |
| Incremental backup (Neo4j) | `./scripts/backup_neo4j.sh incremental` |
| Full backup (TimescaleDB) | `./scripts/backup_timescale.sh full` |
| Incremental backup (TimescaleDB) | `./scripts/backup_timescale.sh incremental` |
| List backups | `aws s3 ls s3://${S3_BUCKET}/neo4j/` |
| Restore Neo4j | `./scripts/restore_neo4j.sh <backup_name>` |
| Restore TimescaleDB | `./scripts/restore_timescale.sh <backup_name>` |
| Run tests | `./scripts/test_backup_recovery.sh` |
| Encrypt file | `./scripts/backup_encryption.sh encrypt <file>` |
| Decrypt file | `./scripts/backup_encryption.sh decrypt <file>` |

## Support

- **Full Documentation**: See `BACKUP_RECOVERY_RUNBOOK.md`
- **Implementation Details**: See `BACKUP_IMPLEMENTATION_SUMMARY.md`
- **Configuration**: See `config/backup-config.env.example`

---

**Need Help?** Check the full runbook at `BACKUP_RECOVERY_RUNBOOK.md`
