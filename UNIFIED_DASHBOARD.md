# Unified ProofHire + Agencity Dashboard

## Overview

The Unified Dashboard integrates **Agencity** (candidate sourcing) with **ProofHire** (candidate evaluation) to provide founders with an end-to-end hiring solution.

```
┌─────────────────────────────────────────────────────────────────────┐
│                     UNIFIED DASHBOARD                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  AGENCITY (Sourcing)          →    PROOFHIRE (Evaluation)           │
│  ┌────────────────────┐            ┌────────────────────┐           │
│  │ • Network Search   │            │ • Work Simulations │           │
│  │ • External APIs    │     →      │ • Evidence Engine  │           │
│  │ • Warm Paths       │            │ • Proof-based      │           │
│  │ • Timing Signals   │            │   Briefs           │           │
│  └────────────────────┘            └────────────────────┘           │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Architecture

### Frontend Structure

```
web/src/app/(founder)/
├── unified-dashboard/
│   ├── page.tsx                       # Main dashboard with 4 tabs
│   └── candidates/
│       └── [id]/
│           └── page.tsx               # Detailed candidate view
```

### API Integration

```
web/src/lib/
├── api.ts                             # ProofHire API client
└── agencity-api.ts                    # Agencity API client (NEW)
```

---

## Dashboard Features

### 1. Overview Tab

**Purpose:** High-level metrics and quick actions

**Components:**
- **Stats Grid** (4 cards):
  - Network Size (from Agencity)
  - Active Roles (from ProofHire)
  - Pipeline Count (candidates tracking)
  - In Evaluation (active simulations)

- **Search Bar:**
  - Quick search for roles
  - Autocomplete suggestions
  - Recent search shortcuts

- **Recent Candidates:**
  - Last 3 candidates from Agencity
  - Quick status view
  - One-click access to details

- **Search History:**
  - Last 2-3 searches
  - Results count
  - Re-run searches

**Mock Data Location:** Lines 75-155 in `unified-dashboard/page.tsx`

---

### 2. Search Tab

**Purpose:** Find candidates using Agencity

**Features:**
- **Search Interface:**
  - Role title input with autocomplete
  - Required skills (multi-select)
  - Experience level dropdown
  - Search mode selector (Full/Network Only/Quick)

- **Search History:**
  - All previous searches
  - View results button
  - Metadata (count, date)

**API Integration:**
```typescript
import { searchCandidates } from '@/lib/agencity-api';

const result = await searchCandidates({
  company_id: orgId,
  role_title: 'ML Engineer',
  required_skills: ['Python', 'PyTorch'],
  mode: 'full',
});
```

---

### 3. Pipeline Tab

**Purpose:** Track candidates from sourcing to hire

**Pipeline Stages:**
1. **Sourced** (gray) - Found via Agencity
2. **Contacted** (blue) - Outreach sent
3. **Invited** (purple) - ProofHire invitation sent
4. **In Simulation** (yellow) - Completing evaluation
5. **Reviewed** (green) - Brief available

**Features:**
- Stage counts in cards
- Filter by stage
- Sort by score/date/status
- Full candidate list with:
  - Name, title, company
  - Score breakdown (fit, warmth, timing)
  - Warm path information
  - Skills tags
  - Timing signals
  - Action buttons

**Candidate Actions:**
- View Details → Navigate to detail page
- Save → Add to saved list
- Invite to ProofHire → Send simulation invitation
- View Brief → Navigate to ProofHire evaluation (if completed)

---

### 4. Network Tab

**Purpose:** Manage professional network

**Features:**
- **Network Overview:**
  - Total contacts
  - Companies represented
  - Schools connected
  - Engineers count

- **Top Companies:**
  - List of companies with most contacts
  - Contact count per company

- **Network Actions:**
  - Import More Connections
  - Request Recommendations
  - View Network Map

---

## Candidate Detail Page

### URL Structure

```
/unified-dashboard/candidates/[id]
```

### Layout

```
┌─────────────────────────────────────────────────────────────────┐
│ [← Back]  Candidate Details                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────┐   ┌──────────────────────────┐   │
│  │  MAIN COLUMN (2/3)       │   │  SIDEBAR (1/3)           │   │
│  │                          │   │                          │   │
│  │  • Header Card           │   │  • Actions Card          │   │
│  │    - Avatar              │   │    - Invite to ProofHire │   │
│  │    - Name, title         │   │    - Contact             │   │
│  │    - Overall score       │   │    - Save                │   │
│  │    - Badges              │   │    - Not Interested      │   │
│  │    - Links               │   │                          │   │
│  │                          │   │  • Scores Breakdown      │   │
│  │  • Tabbed Content        │   │    - Fit (85)            │   │
│  │    [Overview]            │   │    - Warmth (100)        │   │
│  │    [Intelligence]        │   │    - Timing (70)         │   │
│  │    [Activity]            │   │                          │   │
│  │                          │   │  • Status Timeline       │   │
│  │    - Why Consider        │   │    - Sourced ✓           │   │
│  │    - Skills              │   │    - Contacted ✓         │   │
│  │    - Experience          │   │    - Invited ✓           │   │
│  │    - Education           │   │                          │   │
│  │    - Unknowns            │   │                          │   │
│  │                          │   │                          │   │
│  └──────────────────────────┘   └──────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Tabs

