# Agencity: Proactive End-to-End Hiring Agent

## Vision

Build a hiring agent that doesn't just search—it **knows**. It understands the company, the founders, their network, and proactively surfaces the right people at the right time.

---

## Part 1: The Data Collection Problem

### Data Sources You Mentioned

| # | Source | What We Get | How to Collect |
|---|--------|-------------|----------------|
| 1 | **Chatbot Intake** | Company needs, role requirements, success criteria | Conversation engine (built) |
| 2 | **Company UMO** | What makes them unique, culture, mission | Intake + website scraping |
| 3 | **Founder UMO** | Founder background, vision, hiring philosophy | LinkedIn + intake |
| 4 | **Founder Network** | Warm connections, trust relationships | LinkedIn API, contacts import |
| 5 | **Our Candidate DB** | Opted-in candidates with full profiles | Direct database |
| 6 | **Company Network** | Team members, investors, advisors | LinkedIn + intake |
| 7 | **Company's Candidate DB** | Their ATS, past applicants | ATS integration (Lever, Greenhouse) |

### Additional Data Sources to Consider

**Company Intelligence:**
| Source | What We Learn |
|--------|---------------|
| Company's **existing team** | What's working? Who are their best hires? |
| Company's **codebase/product** | Tech stack, complexity, what skills actually needed |
| Company's **hiring history** | Who succeeded? Who churned? Why? |
| Company's **investors** | Warm intro paths, portfolio company talent pools |
| Company's **customers** | Enterprise customers often refer talent |
| Company's **competitors** | Where do their employees come from/go to? |
| Company's **content** | Blog posts, open source, technical reputation |
| **Y Combinator batch** | Batch mates = trusted network |
| **Glassdoor/LinkedIn** | Culture signals, employee sentiment |

**Candidate Intelligence:**
| Source | What We Learn |
|--------|---------------|
| **Work history graph** | Who did they work WITH? (not just where) |
| **Education network** | Classmates, professors, research groups |
| **Open source graph** | Collaborators, maintainers, contributors |
| **Content/writing** | Thought leadership, communication skills |
| **Reference network** | Who vouches for them? |
| **Application history** | Where else have they looked? |
| **Career trajectory** | Where are they going, not just where they've been |

**Market Intelligence:**
| Source | What We Learn |
|--------|---------------|
| **Job change signals** | LinkedIn updates, GitHub activity changes |
| **Layoff announcements** | Talent suddenly available |
| **Funding announcements** | Companies hiring = candidates leaving |
| **Conference attendees** | Who's active in the community |
| **Visa/relocation signals** | Candidates open to moving |

---

## Part 2: The Graph Network Architecture

### Why a Graph?

Traditional search: "Find me Python developers in SF"
Graph-powered search: "Find me people who worked with someone I trust, shipped production ML systems, and are 2 hops from my investor's portfolio"

**The graph lets us capture:**
- Relationships (who knows who)
- Trust propagation (friend of a friend)
- Career trajectories (paths through companies)
- Skill inference (worked on X → probably knows Y)
- Hidden gems (talented but not famous)

### Entity Types (Nodes)

```
┌─────────────────────────────────────────────────────────────────┐
│                         GRAPH ENTITIES                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  PEOPLE                    ORGANIZATIONS                        │
│  ├── Candidates            ├── Companies                        │
│  ├── Founders              ├── Schools                          │
│  ├── Employees             ├── Investors (firms)                │
│  ├── Investors (people)    ├── Accelerators                     │
│  └── Advisors              └── Communities                      │
│                                                                  │
│  ARTIFACTS                 CONCEPTS                             │
│  ├── Projects              ├── Skills                           │
│  ├── Repos                 ├── Technologies                     │
│  ├── Papers                ├── Industries                       │
│  ├── Blog posts            ├── Roles                            │
│  └── Products              └── Locations                        │
│                                                                  │
│  EVENTS                                                          │
│  ├── Jobs (positions)                                           │
│  ├── Hackathons                                                 │
│  ├── Conferences                                                │
│  └── Courses                                                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Relationship Types (Edges)

```
PERSON relationships:
├── WORKS_AT (person → company) [current/past, role, dates]
├── STUDIED_AT (person → school) [degree, dates, field]
├── KNOWS (person → person) [strength, source, recency]
├── WORKED_WITH (person → person) [company, duration, overlap]
├── STUDIED_WITH (person → person) [school, years]
├── COLLABORATED_ON (person → project) [role, contribution]
├── HAS_SKILL (person → skill) [level, evidence]
├── REFERRED (person → person) [outcome]
├── INTERVIEWED_AT (person → company) [outcome, feedback]
└── REPORTS_TO (person → person) [company]

