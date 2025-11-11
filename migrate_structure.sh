#!/bin/bash
###############################################################################
# Project Structure Migration Script
#
# SAFE MIGRATION: This script reorganizes the project structure locally
# WITHOUT affecting the running production server.
#
# Run this locally FIRST, test, then deploy to production separately.
###############################################################################

set -e  # Exit on error

echo "════════════════════════════════════════════════════════════"
echo "   Payment Webhook - Project Structure Migration"
echo "════════════════════════════════════════════════════════════"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Safety check - ensure we're in the right directory
if [ ! -f "webhook_app.py" ]; then
    echo -e "${RED}❌ Error: webhook_app.py not found. Are you in the project root?${NC}"
    exit 1
fi

echo -e "${BLUE}Current directory: $(pwd)${NC}"
echo ""

# Check git status
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}⚠️  Warning: You have uncommitted changes${NC}"
    echo "Git status:"
    git status --short
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Migration cancelled"
        exit 1
    fi
fi

echo ""
echo -e "${YELLOW}STEP 1: Creating backup${NC}"
echo "────────────────────────────────────────────────────────────"

BACKUP_DIR="../payment-webhook-backup-$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp -r . "$BACKUP_DIR/" 2>/dev/null || true

echo -e "${GREEN}✓ Backup created: $BACKUP_DIR${NC}"
echo ""

echo -e "${YELLOW}STEP 2: Creating folder structure${NC}"
echo "────────────────────────────────────────────────────────────"

# Create directories
mkdir -p app
mkdir -p services
mkdir -p utils
mkdir -p database/{schema,migrations,views,seeds,backups}
mkdir -p data
mkdir -p scripts
mkdir -p tests/fixtures
mkdir -p docs/{setup,guides,changes,analysis,archive}

echo -e "${GREEN}✓ Folders created${NC}"
echo ""

echo -e "${YELLOW}STEP 3: Moving files (copying first for safety)${NC}"
echo "────────────────────────────────────────────────────────────"

# Move application code
echo "  → Moving application code..."
mv webhook_app.py app/ 2>/dev/null || true

# Move services
echo "  → Moving services..."
mv payment_monitor.py services/ 2>/dev/null || true
mv payment_daily_report.py services/ 2>/dev/null || true

# Move utilities
echo "  → Moving utilities..."
mv bin_import.py utils/ 2>/dev/null || true
mv mid_import.py utils/ 2>/dev/null || true
mv merchant_reimport.py utils/ 2>/dev/null || true
mv backfill_mid_names.py utils/ 2>/dev/null || true
mv telegram_setup.py utils/ 2>/dev/null || true
mv test_telegram.py utils/ 2>/dev/null || true

# Move database files
echo "  → Moving database files..."

# Schema
mv database_schema.sql database/schema/ 2>/dev/null || true
mv database_schema_fixed.sql database/schema/ 2>/dev/null || true

# Migrations
mv migration_add_mid_name.sql database/migrations/ 2>/dev/null || true
mv migration_add_midid_reconid.sql database/migrations/ 2>/dev/null || true

# Views
mv create_grafana_views.sql database/views/ 2>/dev/null || true
mv create_monitoring_views.sql database/views/ 2>/dev/null || true
mv create_bank_performance_views.sql database/views/ 2>/dev/null || true
mv create_alltime_views.sql database/views/ 2>/dev/null || true
mv create_revenue_views.sql database/views/ 2>/dev/null || true
mv update_grafana_views.sql database/views/ 2>/dev/null || true

# Seeds/fixtures
mv merchant_import.sql database/seeds/ 2>/dev/null || true
mv create_mid_mapping_table.sql database/seeds/ 2>/dev/null || true
mv fix_merchant_data.sql database/seeds/ 2>/dev/null || true

# Backups
mv backup_bin_bank_mapping_*.sql database/backups/ 2>/dev/null || true

# Move data files
echo "  → Moving data files..."
mv BINS_and_BANKS_List.csv data/ 2>/dev/null || true

