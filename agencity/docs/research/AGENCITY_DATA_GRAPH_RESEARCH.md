# Agencity: Data Collection & Graph Modeling Research

## The Core Problem

We need to collect data from multiple sources and model it as a connected graph that can answer questions like:
- "Who in my network knows someone at Stripe?"
- "Find engineers with similar trajectories to my best hire"
- "What's the warmest path to reach this candidate?"

---

## Part 1: Data Collection - Micro Research Questions

### 1.1 Founder Network Data

**The Question:** How do we capture a founder's professional network?

**Sub-questions:**
| Question | Options | Research Needed |
|----------|---------|-----------------|
| How to import LinkedIn connections? | OAuth API, manual CSV export, scraping | LinkedIn API limits, legal risk |
| How to capture relationship strength? | Interaction frequency, recency, explicit rating | What signals correlate with "real" relationships? |
| How to get email contacts? | Google Contacts API, phone contacts | Privacy consent, data format |
| How to capture informal networks? | Manual input, calendar analysis, Slack | How to make input frictionless? |
| How to represent "how they know each other"? | Free text, categories, LLM extraction | What categories matter for hiring? |

**Data Sources:**
```
┌─────────────────────────────────────────────────────────────────┐
│ FOUNDER NETWORK SOURCES                                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  EXPLICIT (founder provides)                                    │
│  ├── LinkedIn connections export (CSV)                          │
│  ├── Google Contacts                                            │
│  ├── Phone contacts                                             │
│  ├── "Who do you know well?" manual input                      │
│  └── Calendar (who do they meet with?)                         │
│                                                                  │
│  IMPLICIT (we infer)                                            │
│  ├── Same company overlap (LinkedIn)                           │
│  ├── Same school overlap                                        │
│  ├── Same investor portfolio                                   │
│  ├── Co-authored papers/patents                                │
│  ├── Open source collaborators                                 │
│  └── Conference co-speakers                                    │
│                                                                  │
│  ENRICHED (we add context)                                      │
│  ├── How long did they overlap?                                │
│  ├── What was the relationship? (peer, manager, report)        │
│  └── When did they last interact?                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Research Tasks:**
- [ ] Test LinkedIn CSV export format
- [ ] Explore LinkedIn OAuth API limits
- [ ] Build Google Contacts integration
- [ ] Design "relationship strength" input UI
- [ ] Prototype calendar analysis for meeting frequency

---

### 1.2 Company Data

**The Question:** How do we capture everything about a company that's relevant for hiring?

**Sub-questions:**
| Question | Options | Research Needed |
|----------|---------|-----------------|
| How to get team composition? | LinkedIn company page, manual input | API access, accuracy |
| How to understand tech stack? | Job postings, GitHub, StackShare | Completeness |
| How to capture culture? | Glassdoor, intake questions, employee content | What signals matter? |
| How to get hiring history? | ATS integration, manual input | Which ATSs have APIs? |
| How to understand what "good" looks like? | Intake questions, outcome tracking | How to ask this well? |

**Data Sources:**
```
┌─────────────────────────────────────────────────────────────────┐
│ COMPANY DATA SOURCES                                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  PUBLIC DATA                                                    │
│  ├── LinkedIn company page (employees, size, industry)         │
│  ├── Crunchbase (funding, investors, founders)                 │
│  ├── GitHub org (repos, contributors, tech stack)              │
│  ├── Company website (about, team page, careers)               │
│  ├── Glassdoor (reviews, salary, interview process)            │
│  ├── Job postings (requirements, tech stack, culture signals)  │
│  └── News/press (recent events, funding, launches)             │
│                                                                  │
│  COMPANY-PROVIDED                                               │
│  ├── Intake conversation (needs, culture, preferences)         │
│  ├── Team roster (who works there now)                         │
│  ├── Org chart (reporting structure)                           │
│  ├── ATS data (past applicants, hiring outcomes)               │
│  ├── "Who are your best hires?" explicit input                 │
│  └── Interview scorecards (what do they evaluate?)             │
│                                                                  │
│  INFERRED                                                       │
│  ├── Company → similar companies (by investors, space)         │
│  ├── Employee trajectories (where do people come from/go?)     │
│  └── Hiring patterns (what roles, how often, success rate)     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Research Tasks:**
- [ ] Map LinkedIn company page data structure
- [ ] Explore Crunchbase API
- [ ] List top ATS APIs (Lever, Greenhouse, Ashby)
- [ ] Design company intake questionnaire v2
- [ ] Prototype website scraper for team pages

