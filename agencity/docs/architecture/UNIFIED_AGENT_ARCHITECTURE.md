# Unified Agent Architecture: Hermes + Network Intelligence

## Dual-Source Candidate Discovery System

**Version 3.0** | Last Updated: February 12, 2026 | Status: Architecture Design

---

## 1. Executive Summary

This architecture unifies two candidate sources into a single intelligent agent:

| Source | Size | Data Quality | Opt-In Status |
|--------|------|--------------|---------------|
| **Hermes Database** | 1,375+ | High (verified, GitHub repos) | Opted-in |
| **LinkedIn Network** | 3,637+ | Medium (30% completeness) | Connected |

**Combined Pool**: ~5,000 unique candidates with intelligent deduplication

The agent uses **Proof Briefs** - structured reasoning artifacts that show the agent's thinking, evidence chain, and confidence levels for each recommendation.

---

## 2. System Architecture Overview

```
                                    SLACK INTERFACE
                                          │
                     ┌────────────────────┴────────────────────┐
                     │           @hermes mention               │
                     │         /hermes slash command           │
                     └────────────────────┬────────────────────┘
                                          │
                     ┌────────────────────▼────────────────────┐
                     │         CONVERSATION ENGINE             │
                     │  ┌─────────────────────────────────┐    │
                     │  │  Intent Classification          │    │
                     │  │  Role Blueprint Extraction      │    │
                     │  │  Clarifying Question Engine     │    │
                     │  └─────────────────────────────────┘    │
                     └────────────────────┬────────────────────┘
                                          │
                                          │ Role Blueprint
                                          │
                     ┌────────────────────▼────────────────────┐
                     │       UNIFIED SEARCH ORCHESTRATOR       │
                     │  ┌─────────────────────────────────┐    │
                     │  │  Source Router                  │    │
                     │  │  Parallel Query Executor        │    │
                     │  │  Deduplication Engine           │    │
                     │  └─────────────────────────────────┘    │
                     └────────────┬───────────────┬────────────┘
                                  │               │
               ┌──────────────────▼───┐       ┌───▼──────────────────┐
               │   HERMES SOURCE      │       │   NETWORK SOURCE     │
               │   (P0 - Highest)     │       │   (P1 - High)        │
               │  ┌───────────────┐   │       │  ┌───────────────┐   │
               │  │ 1,375+ opted  │   │       │  │ 3,637 LinkedIn│   │
               │  │ GitHub repos  │   │       │  │ connections   │   │
               │  │ Verified data │   │       │  │ Warmth paths  │   │
               │  └───────────────┘   │       │  └───────────────┘   │
               └──────────────────────┘       └──────────────────────┘
                                  │               │
                     ┌────────────┴───────────────┴────────────┐
                     │         UNIFIED CANDIDATE POOL          │
                     │              ~5,000 candidates          │
                     └────────────────────┬────────────────────┘
                                          │
                     ┌────────────────────▼────────────────────┐
                     │          REASONING ENGINE               │
                     │  ┌─────────────────────────────────┐    │
                     │  │  Multi-Factor Scoring           │    │
                     │  │  Confidence Calculation         │    │
                     │  │  Evidence Chain Builder         │    │
                     │  │  Proof Brief Generator          │    │
                     │  └─────────────────────────────────┘    │
                     └────────────────────┬────────────────────┘
                                          │
                     ┌────────────────────▼────────────────────┐
                     │       PROGRESSIVE ENRICHMENT            │
                     │  ┌─────────────────────────────────┐    │
                     │  │  Top 30 → Enrichment (PDL)      │    │
                     │  │  Top 5  → Deep Research (PPX)   │    │
                     │  │  Re-rank with new signals       │    │
                     │  └─────────────────────────────────┘    │
                     └────────────────────┬────────────────────┘
                                          │
                     ┌────────────────────▼────────────────────┐
                     │          SHORTLIST BUILDER              │
                     │  ┌─────────────────────────────────┐    │
                     │  │  10-15 candidates               │    │
                     │  │  Proof Brief per candidate      │    │
                     │  │  Warm path recommendations      │    │
                     │  │  Next steps per candidate       │    │
                     │  └─────────────────────────────────┘    │
                     └────────────────────┬────────────────────┘
                                          │
                     ┌────────────────────▼────────────────────┐
                     │           SLACK DELIVERY                │
                     │  ┌─────────────────────────────────┐    │
                     │  │  Formatted shortlist            │    │
                     │  │  Thread-based discussion        │    │
                     │  │  Interactive refinement         │    │
                     │  └─────────────────────────────────┘    │
                     └─────────────────────────────────────────┘
```

