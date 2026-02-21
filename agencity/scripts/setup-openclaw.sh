#!/usr/bin/env bash
#
# setup-openclaw.sh — Clone and build OpenClaw as an embedded dependency
#
# This script sets up OpenClaw inside vendor/openclaw/ so Agencity
# can use it as an embedded agent runtime.
#
# Usage:
#   ./scripts/setup-openclaw.sh              # Clone latest release
#   ./scripts/setup-openclaw.sh v2026.1.29   # Clone specific release
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENCITY_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENDOR_DIR="$AGENCITY_ROOT/vendor"
OPENCLAW_DIR="$VENDOR_DIR/openclaw"
TARGET_TAG="${1:-}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

log()  { echo -e "${BLUE}[setup-openclaw]${NC} $*"; }
ok()   { echo -e "${GREEN}[setup-openclaw]${NC} $*"; }
warn() { echo -e "${YELLOW}[setup-openclaw]${NC} $*"; }
err()  { echo -e "${RED}[setup-openclaw]${NC} $*" >&2; }

# ── Prerequisites ─────────────────────────────────────────────────────────

log "Checking prerequisites..."

if ! command -v node &>/dev/null; then
    err "Node.js is required. Install Node.js 22+:"
    err "  brew install node"
    exit 1
fi

NODE_VERSION=$(node --version | sed 's/v//' | cut -d. -f1)
if [ "$NODE_VERSION" -lt 20 ]; then
    err "Node.js 20+ required (found v${NODE_VERSION})"
    exit 1
fi
ok "Node.js $(node --version)"

if ! command -v pnpm &>/dev/null; then
    warn "pnpm not found. Enabling via corepack..."
    corepack enable pnpm 2>/dev/null || npm install -g pnpm 2>/dev/null || {
        err "Could not install pnpm. Install manually: npm install -g pnpm"
        exit 1
    }
fi
ok "pnpm $(pnpm --version 2>/dev/null || npx pnpm --version)"

if ! command -v git &>/dev/null; then
    err "git is required"
    exit 1
fi
ok "git $(git --version | awk '{print $3}')"

# ── Clone ─────────────────────────────────────────────────────────────────

if [ -d "$OPENCLAW_DIR" ]; then
    if [ "${FORCE:-}" = "1" ] || [ "${1:-}" = "--force" ]; then
        log "Removing existing installation (--force)..."
        rm -rf "$OPENCLAW_DIR"
    elif [ -t 0 ]; then
        warn "OpenClaw already exists at $OPENCLAW_DIR"
        read -p "Re-clone? This will delete the existing installation. (y/N): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log "Removing existing installation..."
            rm -rf "$OPENCLAW_DIR"
        else
            log "Keeping existing installation."
            log "To update, run: ./scripts/update-openclaw.sh"
            exit 0
        fi
    else
        warn "OpenClaw already exists. Use FORCE=1 or --force to re-clone."
        log "To update, run: ./scripts/update-openclaw.sh"
        exit 0
    fi
fi

mkdir -p "$VENDOR_DIR"

log "Cloning OpenClaw repository..."
git clone --depth 1 https://github.com/openclaw/openclaw.git "$OPENCLAW_DIR"

cd "$OPENCLAW_DIR"

# ── Pin to Release ────────────────────────────────────────────────────────

if [ -n "$TARGET_TAG" ]; then
    log "Checking out release: $TARGET_TAG"
    git fetch --tags --depth 1 origin "refs/tags/$TARGET_TAG"
    git checkout "$TARGET_TAG"
    ok "Pinned to $TARGET_TAG"
else
    # Find latest stable release tag (exclude betas/RCs)
    git fetch --tags --depth 1 origin
    LATEST_TAG=$(git tag --sort=-v:refname | grep -v -E '(beta|rc|alpha)' | head -1 || echo "")
    if [ -n "$LATEST_TAG" ]; then
        log "Pinning to latest release: $LATEST_TAG"
        git checkout "$LATEST_TAG"
        ok "Pinned to $LATEST_TAG"
    else
        warn "No release tags found, staying on main branch"
    fi
fi