---

### 1.3 Candidate Data

**The Question:** What do we need to know about candidates, and where do we get it?

**Sub-questions:**
| Question | Options | Research Needed |
|----------|---------|-----------------|
| What's the minimum viable profile? | Name, skills, location, contact | What's required for matching? |
| How to enrich profiles? | APIs (GitHub, LinkedIn), public data | Cost, accuracy, freshness |
| How to capture career trajectory? | Employment history, education | How to normalize across sources? |
| How to infer skills? | From projects, companies, education | Accuracy of inference |
| How to know if they're looking? | Signals, explicit status | What signals work? |

**Data Sources:**
```
┌─────────────────────────────────────────────────────────────────┐
│ CANDIDATE DATA SOURCES                                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  OUR DATABASE (opted-in)                                        │
│  ├── Profile they created                                       │
│  ├── Resume/CV upload                                           │
│  ├── Skills they selected                                       │
│  ├── Job preferences                                            │
│  └── Network connections they shared                            │
│                                                                  │
│  EXTERNAL SEARCH                                                │
│  ├── GitHub (repos, activity, contributions)                   │
│  ├── LinkedIn via Clado/Pearch (profile, experience, skills)   │
│  ├── Devpost (hackathon projects)                              │
│  ├── Stack Overflow (expertise, reputation)                    │
│  ├── Twitter/X (thought leadership)                            │
│  ├── Personal websites/portfolios                              │
│  ├── Research papers (Google Scholar, arXiv)                   │
│  └── Conference talks (YouTube, Luma)                          │
│                                                                  │
│  SIGNALS                                                        │
│  ├── Job change (LinkedIn update)                              │
│  ├── "Open to work" badge                                      │
│  ├── GitHub activity pattern changes                           │
│  ├── New blog posts                                            │
│  └── Conference attendance                                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Research Tasks:**
- [ ] Define minimum viable candidate profile
- [ ] Map data fields across sources (normalize schema)
- [ ] Test enrichment accuracy (Clado vs Pearch vs manual)
- [ ] Identify "looking for job" signals
- [ ] Design candidate opt-in flow

---

### 1.4 Relationship Data

**The Question:** How do we know who knows who, and how well?

**This is the hardest part.** Relationships are:
- Often private (not public data)
- Asymmetric (A might know B better than B knows A)
- Contextual (professional vs personal)
- Time-varying (people drift apart)

**Sub-questions:**
| Question | Options | Research Needed |
|----------|---------|-----------------|
| How to detect implicit relationships? | Company overlap, school overlap, GitHub collaborations | What signals indicate real relationships? |
| How to measure relationship strength? | Duration of overlap, recency of interaction, explicit rating | Which metrics correlate with "would refer"? |
| How to handle asymmetry? | Directed edges, separate strength scores | Does this matter for hiring? |
| How to track relationship decay? | Time-based decay function, activity signals | What decay rate is realistic? |
| How to capture "how they met"? | Categories, free text, inference | What contexts matter? |

**Relationship Evidence Sources:**
```
┌─────────────────────────────────────────────────────────────────┐
│ HOW DO WE KNOW THEY KNOW EACH OTHER?                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  EXPLICIT (highest confidence)                                  │
│  ├── User told us "I know this person well"                    │
│  ├── LinkedIn connection (confirmed)                           │
│  ├── Past referral/recommendation                              │
│  └── Email/calendar showing interaction                        │
│                                                                  │
│  STRONG IMPLICIT                                                │
│  ├── Worked at same company, same time, same team              │
│  ├── Co-authored paper/patent                                  │
│  ├── Co-founded company                                        │
│  ├── Same small school + same years                            │
│  └── Open source: significant PRs to same repo                 │
│                                                                  │
│  WEAK IMPLICIT                                                  │
│  ├── Worked at same large company, same time                   │
│  ├── Same university, different years                          │
│  ├── Same investor portfolio                                   │
│  ├── Same conference attendance                                │
│  └── Mutual connections (friend of friend)                     │
│                                                                  │
│  INFERRED (lowest confidence)                                   │
│  ├── Similar career trajectory                                 │
│  ├── Same industry/space                                       │
│  └── Follow each other on Twitter                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Research Tasks:**
- [ ] Define relationship confidence tiers
- [ ] Test company overlap detection accuracy
- [ ] Design "relationship rating" input UI
- [ ] Research decay functions in social networks
- [ ] Prototype GitHub collaboration detection

