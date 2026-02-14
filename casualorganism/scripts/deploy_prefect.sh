#!/bin/bash
# Deploy Prefect workflows with schedules
# Requirements: 15.7, 15.8

set -e

echo "========================================="
echo "Prefect Workflow Deployment Script"
echo "========================================="
echo ""

# Check if Prefect is installed
if ! command -v prefect &> /dev/null; then
    echo "Error: Prefect is not installed"
    echo "Install with: pip install prefect>=2.14.0"
    exit 1
fi

# Check Prefect server connection
echo "Checking Prefect server connection..."
if ! python backend/prefect_config.py check; then
    echo ""
    echo "Error: Cannot connect to Prefect server"
    echo ""
    echo "To start Prefect server:"
    echo "  Option 1 (Local): prefect server start"
    echo "  Option 2 (Docker): docker-compose -f docker-compose.prefect.yml up -d"
    echo ""
    exit 1
fi

echo ""
echo "✓ Prefect server is accessible"
echo ""

# Setup work queue and deploy flows
echo "Setting up work queue and deploying flows..."
python backend/prefect_config.py setup

echo ""
echo "========================================="
echo "Deployment Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Start Prefect agent:"
echo "   prefect agent start -q default"
echo ""
echo "2. View Prefect UI:"
echo "   http://localhost:4200"
echo ""
echo "3. Monitor flow runs:"
echo "   prefect deployment ls"
echo "   prefect flow-run ls"
echo ""
echo "4. Trigger manual run:"
echo "   prefect deployment run incremental-update-pipeline/incremental-updates"
echo "   prefect deployment run full-analysis-pipeline/full-analysis"
echo ""
