# Claude + Perplexity Architecture Analysis & Enhancement Proposal

## Current Architecture Overview

### Two Separate Search Flows

**1. Master Orchestrator Flow (Full Search)**
- Used by: Master search system
- Location: `app/services/master_orchestrator.py`
- Purpose: Finding NEW candidates from external sources

```
┌─────────────────────────────────────────────────────────────┐
│                   MASTER ORCHESTRATOR                        │
├─────────────────────────────────────────────────────────────┤
│  1. Claude Query Reasoning (reason_about_queries)           │
│     → Generate smart search queries from role + network     │
│     → Returns: primary_query, expansion_queries             │
│                                                              │
│  2. Unified Search (V5)                                      │
│     → Network + External + Warm Paths                        │
│     → Uses Claude queries to find candidates                │
│                                                              │
│  3. Claude Candidate Analysis (Agent Swarm)                  │
│     → Top 10 candidates analyzed                            │
│     → 4 agents: Skill, Trajectory, Fit, Timing              │
│     → Updates: why_consider, unknowns, confidence           │
│                                                              │
│  4. RL Ranking Adjustment                                    │
│     → Reward model adjusts rankings                         │
│                                                              │
│  Result: Ranked list of NEW candidates from search          │
└─────────────────────────────────────────────────────────────┘
```

**2. Curation Engine Flow (Shortlist from Network)**
- Used by: Curation/shortlist generation
- Location: `app/services/curation_engine.py`
- Purpose: Curating EXISTING network candidates for a role

```
┌─────────────────────────────────────────────────────────────┐
│                   CURATION ENGINE                            │
├─────────────────────────────────────────────────────────────┤
│  1. Get ALL network candidates                              │
│     → Build unified candidates in batch                     │
│                                                              │
│  2. Rule-based Fit Scoring                                   │
│     → Skills 40%, Experience 30%, Culture 20%, Signals 10%  │
│                                                              │
│  3. Initial Ranking                                          │
│     → Sort by fit score                                     │
│                                                              │
│  4. PDL Enrich Top 5 ✅ NEW                                  │
│     → Get missing data from PDL                             │
│     → 30-day caching                                        │
│                                                              │
│  5. Claude Reasoning on Enriched Candidates ✅ NEW           │
│     → Agent Swarm: Skill, Trajectory, Fit, Timing          │
│     → Weighted: 70% Claude + 30% rule-based                │
│                                                              │
│  6. Perplexity Deep Research (Top 5)                         │
│     → Web search for GitHub, projects, achievements         │
│     → Parse insights: skills, achievements, presence        │
│                                                              │
│  7. Build Rich Context                                       │
│     → why_consider, unknowns, standout_signal               │
│                                                              │
│  Result: Curated shortlist with deep research               │
└─────────────────────────────────────────────────────────────┘
```

---

## Current Integration Points

### 1. Master Orchestrator Uses:
**Claude Query Reasoning (`reason_about_queries`)**
- **Input:** Role requirements + network context (companies, schools)
- **Output:** Smart search queries that leverage network
- **Purpose:** Find similar talent by reasoning about adjacent roles, company types
- **Location:** Lines 185-207 in `master_orchestrator.py`

**Claude Candidate Analysis (`analyze_candidate`)**
- **Input:** Top 10 search results + role requirements
- **Output:** Agent swarm analysis (skill/trajectory/fit/timing)
- **Purpose:** Deep analysis of NEW candidates found via search
- **Location:** Lines 240-266 in `master_orchestrator.py`

### 2. Curation Engine Uses:
**Perplexity Deep Research**
- **Input:** Top 5 curated candidates + role requirements
- **Output:** Web research on GitHub, achievements, publications
- **Purpose:** Find additional context not in database
- **Location:** Lines 130-156 in `curation_engine.py`
- **Uses:** `DeepResearchEngine.enhance_candidates()`

**Claude Reasoning (NEW - just added)**
- **Input:** Top 5 enriched candidates + role + company context
- **Output:** Agent swarm analysis with weighted scoring
- **Purpose:** AI-enhanced scoring of enriched network candidates
- **Location:** Lines 833-912 in `curation_engine.py`

---

## Key Differences Between Flows

| Aspect | Master Orchestrator | Curation Engine |
|--------|-------------------|-----------------|
| **Input** | Role requirements | Network people + role |
| **Search** | External APIs (Clado, Pearch) | No search - uses existing network |
| **Claude Query** | Yes - generates search queries | No - not searching |
| **Claude Analysis** | Top 10 from search results | Top 5 from network (NEW) |
| **Perplexity** | No web research | Yes - deep research on top 5 |
| **Enrichment** | Not needed (fresh search) | Yes - PDL for missing data |
| **RL Ranking** | Yes - reward model | No RL layer |
| **Output** | New candidates to add | Curated shortlist from network |

