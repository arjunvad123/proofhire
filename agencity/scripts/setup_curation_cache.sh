#!/bin/bash

# Setup script for curation cache system
# Run this after deploying the code to initialize the cache

set -e  # Exit on error

echo "================================================"
echo "Curation Cache Setup Script"
echo "================================================"
echo ""

# Check if running from correct directory
if [ ! -f "app/workers/curation_cache_worker.py" ]; then
    echo "❌ Error: Must run from agencity/ directory"
    echo "   cd agencity && bash scripts/setup_curation_cache.sh"
    exit 1
fi

echo "Step 1: Checking Python environment..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 not found"
    exit 1
fi
echo "✓ Python found: $(python3 --version)"
echo ""

echo "Step 2: Verifying database migration..."
echo "   Please ensure migration 004_curation_cache.sql has been applied"
echo "   Run: supabase migration up"
echo ""
read -p "Has the migration been applied? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Please apply migration first, then re-run this script"
    exit 1
fi
echo "✓ Migration confirmed"
echo ""

echo "Step 3: Testing database connection..."
# This will fail if SUPABASE_URL or SUPABASE_KEY are not set
python3 -c "
from app.core.database import get_supabase_client
try:
    client = get_supabase_client()
    result = client.table('companies').select('id').limit(1).execute()
    print('✓ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
" || exit 1
echo ""

echo "Step 4: Generating initial cache..."
echo "   This will run curation for all active roles"
echo "   Estimated time: ~2 minutes per role"
echo ""
read -p "Proceed with cache generation? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "⚠ Skipping cache generation"
    echo "   Run manually: python3 app/workers/curation_cache_worker.py generate_all"
else
    echo "Running cache generation..."
    python3 app/workers/curation_cache_worker.py generate_all
    echo "✓ Cache generation complete"
fi
echo ""

echo "Step 5: Setting up cron job (optional)..."
echo "   Recommended: Run every 6 hours to keep cache fresh"
echo ""
SCRIPT_DIR=$(pwd)
CRON_LINE="0 */6 * * * cd $SCRIPT_DIR && python3 app/workers/curation_cache_worker.py generate_all >> /var/log/curation_cache.log 2>&1"
CLEANUP_LINE="0 2 * * * cd $SCRIPT_DIR && python3 app/workers/curation_cache_worker.py cleanup >> /var/log/curation_cache.log 2>&1"

echo "Add these lines to crontab:"
echo ""
echo "# Generate cache every 6 hours"
echo "$CRON_LINE"
echo ""
echo "# Clean up expired cache daily at 2am"
echo "$CLEANUP_LINE"
echo ""

read -p "Add to crontab now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Add to crontab
    (crontab -l 2>/dev/null; echo ""; echo "# Agencity Curation Cache"; echo "$CRON_LINE"; echo "$CLEANUP_LINE") | crontab -
    echo "✓ Cron jobs added"
    echo "   View with: crontab -l"
else
    echo "⚠ Skipping cron setup"
    echo "   Add manually with: crontab -e"
fi
echo ""

echo "================================================"
echo "✓ Setup Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Deploy backend (API endpoints are now available)"
echo "2. Deploy frontend (will use cache automatically)"
echo "3. Monitor logs: tail -f /var/log/curation_cache.log"
echo "4. Check cache status: GET /api/curation/cache/status/{company_id}"
echo ""
echo "Manual commands:"
echo "  Generate cache: python3 app/workers/curation_cache_worker.py generate_all"
echo "  Force refresh:  python3 app/workers/curation_cache_worker.py generate_all --force"
echo "  Cleanup:        python3 app/workers/curation_cache_worker.py cleanup"
echo ""
