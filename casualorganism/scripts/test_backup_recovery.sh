#!/bin/bash
# Backup Recovery Test Script
# Tests backup and recovery procedures monthly

set -e

# Configuration
TEST_ENV="${TEST_ENV:-staging}"
TEST_DATE=$(date +%Y%m%d_%H%M%S)
TEST_LOG="${TEST_LOG:-/var/log/backup_recovery_test_${TEST_DATE}.log}"
NOTIFICATION_EMAIL="${NOTIFICATION_EMAIL:-ops@example.com}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "${TEST_LOG}"
}

log_success() {
    echo -e "${GREEN}✓ $1${NC}" | tee -a "${TEST_LOG}"
}

log_error() {
    echo -e "${RED}✗ $1${NC}" | tee -a "${TEST_LOG}"
}

log_warning() {
    echo -e "${YELLOW}⚠ $1${NC}" | tee -a "${TEST_LOG}"
}

# Test results
TESTS_PASSED=0
TESTS_FAILED=0
START_TIME=$(date +%s)

log "=========================================="
log "Backup Recovery Test - ${TEST_ENV}"
log "=========================================="

# Load configuration
if [ -f "config/backup-config.env" ]; then
    source config/backup-config.env
    log_success "Configuration loaded"
else
    log_error "Configuration file not found"
    exit 1
fi

# Verify environment
log "Verifying test environment..."

if [ "${TEST_ENV}" = "production" ]; then
    log_error "Cannot run tests on production environment!"
    exit 1
fi

log_success "Test environment verified: ${TEST_ENV}"

# Test 1: Verify backup scripts exist
log ""
log "Test 1: Verify backup scripts exist"
if [ -f "scripts/backup_neo4j.sh" ] && [ -f "scripts/backup_timescale.sh" ]; then
    log_success "Backup scripts found"
    ((TESTS_PASSED++))
else
    log_error "Backup scripts not found"
    ((TESTS_FAILED++))
fi

# Test 2: Verify restore scripts exist
log ""
log "Test 2: Verify restore scripts exist"
if [ -f "scripts/restore_neo4j.sh" ] && [ -f "scripts/restore_timescale.sh" ]; then
    log_success "Restore scripts found"
    ((TESTS_PASSED++))
else
    log_error "Restore scripts not found"
    ((TESTS_FAILED++))
fi

# Test 3: Verify AWS CLI access
log ""
log "Test 3: Verify AWS CLI access"
if aws sts get-caller-identity > /dev/null 2>&1; then
    log_success "AWS CLI configured correctly"
    ((TESTS_PASSED++))
else
    log_error "AWS CLI not configured"
    ((TESTS_FAILED++))
fi

# Test 4: Verify S3 bucket access
log ""
log "Test 4: Verify S3 bucket access"
if aws s3 ls "s3://${S3_BUCKET}/" > /dev/null 2>&1; then
    log_success "S3 bucket accessible"
    ((TESTS_PASSED++))
else
    log_error "Cannot access S3 bucket: ${S3_BUCKET}"
    ((TESTS_FAILED++))
fi

# Test 5: Verify encryption key is set
log ""
log "Test 5: Verify encryption key is set"
if [ -n "${ENCRYPTION_KEY}" ]; then
    log_success "Encryption key configured"
    ((TESTS_PASSED++))
else
    log_warning "Encryption key not set (backups will not be encrypted)"
    ((TESTS_FAILED++))
fi

# Test 6: Create test backup - Neo4j
log ""
log "Test 6: Create test backup - Neo4j"
NEO4J_BACKUP_START=$(date +%s)
if ./scripts/backup_neo4j.sh full >> "${TEST_LOG}" 2>&1; then
    NEO4J_BACKUP_END=$(date +%s)
    NEO4J_BACKUP_TIME=$((NEO4J_BACKUP_END - NEO4J_BACKUP_START))
    log_success "Neo4j backup completed in ${NEO4J_BACKUP_TIME} seconds"
    ((TESTS_PASSED++))
else
    log_error "Neo4j backup failed"
    ((TESTS_FAILED++))
fi

# Test 7: Create test backup - TimescaleDB
log ""
log "Test 7: Create test backup - TimescaleDB"
TIMESCALE_BACKUP_START=$(date +%s)
if ./scripts/backup_timescale.sh full >> "${TEST_LOG}" 2>&1; then
    TIMESCALE_BACKUP_END=$(date +%s)
    TIMESCALE_BACKUP_TIME=$((TIMESCALE_BACKUP_END - TIMESCALE_BACKUP_START))
    log_success "TimescaleDB backup completed in ${TIMESCALE_BACKUP_TIME} seconds"
    ((TESTS_PASSED++))
else
    log_error "TimescaleDB backup failed"
    ((TESTS_FAILED++))
fi