---

## 3. Data Source Integration

### 3.1 Source Priority & Quality Scoring

```python
SOURCE_CONFIG = {
    "hermes": {
        "priority": 0,           # Highest priority
        "quality_score": 0.95,   # Verified, opted-in
        "table": "candidates",   # Supabase table: candidates
        "strengths": [
            "GitHub repos available",
            "Skills verified",
            "Opted-in to be contacted",
            "University/education verified"
        ],
        "weaknesses": [
            "Smaller pool (1,375)",
            "May not have current company"
        ]
    },
    "network": {
        "priority": 1,           # High priority
        "quality_score": 0.70,   # Variable completeness
        "table": "people",       # Supabase table: people
        "strengths": [
            "Larger pool (3,637)",
            "Warm introduction paths",
            "Current employment known",
            "Network proximity"
        ],
        "weaknesses": [
            "30% average data completeness",
            "May need enrichment"
        ]
    }
}

# Both tables are in the SAME Supabase database
# - candidates: Hermes opted-in database (1,375+)
# - people: LinkedIn network connections (3,637)
```

### 3.2 Unified Candidate Model

```python
@dataclass
class UnifiedCandidate:
    # Identity (for deduplication)
    person_id: str
    linkedin_url: Optional[str]
    github_url: Optional[str]
    email: Optional[str]

    # Basic Info
    full_name: str
    headline: Optional[str]
    location: Optional[str]

    # Current Position
    current_company: Optional[str]
    current_title: Optional[str]
    tenure_months: Optional[int]

    # Skills & Experience
    skills: List[str]
    experience: List[Experience]
    education: List[Education]

    # Source Metadata
    sources: List[str]          # ["hermes", "network"]
    primary_source: str         # Best quality source
    source_quality: float       # 0-1, from best source

    # Network Intelligence (from network source)
    is_direct_connection: bool
    warmth_score: float         # 0-1
    warm_path: Optional[WarmPath]

    # Hermes Intelligence (from hermes source)
    github_repos: List[GitHubRepo]
    opted_in: bool

    # Computed Scores
    data_completeness: float    # 0-1
    needs_enrichment: bool

    # Enrichment Data (populated on-demand)
    enrichment: Optional[EnrichmentData]
    deep_research: Optional[DeepResearchData]
```

### 3.3 Deduplication Strategy

```python
class DeduplicationEngine:
    """
    Merges candidates found in both sources.
    Priority: LinkedIn URL > Email > GitHub URL > Name (fuzzy)
    """

    def deduplicate(
        self,
        hermes_candidates: List[Candidate],
        network_candidates: List[Candidate]
    ) -> List[UnifiedCandidate]:

        unified = {}

        # Index Hermes candidates (higher priority)
        for c in hermes_candidates:
            key = self._get_key(c)
            unified[key] = self._to_unified(c, source="hermes")

        # Merge network candidates
        for c in network_candidates:
            key = self._get_key(c)
            if key in unified:
                # Merge: combine data from both sources
                unified[key] = self._merge(unified[key], c)
            else:
                unified[key] = self._to_unified(c, source="network")

        return list(unified.values())

    def _merge(
        self,
        existing: UnifiedCandidate,
        new: Candidate
    ) -> UnifiedCandidate:
        """Merges two records, preferring verified data."""

        existing.sources.append("network")

        # Add network-specific intelligence
        existing.is_direct_connection = new.is_from_network
        existing.warmth_score = new.warmth_score or 0.5
        existing.warm_path = new.warm_path

        # Merge skills (union)
        existing.skills = list(set(existing.skills + new.skills))

        # Use network data for current position if Hermes missing
        if not existing.current_company and new.current_company:
            existing.current_company = new.current_company
            existing.current_title = new.current_title

        # Boost quality score for multi-source candidates
        existing.source_quality = min(1.0, existing.source_quality + 0.1)

        return existing
```