---

## How They Work Together

### Typical User Flow:

```
1. User creates a role
   ↓
2. Master Orchestrator searches for NEW candidates
   → Claude generates smart queries
   → External search (Clado, Pearch)
   → Claude analyzes top 10 results
   → RL ranks results
   → New candidates added to network
   ↓
3. Curation Engine creates shortlist from ALL network
   → Rule-based fit scoring on all network
   → Rank by fit
   → Enrich top 5 with PDL
   → Claude reasoning on enriched top 5 ✅ NEW
   → Perplexity research on final top 5
   → Build rich context for shortlist
   ↓
4. User sees curated shortlist with deep insights
```

---

## Current Issues & Redundancies

### 1. **Duplicate Claude Analysis**
- Master orchestrator analyzes top 10 **search results**
- Curation engine now analyzes top 5 **network candidates**
- **Problem:** Same candidates might be analyzed twice if they're in both network and search results

### 2. **Missing Query Reasoning in Curation**
- Master orchestrator uses Claude to generate smart queries
- Curation engine doesn't use queries (doesn't search)
- **Opportunity:** Could use query reasoning to identify **gaps** in network

### 3. **Perplexity Only in Curation**
- Master orchestrator doesn't do web research
- Curation engine does Perplexity research on top 5
- **Issue:** Search results from master orchestrator lack web-researched context

### 4. **Different Scoring Methods**
- Master orchestrator: Rule-based fit → RL ranking
- Curation engine: Rule-based fit → Claude reasoning → Perplexity insights
- **Issue:** Inconsistent scoring across flows

---

## Enhancement Proposals

### Option 1: Unified Scoring Pipeline (Recommended)

**Goal:** Use the same scoring + research pipeline for both flows

```python
# Shared pipeline for both flows
async def score_and_enrich_candidates(
    candidates: List[Candidate],
    role: dict,
    company_dna: dict,
    umo: Optional[dict],
    top_n: int = 5
) -> List[CuratedCandidate]:
    """
    Universal candidate scoring pipeline.

    Used by both:
    - Master orchestrator (for search results)
    - Curation engine (for network candidates)
    """

    # 1. Rule-based initial scoring (fast)
    ranked = rank_by_fit_score(candidates, role, company_dna, umo)

    # 2. Enrich top N with PDL (if needed)
    top_n = ranked[:top_n]
    enriched = await enrich_with_pdl(top_n)

    # 3. Claude reasoning on enriched
    claude_scored = await score_with_claude(enriched, role, company_dna, umo)

    # 4. Perplexity deep research
    researched = await perplexity_research(claude_scored, role)

    # 5. Build rich context
    final = build_candidate_context(researched, role, company_dna, umo)

    return final
```

**Changes Required:**
1. Extract scoring logic from `curation_engine.py` into shared module
2. Update `master_orchestrator.py` to use unified pipeline
3. Remove duplicate Claude analysis from master orchestrator
4. Add Perplexity research to master orchestrator flow

**Benefits:**
- ✅ Consistent scoring across all flows
- ✅ All candidates get same treatment (fair comparison)
- ✅ Reduce code duplication
- ✅ Easier to improve pipeline (one place to change)

---

### Option 2: Specialized Pipelines (Current Approach)

**Goal:** Keep flows separate but align them better

**Master Orchestrator Pipeline:**
```python
# For NEW candidates from search
1. Claude query reasoning → smart search
2. External search
3. Rule-based ranking
4. Claude analysis (top 10)  ← Keep this
5. RL ranking adjustment
```

**Curation Engine Pipeline:**
```python
# For EXISTING network candidates
1. Rule-based ranking (all network)
2. PDL enrichment (top 5)
3. Claude reasoning (top 5)  ← Already have this ✅
4. Perplexity research (top 5)
5. Build rich context
```

**Enhancement:** Add Perplexity to Master Orchestrator
```python
# In master_orchestrator.py, after Claude analysis:

# Step 4.5: Perplexity Research (NEW)
if mode == "full":
    print("\n4.5. Deep Research (Perplexity)...")
    research_engine = DeepResearchEngine(settings.perplexity_api_key)

    enhanced = await research_engine.enhance_candidates(
        search_result.candidates[:5],
        role_title=role_title,
        role_skills=required_skills
    )

    # Update candidates with research
    for i, enhanced_candidate in enumerate(enhanced):
        search_result.candidates[i] = enhanced_candidate
```

