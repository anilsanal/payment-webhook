#!/bin/bash
###############################################################################
# Emergency Rollback Script
#
# Use this if something goes wrong after restructuring.
# This restores the flat structure from the most recent backup.
###############################################################################

set -e

echo "════════════════════════════════════════════════════════════"
echo "   🔙 EMERGENCY ROLLBACK - Structure Restoration"
echo "════════════════════════════════════════════════════════════"
echo ""

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${RED}⚠️  WARNING: This will restore the old flat structure${NC}"
echo ""

# Find the most recent backup
BACKUP_DIR=$(ls -td ../payment-webhook-backup-* 2>/dev/null | head -1)

if [ -z "$BACKUP_DIR" ]; then
    echo -e "${RED}❌ No backup found!${NC}"
    echo "Looking for: ../payment-webhook-backup-*"
    exit 1
fi

echo "Found backup: $BACKUP_DIR"
echo ""
read -p "Restore from this backup? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Rollback cancelled"
    exit 1
fi

echo ""
echo -e "${YELLOW}Starting rollback...${NC}"
echo ""

# Save current state just in case
CURRENT_BACKUP="../payment-webhook-before-rollback-$(date +%Y%m%d_%H%M%S)"
mkdir -p "$CURRENT_BACKUP"
cp -r . "$CURRENT_BACKUP/" 2>/dev/null || true
echo -e "${GREEN}✓ Current state saved to: $CURRENT_BACKUP${NC}"
echo ""

# Remove new folders (but keep .git, venv, logs)
echo "Removing new folder structure..."
rm -rf app/ services/ utils/ database/ data/ scripts/ tests/ docs/ 2>/dev/null || true
echo -e "${GREEN}✓ New folders removed${NC}"
echo ""

# Restore files from backup (excluding .git, venv, logs)
echo "Restoring files from backup..."
rsync -av --exclude='.git/' --exclude='venv/' --exclude='logs/' --exclude='*.log' "$BACKUP_DIR/" .
echo -e "${GREEN}✓ Files restored${NC}"
echo ""

# Remove migration scripts
rm -f migrate_structure.sh update_imports.sh update_production.sh rollback_structure.sh MIGRATION_PLAN.md 2>/dev/null || true

echo ""
echo "════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ ROLLBACK COMPLETE${NC}"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Restored from: $BACKUP_DIR"
echo "Previous state saved to: $CURRENT_BACKUP"
echo ""
echo "Run 'git status' to see changes"
echo ""
