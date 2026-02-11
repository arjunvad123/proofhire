# Agencity Demo Plan

## Demo Goal

**Demonstrate the full power of Agencity in finding "unhireable" talent** — people who don't show up in traditional searches but are perfect for the role.

**Target Duration:** 5-7 minutes (investor pitch), expandable to 15 minutes (detailed walkthrough)

---

## Demo Narrative

### The Hook (30 seconds)

> "You're a seed-stage founder. You need a prompt engineer. You go to LinkedIn — 50,000 results. Most have optimized profiles but no real experience. Meanwhile, the perfect candidate — a CS junior at UCSD who built an LLM-powered tutoring app at a hackathon — is invisible because they don't have 'prompt engineer' in their bio.
>
> **Agencity finds the people you can't search for.**"

---

## Demo Flow

### Act 1: The Intake (2 minutes)

**What happens:**
1. Founder types: "I need a prompt engineer for my AI startup"
2. Agencity asks smart follow-up questions:
   - "What does your startup do?"
   - "What will this person actually build?"
   - "What does success look like by day 60?"
   - "Any past hires that worked well or didn't?"
   - "Location or school preferences?"
3. Show the Role Blueprint being built in real-time (side panel)

**Wow moment:** The questions feel like talking to a smart recruiter, not filling out a form.

**Demo prep needed:**
- Pre-scripted founder responses for smooth flow
- Side panel showing Blueprint JSON updating live

---

### Act 2: The Deep Search (2 minutes)

**What happens:**
1. Agencity says: "I have enough context. Searching across 9 sources..."
2. Show search happening across sources (animated):
   - Our Network (6,000+ candidates) ✓
   - GitHub (top repos with LLM APIs) ✓
   - Devpost (hackathon winners) ✓
   - Codeforces (top competitive programmers) ✓
   - Stack Overflow (LLM tag contributors) ✓
   - HackerNews (who wants to be hired) ✓
3. Show deduplication: "Found 847 signals → 156 unique candidates"
4. Show evaluation: "Evaluating 156 candidates against your blueprint..."

**Wow moment:** The breadth of search — we look where others don't.

**Demo prep needed:**
- Pre-run search results cached for demo reliability
- Animated progress indicators for each source
- Real numbers from our 6,000+ database

---

### Act 3: The Honest Results (2 minutes)

**What happens:**
1. Show 5 candidates with our honest evaluation format:

   **Candidate 1: Sarah Chen**

   | Known Facts | Observed Signals | Unknown |
   |------------|------------------|---------|
   | UCSD CS, Class of 2026 | 3 LLM projects on GitHub | Actual prompt engineering depth |
   | AI Club member | Won HackLA with chatbot | Work style in team setting |
   | Took CS 229 (ML) | 47 GitHub stars on LLM wrapper | Interest in your specific startup |

   **Why Consider:** Strong LLM project experience for a junior. Multiple public projects show shipping ability. Won hackathon with AI product — indicates both building and presenting skills.

   **Suggested Next Step:** Ask about the HackLA project — what was the prompt architecture? Did they handle edge cases?

2. Show 2-3 more candidates with different profiles
3. Contrast with what LinkedIn would show (optional)

**Wow moment:** Honest "Unknown" section — we don't pretend to know what we can't verify.

**Demo prep needed:**
- 5 real candidates from our database (anonymized if needed)
- Pre-evaluated with rich signals
- Comparison slide: "What LinkedIn shows vs what we found"

---

### Act 4: The Network Connection (1 minute)

**What happens:**
1. Click on a candidate to see connection path:
   - "You → (via YC batch) → Sarah's co-founder at hackathon → Sarah"
2. Show warm intro possibility
3. Optional: Show candidate's perspective (two-way marketplace preview)

**Wow moment:** We don't just find people — we show how to reach them.

**Demo prep needed:**
- Mock connection graph for demo candidates
- Visual graph representation

---

### Act 5: The Feedback Loop (30 seconds)

**What happens:**
1. Founder clicks "Interested" on Sarah, "Pass" on another
2. Show: "Got it. Adjusting future recommendations..."
3. Quick mention: "Next week, we'll proactively surface new candidates matching your pattern"

**Wow moment:** It learns and comes back to you.

**Demo prep needed:**
- Feedback UI
- Brief mention of proactive recommendations

---

## Data Requirements

### From Our 6,000+ Candidate Database

**Need to extract:**
- Name, email, school, graduation year
- Major/field of study
- GitHub username (if available)
- LinkedIn URL (if available)
- Skills/interests (if captured)
- Any project information
- How they were sourced (referral, application, event?)

