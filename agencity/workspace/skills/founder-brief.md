---
id: founder-brief
name: Founder Brief
description: Generate a weekly recruiting digest for the founder
trigger: manual
cron: "0 8 * 1"
---

# Founder Brief

You compile a weekly recruiting intelligence digest for the founder.
This runs automatically on Monday mornings or can be triggered manually.

## Brief Structure

### 1. Pipeline Summary
Use `agencity_pipeline` to get current pipeline state.
Present:
- Total candidates at each stage
- Movement since last brief (who progressed, who dropped)
- Candidates requiring action (follow-ups due, interviews to schedule)

### 2. New Discoveries
If there are active roles, run `agencity_search` for each to find new candidates since last week.
Highlight:
- Top 3-5 new candidates found
- Any high-urgency candidates (timing signals suggest they're open NOW)
- New warm paths discovered

### 3. Market Intelligence
Summarize relevant signals:
- Companies with recent layoffs (potential talent pool)
- Vesting cliff clusters (people approaching 1-year or 4-year marks)
- Industry trends affecting the talent pool

### 4. Recommended Actions
Based on the above, suggest 2-3 specific actions:
- "Reach out to [Name] — they just hit their 1-year vesting cliff at [Company]"
- "Ask [Connector] for intro to [Name] — strong Tier 2 match"
- "Consider broadening [Role] search to include [adjacent skill]"

## Delivery

Present the brief in a clear, scannable format. Founders are busy — front-load the most important information. Use bullet points, bold key names, and keep paragraphs short.
