#!/bin/bash

SUPABASE_URL="https://npqjuljzpjvcqmrgpyqj.supabase.co"
SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5wcWp1bGp6cGp2Y3FtcmdweXFqIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NDExNzMwNiwiZXhwIjoyMDc5NjkzMzA2fQ.3V42Bj7BJtMioa2bHfqMe9toCXPdwSKgD9jwZLKYMP8"

echo "=== Candidates with GitHub Connected ==="
curl -s "${SUPABASE_URL}/rest/v1/candidates?github_username=not.is.null&select=id" \
  -H "apikey: ${SUPABASE_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_KEY}" \
  -H "Prefer: count=exact" \
  -I 2>/dev/null | grep -i content-range

echo ""
echo "=== Sample Candidates WITH GitHub (5) ==="
curl -s "${SUPABASE_URL}/rest/v1/candidates?github_username=not.is.null&select=id,name,email,skills,university,location,github_username,role_type,years_of_experience,major&limit=10" \
  -H "apikey: ${SUPABASE_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_KEY}"

echo ""
echo ""
echo "=== GitHub Repositories Count ==="
curl -s "${SUPABASE_URL}/rest/v1/github_repositories?select=id" \
  -H "apikey: ${SUPABASE_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_KEY}" \
  -H "Prefer: count=exact" \
  -I 2>/dev/null | grep -i content-range

echo ""
echo "=== Sample GitHub Repos (5) ==="
curl -s "${SUPABASE_URL}/rest/v1/github_repositories?select=id,candidate_id,name,full_name,description,language,stargazers_count,topics&limit=5" \
  -H "apikey: ${SUPABASE_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_KEY}"