---

## 4. Agent Reasoning System

### 4.1 Proof Brief Structure

The agent generates a **Proof Brief** for each candidate - a structured reasoning artifact that shows evidence and confidence.

```python
@dataclass
class ProofBrief:
    """
    Structured reasoning artifact showing the agent's evaluation.
    Designed for founder review and decision-making.
    """

    candidate_id: str
    candidate_name: str

    # Overall Assessment
    recommendation: Literal["strong_consider", "consider", "weak_consider", "pass"]
    confidence: float           # 0-1
    match_score: float          # 0-100

    # Evidence Chain
    known_facts: List[Evidence]     # Verified, high-confidence
    observed_signals: List[Signal]  # Inferred, medium-confidence
    unknowns: List[Unknown]         # Gaps that need verification

    # Reasoning Trace
    reasoning_chain: List[ReasoningStep]

    # Action Items
    warm_path: Optional[WarmPath]
    suggested_next_step: str
    outreach_message: Optional[str]

    # Source Attribution
    sources_used: List[str]
    data_freshness: datetime


@dataclass
class Evidence:
    """A verified fact about the candidate."""
    fact: str
    source: str                 # "hermes", "network", "github", "perplexity"
    confidence: float           # 0-1
    verification_method: str    # "github_api", "linkedin_profile", "opted_in"


@dataclass
class Signal:
    """An inferred signal (not directly verified)."""
    observation: str
    inference: str
    strength: Literal["strong", "medium", "weak"]
    could_be_wrong_because: str


@dataclass
class Unknown:
    """A gap in our knowledge."""
    what_we_dont_know: str
    why_it_matters: str
    how_to_find_out: str


@dataclass
class ReasoningStep:
    """A step in the agent's reasoning chain."""
    step_number: int
    thought: str
    action: str
    observation: str
    conclusion: str
```

### 4.2 Reasoning Engine

```python
class ReasoningEngine:
    """
    Multi-factor reasoning engine that generates Proof Briefs.
    Shows its work at every step.
    """

    SCORING_WEIGHTS = {
        "skills_match": 0.30,       # Technical fit
        "experience_match": 0.25,   # Seniority & relevance
        "source_quality": 0.15,     # Data trustworthiness
        "network_proximity": 0.15,  # Warm path availability
        "readiness_signals": 0.10,  # Likely to be interested
        "culture_signals": 0.05,    # Startup fit indicators
    }

    async def evaluate(
        self,
        candidate: UnifiedCandidate,
        role: RoleBlueprint,
        company: CompanyContext
    ) -> ProofBrief:

        reasoning_chain = []

        # Step 1: Skills Analysis
        skills_result = self._analyze_skills(candidate, role)
        reasoning_chain.append(ReasoningStep(
            step_number=1,
            thought=f"Analyzing skill overlap for {candidate.full_name}",
            action="Compare candidate skills to role requirements",
            observation=f"Found {skills_result.overlap_count}/{len(role.required_skills)} required skills",
            conclusion=skills_result.summary
        ))

        # Step 2: Experience Analysis
        exp_result = self._analyze_experience(candidate, role)
        reasoning_chain.append(ReasoningStep(
            step_number=2,
            thought="Evaluating experience relevance and seniority",
            action="Match job history to role requirements",
            observation=exp_result.observation,
            conclusion=exp_result.summary
        ))

        # Step 3: Source Quality Assessment
        source_result = self._assess_sources(candidate)
        reasoning_chain.append(ReasoningStep(
            step_number=3,
            thought="Assessing data quality and trustworthiness",
            action="Check source origins and verification status",
            observation=f"Sources: {candidate.sources}, Quality: {source_result.score:.2f}",
            conclusion=source_result.summary
        ))

        # Step 4: Network Proximity
        network_result = self._analyze_network(candidate)
        reasoning_chain.append(ReasoningStep(
            step_number=4,
            thought="Determining warm path availability",
            action="Check connection status and introduction paths",
            observation=network_result.observation,
            conclusion=network_result.summary
        ))

        # Step 5: Readiness Signals
        readiness_result = self._analyze_readiness(candidate)
        reasoning_chain.append(ReasoningStep(
            step_number=5,
            thought="Looking for signals they might be open to opportunities",
            action="Check tenure, company situation, profile activity",
            observation=readiness_result.observation,
            conclusion=readiness_result.summary
        ))

        # Step 6: Calculate Final Score
        final_score = self._calculate_final_score(
            skills=skills_result.score,
            experience=exp_result.score,
            source_quality=source_result.score,
            network=network_result.score,
            readiness=readiness_result.score,
            culture=self._analyze_culture(candidate, company).score
        )

        # Step 7: Generate Recommendation
        recommendation = self._get_recommendation(final_score)
        confidence = self._calculate_confidence(candidate)

        # Build Evidence Chain
        known_facts = self._extract_known_facts(candidate, role)
        observed_signals = self._extract_signals(candidate, role)
        unknowns = self._identify_unknowns(candidate, role)

        return ProofBrief(
            candidate_id=candidate.person_id,
            candidate_name=candidate.full_name,
            recommendation=recommendation,
            confidence=confidence,
            match_score=final_score,
            known_facts=known_facts,
            observed_signals=observed_signals,
            unknowns=unknowns,
            reasoning_chain=reasoning_chain,
            warm_path=candidate.warm_path,
            suggested_next_step=self._get_next_step(candidate, recommendation),
            outreach_message=self._generate_outreach(candidate, role) if recommendation != "pass" else None,
            sources_used=candidate.sources,
            data_freshness=datetime.utcnow()
        )
```

