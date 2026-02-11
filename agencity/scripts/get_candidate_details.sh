#!/bin/bash

SUPABASE_URL="https://npqjuljzpjvcqmrgpyqj.supabase.co"
SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5wcWp1bGp6cGp2Y3FtcmdweXFqIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NDExNzMwNiwiZXhwIjoyMDc5NjkzMzA2fQ.3V42Bj7BJtMioa2bHfqMe9toCXPdwSKgD9jwZLKYMP8"

# Top candidates IDs found:
# Aaron Ye: 31621120-aee2-42a7-8ec9-decb7eea6bab
# Owen Hochwald: 6f223fd8-837a-4398-9476-ca152da77381
# Michelle Weon: 9a68cc3a-6db7-4830-9458-e3df8c5601cf
# Gbemileke Onilude: f6e1f6e3-ad53-49c2-842b-a894031381e8
# Rohan: 03245b49-d349-4373-84c2-2dd338fc3bb0
# Vibhor Sharma: 65beb594-2861-47dc-881f-50e5457de029

echo "=== Aaron Ye - Full Profile ==="
curl -s "${SUPABASE_URL}/rest/v1/candidates?id=eq.31621120-aee2-42a7-8ec9-decb7eea6bab&select=*" \
  -H "apikey: ${SUPABASE_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_KEY}"

echo ""
echo ""
echo "=== Aaron Ye - GitHub Repos ==="
curl -s "${SUPABASE_URL}/rest/v1/github_repositories?candidate_id=eq.31621120-aee2-42a7-8ec9-decb7eea6bab&select=name,full_name,description,language,stargazers_count,topics&order=stargazers_count.desc&limit=10" \
  -H "apikey: ${SUPABASE_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_KEY}"

echo ""
echo ""
echo "=== Owen Hochwald - Full Profile ==="
curl -s "${SUPABASE_URL}/rest/v1/candidates?id=eq.6f223fd8-837a-4398-9476-ca152da77381&select=*" \
  -H "apikey: ${SUPABASE_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_KEY}"

echo ""
echo ""
echo "=== Owen Hochwald - GitHub Repos ==="
curl -s "${SUPABASE_URL}/rest/v1/github_repositories?candidate_id=eq.6f223fd8-837a-4398-9476-ca152da77381&select=name,full_name,description,language,stargazers_count,topics&order=stargazers_count.desc&limit=10" \
  -H "apikey: ${SUPABASE_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_KEY}"

echo ""
echo ""
echo "=== Rohan - Full Profile (LLM/RAG expert) ==="
curl -s "${SUPABASE_URL}/rest/v1/candidates?id=eq.03245b49-d349-4373-84c2-2dd338fc3bb0&select=*" \
  -H "apikey: ${SUPABASE_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_KEY}"

echo ""
echo ""
echo "=== Rohan - GitHub Repos ==="
curl -s "${SUPABASE_URL}/rest/v1/github_repositories?candidate_id=eq.03245b49-d349-4373-84c2-2dd338fc3bb0&select=name,full_name,description,language,stargazers_count,topics&order=stargazers_count.desc&limit=10" \
  -H "apikey: ${SUPABASE_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_KEY}"

echo ""
echo ""
echo "=== Michelle Weon (Harvard) - Full Profile ==="
curl -s "${SUPABASE_URL}/rest/v1/candidates?id=eq.9a68cc3a-6db7-4830-9458-e3df8c5601cf&select=*" \
  -H "apikey: ${SUPABASE_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_KEY}"

echo ""
echo ""
echo "=== Gbemileke Onilude (CMU - AI/ML) - Full Profile ==="
curl -s "${SUPABASE_URL}/rest/v1/candidates?id=eq.f6e1f6e3-ad53-49c2-842b-a894031381e8&select=*" \
  -H "apikey: ${SUPABASE_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_KEY}"