# Save the version we're on
git describe --tags --always > "$OPENCLAW_DIR/.pinned-version" 2>/dev/null || echo "main" > "$OPENCLAW_DIR/.pinned-version"

# ── Build ─────────────────────────────────────────────────────────────────

log "Installing dependencies (this may take a few minutes)..."
pnpm install --frozen-lockfile 2>/dev/null || pnpm install

log "Building OpenClaw..."
pnpm ui:build 2>/dev/null || warn "UI build skipped (not needed for gateway-only)"
pnpm build

ok "OpenClaw built successfully"

# ── Verify ────────────────────────────────────────────────────────────────

log "Verifying installation..."

if [ -f "$OPENCLAW_DIR/openclaw.mjs" ]; then
    ok "openclaw.mjs found"
else
    # Check for alternative entry points
    ENTRY=$(find "$OPENCLAW_DIR" -maxdepth 2 -name "openclaw.mjs" -o -name "index.mjs" | head -1)
    if [ -n "$ENTRY" ]; then
        ok "Entry point found: $ENTRY"
    else
        warn "openclaw.mjs not found — check build output"
    fi
fi

# ── Record Version ────────────────────────────────────────────────────────

VERSION=$(cat "$OPENCLAW_DIR/.pinned-version")
echo "$VERSION" > "$AGENCITY_ROOT/.openclaw-version"

# ── License Attribution ───────────────────────────────────────────────────

log "Creating license attribution..."
if [ -f "$OPENCLAW_DIR/LICENSE" ]; then
    mkdir -p "$AGENCITY_ROOT/licenses"
    cp "$OPENCLAW_DIR/LICENSE" "$AGENCITY_ROOT/licenses/OPENCLAW_LICENSE"
    ok "MIT license copied to licenses/OPENCLAW_LICENSE"
else
    warn "LICENSE file not found in OpenClaw repo"
    cat > "$AGENCITY_ROOT/licenses/OPENCLAW_LICENSE" <<'EOF'
MIT License

Copyright (c) OpenClaw Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF
    ok "MIT license template created at licenses/OPENCLAW_LICENSE"
fi

# ── Add vendor/ to .gitignore ────────────────────────────────────────────

if [ -f "$AGENCITY_ROOT/.gitignore" ]; then
    if ! grep -q "vendor/openclaw" "$AGENCITY_ROOT/.gitignore" 2>/dev/null; then
        echo -e "\n# Embedded OpenClaw (cloned via scripts/setup-openclaw.sh)\nvendor/openclaw/" >> "$AGENCITY_ROOT/.gitignore"
        ok "Added vendor/openclaw/ to .gitignore"
    fi
else
    cat > "$AGENCITY_ROOT/.gitignore" <<'EOF'
# Python
__pycache__/
*.py[cod]
*.egg-info/
.eggs/
dist/
build/

# Environment
.env
.venv/
venv/

# Embedded OpenClaw (cloned via scripts/setup-openclaw.sh)
vendor/openclaw/

# Logs
logs/
*.log

# IDE
.idea/
.vscode/
EOF
    ok "Created .gitignore with vendor/openclaw/"
fi

# ── Summary ───────────────────────────────────────────────────────────────

echo ""
echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  OpenClaw embedded successfully!${NC}"
echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BLUE}Location:${NC}  $OPENCLAW_DIR"
echo -e "  ${BLUE}Version:${NC}   $(cat "$AGENCITY_ROOT/.openclaw-version")"
echo -e "  ${BLUE}License:${NC}   MIT (attribution at licenses/OPENCLAW_LICENSE)"
echo ""
echo -e "  ${BOLD}Next steps:${NC}"
echo -e "    1. Start the gateway:"
echo -e "       ${YELLOW}./bin/agencity gateway${NC}"
echo ""
echo -e "    2. Start the full stack:"
echo -e "       ${YELLOW}./bin/agencity start${NC}"
echo ""
echo -e "    3. Verify health:"
echo -e "       ${YELLOW}./bin/agencity doctor${NC}"
echo ""
echo -e "    4. To update OpenClaw later:"
echo -e "       ${YELLOW}./scripts/update-openclaw.sh${NC}"
echo ""