### 4.3 Confidence Calculation

```python
class ConfidenceCalculator:
    """
    Calculates confidence in our assessment.
    Low confidence triggers enrichment.
    """

    def calculate(self, candidate: UnifiedCandidate) -> float:
        """Returns confidence score 0-1."""

        factors = []

        # Data completeness (40% of confidence)
        completeness_score = candidate.data_completeness
        factors.append(("completeness", completeness_score, 0.40))

        # Source quality (30% of confidence)
        source_score = candidate.source_quality
        factors.append(("source_quality", source_score, 0.30))

        # Multi-source bonus (15% of confidence)
        multi_source = 1.0 if len(candidate.sources) > 1 else 0.5
        factors.append(("multi_source", multi_source, 0.15))

        # Verification status (15% of confidence)
        verification = self._verification_score(candidate)
        factors.append(("verification", verification, 0.15))

        confidence = sum(score * weight for _, score, weight in factors)

        return min(1.0, max(0.0, confidence))

    def _verification_score(self, candidate: UnifiedCandidate) -> float:
        score = 0.0

        if candidate.opted_in:
            score += 0.4  # Hermes opted-in
        if candidate.github_repos:
            score += 0.3  # GitHub verified
        if candidate.linkedin_url:
            score += 0.2  # LinkedIn present
        if candidate.is_direct_connection:
            score += 0.1  # Direct network connection

        return min(1.0, score)
```

---

## 5. Search Orchestration

### 5.1 Unified Search Flow