**Benefits:**
- ✅ Less disruptive (smaller changes)
- ✅ Each flow optimized for its use case
- ✅ Search gets web research too

**Drawbacks:**
- ❌ Still have duplicate code
- ❌ Different scoring might confuse users

---

### Option 3: Query Reasoning for Network Gaps

**Goal:** Use Claude query reasoning to identify gaps in network coverage

**New Feature in Curation Engine:**
```python
async def identify_network_gaps(
    self,
    company_id: str,
    role: dict
) -> dict:
    """
    Use Claude to identify gaps in network coverage.

    Returns:
    - missing_skill_profiles: Skills not well-represented
    - adjacent_roles: Similar roles to search for
    - target_companies: Companies to target for outreach
    """
    from app.services.reasoning.claude_engine import claude_engine

    # Get network stats
    network_index = await network_index_service.build_index(company_id)
    stats = network_index_service.get_network_stats(network_index)

    # Use Claude to analyze gaps
    gap_analysis = await claude_engine.analyze_network_gaps(
        role=role,
        network_companies=stats["top_companies"],
        network_schools=stats["top_schools"],
        network_skills=stats["top_skills"]  # if available
    )

    return gap_analysis
```

**Use Case:**
```python
# In curation flow:
shortlist = await engine.curate(company_id, role_id)

# Check if shortlist is thin
if len(shortlist) < 5:
    # Identify gaps
    gaps = await engine.identify_network_gaps(company_id, role)

    # Suggest to user:
    # "Your network lacks senior ML engineers from YC startups.
    #  Consider searching externally or asking for intros."
```

---

## Recommended Implementation Plan

### Phase 1: Enhance Current Architecture (Low Risk)
**Goal:** Make both flows work better independently

1. **Add Perplexity to Master Orchestrator** ✅
   - Give search results the same deep research as curation
   - Location: `master_orchestrator.py` after line 263

2. **Deduplicate Claude Analysis** ✅
   - If candidate already analyzed by master orchestrator, skip in curation
   - Add `last_analyzed` timestamp to candidate model
   - Check timestamp before re-analyzing

3. **Align Scoring Weights** ✅
   - Use same weights (70% Claude, 30% rule-based) in both flows
   - Document why weights differ if they must be different

**Code Changes:**
```python
# 1. In master_orchestrator.py (after line 263)
if mode == "full" and settings.perplexity_api_key:
    print("\n4.5 Deep Research (Perplexity)...")
    from app.services.research.perplexity_researcher import DeepResearchEngine

    research_engine = DeepResearchEngine(settings.perplexity_api_key)
    top_5 = search_result.candidates[:5]

    enhanced = await research_engine.enhance_candidates(
        top_5,
        role_title=role_title,
        role_skills=required_skills,
        top_n=5
    )

    # Update with research
    for i, enhanced_candidate in enumerate(enhanced):
        search_result.candidates[i] = enhanced_candidate

    print(f"   Researched {len(enhanced)} candidates")

# 2. In curation_engine.py (before Claude reasoning)
# Check if candidate was recently analyzed
recent_cutoff = datetime.now() - timedelta(hours=1)
candidates_to_analyze = []

for item in to_enrich:
    candidate = item['candidate']

    # Check if has recent Claude analysis
    last_analyzed = getattr(candidate, 'claude_analyzed_at', None)
    if last_analyzed and last_analyzed > recent_cutoff:
        print(f"  ⏭️  {candidate.full_name} (analyzed {time_ago(last_analyzed)})")
        # Reuse existing scores
        item['claude_score'] = candidate.claude_score
        item['claude_confidence'] = candidate.claude_confidence
        item['claude_reasoning'] = candidate.claude_reasoning
    else:
        candidates_to_analyze.append(item)

# Only analyze candidates without recent analysis
if candidates_to_analyze:
    await self._score_with_claude_reasoning(candidates_to_analyze, ...)
```

---

### Phase 2: Unified Scoring Module (Medium Risk)
**Goal:** Create shared module used by both flows

1. **Extract Common Logic** 📦
   ```
   app/services/scoring/
   ├── __init__.py
   ├── unified_scorer.py        # Main scoring pipeline
   ├── rule_based.py             # Rule-based fit scoring
   ├── claude_reasoning.py       # Claude agent swarm
   └── context_builder.py        # Rich context generation
   ```