COMPANY relationships:
├── INVESTED_BY (company → investor)
├── BATCH_MATE (company → company) [accelerator, batch]
├── COMPETES_WITH (company → company)
├── PARTNERS_WITH (company → company)
├── ACQUIRED (company → company)
└── USES_TECH (company → technology)

TRUST/SIGNAL edges:
├── VOUCHES_FOR (person → person) [strength]
├── RECOMMENDED (person → person) [job]
└── HIRED (company → person) [success_score]
```

### Edge Properties (The Secret Sauce)

Every edge has:

```python
class Edge:
    # Core
    source: Node
    target: Node
    relationship: str

    # Strength & Trust
    weight: float          # 0-1, strength of connection
    trust_score: float     # How verified is this relationship?
    evidence: list[str]    # What proves this relationship?

    # Temporal
    start_date: date
    end_date: date | None
    last_interaction: date
    decay_rate: float      # How fast does this relationship fade?

    # Context
    context: str           # How do they know each other?
    source_type: str       # linkedin, manual, inferred
```

### Graph Database Options

| Option | Pros | Cons |
|--------|------|------|
| **Neo4j** | Best query language (Cypher), mature | Expensive at scale |
| **Amazon Neptune** | Managed, scalable | AWS lock-in |
| **TigerGraph** | Fast for deep traversals | Complex |
| **PostgreSQL + pgvector + ltree** | Simple, already using | Not a true graph DB |
| **Dgraph** | GraphQL native | Less mature |

**Recommendation:** Start with PostgreSQL + adjacency tables + pgvector for embeddings. Migrate to Neo4j when graph queries become complex.

---

## Part 3: The Graph as "Neural Network Memory"

### What You're Describing

You want the graph to work like a neural network's memory—where information propagates, connections strengthen with use, and the system "learns" what matters.

### Implementation: Graph Neural Network (GNN) Layer

```
┌─────────────────────────────────────────────────────────────────┐
│                    GRAPH MEMORY SYSTEM                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Layer 1: RAW GRAPH                                             │
│  ├── Entities as nodes                                          │
│  ├── Relationships as edges                                     │
│  └── Properties as attributes                                   │
│                                                                  │
│  Layer 2: EMBEDDINGS                                            │
│  ├── Each node has a vector embedding                          │
│  ├── Embeddings trained on graph structure + text              │
│  ├── Similar nodes are close in embedding space                │
│  └── Used for semantic similarity search                        │
│                                                                  │
│  Layer 3: PROPAGATION                                           │
│  ├── Trust propagates through edges                            │
│  ├── Skills inferred from neighbors                            │
│  ├── Company culture inferred from employees                   │
│  └── PageRank-style influence scores                           │
│                                                                  │
│  Layer 4: LEARNING                                              │
│  ├── Successful hires strengthen paths                         │
│  ├── Churned hires weaken paths                                │
│  ├── User feedback updates edge weights                        │
│  └── Model fine-tunes on outcomes                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Algorithms

1. **Node Embedding** (Node2Vec, GraphSAGE)
   - Learn vector representations of entities
   - Capture structural + semantic similarity

2. **Link Prediction**
   - Predict missing edges (who SHOULD know who?)
   - Find hidden connections

3. **Trust Propagation** (like PageRank)
   - A trusts B, B trusts C → A has some trust in C
   - Decay with distance

4. **Path Ranking**
   - Find best paths from company → candidate
   - Weight by trust, recency, relevance

5. **Collaborative Filtering**
   - Companies similar to you hired these people
   - Candidates similar to your best hires

---

## Part 4: Enhanced People Search (Leveraging the Graph)

### Current Search (What Everyone Does)

```
Query: "Python developer in SF"
     ↓
LinkedIn/GitHub API
     ↓
Keyword matching
     ↓
Results (mostly noise)
```

### Graph-Enhanced Search (What We Do)