**Ideal candidates for demo:**
- 2-3 with strong GitHub presence (can show projects)
- 1-2 with hackathon wins (Devpost data)
- 1 with competitive programming background
- Mix of schools (not just Stanford/MIT)
- At least 1 "hidden gem" — no LinkedIn, sparse online presence, but great signals

### Sample SQL Queries (once access provided)

```sql
-- Find candidates with GitHub
SELECT * FROM candidates
WHERE github_username IS NOT NULL
LIMIT 100;

-- Find candidates by school
SELECT school, COUNT(*) as count
FROM candidates
GROUP BY school
ORDER BY count DESC;

-- Find candidates with specific skills
SELECT * FROM candidates
WHERE skills ILIKE '%python%'
   OR skills ILIKE '%machine learning%';
```

---

## Technical Demo Requirements

### Backend Must Work

- [ ] Conversation flow (intake → blueprint)
- [ ] Multi-source search (at least Network + GitHub)
- [ ] Candidate evaluation (Known/Observed/Unknown)
- [ ] Shortlist generation

### Frontend Needs

- [ ] Clean chat interface
- [ ] Blueprint side panel
- [ ] Search progress animation
- [ ] Candidate cards with honest evaluation
- [ ] Feedback buttons (Interested/Pass)

### Data Prep

- [ ] Import 6,000+ candidates into PostgreSQL
- [ ] Enrich with GitHub data (batch job)
- [ ] Pre-compute evaluations for demo reliability
- [ ] Create 5-10 "hero" candidates with rich profiles

---

## Demo Variants

### Variant A: Live Demo (Risky but impressive)

- Actually run the full flow live
- Real API calls, real search
- Risk: API failures, slow responses
- Mitigation: Have cached fallback ready

### Variant B: Semi-Live Demo (Recommended)

- Live conversation intake
- Pre-cached search results (appear live)
- Real candidate data, pre-enriched
- Guaranteed reliable, still feels real

### Variant C: Video Demo (Safe but less engaging)

- Pre-recorded walkthrough
- Perfect timing, perfect results
- Use for async distribution

---

## Demo Script (Detailed)

### Setup

- Browser open to Agencity chat interface
- Clean desktop, no notifications
- 2 screens if presenting: demo + notes

### Script

**[00:00]** "Let me show you Agencity. I'm a founder — I need to hire a prompt engineer."

**[00:10]** *Types:* "I need a prompt engineer for my startup"

**[00:15]** *Agencity responds with first question*

**[00:30]** *Answer questions naturally, showing blueprint building*

**[01:30]** *Agencity has enough context, starts search*

**[01:45]** *Show multi-source search animation*

**[02:30]** *Results appear — highlight first candidate*

**[03:00]** "Notice what we DON'T claim to know..." *point to Unknown section*

**[03:30]** *Show connection path to candidate*

**[04:00]** *Give feedback, show learning loop*

**[04:30]** "This person would never show up in a LinkedIn search. But they might be exactly who you need."

**[05:00]** *End with value prop recap*

---

## Success Metrics for Demo

1. **Engagement:** Audience leans in during results reveal
2. **Understanding:** They get the "honest evaluation" concept
3. **Differentiation:** They see why this is better than LinkedIn
4. **Excitement:** They want to try it / invest / partner

---

## Pre-Demo Checklist

### Day Before

- [ ] Test full flow end-to-end
- [ ] Verify all APIs working
- [ ] Cache fallback data ready
- [ ] Test on demo machine
- [ ] Practice script 3x

### Hour Before

- [ ] Clear browser cache
- [ ] Close unnecessary apps
- [ ] Silence notifications
- [ ] Check internet connection
- [ ] Open backup slides

---

## Questions to Answer Before Demo

1. **Can we use real candidate names?** Or need to anonymize?
2. **Do we have GitHub data for our candidates?** Need to enrich if not
3. **What's the database schema?** Need to map to our CandidateData model
4. **Any standout candidates?** Perfect examples for demo
5. **Target audience for demo?** Investors? Founders? Partners?

---

## Next Steps

1. **Get SQL access** to candidate database
2. **Explore the data** — understand what fields we have
3. **Identify 10 hero candidates** for demo
4. **Enrich with GitHub/Devpost data** if missing
5. **Build frontend polish** for demo UX
6. **Practice demo script** 5+ times
7. **Create fallback video** just in case

---

## Appendix: Demo Candidate Profiles

*To be filled after database access*

### Candidate 1: [Name]
- School:
- GitHub:
- Signals:
- Why perfect for demo:

### Candidate 2: [Name]
- School:
- GitHub:
- Signals:
- Why perfect for demo:

*(Continue for 5-10 candidates)*