---

## Part 2: Graph Modeling - Micro Research Questions

### 2.1 Schema Design

**The Question:** What's the right entity-relationship model?

**Key Decisions:**
| Decision | Options | Trade-offs |
|----------|---------|------------|
| Node types | Fine-grained (Person, Candidate, Founder) vs coarse (just Person) | Flexibility vs query simplicity |
| Edge types | Many specific types vs few generic + properties | Expressiveness vs complexity |
| Properties on edges | Embedded vs separate table | Query speed vs flexibility |
| Temporal data | Snapshot vs event log | Storage vs history |
| Multi-tenancy | Separate graphs vs shared with ACL | Isolation vs efficiency |

**Proposed Schema (v1):**

```
NODES:
├── Person
│   ├── id (uuid)
│   ├── name
│   ├── email
│   ├── linkedin_url
│   ├── github_username
│   ├── type: enum[candidate, founder, employee, investor, advisor]
│   └── embedding: vector(1536)
│
├── Company
│   ├── id
│   ├── name
│   ├── domain
│   ├── stage: enum[seed, series_a, series_b, ...]
│   ├── industry
│   └── embedding: vector(1536)
│
├── School
│   ├── id
│   ├── name
│   ├── type: enum[university, bootcamp, high_school]
│   └── location
│
├── Skill
│   ├── id
│   ├── name
│   ├── category
│   └── embedding: vector(1536)
│
└── Project
    ├── id
    ├── name
    ├── url
    ├── type: enum[repo, paper, product, hackathon]
    └── embedding: vector(1536)

EDGES:
├── WORKS_AT (Person → Company)
│   ├── role
│   ├── start_date
│   ├── end_date
│   ├── is_current: bool
│   └── seniority: enum[ic, lead, manager, director, vp, c_level]
│
├── STUDIED_AT (Person → School)
│   ├── degree
│   ├── field
│   ├── start_year
│   └── end_year
│
├── KNOWS (Person → Person)
│   ├── strength: float[0-1]
│   ├── confidence: float[0-1]
│   ├── source: enum[explicit, company_overlap, school_overlap, github, inferred]
│   ├── context: text
│   ├── last_interaction: date
│   └── evidence: jsonb
│
├── HAS_SKILL (Person → Skill)
│   ├── level: enum[learning, competent, proficient, expert]
│   ├── evidence: jsonb
│   └── confidence: float
│
├── CONTRIBUTED_TO (Person → Project)
│   ├── role: enum[owner, maintainer, contributor]
│   ├── contribution_type: text
│   └── dates
│
├── INVESTED_IN (Person|Company → Company)
│   ├── round
│   ├── date
│   └── amount
│
└── HIRED (Company → Person)
    ├── role
    ├── date
    ├── source: enum[referral, inbound, outbound, agency]
    ├── outcome: enum[active, churned, promoted, left]
    └── tenure_days
```

**Research Tasks:**
- [ ] Review graph database best practices
- [ ] Test schema with sample queries
- [ ] Decide on PostgreSQL vs Neo4j
- [ ] Design multi-tenancy model
- [ ] Plan migration strategy

---

### 2.2 Data Normalization

**The Question:** How do we merge the same entity from different sources?

**The Problem:**
```
LinkedIn: "John Smith - Software Engineer at Google"
GitHub:   "johnsmith" - location: "Mountain View"
Devpost:  "John S." - Stanford University
Our DB:   "John Smith" - john@gmail.com

Are these the same person? How do we merge them?
```