2. **Update Both Flows to Use Module** 🔄
   - Master orchestrator uses `unified_scorer.score_candidates()`
   - Curation engine uses same
   - Consistent output format

3. **Add Caching Layer** 💾
   - Cache Claude analyses (1 hour TTL)
   - Cache Perplexity research (7 days TTL)
   - Avoid duplicate API calls

---

### Phase 3: Network Gap Analysis (High Value)
**Goal:** Use Claude to identify hiring gaps

1. **Add Gap Analysis to Claude Engine** 🧠
   ```python
   # In claude_engine.py
   async def analyze_network_gaps(
       self,
       role: dict,
       network_stats: dict
   ) -> NetworkGapAnalysis:
       """Identify gaps in network for this role."""
       # Claude analyzes role vs. network
       # Returns: missing skills, target companies, etc.
   ```

2. **Surface Gaps in Curation** 📊
   - Show user when network is weak for a role
   - Suggest external search or outreach
   - Track gap closure over time

---

## Cost Optimization Strategy

### Current Costs (per role):
- **Curation Engine:**
  - PDL: 5 × $0.10 = $0.50
  - Claude: 5 × 4 agents × $0.0003 = $0.006
  - Perplexity: 5 × $0.005 = $0.025
  - **Total: ~$0.53**

- **Master Orchestrator:**
  - Claude query: 1 × $0.001 = $0.001
  - Claude analysis: 10 × 4 agents × $0.0003 = $0.012
  - External search: Varies (Clado/Pearch)
  - **Total: ~$0.013 + search costs**

### With Perplexity Added to Master Orchestrator:
- Perplexity: 5 × $0.005 = $0.025
- **New total: ~$0.038 + search costs**

### Optimization Strategies:

1. **Smart Caching** 💾
   ```python
   # Cache all Claude analyses
   - Key: candidate_id + role_id + version
   - TTL: 1 hour (same role), 1 week (any role)
   - Savings: 80% on re-curations
   ```

2. **Batch Processing** 📦
   ```python
   # Send multiple candidates to Claude in one request
   - Instead of: 5 requests × 4 agents = 20 API calls
   - Do: 1 request with 5 candidates × 4 agents = 4 API calls
   - Savings: 80% on API overhead
   ```

3. **Incremental Enrichment** 🔄
   ```python
   # Only enrich missing fields
   - Check what fields PDL has
   - Only request missing fields
   - Savings: 30-50% on PDL costs
   ```

4. **Conditional Deep Research** 🎯
   ```python
   # Only Perplexity if needed
   if candidate.data_completeness < 0.7:
       research = await perplexity_research(candidate)
   else:
       # Already have enough data
       skip_research()

   # Savings: 40-60% on Perplexity
   ```

---

## Migration Path

### Week 1: Enhance Current (Low Risk) ✅
- Add Perplexity to master orchestrator
- Add deduplication checks for Claude
- Align scoring weights
- **No breaking changes**

### Week 2: Unified Scoring Module 🔄
- Extract common logic to `app/services/scoring/`
- Update both flows to use it
- Add comprehensive tests
- **Minor API changes**

### Week 3: Network Gap Analysis 🚀
- Add gap analysis to Claude engine
- Integrate into curation flow
- Build UI for gap insights
- **New feature, no breaking changes**

### Week 4: Optimization & Monitoring 📊
- Implement caching layer
- Add batch processing
- Build cost monitoring dashboard
- **Performance improvements**

---

## Code Examples

### 1. Add Perplexity to Master Orchestrator

```python
# In master_orchestrator.py, after line 263

# Step 4.5: Deep Research with Perplexity (NEW)
if mode == "full" and settings.perplexity_api_key:
    print("\n4.5 Deep Research (Perplexity)...")
    features_used.append("perplexity_research")

    from app.services.research.perplexity_researcher import DeepResearchEngine
    research_engine = DeepResearchEngine(settings.perplexity_api_key)

    # Research top 5 candidates
    top_5_to_research = search_result.candidates[:5]

    enhanced_candidates = await research_engine.enhance_candidates(
        top_5_to_research,
        role_title=role_title,
        role_skills=required_skills,
        top_n=5
    )

    # Update candidates with research insights
    for i, enhanced in enumerate(enhanced_candidates):
        search_result.candidates[i] = enhanced

    print(f"   Researched {len(enhanced_candidates)} candidates")
else:
    print("\n4.5 Deep Research: Skipped")
```

### 2. Deduplicate Claude Analysis

