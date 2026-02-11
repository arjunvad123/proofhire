#!/bin/bash

SUPABASE_URL="https://npqjuljzpjvcqmrgpyqj.supabase.co"
SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5wcWp1bGp6cGp2Y3FtcmdweXFqIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NDExNzMwNiwiZXhwIjoyMDc5NjkzMzA2fQ.3V42Bj7BJtMioa2bHfqMe9toCXPdwSKgD9jwZLKYMP8"

echo "=== GitHub Repos with Stars (sorted by stars) ==="
curl -s "${SUPABASE_URL}/rest/v1/github_repositories?stargazers_count=gt.0&select=id,candidate_id,name,full_name,description,language,stargazers_count,topics&order=stargazers_count.desc&limit=20" \
  -H "apikey: ${SUPABASE_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_KEY}"

echo ""
echo ""
echo "=== Top University Candidates ==="
curl -s "${SUPABASE_URL}/rest/v1/candidates?or=(university.ilike.*stanford*,university.ilike.*mit*,university.ilike.*berkeley*,university.ilike.*carnegie*,university.ilike.*harvard*,university.ilike.*waterloo*,university.ilike.*columbia*)&github_username=not.is.null&select=id,name,university,github_username,skills,role_type&limit=15" \
  -H "apikey: ${SUPABASE_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_KEY}"

echo ""
echo ""
echo "=== AI/ML Focused Candidates with GitHub ==="
curl -s "${SUPABASE_URL}/rest/v1/candidates?github_username=not.is.null&or=(skills.ilike.*llm*,skills.ilike.*langchain*,skills.ilike.*openai*,skills.ilike.*machine learning*,skills.ilike.*pytorch*,skills.ilike.*tensorflow*)&select=id,name,university,github_username,skills,role_type&limit=15" \
  -H "apikey: ${SUPABASE_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_KEY}"

echo ""
echo ""
echo "=== GitHub Verified Candidates (Passed) ==="
curl -s "${SUPABASE_URL}/rest/v1/latest_github_verifications?verification_status=eq.passed&select=candidate_id,candidate_name,github_username,email,total_criteria_passed,meaningful_projects_passed,activity_window_passed&order=total_criteria_passed.desc&limit=15" \
  -H "apikey: ${SUPABASE_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_KEY}"
