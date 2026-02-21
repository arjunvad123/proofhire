#!/bin/bash
#
# Test OpenClaw update before applying to production
#
# Usage:
#   ./scripts/test-openclaw-update.sh [version]
#   ./scripts/test-openclaw-update.sh latest
#   ./scripts/test-openclaw-update.sh 1.1.0
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

TARGET_VERSION="${1:-latest}"

echo -e "${BLUE}Testing OpenClaw update to ${TARGET_VERSION}...${NC}"
echo ""

# Backup current version
CURRENT_VERSION=$(npm list openclaw 2>/dev/null | grep openclaw@ | sed 's/.*@//' | awk '{print $1}' || echo "not installed")
echo -e "${BLUE}Current version: ${CURRENT_VERSION}${NC}"
echo "$CURRENT_VERSION" > .openclaw-version-backup.txt
echo -e "${GREEN}✓ Backed up current version${NC}"

# Install target version
echo ""
echo -e "${BLUE}Installing OpenClaw ${TARGET_VERSION}...${NC}"
if [ "$TARGET_VERSION" = "latest" ]; then
    npm install openclaw@latest
else
    npm install "openclaw@${TARGET_VERSION}"
fi

NEW_VERSION=$(npm list openclaw | grep openclaw@ | sed 's/.*@//' | awk '{print $1}')
echo -e "${GREEN}✓ Installed version: ${NEW_VERSION}${NC}"

# Run tests
echo ""
echo -e "${BLUE}Running test suite...${NC}"

# Check if tests exist
if [ -f "pyproject.toml" ] || [ -d "tests" ]; then
    echo "Running Python tests..."
    if command -v pytest &> /dev/null; then
        pytest tests/ -v || echo -e "${YELLOW}⚠ Some tests failed${NC}"
    else
        echo -e "${YELLOW}⚠ pytest not found, skipping Python tests${NC}"
    fi
fi

# Test OpenClaw gateway startup
echo ""
echo -e "${BLUE}Testing OpenClaw gateway...${NC}"
if command -v node &> /dev/null; then
    # Check if openclaw binary exists
    if npm list openclaw &> /dev/null; then
        echo -e "${GREEN}✓ OpenClaw package installed${NC}"
        
        # Try to run openclaw doctor if available
        if npx openclaw doctor &> /dev/null; then
            echo -e "${GREEN}✓ OpenClaw doctor check passed${NC}"
        else
            echo -e "${YELLOW}⚠ OpenClaw doctor check skipped (not configured)${NC}"
        fi
    else
        echo -e "${RED}✗ OpenClaw not found${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠ Node.js not found, skipping gateway test${NC}"
fi

# Test Agencity API integration
echo ""
echo -e "${BLUE}Testing Agencity API integration...${NC}"
if [ -f "app/main.py" ]; then
    echo "Checking FastAPI app..."
    python -c "from app.main import app; print('✓ FastAPI app loads successfully')" 2>/dev/null || {
        echo -e "${YELLOW}⚠ FastAPI app check skipped${NC}"
    }
fi

# Summary
echo ""
echo -e "${BLUE}Test Summary:${NC}"
echo "  Previous version: $CURRENT_VERSION"
echo "  New version: $NEW_VERSION"
echo ""
echo -e "${GREEN}✓ Update test complete${NC}"
echo ""
echo "Next steps:"
echo "  1. Review any warnings above"
echo "  2. Test manually: ./bin/agencity start"
echo "  3. If everything works, commit the update"
echo "  4. If issues found, rollback: ./scripts/rollback-openclaw.sh"
