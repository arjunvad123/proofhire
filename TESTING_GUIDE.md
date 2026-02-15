# Enhanced Candidate Enrichment UI - Testing Guide

## Quick Start Testing

### Prerequisites
1. Backend running on port 8001
2. Frontend running on port 3000
3. At least one company with roles configured
4. Network candidates imported

---

## Test Scenarios

### Scenario 1: View Enriched Candidates

**Steps:**
1. Navigate to `/dashboard/candidates`
2. Select a role from the dropdown
3. Wait for curation to complete (~30s first time, <1s from cache)

**Expected Results:**
✅ Stats card shows:
- Total searched count
- Enriched count with percentage
- AI-Analyzed count with percentage (if Claude ran)
- Shortlist count
- Average score

✅ Top 5 candidates show badges:
- Blue "PDL" badge if enriched with PDL
- Purple "AI" badge if Perplexity research ran

✅ Match score column shows:
- Progress bar with score
- "AI: X% (Y% conf)" if Claude analyzed
- Falls back to confidence otherwise

---

### Scenario 2: Expand Candidate Analysis

**Steps:**
1. In Match mode, find a candidate with enrichment badges
2. Click "Show full analysis"

**Expected Results:**
✅ Three new sections appear at top:

**1. Data Sources Section:**
- Shows enrichment badges (PDL, Perplexity)
- Lists which fields PDL enriched (skills, experience, education)
- Shows data quality percentage
- Displays "Last enriched: Recently"

**2. Claude AI Analysis Section:**
- Shows gradient purple/indigo card
- Overall score out of 100
- Confidence percentage with color coding:
  - Green (>80%)
  - Amber (60-80%)
  - Orange (<60%)
- Four agent breakdowns:
  - 🎯 Skills Match (40%)
  - 📈 Career Growth (30%)
  - 🤝 Culture Fit (20%)
  - ⏰ Timing (10%)
- Each agent shows:
  - Score percentage
  - Progress bar (green/amber/red)
  - Reasoning text (truncated)
- Footer shows weighted calculation

**3. Research Insights Section:**
- Shows gradient purple/pink card
- Grouped by type with icons:
  - 💻 GitHub Projects & Code
  - 📚 Publications & Talks
  - 🏆 Notable Achievements
  - 🔬 Technical Skills
- Each group shows item count
- Bullet points with descriptions
- Clickable links if URLs available

✅ Existing sections still work:
- Why Consider This Candidate
- Skills Analysis (matched vs missing)
- Open Questions
- Interview Questions
- Profile Completeness
- Standout Signal

---

### Scenario 3: Non-Enriched Candidates

**Steps:**
1. View candidates beyond top 5 (positions 6-15)
2. These should NOT have enrichment

**Expected Results:**
✅ No enrichment badges shown
✅ No "AI: X%" in match score column
✅ Expanded analysis shows:
- Data Sources section MISSING
- Claude AI Analysis section MISSING
- Research Insights section MISSING
✅ Existing sections still display normally

**Purpose:** Verify graceful degradation

---

### Scenario 4: Stats Card Variants

**Test A: No AI Analysis**
- If Claude didn't run, stats card shows 4 columns
- AI-Analyzed stat is hidden

**Test B: With AI Analysis**
- If Claude ran on some candidates, shows 5 columns
- AI-Analyzed shows count and percentage

---

### Scenario 5: Mobile Responsiveness

**Steps:**
1. Resize browser to mobile width (375px)
2. View enriched candidate
3. Expand full analysis

**Expected Results:**
✅ Badges stack vertically
✅ Stats card grid stacks
✅ Agent scores display in single column
✅ Agent reasoning text stays truncated (space optimization)
✅ Core functionality intact

---

## Visual Verification Checklist

### Color Scheme
- [ ] PDL badges are blue (`bg-blue-100 text-blue-800`)
- [ ] Perplexity badges are purple (`bg-purple-100 text-purple-800`)
- [ ] Claude AI section has indigo-to-purple gradient
- [ ] Research section has purple-to-pink gradient
- [ ] High confidence scores are green
- [ ] Medium confidence scores are amber
- [ ] Low confidence scores are orange

### Icons
- [ ] Data sources section has database icon
- [ ] Claude AI section has lightbulb icon
- [ ] Research section has magnifying glass icon
- [ ] Each agent has emoji (🎯📈🤝⏰)
- [ ] Research types have emojis (💻📚🏆🔬)

### Typography
- [ ] Badge text is uppercase and bold
- [ ] Section headers are clear and consistent
- [ ] Score numbers are large and prominent
- [ ] Reasoning text is readable but secondary

---

## Edge Cases to Test

### 1. Partial Enrichment
**Scenario:** Candidate has PDL but no Perplexity
**Expected:** Only PDL badge shows, no research insights section

### 2. Missing Claude Reasoning
**Scenario:** Claude API failed or timed out
**Expected:** No AI score in column, no Claude section in analysis

### 3. Empty Research
**Scenario:** Perplexity returned no useful insights
**Expected:** No Perplexity badge, research section hidden