**Entity Resolution Strategies:**
| Strategy | How It Works | Accuracy |
|----------|--------------|----------|
| Exact email match | Same email = same person | High but incomplete |
| LinkedIn URL match | Unique identifier | High when available |
| GitHub username match | Unique identifier | High when available |
| Name + Company + Dates | Fuzzy match on multiple fields | Medium |
| Embedding similarity | Vector similarity of profile text | Medium |
| LLM-assisted | Ask GPT if same person | High but expensive |

**Proposed Approach:**
```python
def resolve_entity(new_entity, existing_entities):
    # 1. Exact matches (highest confidence)
    if new_entity.email:
        match = find_by_email(new_entity.email)
        if match:
            return merge(match, new_entity, confidence=1.0)

    if new_entity.linkedin_url:
        match = find_by_linkedin(new_entity.linkedin_url)
        if match:
            return merge(match, new_entity, confidence=1.0)

    # 2. Strong matches
    if new_entity.github_username:
        match = find_by_github(new_entity.github_username)
        if match:
            return merge(match, new_entity, confidence=0.95)

    # 3. Fuzzy matches
    candidates = fuzzy_search(new_entity.name, new_entity.company)
    for candidate in candidates:
        similarity = compute_similarity(new_entity, candidate)
        if similarity > 0.9:
            return merge(candidate, new_entity, confidence=similarity)

    # 4. LLM verification for borderline cases
    if candidates and 0.7 < similarity < 0.9:
        is_same = llm_verify(new_entity, candidate)
        if is_same:
            return merge(candidate, new_entity, confidence=0.85)

    # 5. Create new entity
    return create_new(new_entity)
```

**Research Tasks:**
- [ ] Test entity resolution accuracy on sample data
- [ ] Build fuzzy matching pipeline
- [ ] Evaluate LLM for entity resolution
- [ ] Design merge conflict resolution
- [ ] Create deduplication dashboard

---

### 2.3 Relationship Inference

**The Question:** How do we infer relationships that aren't explicitly stated?

**Inference Rules:**
```python
INFERENCE_RULES = [
    # Company overlap
    {
        "condition": "A.worked_at(X) AND B.worked_at(X) AND overlap(A, B, X) > 6 months",
        "infer": "KNOWS(A, B)",
        "strength": "0.3 + 0.1 * years_overlap",
        "confidence": 0.7,
        "source": "company_overlap"
    },

    # Same team (if we know org structure)
    {
        "condition": "A.reports_to(M) AND B.reports_to(M)",
        "infer": "KNOWS(A, B)",
        "strength": 0.7,
        "confidence": 0.9,
        "source": "same_team"
    },

    # School overlap
    {
        "condition": "A.studied_at(S) AND B.studied_at(S) AND overlap_years(A, B, S) >= 1",
        "infer": "KNOWS(A, B)",
        "strength": "0.2 + 0.05 * overlap_years",
        "confidence": 0.5,
        "source": "school_overlap"
    },

    # Same small school, same major
    {
        "condition": "A.studied_at(S) AND B.studied_at(S) AND S.size < 5000 AND A.major == B.major",
        "infer": "KNOWS(A, B)",
        "strength": 0.5,
        "confidence": 0.7,
        "source": "school_major_overlap"
    },

    # GitHub collaboration
    {
        "condition": "A.contributed_to(R) AND B.contributed_to(R) AND R.contributors < 20",
        "infer": "KNOWS(A, B)",
        "strength": 0.6,
        "confidence": 0.8,
        "source": "github_collaboration"
    },

    # Co-authored paper
    {
        "condition": "A.authored(P) AND B.authored(P)",
        "infer": "KNOWS(A, B)",
        "strength": 0.8,
        "confidence": 0.95,
        "source": "co_author"
    },

    # Same investor portfolio (for founders)
    {
        "condition": "A.founded(C1) AND B.founded(C2) AND C1.investor == C2.investor",
        "infer": "KNOWS(A, B)",
        "strength": 0.3,
        "confidence": 0.5,
        "source": "portfolio_peers"
    },

    # Transitive (friend of friend)
    {
        "condition": "KNOWS(A, B, strength > 0.7) AND KNOWS(B, C, strength > 0.7)",
        "infer": "MAY_KNOW(A, C)",
        "strength": "A_B_strength * B_C_strength * 0.5",
        "confidence": 0.4,
        "source": "transitive"
    }
]
```

