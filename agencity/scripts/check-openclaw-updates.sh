#!/bin/bash
#
# Check for OpenClaw updates and security advisories
#
# Usage:
#   ./scripts/check-openclaw-updates.sh
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

echo -e "${BLUE}Checking OpenClaw updates...${NC}"
echo ""

# Check if package.json exists
if [ ! -f "package.json" ]; then
    echo -e "${YELLOW}⚠ package.json not found. Creating one...${NC}"
    cat > package.json <<EOF
{
  "name": "agencity",
  "version": "0.1.0",
  "dependencies": {
    "openclaw": "^1.0.0"
  }
}
EOF
fi

# Check current version
CURRENT_VERSION=$(npm list openclaw 2>/dev/null | grep openclaw@ | sed 's/.*@//' | awk '{print $1}' || echo "not installed")
echo -e "${BLUE}Current OpenClaw version: ${CURRENT_VERSION}${NC}"

# Check for updates
echo ""
echo -e "${BLUE}Checking for available updates...${NC}"
npm outdated openclaw 2>/dev/null || echo -e "${GREEN}✓ OpenClaw is up to date${NC}"

# Check security vulnerabilities
echo ""
echo -e "${BLUE}Checking for security vulnerabilities...${NC}"
if npm audit openclaw 2>/dev/null; then
    echo -e "${GREEN}✓ No known security vulnerabilities${NC}"
else
    echo -e "${YELLOW}⚠ Security vulnerabilities found. Run 'npm audit fix'${NC}"
fi

# Check GitHub releases (requires gh CLI)
if command -v gh &> /dev/null; then
    echo ""
    echo -e "${BLUE}Recent OpenClaw releases:${NC}"
    gh release list --repo openclaw/openclaw --limit 5 2>/dev/null || echo "  (GitHub CLI not authenticated)"
fi

# Check npm registry for latest version
echo ""
echo -e "${BLUE}Latest version on npm:${NC}"
LATEST=$(npm view openclaw version 2>/dev/null || echo "unknown")
echo "  Latest: $LATEST"
echo "  Current: $CURRENT_VERSION"

if [ "$CURRENT_VERSION" != "$LATEST" ] && [ "$LATEST" != "unknown" ]; then
    echo ""
    echo -e "${YELLOW}⚠ Update available: $CURRENT_VERSION → $LATEST${NC}"
    echo ""
    echo "To update:"
    echo "  1. Review changelog: npm view openclaw changelog"
    echo "  2. Test update: ./scripts/test-openclaw-update.sh"
    echo "  3. Apply update: npm install openclaw@latest"
else
    echo -e "${GREEN}✓ You're on the latest version${NC}"
fi

echo ""
