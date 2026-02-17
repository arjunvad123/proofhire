# Regenerate AI Summary API

## Endpoint
`POST /v1/curation/candidate/{person_id}/regenerate-summary`

## Purpose
Regenerate the AI summary for a candidate **without re-enriching** their entire profile. Uses existing candidate data and Claude AI to generate a fresh narrative summary.

## Use Case
You have a candidate like **Nikhil Hooda** (Software Engineer at Shopify, Canada, has SQL skills) whose summary is currently showing the rules-based template. You want a more natural, AI-generated narrative without paying for PDL enrichment again.

## Request

### Query Parameters
- `person_id` (path): The candidate's UUID
- `role_id` (query): The role UUID you're evaluating them for

### Example
```bash
curl -X POST "http://localhost:8000/v1/curation/candidate/abc-123/regenerate-summary?role_id=role-456" \
  -H "Content-Type: application/json"
```

## Response

```json
{
  "status": "success",
  "person_id": "abc-123",
  "full_name": "Nikhil Hooda",
  "ai_summary": {
    "overall_assessment": "Nikhil is a strong backend engineer with proven experience at scale. His Shopify background demonstrates he can handle high-traffic systems, and his SQL expertise aligns well with our data-intensive role. Worth exploring his interest in startups.",
    "why_consider": [
      "5+ years at a top-tier company (Shopify)",
      "Strong SQL and database optimization skills",
      "Experience with distributed systems at scale"
    ],
    "concerns": [
      "May be comfortable at Shopify - need to gauge interest in startup environment",
      "Unclear if they have frontend experience (if required)"
    ],
    "unknowns": [
      "Interest in this opportunity",
      "Salary expectations",
      "Availability timeline"
    ],
    "skill_reasoning": "Strong match on SQL (explicitly listed). Backend experience at Shopify suggests exposure to Ruby, Go, or similar. Score: 85/100",
    "trajectory_reasoning": "5 years at Shopify shows stability and growth potential. Currently mid-level, ready for senior or lead role. Score: 80/100",
    "fit_reasoning": "Big company background may need cultural adjustment to startup pace. Canada location noted - confirm remote policy. Score: 70/100",
    "timing_reasoning": "No immediate signals of job searching, but engineers at 5-year mark often explore options. Worth a warm reach-out. Score: 65/100"
  },
  "message": "AI summary regenerated successfully"
}
```

## Database Storage (Optional)

The endpoint will attempt to store the AI summary in the `people` table under an `ai_summary` JSONB column. If the column doesn't exist yet, you can add it:

```sql
-- Add ai_summary column to people table (optional)
ALTER TABLE people ADD COLUMN IF NOT EXISTS ai_summary JSONB;

-- Add index for faster queries
CREATE INDEX IF NOT EXISTS idx_people_ai_summary ON people USING gin(ai_summary);
```

If the column doesn't exist, the endpoint will still return the summary - it just won't be stored for future use.

## Frontend Integration

### Option 1: Replace Rules-Based Summary
Update `CandidateDetailedAnalysis.tsx` to fetch and display the AI summary instead of the template:

```typescript
// Add to component state
const [aiSummary, setAiSummary] = useState<AISummary | null>(null);

// Fetch AI summary
const fetchAISummary = async () => {
  const response = await fetch(
    `/v1/curation/candidate/${candidate.person_id}/regenerate-summary?role_id=${roleId}`,
    { method: 'POST' }
  );
  const data = await response.json();
  setAiSummary(data.ai_summary);
};

// Display
{aiSummary ? (
  <div className="ai-summary">
    <p className="font-medium">{aiSummary.overall_assessment}</p>
    <div className="mt-2">
      <h4 className="text-sm font-semibold">Why Consider:</h4>
      <ul>
        {aiSummary.why_consider.map((point, i) => (
          <li key={i}>✓ {point}</li>
        ))}
      </ul>
    </div>
  </div>
) : (
  // Fallback to rules-based template
  generateAISummary(candidate)
)}
```

### Option 2: Add "Regenerate Summary" Button
Add a button to manually trigger regeneration:

```typescript
<button
  onClick={async () => {
    setLoading(true);
    await fetchAISummary();
    setLoading(false);
  }}
  className="btn-secondary"
>
  ✨ Generate AI Summary
</button>
```

## Benefits
- ✅ No re-enrichment cost (no PDL API calls)
- ✅ Uses existing candidate data
- ✅ AI-generated natural language summary
- ✅ Consistent tone across all candidates
- ✅ Can be regenerated anytime with updated prompts

## Performance
- ~2-3 seconds per candidate (Claude API latency)
- Can batch if needed (add `regenerate-summaries` endpoint for multiple candidates)