**Research Tasks:**
- [ ] Validate inference rules with real data
- [ ] Calibrate strength/confidence values
- [ ] Test transitive inference accuracy
- [ ] Build inference pipeline
- [ ] Create inference audit log

---

### 2.4 Embeddings & Similarity

**The Question:** How do we compute semantic similarity between entities?

**What Gets Embedded:**
```python
def embed_person(person):
    text = f"""
    {person.name}
    Current: {person.current_role} at {person.current_company}
    Previously: {format_work_history(person.work_history)}
    Education: {format_education(person.education)}
    Skills: {', '.join(person.skills)}
    Projects: {format_projects(person.projects)}
    About: {person.bio}
    """
    return openai.embed(text)

def embed_company(company):
    text = f"""
    {company.name}
    Industry: {company.industry}
    Stage: {company.stage}
    What they do: {company.description}
    Tech stack: {', '.join(company.tech_stack)}
    Team size: {company.employee_count}
    Culture: {company.culture_description}
    Looking for: {company.hiring_needs}
    """
    return openai.embed(text)

def embed_role(role_blueprint):
    text = f"""
    Role: {role.title}
    Company context: {role.company_context}
    The work: {role.specific_work}
    Success criteria: {role.success_criteria}
    Must have: {', '.join(role.must_haves)}
    Nice to have: {', '.join(role.nice_to_haves)}
    """
    return openai.embed(text)
```

**Similarity Uses:**
| Use Case | Comparison |
|----------|------------|
| Candidate-Role match | embed(candidate) · embed(role) |
| Similar candidates | embed(candidate_A) · embed(candidate_B) |
| Similar companies | embed(company_A) · embed(company_B) |
| Similar trajectories | embed(career_path_A) · embed(career_path_B) |

**Research Tasks:**
- [ ] Test embedding models (OpenAI vs Voyage vs Cohere)
- [ ] Evaluate embedding quality for hiring match
- [ ] Design embedding update strategy
- [ ] Build similarity search index (pgvector)
- [ ] Benchmark query performance

---

### 2.5 Graph Storage

**The Question:** Where do we store this graph?

**Option 1: PostgreSQL + Adjacency Tables**
```sql
-- Nodes
CREATE TABLE persons (
    id UUID PRIMARY KEY,
    name TEXT,
    email TEXT UNIQUE,
    linkedin_url TEXT UNIQUE,
    github_username TEXT UNIQUE,
    type person_type,
    data JSONB,
    embedding vector(1536),
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
);

-- Edges
CREATE TABLE relationships (
    id UUID PRIMARY KEY,
    source_id UUID REFERENCES persons(id),
    target_id UUID REFERENCES persons(id),
    type relationship_type,
    strength FLOAT,
    confidence FLOAT,
    evidence JSONB,
    source TEXT,
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMPTZ,

    UNIQUE(source_id, target_id, type)
);

-- Indexes
CREATE INDEX idx_rel_source ON relationships(source_id);
CREATE INDEX idx_rel_target ON relationships(target_id);
CREATE INDEX idx_rel_type ON relationships(type);
CREATE INDEX idx_persons_embedding ON persons USING ivfflat (embedding vector_cosine_ops);
```

**Pros:** Simple, we already use Postgres, pgvector for embeddings
**Cons:** Complex path queries, no native graph algorithms

**Option 2: Neo4j**
```cypher
// Nodes
CREATE (p:Person {id: $id, name: $name, email: $email, ...})
CREATE (c:Company {id: $id, name: $name, ...})

// Edges
MATCH (a:Person), (b:Person)
WHERE a.id = $source AND b.id = $target
CREATE (a)-[r:KNOWS {strength: $strength, confidence: $confidence}]->(b)

// Path query
MATCH path = shortestPath((founder:Person)-[:KNOWS*1..3]-(candidate:Person))
WHERE founder.id = $founder_id AND candidate.id = $candidate_id
RETURN path
```

**Pros:** Native graph queries, built-in algorithms
**Cons:** Another database to manage, cost

**Recommendation:** Start with PostgreSQL, add Neo4j when path queries become critical.