**1. Overview Tab:**
- Why Consider (AI-generated narrative)
- Skills (chips)
- Experience timeline
- Education
- Unknowns (questions for interview)

**2. Intelligence Tab:**
- Warm path details with strength %
- Timing signals (cliff approaching, profile updated, etc.)
- Network insights

**3. Activity Tab:**
- Full timeline of interactions
- Sourcing details
- Contact history
- ProofHire status

---

## Data Flow

### Complete Candidate Journey

```
1. SOURCING (Agencity)
   ↓
   User searches for "ML Engineer"
   ↓
   Agencity returns 47 candidates with:
   - Fit scores
   - Warm paths
   - Timing signals
   ↓
   User views candidate details
   ↓

2. INVITATION (Bridge)
   ↓
   User clicks "Invite to ProofHire"
   ↓
   API call: agencity-api.inviteToProofHire()
   ↓
   Creates ProofHire application
   ↓
   Sends email to candidate
   ↓
   Links Agencity candidate_id ↔ ProofHire application_id
   ↓

3. EVALUATION (ProofHire)
   ↓
   Candidate clicks link, starts simulation
   ↓
   Runner executes in Docker sandbox
   ↓
   Evidence extracted (code diffs, tests, metrics)
   ↓
   Proof engine generates brief
   ↓

4. REVIEW (Unified View)
   ↓
   Dashboard shows candidate status: "In Simulation" → "Reviewed"
   ↓
   "View Brief" button appears
   ↓
   User clicks, navigates to ProofHire brief page
   ↓
   Brief shows:
   - Proven claims with evidence
   - Unproven claims with interview questions
   - Links back to Agencity warm path info
   ↓

5. FEEDBACK LOOP
   ↓
   User marks candidate as: Hired / Rejected / Interviewing
   ↓
   Feedback sent to Agencity
   ↓
   GRPO reward model learns
   ↓
   Future searches improved
```

---

## API Integration Points

### Agencity APIs

**Search:**
```typescript
POST /api/search
{
  "company_id": "uuid",
  "role_title": "ML Engineer",
  "required_skills": ["Python", "PyTorch"],
  "mode": "full"
}

Response:
{
  "candidates": [ ... ],
  "search_id": "search-123",
  "total_count": 47,
  "tier1_count": 12,  // Network
  "tier2_count": 23,  // Warm
  "tier3_count": 12   // Cold
}
```

**Network Stats:**
```typescript
GET /api/v3/network/{company_id}/stats

Response:
{
  "total_contacts": 1247,
  "companies": 312,
  "schools": 89,
  "engineers": 423,
  "by_company": { "Google": 23, "Meta": 18, ... }
}
```

**Warm Paths:**
```typescript
POST /api/v3/warm-paths/{company_id}
{
  "linkedin_urls": ["https://linkedin.com/in/sarachen"]
}

Response:
{
  "paths": [
    {
      "type": "direct",
      "description": "You met at YC Demo Day 2022",
      "strength": 100
    }
  ]
}
```

**Invite to ProofHire:**
```typescript
POST /api/integration/proofhire/invite
{
  "candidate_id": "agencity-candidate-id",
  "proofhire_role_id": "proofhire-role-uuid",
  "agencity_search_id": "search-123"
}

Response:
{
  "application_id": "proofhire-app-uuid",
  "invitation_sent": true
}
```

**Feedback:**
```typescript
POST /api/feedback/action
{
  "company_id": "uuid",
  "candidate_id": "candidate-id",
  "action": "hired",  // or interviewed, rejected, etc.
  "search_id": "search-123"
}
```

---

## Implementation Checklist

### Phase 1: Basic Integration (Current)
- [x] Create unified dashboard UI
- [x] Mock Agencity data
- [x] Create candidate detail page
- [x] Create agencity-api.ts client
- [ ] Connect to live Agencity API
- [ ] Test search functionality