```
Query: "I need a backend engineer"
     ↓
┌─────────────────────────────────────────────────────────────────┐
│                     SEARCH STRATEGY                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. WARM PATHS (highest priority)                               │
│     └── People reachable through founder's network              │
│     └── 1-hop: Direct connections                               │
│     └── 2-hop: Friend of friend                                 │
│     └── 3-hop: Extended network                                 │
│                                                                  │
│  2. SIMILAR TRAJECTORIES                                        │
│     └── Find your best engineers                                │
│     └── Find people with similar career paths                   │
│     └── "Engineers who went Stripe → Series A startup"          │
│                                                                  │
│  3. TALENT POOLS                                                │
│     └── Companies known for great engineers                     │
│     └── Schools with strong programs                            │
│     └── Communities (open source, hackathons)                   │
│                                                                  │
│  4. HIDDEN GEMS                                                 │
│     └── High graph centrality but low visibility                │
│     └── Strong collaborators of known good engineers            │
│     └── Recent graduates of great engineers' schools            │
│                                                                  │
│  5. EXTERNAL SEARCH (fallback)                                  │
│     └── GitHub, LinkedIn, etc.                                  │
│     └── But RANK results by graph proximity                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### What Makes Us Better Than LinkedIn Recruiter

| LinkedIn | Agencity |
|----------|----------|
| Keyword matching | Semantic + Graph understanding |
| Generic "connections" | Trust-weighted paths |
| No context about YOUR company | Deep company understanding |
| Static profiles | Dynamic signals (activity, job changes) |
| No warm intro paths | Shows exactly how to reach someone |
| One-size-fits-all | Learns from YOUR hiring patterns |

---

## Part 5: Proactive Candidate Evaluation

### Connect Evaluation Back to the Graph

When evaluating a candidate, we don't just look at their resume—we look at their **position in the graph**:

```python
def evaluate_candidate(candidate, company, graph):
    # 1. Path Analysis
    paths = graph.find_paths(company, candidate, max_hops=4)
    warm_intro_score = score_warmest_path(paths)

    # 2. Trajectory Similarity
    successful_hires = company.get_successful_hires()
    trajectory_similarity = compare_trajectories(candidate, successful_hires)

    # 3. Skill Inference
    explicit_skills = candidate.skills
    inferred_skills = graph.infer_skills(candidate)  # From projects, collaborators
    skill_match = match_skills(company.needs, explicit_skills + inferred_skills)

    # 4. Trust Score
    trust = graph.propagate_trust(company.founders, candidate)

    # 5. Culture Fit Signals
    culture_overlap = compare_company_cultures(
        candidate.past_companies,
        company
    )

    # 6. Risk Signals
    tenure_patterns = analyze_tenure(candidate)
    job_hop_risk = predict_churn(candidate, company)

    return CandidateEvaluation(
        warm_intro=paths[0] if paths else None,
        trajectory_match=trajectory_similarity,
        skill_match=skill_match,
        trust_score=trust,
        culture_signals=culture_overlap,
        risks=tenure_patterns,
    )
```

---

## Part 6: Proactive Suggestions (Clock Cycle)

### The Proactive Loop

Instead of waiting for the company to search, we push candidates to them:

```
┌─────────────────────────────────────────────────────────────────┐
│                     PROACTIVE AGENT LOOP                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  TRIGGERS (Clock Cycle Events):                                 │
│  ├── Daily: New candidates matching open roles                  │
│  ├── Real-time: Job change signals (someone left FAANG)        │
│  ├── Weekly: Network expansion (new 2nd-degree connections)    │
│  ├── Event-driven: Layoff announcements                        │
│  └── Continuous: Candidate profile updates                      │
│                                                                  │
│  ACTIONS:                                                        │
│  ├── Push notification: "3 new candidates for your Eng role"   │
│  ├── Slack message: "Your investor's portfolio company is      │
│  │                   laying off—here are 5 relevant engineers"  │
│  ├── Email digest: Weekly summary of pipeline                   │
│  └── Calendar: Auto-schedule intro calls                        │
│                                                                  │
│  LEARNING:                                                       │
│  ├── Company clicks → strengthen that candidate type           │
│  ├── Company passes → weaken that candidate type               │
│  ├── Successful hire → major signal, update all models         │
│  └── Churned hire → negative signal, learn why                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Signal Sources for Proactive Triggers

| Signal | Source | What It Means |
|--------|--------|---------------|
| Profile update | LinkedIn | Might be looking |
| GitHub activity drop | GitHub API | Might be leaving job |
| "Open to work" | LinkedIn | Actively looking |
| Company layoff | News/Twitter | Talent available |
| Funding round | Crunchbase | Competitors hiring |
| Job posting closed | Job boards | Someone was hired |
| Conference attendance | Event APIs | Active in community |
| New blog post | RSS/Medium | Thought leadership |

---

## Part 7: Two-Way Marketplace

### Candidate Side

Candidates come to us to find startup jobs:

```
┌─────────────────────────────────────────────────────────────────┐
│                    CANDIDATE PORTAL                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  DISCOVERY                                                       │
│  ├── Browse curated startup jobs                                │
│  ├── "Jobs at companies like X" (graph similarity)             │
│  ├── "Jobs your network is hiring for"                         │
│  └── Salary transparency                                        │
│                                                                  │
│  NETWORK INSIGHTS                                                │
│  ├── "You know 3 people at this company"                       │
│  ├── "Your classmate works here"                               │
│  └── Warm intro requests                                        │
│                                                                  │
│  PROFILE ENRICHMENT                                             │
│  ├── Connect LinkedIn, GitHub, portfolio                        │
│  ├── Add projects, skills, preferences                         │
│  └── Set job search status                                      │
│                                                                  │
│  VALUE EXCHANGE                                                  │
│  └── Candidates get: Better job matches, warm intros           │
│  └── We get: Enriched candidate database                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### The Flywheel

```
More candidates sign up
        ↓