**Research Tasks:**
- [ ] Benchmark path queries in Postgres vs Neo4j
- [ ] Design Postgres schema for graph
- [ ] Test recursive CTEs for path finding
- [ ] Evaluate graph algorithms we need
- [ ] Plan potential Neo4j migration

---

## Part 3: Implementation Plan

### Phase 1: Schema & Storage (Week 1)

**Goal:** Set up the graph database and schema

**Tasks:**
1. Create PostgreSQL tables for all node types
2. Create relationship tables with proper indexes
3. Set up pgvector for embeddings
4. Build basic CRUD operations
5. Create data validation layer

**Deliverable:** Empty graph database ready for data

---

### Phase 2: Data Ingestion Pipeline (Week 2-3)

**Goal:** Build pipelines to load data from all sources

**Tasks:**
1. **LinkedIn CSV Import**
   - Parse export format
   - Extract connections
   - Create person nodes
   - Infer relationships

2. **GitHub Enrichment**
   - Fetch user profiles
   - Extract repos, contributions
   - Create project nodes
   - Link contributors

3. **Company Data**
   - Crunchbase integration
   - LinkedIn company pages
   - Website scraping

4. **Our Candidate DB**
   - Map existing schema to graph
   - Create person nodes
   - Link to companies, schools

**Deliverable:** Populated graph with initial data

---

### Phase 3: Relationship Inference (Week 4)

**Goal:** Build the inference engine

**Tasks:**
1. Implement inference rules
2. Run company overlap detection
3. Run school overlap detection
4. Run GitHub collaboration detection
5. Create inference audit log
6. Build confidence calibration

**Deliverable:** Graph with inferred relationships

---

### Phase 4: Embeddings & Similarity (Week 5)

**Goal:** Add semantic understanding

**Tasks:**
1. Design embedding prompts
2. Generate embeddings for all entities
3. Build similarity search
4. Create trajectory embedding
5. Test matching accuracy

**Deliverable:** Semantic search working

---

### Phase 5: Path Finding & Warm Intros (Week 6)

**Goal:** Find connection paths

**Tasks:**
1. Implement shortest path algorithm
2. Add path scoring (by trust/strength)
3. Build "warmest path" finder
4. Create path visualization
5. Integrate with search results

**Deliverable:** Warm intro paths in candidate cards

---

## Part 4: Open Research Questions

### Questions We Need to Answer

1. **What makes a relationship "warm enough" for a referral?**
   - Hypothesis: 2+ years overlap, or explicit "would refer"
   - How to validate: Survey founders on referral likelihood

2. **How does relationship strength decay over time?**
   - Hypothesis: Half-life of 2-3 years without interaction
   - How to validate: Track referral success by recency

3. **What's the accuracy of inferred relationships?**
   - Hypothesis: Company overlap = 70% accuracy
   - How to validate: Sample and manually verify

4. **How many hops is too many for a warm intro?**
   - Hypothesis: 3 hops max, preferably 2
   - How to validate: Track response rates by path length

5. **What signals predict "actively looking"?**
   - Hypothesis: Profile updates + activity changes
   - How to validate: Track against actual job changes

6. **How do we handle false positives in entity resolution?**
   - Hypothesis: Conservative merging + manual review queue
   - How to validate: Error rate tracking

---

## Part 5: Immediate Next Steps

### This Week

1. **Design final graph schema**
   - Finalize node types and properties
   - Finalize edge types and properties
   - Create SQL migration files

2. **Build LinkedIn CSV parser**
   - Test with real export
   - Extract all available fields
   - Map to graph schema

3. **Create entity resolution prototype**
   - Build fuzzy matching
   - Test on sample data
   - Measure accuracy

4. **Set up pgvector**
   - Install extension
   - Create embedding columns
   - Test similarity search

---

## Questions for You

1. **Do you have sample data we can test with?**
   - A LinkedIn connections export?
   - Your candidate database?
   - A company's team list?

2. **What's the priority order for data sources?**
   - Founder network first? Or candidate DB first?

3. **How important is historical data?**
   - Do we need to track when relationships change?
   - Or just current state?

4. **What's the privacy model?**
   - What data can we store?
   - What requires consent?

5. **What's the first query we want to answer?**
   - "Find me engineers my network knows"?
   - "Show warm paths to this candidate"?
