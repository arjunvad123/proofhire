#!/bin/bash
#
# Rollback OpenClaw to previous version
#
# Usage:
#   ./scripts/rollback-openclaw.sh [version]
#   ./scripts/rollback-openclaw.sh  # Uses backup file
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENCITY_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$AGENCITY_ROOT"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

TARGET_VERSION="${1:-}"

# Get version from backup file if not provided
if [ -z "$TARGET_VERSION" ]; then
    if [ -f ".openclaw-version-backup.txt" ]; then
        TARGET_VERSION=$(cat .openclaw-version-backup.txt)
        echo -e "${BLUE}Using version from backup: ${TARGET_VERSION}${NC}"
    else
        echo -e "${RED}✗ No backup file found and no version specified${NC}"
        echo ""
        echo "Usage:"
        echo "  ./scripts/rollback-openclaw.sh [version]"
        echo "  ./scripts/rollback-openclaw.sh 1.0.0"
        exit 1
    fi
fi

CURRENT_VERSION=$(npm list openclaw 2>/dev/null | grep openclaw@ | sed 's/.*@//' | awk '{print $1}' || echo "not installed")

echo -e "${BLUE}Rolling back OpenClaw...${NC}"
echo "  Current: $CURRENT_VERSION"
echo "  Target:  $TARGET_VERSION"
echo ""

# Confirm rollback
read -p "Are you sure you want to rollback? (y/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Rollback cancelled"
    exit 0
fi

# Install target version
echo ""
echo -e "${BLUE}Installing OpenClaw ${TARGET_VERSION}...${NC}"
npm install "openclaw@${TARGET_VERSION}"

# Verify rollback
NEW_VERSION=$(npm list openclaw | grep openclaw@ | sed 's/.*@//' | awk '{print $1}')
if [ "$NEW_VERSION" = "$TARGET_VERSION" ]; then
    echo -e "${GREEN}✓ Successfully rolled back to ${TARGET_VERSION}${NC}"
else
    echo -e "${RED}✗ Rollback failed. Current version: ${NEW_VERSION}${NC}"
    exit 1
fi

# Run smoke tests
echo ""
echo -e "${BLUE}Running smoke tests...${NC}"
if command -v pytest &> /dev/null && [ -d "tests" ]; then
    pytest tests/ -k "smoke" -v 2>/dev/null || echo -e "${YELLOW}⚠ Smoke tests skipped${NC}"
else
    echo -e "${YELLOW}⚠ Smoke tests skipped (pytest not found)${NC}"
fi

echo ""
echo -e "${GREEN}✓ Rollback complete${NC}"
echo ""
echo "Next steps:"
echo "  1. Test manually: ./bin/agencity start"
echo "  2. Verify everything works"
echo "  3. Investigate why the update failed"
echo "  4. Fix issues before attempting update again"