Better candidate database
        ↓
Better matches for companies
        ↓
More companies use Agencity
        ↓
More job listings
        ↓
More candidates sign up
        ↓
(Flywheel accelerates)
```

---

## Part 8: Things You Might Not Have Considered

### 1. The Cold Start Problem
- New company = empty graph
- Solution: Bootstrap from public data (LinkedIn, GitHub, Crunchbase)
- Then enrich through intake

### 2. Data Freshness
- People change jobs, skills evolve
- Solution: Continuous crawling + decay functions on edges

### 3. Privacy & Consent
- Using LinkedIn data at scale = legal risk
- Solution: Candidate opt-in, company-provided data, public sources only

### 4. The "Poaching" Problem
- Companies don't want you poaching their employees
- Solution: Respect "do not contact" lists, focus on candidates who signal availability

### 5. Bias in the Graph
- Networks are not equal—some groups are underrepresented
- Solution: Explicitly diversify search, don't over-weight network proximity

### 6. Trust Calibration
- Not all vouches are equal
- Solution: Weight by track record (did their referrals work out?)

### 7. Multi-Tenant Graph
- Each company sees a different view of the graph
- Solution: Row-level security, permission-aware queries

### 8. The Referral Incentive
- People should WANT to add their network
- Solution: Referral bonuses, social proof, career karma

---

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)
- [ ] Design graph schema (entities, relationships)
- [ ] Set up PostgreSQL with graph-like tables
- [ ] Build entity extraction from existing data
- [ ] Create basic relationship mapping

### Phase 2: Data Ingestion (Weeks 3-4)
- [ ] Company intake chatbot (enhance existing)
- [ ] Founder network import (LinkedIn OAuth)
- [ ] Candidate database loading
- [ ] External API integrations (GitHub, etc.)

### Phase 3: Graph Intelligence (Weeks 5-6)
- [ ] Path finding algorithms
- [ ] Node embeddings (using LLM or Node2Vec)
- [ ] Trust propagation
- [ ] Similarity scoring

### Phase 4: Enhanced Search (Weeks 7-8)
- [ ] Graph-aware candidate ranking
- [ ] Warm intro path finding
- [ ] Hidden gem discovery
- [ ] Trajectory matching

### Phase 5: Proactive Agent (Weeks 9-10)
- [ ] Signal ingestion pipeline
- [ ] Clock cycle scheduler
- [ ] Alert/notification system
- [ ] Digest generation

### Phase 6: Candidate Portal (Weeks 11-12)
- [ ] Candidate signup flow
- [ ] Job discovery interface
- [ ] Network visualization
- [ ] Profile enrichment

### Phase 7: Learning Loop (Ongoing)
- [ ] Outcome tracking (hire/pass/churn)
- [ ] Model fine-tuning
- [ ] Edge weight updates
- [ ] A/B testing recommendations

---

## Tech Stack Recommendation

| Layer | Technology | Why |
|-------|------------|-----|
| Graph Storage | PostgreSQL + ltree + jsonb | Start simple, migrate later |
| Vector Search | pgvector | Embeddings for similarity |
| Embeddings | OpenAI text-embedding-3-large | Best quality |
| Graph Queries | Custom SQL + Python | Flexibility |
| Cache | Redis | Fast path lookups |
| Queue | Redis Queue | Async signal processing |
| API | FastAPI | Already using |
| LLM | GPT-4o | Conversation + evaluation |

---

## Success Metrics

| Metric | Target | Why It Matters |
|--------|--------|----------------|
| Time to first candidate | < 5 min | Speed |
| Warm intro rate | > 30% | Network leverage |
| Response rate (outreach) | > 40% | Quality of matches |
| Interview-to-offer | > 25% | Evaluation accuracy |
| 90-day retention | > 90% | Long-term fit |
| Candidate NPS | > 50 | Two-sided value |

---

## Next Steps

1. **Validate the graph schema** - Draw out the full entity-relationship diagram
2. **Identify data sources** - What can we access TODAY?
3. **Build the ingestion pipeline** - Start populating the graph
4. **Prototype warm path search** - Prove the value of graph-based ranking
5. **Launch candidate portal** - Start the flywheel

---

## Questions to Answer

1. How do we get founder networks without being creepy?
2. What's the minimum viable graph to show value?
3. How do we handle multi-tenant data isolation?
4. What signals actually predict successful hires?
5. How do we compete with LinkedIn's data moat?