```python
class UnifiedSearchOrchestrator:
    """
    Orchestrates search across both sources.
    Returns unified, deduplicated, scored candidates.
    """

    async def search(
        self,
        role: RoleBlueprint,
        company_id: str,
        limit: int = 100
    ) -> SearchResult:

        # Step 1: Parallel search both sources
        hermes_task = self._search_hermes(role, limit)
        network_task = self._search_network(role, company_id, limit)

        hermes_results, network_results = await asyncio.gather(
            hermes_task, network_task
        )

        # Step 2: Deduplicate
        unified = self.deduplication_engine.deduplicate(
            hermes_results, network_results
        )

        # Step 3: Initial scoring (pre-enrichment)
        scored = []
        for candidate in unified:
            brief = await self.reasoning_engine.evaluate(
                candidate, role, self.company_context
            )
            scored.append((candidate, brief))

        # Step 4: Sort by score
        scored.sort(key=lambda x: x[1].match_score, reverse=True)

        # Step 5: Progressive enrichment
        top_30 = scored[:30]
        top_30_enriched = await self._enrich_batch(top_30)

        # Step 6: Deep research top 5
        top_5 = top_30_enriched[:5]
        top_5_researched = await self._deep_research_batch(top_5)

        # Step 7: Re-score with enriched data
        final_scored = []
        for candidate, brief in top_5_researched + top_30_enriched[5:]:
            updated_brief = await self.reasoning_engine.evaluate(
                candidate, role, self.company_context
            )
            final_scored.append((candidate, updated_brief))

        # Step 8: Final sort and return
        final_scored.sort(key=lambda x: x[1].match_score, reverse=True)

        return SearchResult(
            candidates=final_scored[:limit],
            total_searched=len(unified),
            hermes_count=len(hermes_results),
            network_count=len(network_results),
            deduplicated_count=len(unified) - (len(hermes_results) + len(network_results) - len(unified)),
            enriched_count=min(30, len(unified)),
            researched_count=min(5, len(unified))
        )

    async def _search_hermes(
        self,
        role: RoleBlueprint,
        limit: int
    ) -> List[Candidate]:
        """Search the `candidates` table (1,375+ opted-in Hermes candidates)."""

        query = self.supabase.table("candidates").select("*")

        # Skill matching
        if role.required_skills:
            skill_filter = " | ".join(f"skills.ilike.%{s}%" for s in role.required_skills)
            query = query.or_(skill_filter)

        # Location if specified
        if role.locations:
            query = query.in_("location", role.locations)

        results = query.limit(limit).execute()

        return [self._to_candidate(r, source="hermes") for r in results.data]

    async def _search_network(
        self,
        role: RoleBlueprint,
        company_id: str,
        limit: int
    ) -> List[Candidate]:
        """Search the `people` table (3,637 LinkedIn connections)."""

        query = self.supabase.table("people").select("""
            *,
            person_enrichments(*)
        """).eq("company_id", company_id)

        # Title matching
        if role.title:
            query = query.ilike("current_title", f"%{role.title}%")

        results = query.limit(limit).execute()

        return [self._to_candidate(r, source="network") for r in results.data]
```

### 5.2 Tiered Results Structure

```python
class TieredSearchResult:
    """
    Search results organized by warmth and recommendation strength.
    """

    # Tier 1: Direct network + opted-in Hermes candidates
    tier_1_warm_ready: List[Tuple[UnifiedCandidate, ProofBrief]]

    # Tier 2: One introduction away
    tier_2_warm_intro: List[Tuple[UnifiedCandidate, ProofBrief]]

    # Tier 3: Hermes only (opted-in but no network connection)
    tier_3_hermes_cold: List[Tuple[UnifiedCandidate, ProofBrief]]

    # Tier 4: Network only (need enrichment/verification)
    tier_4_network_cold: List[Tuple[UnifiedCandidate, ProofBrief]]

    # Metadata
    search_duration_seconds: float
    recommendation: str  # What the agent recommends doing first
```

---

## 6. Shortlist Generation

### 6.1 Shortlist Builder