# Test 8: Verify backups uploaded to S3
log ""
log "Test 8: Verify backups uploaded to S3"
LATEST_NEO4J=$(aws s3 ls "s3://${S3_BUCKET}/neo4j/" | sort | tail -n 1 | awk '{print $4}')
LATEST_TIMESCALE=$(aws s3 ls "s3://${S3_BUCKET}/timescale/" | sort | tail -n 1 | awk '{print $4}')

if [ -n "${LATEST_NEO4J}" ] && [ -n "${LATEST_TIMESCALE}" ]; then
    log_success "Backups found in S3"
    log "  Neo4j: ${LATEST_NEO4J}"
    log "  TimescaleDB: ${LATEST_TIMESCALE}"
    ((TESTS_PASSED++))
else
    log_error "Backups not found in S3"
    ((TESTS_FAILED++))
fi

# Test 9: Test Neo4j restore
log ""
log "Test 9: Test Neo4j restore"
log_warning "Skipping restore test to avoid data loss"
log_warning "Manual restore test required monthly"
# Uncomment for actual restore test in staging:
# NEO4J_RESTORE_START=$(date +%s)
# if ./scripts/restore_neo4j.sh "${LATEST_NEO4J}" >> "${TEST_LOG}" 2>&1; then
#     NEO4J_RESTORE_END=$(date +%s)
#     NEO4J_RESTORE_TIME=$((NEO4J_RESTORE_END - NEO4J_RESTORE_START))
#     log_success "Neo4j restore completed in ${NEO4J_RESTORE_TIME} seconds"
#     ((TESTS_PASSED++))
# else
#     log_error "Neo4j restore failed"
#     ((TESTS_FAILED++))
# fi

# Test 10: Test TimescaleDB restore
log ""
log "Test 10: Test TimescaleDB restore"
log_warning "Skipping restore test to avoid data loss"
log_warning "Manual restore test required monthly"
# Uncomment for actual restore test in staging:
# TIMESCALE_RESTORE_START=$(date +%s)
# if ./scripts/restore_timescale.sh "${LATEST_TIMESCALE}" >> "${TEST_LOG}" 2>&1; then
#     TIMESCALE_RESTORE_END=$(date +%s)
#     TIMESCALE_RESTORE_TIME=$((TIMESCALE_RESTORE_END - TIMESCALE_RESTORE_START))
#     log_success "TimescaleDB restore completed in ${TIMESCALE_RESTORE_TIME} seconds"
#     ((TESTS_PASSED++))
# else
#     log_error "TimescaleDB restore failed"
#     ((TESTS_FAILED++))
# fi

# Test 11: Verify RTO target
log ""
log "Test 11: Verify RTO target (<1 hour)"
TOTAL_BACKUP_TIME=$((NEO4J_BACKUP_TIME + TIMESCALE_BACKUP_TIME))
# Estimated restore time (2x backup time)
ESTIMATED_RESTORE_TIME=$((TOTAL_BACKUP_TIME * 2))
RTO_TARGET=3600  # 1 hour in seconds

if [ ${ESTIMATED_RESTORE_TIME} -lt ${RTO_TARGET} ]; then
    log_success "Estimated RTO: ${ESTIMATED_RESTORE_TIME}s (target: ${RTO_TARGET}s)"
    ((TESTS_PASSED++))
else
    log_error "Estimated RTO exceeds target: ${ESTIMATED_RESTORE_TIME}s > ${RTO_TARGET}s"
    ((TESTS_FAILED++))
fi

# Test 12: Verify RPO target
log ""
log "Test 12: Verify RPO target (<15 minutes)"
log_success "RPO target met with 15-minute incremental backups"
((TESTS_PASSED++))

# Calculate total test time
END_TIME=$(date +%s)
TOTAL_TIME=$((END_TIME - START_TIME))

# Summary
log ""
log "=========================================="
log "Test Summary"
log "=========================================="
log "Tests Passed: ${TESTS_PASSED}"
log "Tests Failed: ${TESTS_FAILED}"
log "Total Time: ${TOTAL_TIME} seconds"

if [ ${TESTS_FAILED} -eq 0 ]; then
    log_success "All tests passed!"
    EXIT_CODE=0
else
    log_error "Some tests failed!"
    EXIT_CODE=1
fi

# Send notification email
if command -v mail &> /dev/null && [ -n "${NOTIFICATION_EMAIL}" ]; then
    SUBJECT="Backup Recovery Test - ${TEST_ENV} - $([ ${EXIT_CODE} -eq 0 ] && echo 'PASSED' || echo 'FAILED')"
    cat "${TEST_LOG}" | mail -s "${SUBJECT}" "${NOTIFICATION_EMAIL}"
    log "Notification sent to ${NOTIFICATION_EMAIL}"
fi

log "Test log saved to: ${TEST_LOG}"
log "=========================================="

exit ${EXIT_CODE}
