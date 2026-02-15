#!/bin/bash
# Quick test script to verify curation cache is working

echo "=================================="
echo "🧪 CURATION CACHE TEST"
echo "=================================="
echo ""

# Check if .env exists
if [ ! -f "../.env" ] && [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found"
    echo "Please create .env with SUPABASE_URL and SUPABASE_KEY"
    exit 1
fi

# Load environment variables
if [ -f "../.env" ]; then
    export $(cat ../.env | grep -v '^#' | xargs)
elif [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

echo "1️⃣  Checking database tables..."
python3 -c "
from app.core.database import get_supabase_client
sb = get_supabase_client()

# Check tables exist
tables = ['people', 'roles', 'curation_cache']
for table in tables:
    try:
        result = sb.table(table).select('id', count='exact').limit(1).execute()
        print(f'  ✓ {table} table exists (count: {result.count})')
    except Exception as e:
        print(f'  ✗ {table} table error: {e}')
" || exit 1

echo ""
echo "2️⃣  Checking for companies and roles..."
python3 -c "
from app.core.database import get_supabase_client
import json

sb = get_supabase_client()

# Get companies
companies = sb.table('companies').select('id, name').execute()
if not companies.data:
    print('  ⚠️  No companies found - need to run onboarding first')
    exit(1)

print(f'  ✓ Found {len(companies.data)} companies')

# Get roles
for company in companies.data[:1]:  # Check first company
    roles = sb.table('roles').select('id, title, curation_status').eq('company_id', company['id']).execute()
    print(f'  ✓ Company: {company[\"name\"]}')
    print(f'    - Roles: {len(roles.data)}')

    if roles.data:
        print(f'    - Sample role: {roles.data[0][\"title\"]} (status: {roles.data[0].get(\"curation_status\", \"N/A\")})')

    # Check people
    people = sb.table('people').select('id', count='exact').eq('company_id', company['id']).execute()
    print(f'    - Candidates: {people.count}')

    # Store for next step
    if roles.data:
        print(f'COMPANY_ID={company[\"id\"]}')
        print(f'ROLE_ID={roles.data[0][\"id\"]}')
" > /tmp/cache_test_ids.txt || exit 1

echo ""

# Load IDs
if [ -f /tmp/cache_test_ids.txt ]; then
    export COMPANY_ID=$(grep COMPANY_ID /tmp/cache_test_ids.txt | cut -d= -f2)
    export ROLE_ID=$(grep ROLE_ID /tmp/cache_test_ids.txt | cut -d= -f2)

    if [ -n "$COMPANY_ID" ] && [ -n "$ROLE_ID" ]; then
        echo "3️⃣  Checking cache status..."
        python3 -c "
from app.core.database import get_supabase_client
import os

sb = get_supabase_client()
company_id = os.environ.get('COMPANY_ID')
role_id = os.environ.get('ROLE_ID')

# Check if cache exists
cache = sb.table('curation_cache').select('*').eq('company_id', company_id).eq('role_id', role_id).execute()

if cache.data:
    c = cache.data[0]
    import json
    shortlist = json.loads(c['shortlist']) if isinstance(c['shortlist'], str) else c['shortlist']
    print(f'  ✓ Cache EXISTS')
    print(f'    - Cached candidates: {len(shortlist) if isinstance(shortlist, list) else \"N/A\"}')
    print(f'    - Total searched: {c[\"total_searched\"]}')
    print(f'    - Avg score: {c[\"avg_match_score\"]}')
    print(f'    - Generated: {c[\"generated_at\"]}')
    print(f'    - Expires: {c[\"expires_at\"]}')
else:
    print(f'  ⚠️  Cache DOES NOT EXIST for role {role_id}')
    print(f'  💡 Run: python scripts/populate_curation_cache.py')
"
        echo ""
        echo "=================================="
        echo "✅ Test complete!"
        echo ""
        echo "Next steps:"
        echo "  1. If cache doesn't exist, run:"
        echo "     cd agencity"
        echo "     python scripts/populate_curation_cache.py"
        echo ""
        echo "  2. Then test the frontend:"
        echo "     Open http://localhost:3000/dashboard/candidates"
        echo "     Select a role and check browser console"
        echo "=================================="
    else
        echo "❌ Could not extract company/role IDs"
    fi
else
    echo "⚠️  No companies or roles found"
fi