```python
class ShortlistBuilder:
    """
    Builds a 10-15 candidate shortlist with Proof Briefs.
    """

    def build(
        self,
        search_results: TieredSearchResult,
        target_size: int = 12
    ) -> Shortlist:

        shortlist = []

        # Priority 1: Warm + Ready (50% of shortlist)
        warm_ready_count = int(target_size * 0.50)
        shortlist.extend(search_results.tier_1_warm_ready[:warm_ready_count])

        # Priority 2: Warm Intro (30% of shortlist)
        warm_intro_count = int(target_size * 0.30)
        shortlist.extend(search_results.tier_2_warm_intro[:warm_intro_count])

        # Priority 3: Hermes Cold (15% of shortlist)
        hermes_cold_count = int(target_size * 0.15)
        shortlist.extend(search_results.tier_3_hermes_cold[:hermes_cold_count])

        # Fill remaining with best from any tier
        remaining = target_size - len(shortlist)
        all_remaining = (
            search_results.tier_1_warm_ready[warm_ready_count:] +
            search_results.tier_2_warm_intro[warm_intro_count:] +
            search_results.tier_3_hermes_cold[hermes_cold_count:] +
            search_results.tier_4_network_cold
        )
        all_remaining.sort(key=lambda x: x[1].match_score, reverse=True)
        shortlist.extend(all_remaining[:remaining])

        return Shortlist(
            candidates=shortlist,
            generated_at=datetime.utcnow(),
            methodology=self._explain_methodology(),
            total_pool_searched=self._get_pool_size(search_results)
        )

    def format_for_slack(self, shortlist: Shortlist) -> List[dict]:
        """Format shortlist for Slack delivery."""

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"Shortlist: {len(shortlist.candidates)} candidates"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"_Searched {shortlist.total_pool_searched} candidates across Hermes + Network_"
                }
            },
            {"type": "divider"}
        ]

        for i, (candidate, brief) in enumerate(shortlist.candidates, 1):
            blocks.extend(self._format_candidate_block(i, candidate, brief))

        return blocks

    def _format_candidate_block(
        self,
        rank: int,
        candidate: UnifiedCandidate,
        brief: ProofBrief
    ) -> List[dict]:
        """Format a single candidate for Slack."""

        # Confidence indicator
        confidence_emoji = "🟢" if brief.confidence > 0.7 else "🟡" if brief.confidence > 0.4 else "🔴"

        # Source badges
        source_badges = []
        if "hermes" in candidate.sources:
            source_badges.append("📋 Hermes")
        if "network" in candidate.sources:
            source_badges.append("🔗 Network")
        if len(candidate.sources) > 1:
            source_badges.append("✨ Multi-source")

        return [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*#{rank} - {candidate.full_name}*\n"
                        f"{candidate.current_title or 'Unknown'} @ {candidate.current_company or 'Unknown'}\n"
                        f"Score: {brief.match_score:.0f}/100 {confidence_emoji} ({brief.confidence:.0%} confidence)\n"
                        f"_{' | '.join(source_badges)}_"
                    )
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": self._format_proof_brief_summary(brief)
                }
            },
            {"type": "divider"}
        ]

    def _format_proof_brief_summary(self, brief: ProofBrief) -> str:
        """Format Proof Brief as Slack message."""

        lines = []

        # Known Facts (top 3)
        if brief.known_facts:
            facts = brief.known_facts[:3]
            lines.append("*Known Facts:*")
            for fact in facts:
                lines.append(f"  • {fact.fact}")

        # Key Signals
        if brief.observed_signals:
            strong_signals = [s for s in brief.observed_signals if s.strength == "strong"][:2]
            if strong_signals:
                lines.append("*Key Signals:*")
                for signal in strong_signals:
                    lines.append(f"  • {signal.observation}")

        # Top Unknown
        if brief.unknowns:
            lines.append(f"*Unknown:* {brief.unknowns[0].what_we_dont_know}")

        # Warm Path
        if brief.warm_path:
            lines.append(f"*Warm Path:* {brief.warm_path.description}")

        # Next Step
        lines.append(f"*Next Step:* {brief.suggested_next_step}")

        return "\n".join(lines)
```

---

## 7. Slack Integration

### 7.1 Updated Slack Handler