### Phase 2: ProofHire Integration
- [ ] Add "Invite to ProofHire" functionality
- [ ] Create linking between systems (candidate_id ↔ application_id)
- [ ] Show ProofHire status in pipeline
- [ ] Add "View Brief" button when evaluation complete
- [ ] Test end-to-end flow

### Phase 3: Feedback Loop
- [ ] Record user actions (viewed, saved, contacted, etc.)
- [ ] Send feedback to Agencity
- [ ] Display feedback stats in dashboard
- [ ] Test RL reward model learning

### Phase 4: Advanced Features (Future)
- [ ] Saved candidates list
- [ ] Search history with re-run
- [ ] Network visualization
- [ ] Batch invite candidates
- [ ] Export candidate data
- [ ] Email templates
- [ ] Calendar integration
- [ ] Slack notifications

---

## Environment Variables

Add to `.env.local`:

```bash
# Agencity Integration
NEXT_PUBLIC_AGENCITY_URL=http://107.20.131.235
AGENCITY_API_KEY=your-api-key

# ProofHire (existing)
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

---

## Design System

Following `DASHBOARD_DESIGN.md` specifications:

**Colors:**
- Primary: Blue (`bg-blue-600`, `text-blue-600`)
- Success/Network: Green (`bg-green-50`, `text-green-700`)
- Warning/Warm: Yellow (`bg-yellow-50`, `text-yellow-700`)
- Error/Cold: Gray (`bg-gray-50`, `text-gray-700`)
- Black for headings: `text-black`
- Gray scale for body text

**Typography:**
- Headings: `font-bold`, `text-3xl` to `text-5xl`
- Body: `text-base`, `text-sm` for secondary
- Labels: `text-xs`

**Components:**
- Border radius: `rounded-lg` or `rounded-2xl`
- Shadows: `shadow` with `border border-gray-200`
- Padding: `p-6` for cards, `p-3` for compact items
- Transitions: `transition-colors`, `hover:bg-gray-50`

**Buttons:**
- Primary: `bg-blue-600 text-white rounded-2xl hover:bg-blue-700`
- Secondary: `bg-white border border-gray-200 rounded-lg hover:bg-gray-50`

---

## Testing

### Manual Testing Flow

1. **Navigate to Dashboard:**
   ```
   http://localhost:3000/unified-dashboard
   ```

2. **Test Overview Tab:**
   - Verify stats display
   - Click search shortcuts
   - View recent candidates
   - Click recent searches

3. **Test Search Tab:**
   - Enter role title
   - Select skills
   - Change experience level
   - Change search mode
   - Click "Search Candidates"
   - View search history

4. **Test Pipeline Tab:**
   - View pipeline stage counts
   - Filter by stage
   - Sort candidates
   - Click "View Details" on a candidate

5. **Test Candidate Detail Page:**
   - Verify all tabs load
   - Check Overview data display
   - Check Intelligence warm path
   - Check Activity timeline
   - Test action buttons
   - Navigate back

6. **Test Network Tab:**
   - Verify network stats
   - View top companies
   - Test action buttons

---

## Next Steps

### Immediate (Week 1)
1. Connect to live Agencity API endpoints
2. Test search functionality with real data
3. Implement saved candidates feature
4. Add loading states and error handling

### Short-term (Week 2-3)
1. Build "Invite to ProofHire" integration
2. Create candidate ↔ application linking
3. Show ProofHire status in dashboard
4. Add "View Brief" functionality

### Medium-term (Month 1)
1. Implement feedback recording
2. Add search history with re-run
3. Build batch operations
4. Add export functionality

### Long-term (Month 2+)
1. Network visualization
2. Email templates
3. Calendar integration
4. Advanced filtering and sorting
5. Analytics dashboard

---

## Troubleshooting

### Common Issues

**1. Agencity API not connecting:**
- Check `NEXT_PUBLIC_AGENCITY_URL` in `.env.local`
- Verify Agencity service is running: `http://107.20.131.235/health`
- Check CORS settings on Agencity backend

**2. Mock data not showing:**
- Ensure `getCurrentOrg()` returns valid org ID
- Check browser console for errors
- Verify data structure matches types in `agencity-api.ts`

**3. Routing issues:**
- Verify Next.js app directory structure
- Check that folder is under `app/(founder)/`
- Restart Next.js dev server

**4. Styling not applied:**
- Verify Tailwind CSS is configured
- Check that classes are not purged
- Restart dev server after config changes

---

## Support

For questions or issues:
1. Check this README
2. Review `DASHBOARD_DESIGN.md` for UI specs
3. See `TECHNICAL_ARCHITECTURE.md` for backend details
4. Check Agencity `docs/ARCHITECTURE.md` for API specs

---

*Last Updated: February 13, 2026*
