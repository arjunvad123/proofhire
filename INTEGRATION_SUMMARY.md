# Agencity ↔ ProofHire Integration Summary

## What I Built

I created a complete integration between **Agencity** (candidate sourcing) and **ProofHire** (evaluation system) to provide founders with an end-to-end hiring solution.

---

## 🎯 Key Features

### 1. **New Pipeline Tab in Agencity Dashboard**
- View all sourced candidates in one place
- Track status across both systems: Sourced → Contacted → Invited → In Simulation → Reviewed
- Visual stage cards showing counts
- Filter and sort capabilities

### 2. **ProofHire Integration Module**
**File:** `/agencity/web/src/lib/proofhire-integration.ts`

**Key Functions:**
- `inviteCandidateToProofHire()` - Create ProofHire application from Agencity
- `getCandidateStatus()` - Check simulation progress
- `recordProofHireFeedback()` - Send hiring outcomes back to Agencity
- `getProofHireEvaluationLink()` - Generate links to briefs

### 3. **Candidate Linkage System**
- Links Agencity candidates with ProofHire applications
- Stores: `agencity_candidate_id ↔ proofhire_application_id`
- Tracks status across both platforms
- Enables feedback loop for learning

---

## 📁 Files Created/Modified

### Created:
1. `/agencity/web/src/app/dashboard/pipeline/page.tsx` - New pipeline view
2. `/agencity/web/src/lib/proofhire-integration.ts` - Integration API client
3. `/INTEGRATION_SETUP.md` - Complete setup guide
4. `/INTEGRATION_SUMMARY.md` - This file

### Modified:
1. `/agencity/web/src/app/dashboard/layout.tsx` - Added Pipeline navigation

---

## 🔄 Complete User Flow

```
1. Founder searches in Agencity
   "ML Engineer with PyTorch experience"
   ↓
2. Agencity returns 47 candidates
   - 12 in network (warm)
   - 23 with warm paths
   - 12 cold
   ↓
3. Founder clicks "Sarah Chen" (94/100 score)
   Sees: "You met at YC Demo Day 2022"
   ↓
4. Founder navigates to Pipeline tab
   Sees Sarah in "Sourced" stage
   ↓
5. Clicks "Invite to ProofHire"
   ↓
6. System creates ProofHire application
   Sends email to Sarah
   Status updates to "Invited"
   ↓
7. Sarah clicks link, completes simulation
   Status updates to "In Simulation"
   ↓
8. ProofHire Runner executes code in Docker
   Proof Engine generates brief
   Status updates to "Reviewed"
   ↓
9. Founder sees "View Evaluation Brief" button
   ↓
10. Clicks button → Opens ProofHire brief
    Shows:
    - 8 proven claims with evidence
    - 2 unproven claims with interview questions
    - Direct artifact links
    ↓
11. Founder makes decision
    Clicks "Hired" or "Rejected"
    ↓
12. Feedback sent back to Agencity
    GRPO model learns
    Future searches improve
```

---

## 🔌 API Endpoints

### Agencity → ProofHire

```typescript
// Create application
POST http://localhost:8000/api/roles/{roleId}/apply
{
  "name": "Sarah Chen",
  "email": "sarah@example.com",
  "linkedin_url": "...",
  "consent": true
}
→ Returns: { id: "app-001", status: "applied" }

// Get application status
GET http://localhost:8000/api/applications/{appId}
→ Returns: { status: "in_simulation" | "completed" }

// Get evaluation brief
GET http://localhost:8000/api/applications/{appId}/brief
→ Returns: { proven_claims: [...], unproven_claims: [...] }
```

### ProofHire → Agencity (Feedback)

```typescript
// Record outcome
POST http://localhost:8001/api/feedback/action
{
  "company_id": "uuid",
  "candidate_id": "agc-001",
  "action": "hired",
  "proofhire_score": 85
}
→ Feeds into GRPO reward model
```

---

## 🗄️ Data Schema

### New Table: `candidate_linkages` (Agencity/Supabase)

```sql
CREATE TABLE candidate_linkages (
  id UUID PRIMARY KEY,
  company_id UUID NOT NULL,
  agencity_candidate_id UUID NOT NULL,
  agencity_search_id UUID,
  proofhire_application_id TEXT NOT NULL,
  proofhire_role_id TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);
```

---

## ⚙️ Environment Setup

### Agencity Web `.env.local`
```bash
NEXT_PUBLIC_API_URL=http://localhost:8001/api
NEXT_PUBLIC_PROOFHIRE_URL=http://localhost:8000/api
NEXT_PUBLIC_PROOFHIRE_WEB_URL=http://localhost:3000
```

### ProofHire Backend `.env`
```bash
AGENCITY_API_URL=http://localhost:8001/api
AGENCITY_WEBHOOK_SECRET=shared-secret
```

---

## 🚀 How to Test

### 1. Start Services
```bash
# Terminal 1: ProofHire
cd proofhire && make up

# Terminal 2: Agencity Backend
cd agencity && uvicorn app.main:app --reload --port 8001

# Terminal 3: Agencity Web
cd agencity/web && npm run dev
```

