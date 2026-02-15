# Curation Cache Generation Guide

## Overview
The cache generation script runs the full curation pipeline (including PDL enrichment and Claude AI) for all roles, but with **intelligent cost optimization** to prevent redundant API calls.

## Cost Optimization Strategy

### 1. PDL Enrichment (30-Day Cache)
- **Enriches**: Top 5 candidates per role
- **Cost**: $0.10 per enrichment
- **Cache Duration**: 30 days
- **Key Optimization**: If a candidate was enriched in the last 30 days, the cached data is reused across ALL roles

**Example:**
```
Role 1 (Software Engineer):
  Top 5: Alice, Bob, Charlie, David, Eve
  PDL calls: 5 (all new) = $0.50

Role 2 (Senior Engineer):
  Top 5: Alice, Bob, Frank, Grace, Charlie
  PDL calls: 2 (Frank, Grace are new, others cached) = $0.20

Role 3 (Tech Lead):
  Top 5: Alice, Charlie, Frank, Henry, Grace
  PDL calls: 1 (Henry is new, others cached) = $0.10

Total: $0.80 (instead of $1.50 without cache)
```

### 2. Claude AI Reasoning
- **Analyzes**: Top 5 candidates per role
- **Cost**: ~$0.006 per role (4 agents × 5 candidates × $0.0003)
- **No Cache**: Runs fresh for each role (intentional - role-specific analysis)

### 3. Perplexity Research
- **Status**: DISABLED during cache generation
- **Why**: Saves ~$0.025 per role (5 × $0.005)
- **When Enabled**: Only on live curation (user-initiated)

## Expected Costs

### Single Role
- First time (no cache): ~$0.50-0.53
- With 50% cache hit: ~$0.25-0.30
- With 80% cache hit: ~$0.10-0.15

### Multiple Roles (10 roles)
```
Scenario 1: High Overlap (typical)
- First role: $0.50 (5 new enrichments)
- Next 9 roles: ~$1.50 (avg 1.5 new enrichments per role)
- Total: ~$2.00 for 10 roles

Scenario 2: Low Overlap
- Each role needs 3-4 new enrichments
- Total: ~$3.50 for 10 roles

Scenario 3: Very High Overlap (best case)
- Most candidates repeat across roles
- Total: ~$1.50 for 10 roles
```

### Monthly Budget
```
Initial cache generation: $2-3 (one-time)
Weekly refresh (4x/month): $0.50-1.00 (only new candidates)
Monthly total: ~$4-7
```

## Running the Cache Generator

### Basic Usage

```bash
cd /Users/aidannguyen/Downloads/proofhire/proofhire/agencity

# Generate cache for ALL companies and roles
python scripts/populate_curation_cache.py

# Force refresh all caches (ignore existing)
python scripts/populate_curation_cache.py --force

# Generate for specific company
python scripts/populate_curation_cache.py --company <company_id>

# Generate for specific role
python scripts/populate_curation_cache.py --role <company_id> <role_id>
```

### What Happens During Generation

```
For each role:
1. ✓ Fetch all network candidates
2. ✓ Calculate initial fit scores (rule-based)
3. ✓ Rank candidates
4. ✓ PDL enrich top 5 (30-day cache check first!)
5. ✓ Claude AI analyzes enriched candidates (4-agent swarm)
6. ✓ Re-rank with weighted scores (70% AI + 30% rules)
7. ✓ Build rich context
8. ✗ Skip Perplexity research (cost savings)
9. ✓ Store in curation_cache table
10. ✓ Update role status to "cached"
```

## Monitoring Costs

### Check PDL Enrichment Usage

```sql
-- Enrichments in last 7 days
SELECT
  DATE(created_at) as date,
  COUNT(*) as enrichments,
  COUNT(*) * 0.10 as cost_usd
FROM person_enrichments
WHERE enrichment_source = 'pdl'
  AND created_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Cache hit rate by checking updates vs inserts
SELECT
  DATE(updated_at) as date,
  COUNT(*) as total_enrichments,
  COUNT(CASE WHEN created_at = updated_at THEN 1 END) as new_enrichments,
  COUNT(CASE WHEN created_at != updated_at THEN 1 END) as cache_hits,
  ROUND(
    100.0 * COUNT(CASE WHEN created_at != updated_at THEN 1 END) / COUNT(*),
    1
  ) as cache_hit_rate_percent
FROM person_enrichments
WHERE updated_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(updated_at)
ORDER BY date DESC;
```

### Check Cache Status

```bash
# Via API
curl http://localhost:8001/api/curation/cache/status/<company_id>

# Via Python
python -c "
import asyncio
from app.core.database import get_supabase_client

supabase = get_supabase_client()
result = supabase.table('curation_cache').select('*').execute()
print(f'Cached roles: {len(result.data)}')
for cache in result.data:
    print(f\"  - {cache['role_id']}: {len(cache['shortlist'])} candidates\")
"
```