```python
# In curation_engine.py, update _score_with_claude_reasoning()

async def _score_with_claude_reasoning(
    self,
    candidates: List[dict],
    role: dict,
    company_dna: dict,
    umo: Optional[dict]
) -> List[dict]:
    """Use Claude reasoning engine to re-score enriched candidates."""
    from app.services.reasoning.claude_engine import claude_engine

    if not settings.anthropic_api_key:
        print("⚠️  Claude API key not configured")
        for item in candidates:
            item['claude_score'] = item['fit_score']
            item['claude_confidence'] = item['confidence']
        return candidates

    # Filter out recently analyzed candidates
    recent_cutoff = datetime.now() - timedelta(hours=1)
    candidates_to_analyze = []
    cached_analyses = 0

    for item in candidates:
        c = item['candidate']

        # Check for recent analysis
        if (hasattr(c, 'claude_analyzed_at') and
            c.claude_analyzed_at and
            c.claude_analyzed_at > recent_cutoff):

            # Reuse cached analysis
            print(f"  ♻️  {c.full_name} (cached Claude analysis)")
            item['claude_score'] = c.claude_score
            item['claude_confidence'] = c.claude_confidence
            item['claude_reasoning'] = c.claude_reasoning
            cached_analyses += 1
        else:
            candidates_to_analyze.append(item)

    if cached_analyses > 0:
        print(f"  ♻️  Reused {cached_analyses} cached Claude analyses")

    # Analyze remaining candidates
    if not candidates_to_analyze:
        return candidates

    # ... rest of Claude analysis logic ...

    # After analysis, store timestamp
    for item in candidates_to_analyze:
        item['candidate'].claude_analyzed_at = datetime.now()

    return candidates
```

### 3. Unified Scoring Module (Future)

```python
# app/services/scoring/unified_scorer.py

from typing import List, Optional
from app.models.curation import UnifiedCandidate, CuratedCandidate

class UnifiedScoringPipeline:
    """
    Universal candidate scoring pipeline.

    Used by both master orchestrator and curation engine.
    """

    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.rule_scorer = RuleBasedScorer()
        self.claude_scorer = ClaudeReasoningScorer()
        self.perplexity_researcher = PerplexityResearcher()
        self.context_builder = ContextBuilder()

    async def score_and_enrich(
        self,
        candidates: List[UnifiedCandidate],
        role: dict,
        company_dna: dict,
        umo: Optional[dict],
        top_n: int = 5,
        skip_enrichment: bool = False
    ) -> List[CuratedCandidate]:
        """
        Full scoring pipeline.

        Steps:
        1. Rule-based scoring (all candidates)
        2. Rank by score
        3. Enrich top N with PDL (if needed)
        4. Claude reasoning on enriched
        5. Perplexity research on final top N
        6. Build rich context
        """

        # 1. Rule-based scoring
        scored = await self.rule_scorer.score_all(
            candidates, role, company_dna, umo
        )

        # 2. Rank
        ranked = sorted(scored, key=lambda x: x.score, reverse=True)

        # 3. Enrich top N
        top_n_candidates = ranked[:top_n]
        if not skip_enrichment:
            enriched = await self._enrich_with_pdl(top_n_candidates)
        else:
            enriched = top_n_candidates

        # 4. Claude reasoning
        claude_scored = await self.claude_scorer.score(
            enriched, role, company_dna, umo
        )

        # 5. Perplexity research
        researched = await self.perplexity_researcher.research(
            claude_scored, role
        )

        # 6. Build context
        final = await self.context_builder.build(
            researched, role, company_dna, umo
        )

        return final
```

---

## Summary & Recommendations

### ✅ Immediate Actions (Week 1)
1. **Add Perplexity to master orchestrator** - gives search results same depth
2. **Add Claude analysis deduplication** - avoid double-charging
3. **Document current architecture** - help team understand flows

### 🔄 Medium Term (Weeks 2-3)
1. **Extract unified scoring module** - reduce code duplication
2. **Implement caching layer** - save on API costs
3. **Add network gap analysis** - help users know when to search externally

### 🚀 Long Term (Month 2+)
1. **Optimize batch processing** - reduce API overhead
2. **Build cost monitoring** - track spend per feature
3. **A/B test scoring methods** - validate Claude improvements

### 💡 Key Insight
The current separation of flows (search vs. curation) makes sense architecturally, but the scoring/enrichment pipeline should be unified to ensure consistency and reduce costs.

**Recommended Approach:** Start with Option 1 (Unified Pipeline) but implement gradually using the migration path above.