```python
class HermesSlackBot:
    """
    Slack bot that uses unified search and delivers shortlists.
    """

    async def handle_mention(
        self,
        channel: str,
        thread_ts: str,
        user_id: str,
        text: str
    ):
        # Add thinking reaction
        await self.slack.reactions_add(
            channel=channel,
            timestamp=thread_ts,
            name="thinking_face"
        )

        try:
            # Get or create conversation context
            context = await self.conversation_engine.get_context(
                channel, thread_ts
            )

            # Process message through conversation engine
            response = await self.conversation_engine.process(
                context=context,
                message=text,
                user_id=user_id
            )

            if response.needs_clarification:
                # Ask clarifying questions
                await self.slack.chat_postMessage(
                    channel=channel,
                    thread_ts=thread_ts,
                    text=response.question
                )

            elif response.role_blueprint:
                # We have enough info - run search
                await self._run_search_and_deliver(
                    channel=channel,
                    thread_ts=thread_ts,
                    role=response.role_blueprint,
                    company_id=context.company_id
                )

            # Success reaction
            await self.slack.reactions_add(
                channel=channel,
                timestamp=thread_ts,
                name="white_check_mark"
            )

        except Exception as e:
            await self.slack.reactions_add(
                channel=channel,
                timestamp=thread_ts,
                name="x"
            )
            await self.slack.chat_postMessage(
                channel=channel,
                thread_ts=thread_ts,
                text=f"Something went wrong: {str(e)}"
            )

    async def _run_search_and_deliver(
        self,
        channel: str,
        thread_ts: str,
        role: RoleBlueprint,
        company_id: str
    ):
        # Status update
        await self.slack.chat_postMessage(
            channel=channel,
            thread_ts=thread_ts,
            text=f"Searching ~5,000 candidates (Hermes + Network) for: *{role.title}*..."
        )

        # Run unified search
        search_results = await self.search_orchestrator.search(
            role=role,
            company_id=company_id,
            limit=100
        )

        # Build shortlist
        shortlist = self.shortlist_builder.build(
            search_results=search_results,
            target_size=12
        )

        # Format for Slack
        blocks = self.shortlist_builder.format_for_slack(shortlist)

        # Deliver
        await self.slack.chat_postMessage(
            channel=channel,
            thread_ts=thread_ts,
            blocks=blocks,
            text=f"Found {len(shortlist.candidates)} candidates"  # Fallback
        )

        # Summary stats
        stats_text = (
            f"_Search complete:_\n"
            f"• Hermes candidates searched: {search_results.hermes_count}\n"
            f"• Network candidates searched: {search_results.network_count}\n"
            f"• Duplicates merged: {search_results.deduplicated_count}\n"
            f"• Top 30 enriched, Top 5 deep researched\n"
            f"• Time: {search_results.search_duration_seconds:.1f}s_"
        )

        await self.slack.chat_postMessage(
            channel=channel,
            thread_ts=thread_ts,
            text=stats_text
        )
```

### 7.2 Conversation Flow

```
User: @hermes I need a prompt engineer for my AI startup

Hermes: I'll help you find prompt engineers. A few quick questions:
        1. What does your startup do specifically?
        2. What will this person work on day-to-day?
        3. Any must-have skills or background?

User: We're building a RAG-based writing assistant. They'll design
      prompts and improve output quality. Need someone with LLM experience.

Hermes: Got it. Searching ~5,000 candidates (Hermes + Network) for:
        *Prompt Engineer*...

        [60 seconds later]

        Shortlist: 12 candidates
        _Searched 4,892 candidates across Hermes + Network_
        ─────────────────────────────

        #1 - Sarah Chen
        ML Engineer @ OpenAI
        Score: 87/100 🟢 (85% confidence)
        _📋 Hermes | 🔗 Network | ✨ Multi-source_

        *Known Facts:*
          • 3 years prompt engineering at OpenAI
          • Published papers on LLM optimization
          • MIT CS grad, focus on NLP

        *Key Signals:*
          • Recently updated LinkedIn (may be exploring)
          • GitHub active with prompt engineering repos

        *Unknown:* Current compensation expectations

        *Warm Path:* Connected via John (worked together at Google)

        *Next Step:* Ask John for intro, mention RAG project
        ─────────────────────────────

        [... 11 more candidates ...]

        _Search complete:_
        • Hermes candidates searched: 1,375
        • Network candidates searched: 3,637
        • Duplicates merged: 120
        • Top 30 enriched, Top 5 deep researched
        • Time: 47.3s
```

---

## 8. Database Schema Updates

### 8.1 New Tables Required

```sql
-- Track candidates that appear in both sources
CREATE TABLE candidate_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hermes_candidate_id UUID REFERENCES candidates(id),
    network_person_id UUID REFERENCES people(id),
    link_method TEXT,  -- 'linkedin', 'email', 'github', 'name_match'
    link_confidence FLOAT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Store Proof Briefs for audit trail
CREATE TABLE proof_briefs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID,
    source TEXT,  -- 'hermes' or 'network'
    role_id UUID REFERENCES roles(id),
    recommendation TEXT,
    confidence FLOAT,
    match_score FLOAT,
    known_facts JSONB,
    observed_signals JSONB,
    unknowns JSONB,
    reasoning_chain JSONB,
    warm_path JSONB,
    suggested_next_step TEXT,
    sources_used TEXT[],
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Track search sessions for analytics
CREATE TABLE search_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id),
    role_id UUID REFERENCES roles(id),
    slack_channel TEXT,
    slack_thread_ts TEXT,
    hermes_searched INT,
    network_searched INT,
    duplicates_merged INT,
    shortlist_size INT,
    duration_seconds FLOAT,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 9. Configuration

### 9.1 Environment Variables

```bash
# Supabase (single database - both sources)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=xxx

