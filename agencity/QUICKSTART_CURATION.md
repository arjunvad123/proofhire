# Quick Start: Candidate Curation

Get the curation system running in 5 minutes.

## Prerequisites

- Python 3.11+
- Supabase database with existing schema (companies, roles, people tables)
- At least one company with people in their network

## Step 1: Install Dependencies

```bash
pip install supabase-py pydantic python-dotenv fastapi uvicorn
```

## Step 2: Set Environment Variables

Your `.env` should have:
```bash
SUPABASE_URL=https://npqjuljzpjvcqmrgpyqj.supabase.co  # Your Supabase URL
SUPABASE_KEY=your-service-role-key-here                 # Your service role key
```

## Step 3: Test the System

```bash
# From agencity directory
python scripts/test_curation.py
```

This will list your companies. You should see something like:

```
════════════════════════════════════════════════════════════════════════════════
AVAILABLE COMPANIES
════════════════════════════════════════════════════════════════════════════════

  Confido
    ID: 100b5ac1-1912-4970-a378-04d0169fd597
    People: 305
```

## Step 4: List Roles

```bash
python scripts/test_curation.py 100b5ac1-1912-4970-a378-04d0169fd597
```

You'll see roles for that company:

```
════════════════════════════════════════════════════════════════════════════════
ROLES FOR COMPANY
════════════════════════════════════════════════════════════════════════════════

  Software Engineer
    ID: role-uuid-123
    Skills: Python, React, TypeScript, FastAPI, PostgreSQL
```

## Step 5: Run Curation!

```bash
python scripts/test_curation.py 100b5ac1-1912-4970-a378-04d0169fd597 role-uuid-123
```

You'll see:

```
════════════════════════════════════════════════════════════════════════════════
🎯 Starting curation for role role-uuid-123
════════════════════════════════════════════════════════════════════════════════

📋 Role: Software Engineer
🏢 Company: Confido
📊 Searching 305 network connections
📈 Top candidate score: 87.3
🎲 Average confidence: 0.67
✅ Curated shortlist of 10 candidates

════════════════════════════════════════════════════════════════════════════════
SHORTLIST (10 candidates)
════════════════════════════════════════════════════════════════════════════════

#1 - Maya Patel
────────────────────────────────────────────────────────────────────────────────
  Match Score: 87.3/100 (confidence: 0.85)
  Headline: CS @ UCSD | AI/ML Enthusiast
  Current: Student

  WHY CONSIDER:
    Skills Match (HIGH)
      ✓ Python
      ✓ React
      ~ Machine Learning

    Education (MEDIUM)
      ✓ BS in Computer Science from UC San Diego

  UNKNOWNS:
    • Specific technical skills
    • Detailed work experience
    • Interest in this specific opportunity

  WARM PATH: Connected on LinkedIn
  Data Completeness: 60%

#2 - John Smith
...
```

## Step 6: Use in API

Start the FastAPI server:

```bash
uvicorn app.main:app --reload --port 8001
```

Call the curation endpoint:

```bash
curl -X POST http://localhost:8001/api/v1/curation/curate \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "100b5ac1-1912-4970-a378-04d0169fd597",
    "role_id": "role-uuid-123",
    "limit": 10
  }'
```

## Expected Results

For a network of 305 connections and a Software Engineer role:

- **Total searched:** 305 people
- **Shortlist size:** 10-15 candidates
- **Average match score:** 65-75
- **Time to run:** 5-10 seconds
- **Enrichment cost:** $0-1 (only enriches if needed)

## What You Should See

### Good Match (Score 80+)
- Strong skills overlap with role requirements
- Relevant experience or education
- Active GitHub profile or projects
- Clear warm intro path

### Medium Match (Score 60-80)
- Some skills match
- Related background (e.g., similar industry)
- Less complete profile data
- May need enrichment

### Low Match (Score <60)
- Few matching skills
- Different field/industry
- Very incomplete data
- Probably won't appear in top 15

## Troubleshooting

### "ModuleNotFoundError: No module named 'app'"

Run from the `agencity` directory:
```bash
cd agencity
python scripts/test_curation.py
```

### "SUPABASE_URL and SUPABASE_KEY must be set"

Create `.env` file in `agencity` directory:
```bash
cp .env.example .env
# Then edit .env with your credentials
```

### "No candidates found"

Check your database has people:
```bash
python
>>> from app.core.database import get_supabase_client
>>> supabase = get_supabase_client()
>>> result = supabase.table('people').select('id', count='exact').execute()
>>> print(f"Total people: {result.count}")
```

### All scores are low

Check your role has `required_skills` defined:
```sql
SELECT * FROM roles WHERE id = 'your-role-id';
```

If `required_skills` is empty or null, add some:
```sql
UPDATE roles
SET required_skills = ARRAY['Python', 'React', 'TypeScript']
WHERE id = 'your-role-id';
```

## Next Steps

1. ✅ **Test with existing data** (you just did this!)
2. 📝 **Review top candidates** - Are they good matches?
3. 🎯 **Adjust role requirements** if needed
4. 🚀 **Integrate into your app** via API
5. 💰 **Add enrichment** (optional - Week 2)

## Understanding the Output

### Match Score (0-100)
- **90-100:** Excellent match, definitely interview
- **75-90:** Strong match, very likely good fit
- **60-75:** Good match, worth considering
- **<60:** Weak match, probably not right fit

### Confidence (0-1)
- **>0.7:** High confidence - we have good data
- **0.4-0.7:** Medium confidence - some data missing
- **<0.4:** Low confidence - needs enrichment

### Data Completeness (0-100%)
- **>70%:** Complete profile (skills, experience, education)
- **30-70%:** Partial profile (title + some data)
- **<30%:** Basic profile (just name + title)

## Success Criteria

You know it's working if:
- ✅ Returns 10-15 candidates in <10 seconds
- ✅ Top candidates have match scores >70
- ✅ "Why Consider" sections make sense
- ✅ Warm path shows LinkedIn connection
- ✅ Unknowns accurately reflect missing data

## Ready for Production?

When you're ready to use this in production:

1. Add authentication to API endpoints
2. Set up enrichment API (People Data Labs)
3. Add GitHub fetcher for technical roles
4. Build frontend to display shortlist
5. Add feedback loop (founder marks "yes/no")

See `docs/CURATION_SYSTEM.md` for full documentation.