### 4. Cache vs Live
**Scenario:** First load vs cached load
**Expected:**
- First: 30+ seconds, shows "Generating shortlist..."
- Cached: <1 second, instant load
- Both show same enrichment data

### 5. Network with No Candidates
**Scenario:** No candidates in company network
**Expected:** Empty state with helpful message

---

## Performance Verification

### Backend
- [ ] API response time <500ms (cached)
- [ ] API response time <30s (live generation)
- [ ] No errors in backend logs
- [ ] Enrichment details properly serialized

### Frontend
- [ ] Initial page load <2s
- [ ] No console errors
- [ ] No type errors
- [ ] Smooth expand/collapse animations
- [ ] No layout shift when expanding

---

## Data Integrity Checks

### Enrichment Sources
```typescript
// Should see in browser DevTools Network tab:
{
  enrichment_details: {
    sources: ["pdl", "perplexity"],  // ✓ Correct
    pdl_fields: ["skills", "experience", "education"],  // ✓ Specific
    research_highlights: [...],  // ✓ Structured
    data_quality_score: 0.85  // ✓ 0-1 range
  }
}
```

### Claude Reasoning
```typescript
{
  claude_reasoning: {
    overall_score: 87.5,  // ✓ 0-100 range
    confidence: 0.92,  // ✓ 0-1 range
    agent_scores: {
      skills_agent: { score: 85, reasoning: "..." },  // ✓ Present
      trajectory_agent: { score: 78, reasoning: "..." },  // ✓ Present
      fit_agent: { score: 92, reasoning: "..." },  // ✓ Present
      timing_agent: { score: 65, reasoning: "..." }  // ✓ Present
    },
    weighted_calculation: "70% Claude (87) + 30% rule-based (75) = 83"  // ✓ Explanation
  }
}
```

---

## Common Issues & Solutions

### Issue: No enrichment badges showing
**Check:**
- Is candidate in top 5?
- Did PDL enrichment succeed? (check backend logs)
- Is `enrichment_details.sources` populated?

**Solution:** Check backend logs for enrichment failures

### Issue: Claude AI section not appearing
**Check:**
- Is `claude_reasoning` present in API response?
- Did Claude API call succeed? (check backend logs)
- Is Anthropic API key configured?

**Solution:** Verify `settings.anthropic_api_key` is set

### Issue: Research insights empty
**Check:**
- Did Perplexity research run? (check backend logs)
- Are `research_highlights` populated?
- Is Perplexity API key configured?

**Solution:** Verify `settings.perplexity_api_key` is set

### Issue: TypeScript errors
**Check:**
- Run `npm run type-check` in `web/` directory
- Verify interface alignment

**Solution:** Ensure frontend types match backend models

---

## Test Data Requirements

### Minimum Test Data
- 1 company
- 1 role with required skills
- 10+ candidates in network
- At least 5 candidates with LinkedIn URLs

### Optimal Test Data
- 2+ companies
- 3+ roles per company
- 50+ candidates per company
- Mix of complete and incomplete profiles
- Some candidates with GitHub URLs

---

## Browser Compatibility

Test in:
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile Safari (iOS)
- [ ] Mobile Chrome (Android)

---

## API Testing with curl

### Test Curation Endpoint
```bash
curl -X POST http://localhost:8001/api/v1/curation/curate \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "YOUR_COMPANY_ID",
    "role_id": "YOUR_ROLE_ID",
    "limit": 15
  }' | jq '.shortlist[0].context | {enrichment_details, claude_reasoning}'
```

**Expected:** JSON with enrichment_details and claude_reasoning (if available)

---

## Success Criteria

Test passes if:
✅ All enrichment data visible in UI
✅ Claude agent breakdown displays correctly
✅ Perplexity insights show in structured format
✅ Sources clearly attributed
✅ Graceful degradation for non-enriched
✅ No console errors
✅ No type errors
✅ Performance <2s page load
✅ Mobile responsive

---

## Reporting Issues

When reporting bugs, include:
1. Screenshot of issue
2. Browser console logs
3. Network tab showing API response
4. Backend logs (if available)
5. Steps to reproduce
6. Expected vs actual behavior

---

## Next Steps After Testing

1. Collect user feedback on:
   - Visual clarity
   - Information hierarchy
   - Useful vs overwhelming
   - Missing insights

2. Performance optimization:
   - Monitor API response times
   - Optimize rendering for large lists
   - Consider pagination for >50 candidates

3. Feature enhancements:
   - Interactive agent reasoning (click to expand)
   - Enrichment refresh button
   - Export enriched data
   - Custom agent weights

---

## Automated Testing (Future)

Consider adding:
- E2E tests with Playwright
- Component tests with React Testing Library
- API integration tests
- Performance regression tests

Example E2E test:
```typescript
test('enriched candidate shows badges', async ({ page }) => {
  await page.goto('/dashboard/candidates');
  await page.selectOption('[name="role"]', 'Software Engineer');
  await expect(page.locator('[title="PDL Enriched"]')).toBeVisible();
});
```
