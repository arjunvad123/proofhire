#!/usr/bin/env bash
#
# update-openclaw.sh — Update embedded OpenClaw to a new release
#
# Usage:
#   ./scripts/update-openclaw.sh              # Update to latest release
#   ./scripts/update-openclaw.sh v2026.2.15   # Update to specific release
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENCITY_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OPENCLAW_DIR="$AGENCITY_ROOT/vendor/openclaw"
TARGET_TAG="${1:-}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log()  { echo -e "${BLUE}[update-openclaw]${NC} $*"; }
ok()   { echo -e "${GREEN}[update-openclaw]${NC} $*"; }
warn() { echo -e "${YELLOW}[update-openclaw]${NC} $*"; }
err()  { echo -e "${RED}[update-openclaw]${NC} $*" >&2; }

if [ ! -d "$OPENCLAW_DIR" ]; then
    err "OpenClaw not found at $OPENCLAW_DIR"
    err "Run ./scripts/setup-openclaw.sh first"
    exit 1
fi

cd "$OPENCLAW_DIR"

# Current version
CURRENT=$(cat "$AGENCITY_ROOT/.openclaw-version" 2>/dev/null || echo "unknown")
log "Current version: $CURRENT"

# Fetch releases
log "Fetching releases..."
git fetch --tags origin

# Determine target
if [ -n "$TARGET_TAG" ]; then
    TARGET="$TARGET_TAG"
else
    TARGET=$(git tag --sort=-v:refname | head -1)
    if [ -z "$TARGET" ]; then
        err "No release tags found"
        exit 1
    fi
fi

if [ "$CURRENT" = "$TARGET" ]; then
    ok "Already on $TARGET — nothing to update"
    exit 0
fi

log "Updating: $CURRENT → $TARGET"

# Backup current version for rollback
echo "$CURRENT" > "$AGENCITY_ROOT/.openclaw-version-backup"

# Checkout target release
git checkout "$TARGET"
ok "Checked out $TARGET"

# Rebuild
log "Rebuilding..."
pnpm install --frozen-lockfile 2>/dev/null || pnpm install
pnpm build

# Update version file
echo "$TARGET" > "$AGENCITY_ROOT/.openclaw-version"
git describe --tags --always > "$OPENCLAW_DIR/.pinned-version" 2>/dev/null || echo "$TARGET" > "$OPENCLAW_DIR/.pinned-version"

# Update license if changed
if [ -f "$OPENCLAW_DIR/LICENSE" ]; then
    cp "$OPENCLAW_DIR/LICENSE" "$AGENCITY_ROOT/licenses/OPENCLAW_LICENSE"
fi

echo ""
ok "Updated OpenClaw: $CURRENT → $TARGET"
echo ""
echo "  Next steps:"
echo "    1. Test: ./bin/agencity doctor"
echo "    2. If issues: ./scripts/update-openclaw.sh $CURRENT"
echo ""