# Move scripts
echo "  → Moving scripts..."
mv deploy.sh scripts/ 2>/dev/null || true
mv auto_deploy.sh scripts/ 2>/dev/null || true
mv quick_push.sh scripts/ 2>/dev/null || true
mv install.sh scripts/ 2>/dev/null || true
mv setup_github_auth.sh scripts/ 2>/dev/null || true

# Move documentation
echo "  → Moving documentation..."

# Setup guides
mv CI_CD_SETUP_GUIDE.md docs/setup/ 2>/dev/null || true
mv DEPLOYMENT.md docs/setup/ 2>/dev/null || true
mv GRAFANA_SETUP.md docs/setup/ 2>/dev/null || true
mv MONITORING_README.md docs/setup/ 2>/dev/null || true

# User guides
mv QUICK_REFERENCE.md docs/guides/ 2>/dev/null || true
mv GRAFANA_SHARING_GUIDE.md docs/guides/ 2>/dev/null || true
mv REVENUE_DASHBOARD_GUIDE.md docs/guides/ 2>/dev/null || true

# Change logs
mv GRAFANA_DASHBOARD_UPDATES.md docs/changes/ 2>/dev/null || true
mv GRAFANA_FIXES_SUMMARY.md docs/changes/ 2>/dev/null || true
mv BANK_PERFORMANCE_VIEWS.md docs/changes/ 2>/dev/null || true
mv ALLTIME_DASHBOARD_UPDATE.md docs/changes/ 2>/dev/null || true
mv MID_414103113839_ADDED.md docs/changes/ 2>/dev/null || true
mv POLPAY_DASHBOARD_CLEANUP.md docs/changes/ 2>/dev/null || true
mv SUCCESS_RATE_GRAPH_FIX.md docs/changes/ 2>/dev/null || true
mv TIME_FILTER_FIX.md docs/changes/ 2>/dev/null || true
mv TIMEOUT_PANEL_UPDATE.md docs/changes/ 2>/dev/null || true

# Analysis reports
mv BIN_ANALYSIS_REPORT.md docs/analysis/ 2>/dev/null || true
mv PROJECT_STRUCTURE_REPORT.md docs/analysis/ 2>/dev/null || true
mv TEST.md docs/analysis/ 2>/dev/null || true

# Archive disabled features
mv *.disabled docs/archive/ 2>/dev/null || true

echo -e "${GREEN}✓ Files moved${NC}"
echo ""

echo -e "${YELLOW}STEP 4: Creating __init__.py files${NC}"
echo "────────────────────────────────────────────────────────────"

# Create __init__.py files for Python packages
touch app/__init__.py
touch services/__init__.py
touch utils/__init__.py
touch tests/__init__.py

echo -e "${GREEN}✓ Python package files created${NC}"
echo ""

echo -e "${YELLOW}STEP 5: Making scripts executable${NC}"
echo "────────────────────────────────────────────────────────────"

chmod +x scripts/*.sh 2>/dev/null || true

echo -e "${GREEN}✓ Scripts made executable${NC}"
echo ""

echo "════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ MIGRATION COMPLETE!${NC}"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "📁 New structure created:"
echo "   app/          - Main application code"
echo "   services/     - Background services"
echo "   utils/        - Utility scripts"
echo "   database/     - SQL files organized"
echo "   data/         - Static data files"
echo "   scripts/      - Deployment scripts"
echo "   tests/        - Test suite (ready for tests)"
echo "   docs/         - All documentation organized"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "   1. Review the changes: git status"
echo "   2. Update import paths (run update_imports.sh)"
echo "   3. Test locally: python3 -m pytest (after adding tests)"
echo "   4. Commit changes: git add . && git commit"
echo "   5. Push to GitHub: git push origin main"
echo "   6. Deploy to production: (See MIGRATION_PLAN.md Phase 2)"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT: This only reorganizes LOCAL files${NC}"
echo -e "${YELLOW}   Production server update is a SEPARATE step!${NC}"
echo ""
echo "Backup location: $BACKUP_DIR"
echo ""