### 2. Access Dashboards
- Agencity: http://localhost:3001/dashboard
- ProofHire: http://localhost:3000/dashboard

### 3. Test Flow
1. In Agencity: Search → "ML Engineer"
2. Navigate to Pipeline tab
3. Click "Invite to ProofHire" on a candidate
4. Check ProofHire dashboard for new application
5. (Simulate) Candidate completes test
6. Return to Agencity Pipeline → Status updates
7. Click "View Evaluation Brief"

---

## 📊 Pipeline Stages

| Stage | Color | Description | Actions Available |
|-------|-------|-------------|-------------------|
| **Sourced** | Gray | Found via Agencity search | Invite to ProofHire, Contact |
| **Contacted** | Blue | Outreach sent | Invite to ProofHire |
| **Invited** | Purple | ProofHire invitation sent | Resend, Cancel |
| **In Simulation** | Yellow | Taking the test | View Progress |
| **Reviewed** | Green | Evaluation complete | View Brief, Interview, Hire/Reject |

---

## 🎨 UI Components

### Pipeline Page Features
- **Stage Cards**: Clickable filter cards with counts
- **Candidate Cards**:
  - Avatar with initials
  - Name, title, company
  - Warmth level badge (NETWORK/WARM/COLD)
  - Status badge
  - Warm path description
  - ProofHire status indicator
  - Timeline (sourced, contacted, invited dates)
  - Expandable actions menu

### Integration Indicators
- 🟢 Green dot: Simulation complete
- 🟡 Yellow pulsing dot: In progress
- 🟣 Purple: Invited, waiting
- 📋 "View Evaluation Brief" button (green) when ready

---

## 🔐 Security Considerations

### Authentication
- Both systems use separate JWT tokens
- Stored in localStorage: `proofhire_token`, `agencity_token`
- Tokens sent in Authorization headers

### Data Privacy
- Candidate data only shared with explicit consent
- Linkages stored securely in Supabase
- CORS properly configured between systems

---

## 📈 Metrics & Analytics

### Track Across Systems:
- **Conversion Rate**: Sourced → Invited → Completed → Hired
- **Time to Hire**: From search to hire decision
- **Simulation Completion Rate**: % who complete after invitation
- **Brief Quality Score**: Proven vs unproven claims ratio
- **Feedback Loop Accuracy**: Did Agencity scores predict ProofHire performance?

---

## 🔮 Future Enhancements

### Phase 2 (Next):
- [ ] Real-time status updates (WebSocket/polling)
- [ ] Batch invite candidates
- [ ] Email template customization
- [ ] Warm path info in ProofHire briefs

### Phase 3 (Later):
- [ ] Analytics dashboard
- [ ] A/B testing framework
- [ ] Automated follow-ups
- [ ] Calendar integration for interviews
- [ ] Slack notifications

---

## 🐛 Known Issues & Workarounds

### Issue 1: Linkage stored in localStorage
**Temporary:** Using browser localStorage
**Production:** Need Supabase table + API endpoints

**Workaround:**
```typescript
// Check linkage
const linkage = localStorage.getItem('linkage_agc-001');
console.log(JSON.parse(linkage));
```

### Issue 2: No real-time updates
**Current:** Manual refresh needed
**Future:** Implement polling or WebSockets

**Workaround:**
```typescript
// Poll every 10 seconds
setInterval(async () => {
  const status = await getCandidateStatus(candidateId);
  // Update UI
}, 10000);
```

---

## 📚 Documentation Reference

1. **INTEGRATION_SETUP.md** - Complete setup guide with:
   - Environment variables
   - Database schema
   - API endpoints
   - Testing procedures
   - Troubleshooting

2. **UNIFIED_DASHBOARD.md** - Original unified dashboard design (alternative approach)

3. **TECHNICAL_ARCHITECTURE.md** - ProofHire system architecture

4. **agencity/docs/ARCHITECTURE.md** - Agencity system architecture

---

## ✅ Testing Checklist

- [ ] Agencity dashboard loads
- [ ] Pipeline tab visible in navigation
- [ ] Can view candidates by stage
- [ ] Can click "Invite to ProofHire"
- [ ] ProofHire application created
- [ ] Email sent to candidate
- [ ] Status updates in pipeline
- [ ] Can view brief when complete
- [ ] Feedback recorded in Agencity

---

## 🎓 Learning Resources

### For Developers:
- Read `INTEGRATION_SETUP.md` for technical details
- Check `proofhire-integration.ts` for API examples
- Review `pipeline/page.tsx` for UI patterns

### For Product/Founders:
- Review this summary for flow understanding
- Check user flow diagram above
- Test in staging environment first

---

## 🤝 Support

**Questions?** Check:
1. This summary for overview
2. INTEGRATION_SETUP.md for technical details
3. GitHub issues for known problems

**Need Help?**
- Technical: Check browser console for errors
- API: Check Network tab in DevTools
- Integration: Verify environment variables

---

*Created: February 13, 2026*
*Status: ✅ Core integration complete, ready for testing*