# APIs
OPENAI_API_KEY=xxx
PERPLEXITY_API_KEY=xxx

# Slack
SLACK_BOT_TOKEN=xoxb-xxx
SLACK_SIGNING_SECRET=xxx

# Search tuning
SEARCH_HERMES_WEIGHT=0.95      # Source quality weight
SEARCH_NETWORK_WEIGHT=0.70
ENRICHMENT_TOP_N=30
DEEP_RESEARCH_TOP_N=5
SHORTLIST_SIZE=12
```

### 9.2 Tunable Parameters

```python
AGENT_CONFIG = {
    # Scoring weights
    "scoring": {
        "skills_match": 0.30,
        "experience_match": 0.25,
        "source_quality": 0.15,
        "network_proximity": 0.15,
        "readiness_signals": 0.10,
        "culture_signals": 0.05,
    },

    # Confidence thresholds
    "confidence": {
        "high": 0.7,           # Show as 🟢
        "medium": 0.4,         # Show as 🟡
        "low": 0.0,            # Show as 🔴
        "enrich_threshold": 0.6  # Trigger enrichment below this
    },

    # Shortlist composition
    "shortlist": {
        "target_size": 12,
        "tier_1_pct": 0.50,    # Warm + Ready
        "tier_2_pct": 0.30,    # Warm Intro
        "tier_3_pct": 0.15,    # Hermes Cold
        "tier_4_pct": 0.05,    # Network Cold
    },

    # Enrichment limits
    "enrichment": {
        "batch_size": 30,
        "deep_research_size": 5,
        "timeout_seconds": 60
    }
}
```

---

## 10. Implementation Roadmap

### Phase 1: Data Integration (Week 1)
- [ ] Create `candidate_links` table
- [ ] Implement `DeduplicationEngine`
- [ ] Test deduplication with real data
- [ ] Verify ~120 expected duplicates between sources

### Phase 2: Reasoning Engine (Week 2)
- [ ] Implement `ProofBrief` data model
- [ ] Build `ReasoningEngine` with scoring
- [ ] Add `ConfidenceCalculator`
- [ ] Test with sample candidates

### Phase 3: Search Orchestration (Week 3)
- [ ] Implement `UnifiedSearchOrchestrator`
- [ ] Add parallel search execution
- [ ] Integrate progressive enrichment
- [ ] Test end-to-end search flow

### Phase 4: Shortlist & Slack (Week 4)
- [ ] Build `ShortlistBuilder`
- [ ] Create Slack block formatters
- [ ] Update `HermesSlackBot` with new flow
- [ ] Test full Slack integration

### Phase 5: Tuning & Polish (Week 5)
- [ ] A/B test scoring weights
- [ ] Gather founder feedback
- [ ] Tune confidence thresholds
- [ ] Add analytics tracking

---

## Related Documentation

| Document | Purpose |
|----------|---------|
| [IMPLEMENTATION_GUIDE.md](../IMPLEMENTATION_GUIDE.md) | End-to-end code implementation |
| [SLACK_SETUP.md](../slack/SLACK_SETUP.md) | Slack bot configuration |
| [AGENCITY_ARCHITECTURE.md](./AGENCITY_ARCHITECTURE.md) | Original system (V1-V2) |

---

## Version History

- **v3.0** (Feb 12, 2026): Unified Agent Architecture designed
  - Dual-source search (Hermes + Network)
  - Proof Brief reasoning system
  - Shortlist delivery via Slack
  - Confidence-based progressive enrichment

---

*Architecture by: Agencity Team*
*Combined Pool: ~5,000 candidates | Two sources unified | Agent reasoning with Proof Briefs*
