#!/bin/bash

SUPABASE_URL="https://npqjuljzpjvcqmrgpyqj.supabase.co"
SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5wcWp1bGp6cGp2Y3FtcmdweXFqIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NDExNzMwNiwiZXhwIjoyMDc5NjkzMzA2fQ.3V42Bj7BJtMioa2bHfqMe9toCXPdwSKgD9jwZLKYMP8"

echo "=== Listing Tables ==="
curl -s "${SUPABASE_URL}/rest/v1/" \
  -H "apikey: ${SUPABASE_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_KEY}"