## Safety Features

### 1. No Duplicate Enrichments
- Before calling PDL, checks `person_enrichments` table
- If enrichment exists and is <30 days old, reuses it
- Only calls PDL API for truly new data

### 2. Graceful Failures
- If PDL fails for a candidate, skips and continues
- If Claude fails, falls back to rule-based scoring
- Cache generation never crashes entire process

### 3. Rate Limiting
- Processes roles sequentially (not parallel)
- Respects API rate limits
- Can be interrupted with Ctrl+C

## Best Practices

### When to Run Cache Generation

✅ **DO run after:**
- Importing new candidates
- Creating new roles
- Weekly (to refresh caches)

❌ **DON'T run:**
- Multiple times per day (wastes money)
- Before importing candidates (no one to enrich)
- With `--force` unless necessary (ignores cache)

### Recommended Schedule

```bash
# Initial setup
python scripts/populate_curation_cache.py

# Weekly refresh (cron job)
0 2 * * 0 cd /path/to/agencity && python scripts/populate_curation_cache.py

# After bulk import
python scripts/populate_curation_cache.py --company <company_id>
```

## Troubleshooting

### Issue: High Costs

**Check:**
```sql
-- Find candidates being enriched multiple times
SELECT
  person_id,
  COUNT(*) as enrichment_count,
  MAX(updated_at) as last_enriched,
  COUNT(*) * 0.10 as total_cost
FROM person_enrichments
WHERE enrichment_source = 'pdl'
GROUP BY person_id
HAVING COUNT(*) > 5  -- Should not happen!
ORDER BY enrichment_count DESC;
```

**Likely Cause:**
- Cache not working (check `updated_at` field)
- Running with `--force` flag too often
- Bug in cache checking logic

### Issue: No Enrichments Happening

**Check:**
1. PDL API key configured: `echo $PDL_API_KEY`
2. Candidates have LinkedIn URLs:
   ```sql
   SELECT COUNT(*) FROM people WHERE linkedin_url IS NOT NULL;
   ```
3. Backend logs for errors

### Issue: Slow Cache Generation

**Expected Times:**
- 30-40 seconds per role (with enrichment)
- 10-15 seconds per role (all cached)
- 5+ minutes for 10 roles

**Speed it up:**
- Don't run with `--force` (uses cache)
- Generate during off-hours
- Process companies sequentially, not all at once

## Understanding the Output

```
🎯 CURATION CACHE GENERATOR
=====================================

📊 Cost Optimization Strategy:
  • PDL Enrichment: Top 5 candidates per role
  • 30-day cache: Reuses enriched data across roles
  • Claude AI: Analyzes top 5 (~$0.006/role)
  • Perplexity: DISABLED during cache generation

💰 Expected Costs:
  • First role: ~$0.50 (5 new enrichments)
  • Subsequent roles: ~$0.10-0.30 (cache hits)
  • 10 roles: ~$2-3 total (with overlap)

=====================================

Processing role: Software Engineer
  🔍 Enriching top 5 candidates via PDL...
  ✓ Alice (cached, 5d old)           # $0.00 - using cache
  🔍 Bob via PDL...                   # $0.10 - new enrichment
  ✓ Charlie (cached, 12d old)        # $0.00 - using cache
  🔍 David via PDL...                 # $0.10 - new enrichment
  ✓ Eve (cached, 2d old)             # $0.00 - using cache
  ✅ Enriched 2/5 candidates          # Only charged for 2!
  💰 Total enrichment cost: $0.20
  🧠 Claude reasoning on 5 candidates
  📊 Enriched: 5/15 candidates
  ✓ Cache generated for Software Engineer

Total Cost: $0.206 (PDL: $0.20, Claude: $0.006)
```

## Advanced: Custom Cache Strategy

If you want to customize the enrichment strategy, modify:

**File:** `agencity/app/services/curation_engine.py`

```python
# Line 102: Change number of candidates to enrich
top_5 = ranked_candidates[:5]  # Change 5 to any number

# Line 779-780: Change cache duration
age_days = (datetime.now(updated_at.tzinfo) - updated_at).days
if age_days < 30:  # Change 30 to desired days
    # Use cache
```

⚠️ **Warning**: Increasing from top 5 increases costs proportionally:
- Top 10: ~2x cost ($0.50 → $1.00 per role)
- Top 20: ~4x cost ($0.50 → $2.00 per role)

## Summary

The cache generation script is **designed to be cost-efficient**:

✅ PDL enrichment respects 30-day cache
✅ Shared enrichments across roles
✅ Claude AI only on top 5 (~$0.006)
✅ Perplexity disabled (saves ~$0.025)
✅ Expected: $2-3 for 10 roles

**You can safely run it without worrying about excessive PDL costs!** The 30-day cache ensures candidates aren't re-enriched across multiple roles.
