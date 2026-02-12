# Candidate Data Aggregation System

## Overview

A simple data aggregation system that pulls together all available information about candidates from multiple sources (LinkedIn, GitHub, DevPost, etc.) into a unified profile. Founders can quickly see the complete picture of who this person is without jumping between platforms.

**Core Principle:** Aggregate, normalize, and present. No complex scoring or evaluation - just give founders all the data in one place.

---

## 1. Simple Architecture

### 1.1 Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA SOURCES                             │
│  LinkedIn | GitHub | DevPost | Portfolio | Resume           │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ├─> Fetch & Store
                  │
┌─────────────────▼───────────────────────────────────────────┐
│                    RAW DATA STORE                           │
│  Store original API responses/scraped data                  │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ├─> Normalize & Merge
                  │
┌─────────────────▼───────────────────────────────────────────┐
│                 UNIFIED PROFILE                             │
│  Single view with all candidate data                        │
│  Education | Experience | Projects | Activity               │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 What We Aggregate

| Data Category | Sources | What We Show |
|--------------|---------|--------------|
| **Basic Info** | LinkedIn, Resume | Name, headline, location, contact |
| **Experience** | LinkedIn, Resume | Job history, titles, companies, tenure |
| **Education** | LinkedIn, Resume | Schools, degrees, graduation years |
| **Technical Skills** | GitHub, LinkedIn | Languages used, frameworks, tools |
| **Projects** | GitHub, DevPost, Portfolio | Repos, hackathons, personal projects |
| **Activity** | GitHub | Commits, contributions, repos |
| **Social Presence** | All sources | Profile links, follower counts |

---

## 2. Data Models

### 2.1 Core Models

```python
from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class DataSourceType(str, Enum):
    LINKEDIN = "linkedin"
    GITHUB = "github"
    DEVPOST = "devpost"
    PORTFOLIO = "portfolio"
    RESUME = "resume"
    TWITTER = "twitter"

class DataSource(BaseModel):
    """A candidate's profile on a specific platform."""
    id: str
    person_id: str
    source_type: DataSourceType
    profile_url: str
    username: Optional[str]
    raw_data: dict  # Original API response or scraped data
    last_fetched: datetime
    is_verified: bool = False  # Did we successfully fetch data?
    fetch_error: Optional[str] = None

class AggregatedProfile(BaseModel):
    """Unified candidate profile aggregated from all sources."""
    person_id: str

    # Basic Info (merged from all sources)
    full_name: str
    headline: Optional[str]
    location: Optional[str]
    email: Optional[str]

    # Professional
    current_title: Optional[str]
    current_company: Optional[str]
    experience: List[Experience]

    # Education
    education: List[Education]

    # Technical Profile (from GitHub)
    github_stats: Optional[GitHubStats]
    top_languages: List[str]
    repositories: List[Repository]

    # Projects & Achievements
    hackathon_projects: List[HackathonProject]  # From DevPost
    portfolio_projects: List[PortfolioProject]  # From portfolio

    # Skills (deduplicated from all sources)
    skills: List[str]

    # Social Links
    linkedin_url: Optional[str]
    github_url: Optional[str]
    portfolio_url: Optional[str]
    twitter_url: Optional[str]

    # Metadata
    data_sources: List[DataSourceType]  # Which sources we have
    completeness_score: float  # 0-1, how complete
    last_updated: datetime

class Experience(BaseModel):
    company: str
    title: str
    start_date: Optional[str]
    end_date: Optional[str]  # None if current
    duration_months: Optional[int]
    description: Optional[str]
    location: Optional[str]
    source: DataSourceType

class Education(BaseModel):
    school: str
    degree: Optional[str]
    field: Optional[str]
    start_year: Optional[int]
    end_year: Optional[int]
    activities: Optional[str]
    source: DataSourceType

class GitHubStats(BaseModel):
    username: str
    profile_url: str
    total_repos: int
    total_stars: int
    followers: int
    most_used_languages: Dict[str, int]  # language -> count
    account_created: datetime

class Repository(BaseModel):
    name: str
    description: Optional[str]
    url: str
    stars: int
    forks: int
    language: Optional[str]
    topics: List[str]
    last_updated: datetime

class HackathonProject(BaseModel):
    name: str
    tagline: Optional[str]
    description: str
    hackathon_name: str
    awards: List[str]
    tech_stack: List[str]
    project_url: str

class PortfolioProject(BaseModel):
    name: str
    description: str
    tech_stack: List[str]
    demo_url: Optional[str]
    github_url: Optional[str]
```

---

## 3. Data Fetchers

### 3.1 Base Interface

```python
class DataFetcher(ABC):
    """Base class for source-specific data fetchers."""

    @abstractmethod
    async def fetch(self, identifier: str) -> Dict[str, Any]:
        """Fetch data from this source."""
        pass

    @abstractmethod
    def normalize(self, raw_data: Dict) -> Dict[str, Any]:
        """Normalize raw data into standard format."""
        pass
```

### 3.2 GitHub Fetcher

```python
class GitHubFetcher(DataFetcher):
    """Fetch data from GitHub."""

    def __init__(self, github_token: str):
        self.token = github_token
        self.base_url = "https://api.github.com"

    async def fetch(self, username: str) -> Dict[str, Any]:
        """Fetch all GitHub data for a user."""

        headers = {"Authorization": f"token {self.token}"}

        async with httpx.AsyncClient(headers=headers) as client:
            # Fetch user profile
            user_resp = await client.get(f"{self.base_url}/users/{username}")
            user_data = user_resp.json()

            # Fetch repositories
            repos_resp = await client.get(
                f"{self.base_url}/users/{username}/repos?per_page=100&sort=updated"
            )
            repos_data = repos_resp.json()

        return {
            "user": user_data,
            "repositories": repos_data,
            "fetched_at": datetime.now().isoformat()
        }

    def normalize(self, raw_data: Dict) -> Dict[str, Any]:
        """Normalize GitHub data."""
        user = raw_data["user"]
        repos = raw_data["repositories"]

        # Calculate language distribution
        language_counts = {}
        for repo in repos:
            if lang := repo.get("language"):
                language_counts[lang] = language_counts.get(lang, 0) + 1

        # Get top languages
        top_languages = sorted(
            language_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        return {
            "stats": {
                "username": user["login"],
                "profile_url": user["html_url"],
                "total_repos": user["public_repos"],
                "total_stars": sum(r["stargazers_count"] for r in repos),
                "followers": user["followers"],
                "most_used_languages": dict(top_languages),
                "account_created": user["created_at"]
            },
            "repositories": [
                {
                    "name": repo["name"],
                    "description": repo.get("description"),
                    "url": repo["html_url"],
                    "stars": repo["stargazers_count"],
                    "forks": repo["forks_count"],
                    "language": repo.get("language"),
                    "topics": repo.get("topics", []),
                    "last_updated": repo["updated_at"]
                }
                for repo in repos
                if not repo.get("fork")  # Exclude forks
            ][:20],  # Top 20 repos
            "top_languages": [lang for lang, _ in top_languages]
        }
```

### 3.3 DevPost Fetcher

```python
class DevPostFetcher(DataFetcher):
    """Fetch data from DevPost."""

    async def fetch(self, username: str) -> Dict[str, Any]:
        """Scrape DevPost profile."""

        url = f"https://devpost.com/{username}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            html = response.text

        # Parse with BeautifulSoup
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        # Extract projects
        projects = []
        for project_card in soup.find_all('div', class_='software-list-content'):
            project = {
                'name': project_card.find('h5').text.strip(),
                'tagline': project_card.find('p', class_='tagline').text.strip(),
                'url': project_card.find('a')['href'],
                'image': project_card.find('img')['src'] if project_card.find('img') else None
            }
            projects.append(project)

        return {
            'username': username,
            'profile_url': url,
            'projects': projects,
            'fetched_at': datetime.now().isoformat()
        }

    def normalize(self, raw_data: Dict) -> Dict[str, Any]:
        """Normalize DevPost data."""
        return {
            'hackathon_projects': [
                {
                    'name': p['name'],
                    'tagline': p.get('tagline'),
                    'project_url': p['url'],
                    'image_url': p.get('image')
                }
                for p in raw_data['projects']
            ]
        }
```

### 3.4 LinkedIn Fetcher

```python
class LinkedInFetcher(DataFetcher):
    """Fetch LinkedIn data (from existing database)."""

    def __init__(self, supabase_client):
        self.supabase = supabase_client

    async def fetch(self, person_id: str) -> Dict[str, Any]:
        """Get LinkedIn data from people table."""

        response = self.supabase.table('people')\
            .select('*')\
            .eq('id', person_id)\
            .single()\
            .execute()

        return response.data

    def normalize(self, raw_data: Dict) -> Dict[str, Any]:
        """Normalize LinkedIn data from people table."""
        return {
            'basic_info': {
                'name': raw_data.get('full_name'),
                'headline': raw_data.get('headline'),
                'location': raw_data.get('location'),
                'current_company': raw_data.get('current_company'),
                'current_title': raw_data.get('current_title')
            },
            'experience': raw_data.get('experience', []),
            'education': raw_data.get('education', []),
            'skills': raw_data.get('skills', []),
            'linkedin_url': raw_data.get('linkedin_url')
        }
```

---

## 4. Aggregation Engine

### 4.1 Profile Aggregator

```python
class ProfileAggregator:
    """Aggregates data from multiple sources into unified profile."""

    def __init__(
        self,
        linkedin_fetcher: LinkedInFetcher,
        github_fetcher: GitHubFetcher,
        devpost_fetcher: DevPostFetcher
    ):
        self.fetchers = {
            DataSourceType.LINKEDIN: linkedin_fetcher,
            DataSourceType.GITHUB: github_fetcher,
            DataSourceType.DEVPOST: devpost_fetcher
        }

    async def aggregate(self, person_id: str) -> AggregatedProfile:
        """
        Aggregate all available data sources for a person.

        Steps:
        1. Fetch data from each available source
        2. Normalize each source's data
        3. Merge into unified profile
        4. Deduplicate and resolve conflicts
        """

        # Get person's data sources
        data_sources = await self._get_data_sources(person_id)

        # Fetch and normalize from each source
        normalized_data = {}
        for source_type in data_sources:
            if fetcher := self.fetchers.get(source_type):
                try:
                    raw_data = await fetcher.fetch(person_id)
                    normalized = fetcher.normalize(raw_data)
                    normalized_data[source_type] = normalized
                except Exception as e:
                    print(f"Error fetching {source_type}: {e}")
                    continue

        # Merge into unified profile
        profile = await self._merge_data(person_id, normalized_data)

        return profile

    async def _merge_data(
        self,
        person_id: str,
        normalized_data: Dict[DataSourceType, Dict]
    ) -> AggregatedProfile:
        """Merge data from multiple sources."""

        # Start with LinkedIn as base (most complete professional data)
        linkedin_data = normalized_data.get(DataSourceType.LINKEDIN, {})
        basic_info = linkedin_data.get('basic_info', {})

        # Add GitHub data
        github_data = normalized_data.get(DataSourceType.GITHUB, {})
        github_stats = github_data.get('stats')
        repositories = github_data.get('repositories', [])
        top_languages = github_data.get('top_languages', [])

        # Add DevPost data
        devpost_data = normalized_data.get(DataSourceType.DEVPOST, {})
        hackathon_projects = devpost_data.get('hackathon_projects', [])

        # Merge experience (deduplicate by company+title)
        experience = self._merge_experience(
            linkedin_data.get('experience', [])
        )

        # Merge education (deduplicate by school+degree)
        education = self._merge_education(
            linkedin_data.get('education', [])
        )

        # Merge skills (deduplicate)
        skills = self._merge_skills(
            linkedin_data.get('skills', []),
            top_languages
        )

        # Calculate completeness
        completeness = self._calculate_completeness(normalized_data)

        return AggregatedProfile(
            person_id=person_id,
            full_name=basic_info.get('name', ''),
            headline=basic_info.get('headline'),
            location=basic_info.get('location'),
            email=None,  # We don't have email from these sources
            current_title=basic_info.get('current_title'),
            current_company=basic_info.get('current_company'),
            experience=experience,
            education=education,
            github_stats=GitHubStats(**github_stats) if github_stats else None,
            top_languages=top_languages,
            repositories=[Repository(**r) for r in repositories],
            hackathon_projects=[HackathonProject(**h) for h in hackathon_projects],
            portfolio_projects=[],  # Add portfolio fetcher later
            skills=skills,
            linkedin_url=linkedin_data.get('linkedin_url'),
            github_url=github_stats['profile_url'] if github_stats else None,
            portfolio_url=None,
            twitter_url=None,
            data_sources=list(normalized_data.keys()),
            completeness_score=completeness,
            last_updated=datetime.now()
        )

    def _merge_experience(self, linkedin_exp: List[Dict]) -> List[Experience]:
        """Merge and deduplicate experience entries."""
        # For now, just use LinkedIn data
        return [
            Experience(
                company=exp.get('company', ''),
                title=exp.get('title', ''),
                start_date=exp.get('start_date'),
                end_date=exp.get('end_date'),
                duration_months=self._calculate_duration(
                    exp.get('start_date'),
                    exp.get('end_date')
                ),
                description=exp.get('description'),
                location=exp.get('location'),
                source=DataSourceType.LINKEDIN
            )
            for exp in linkedin_exp
        ]

    def _merge_education(self, linkedin_edu: List[Dict]) -> List[Education]:
        """Merge and deduplicate education entries."""
        # For now, just use LinkedIn data
        return [
            Education(
                school=edu.get('school', ''),
                degree=edu.get('degree'),
                field=edu.get('field_of_study'),
                start_year=self._extract_year(edu.get('start_date')),
                end_year=self._extract_year(edu.get('end_date')),
                activities=edu.get('activities'),
                source=DataSourceType.LINKEDIN
            )
            for edu in linkedin_edu
        ]

    def _merge_skills(
        self,
        linkedin_skills: List[str],
        github_languages: List[str]
    ) -> List[str]:
        """Merge and deduplicate skills."""
        # Combine and deduplicate
        all_skills = set(linkedin_skills + github_languages)
        return sorted(list(all_skills))

    def _calculate_completeness(self, normalized_data: Dict) -> float:
        """Calculate profile completeness score (0-1)."""
        score = 0.0

        # LinkedIn data: 40% weight
        if DataSourceType.LINKEDIN in normalized_data:
            score += 0.4

        # GitHub data: 30% weight
        if DataSourceType.GITHUB in normalized_data:
            score += 0.3

        # DevPost data: 20% weight
        if DataSourceType.DEVPOST in normalized_data:
            score += 0.2

        # Portfolio: 10% weight
        if DataSourceType.PORTFOLIO in normalized_data:
            score += 0.1

        return min(score, 1.0)

    def _calculate_duration(self, start_date: str, end_date: Optional[str]) -> Optional[int]:
        """Calculate duration in months."""
        # Simplified - would need proper date parsing
        return None

    def _extract_year(self, date_str: Optional[str]) -> Optional[int]:
        """Extract year from date string."""
        if not date_str:
            return None
        try:
            return int(date_str[:4])
        except:
            return None

    async def _get_data_sources(self, person_id: str) -> List[DataSourceType]:
        """Get list of available data sources for a person."""
        # Query data_sources table
        # For MVP, assume we have LinkedIn for all, check for GitHub username
        return [DataSourceType.LINKEDIN]
```

---

## 5. Database Schema

```sql
-- Data sources table
CREATE TABLE data_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    source_type TEXT NOT NULL,
    profile_url TEXT,
    username TEXT,
    raw_data JSONB DEFAULT '{}'::jsonb,
    last_fetched TIMESTAMPTZ,
    is_verified BOOLEAN DEFAULT FALSE,
    fetch_error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT valid_source_type CHECK (
        source_type IN ('linkedin', 'github', 'devpost', 'portfolio', 'resume', 'twitter')
    ),
    UNIQUE(person_id, source_type)
);

CREATE INDEX idx_data_sources_person ON data_sources(person_id);
CREATE INDEX idx_data_sources_type ON data_sources(source_type);

-- Aggregated profiles cache
CREATE TABLE aggregated_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID NOT NULL REFERENCES people(id) ON DELETE CASCADE UNIQUE,

    -- Cached aggregated data
    profile_data JSONB NOT NULL,

    -- Metadata
    data_sources TEXT[] NOT NULL,  -- Array of source types
    completeness_score FLOAT DEFAULT 0.0,
    last_updated TIMESTAMPTZ DEFAULT NOW(),

    CHECK (completeness_score >= 0 AND completeness_score <= 1)
);

CREATE INDEX idx_aggregated_profiles_person ON aggregated_profiles(person_id);
CREATE INDEX idx_aggregated_profiles_updated ON aggregated_profiles(last_updated DESC);
CREATE INDEX idx_aggregated_profiles_completeness ON aggregated_profiles(completeness_score DESC);

-- View: Quick profile summary
CREATE OR REPLACE VIEW profile_summary AS
SELECT
    p.id as person_id,
    p.full_name,
    p.current_title,
    p.current_company,
    ap.completeness_score,
    ap.data_sources,
    COUNT(DISTINCT ds.source_type) as sources_count,
    ap.last_updated
FROM people p
LEFT JOIN aggregated_profiles ap ON p.id = ap.person_id
LEFT JOIN data_sources ds ON p.id = ds.person_id AND ds.is_verified = TRUE
GROUP BY p.id, p.full_name, p.current_title, p.current_company,
         ap.completeness_score, ap.data_sources, ap.last_updated;
```

---

## 6. API Endpoints

```python
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/api/v1/profiles", tags=["profiles"])

@router.get("/{person_id}/aggregated")
async def get_aggregated_profile(person_id: str):
    """
    Get complete aggregated profile for a candidate.

    Returns unified view of all data sources.
    """
    aggregator = ProfileAggregator(...)

    # Check cache first
    cached = await get_cached_profile(person_id)
    if cached and is_fresh(cached):
        return cached['profile_data']

    # Aggregate fresh data
    profile = await aggregator.aggregate(person_id)

    # Cache result
    await cache_profile(person_id, profile)

    return profile

@router.post("/{person_id}/refresh")
async def refresh_profile(person_id: str, sources: List[DataSourceType] = None):
    """
    Force refresh profile data from sources.

    If sources specified, only refresh those.
    Otherwise refresh all available sources.
    """
    aggregator = ProfileAggregator(...)

    # Clear cache
    await clear_cache(person_id)

    # Re-aggregate
    profile = await aggregator.aggregate(person_id)

    return profile

@router.get("/{person_id}/sources")
async def get_data_sources(person_id: str):
    """
    Get list of data sources for a candidate.

    Shows which platforms we have data from and last fetch time.
    """
    supabase = get_supabase_client()

    response = supabase.table('data_sources')\
        .select('*')\
        .eq('person_id', person_id)\
        .execute()

    return {'sources': response.data}

@router.post("/{person_id}/sources")
async def add_data_source(person_id: str, request: AddSourceRequest):
    """
    Add a new data source for a candidate.

    Request:
    {
        "source_type": "github",
        "username": "maya-codes"
    }
    """
    supabase = get_supabase_client()

    # Create data source entry
    source = {
        'person_id': person_id,
        'source_type': request.source_type,
        'username': request.username,
        'profile_url': build_profile_url(request.source_type, request.username)
    }

    supabase.table('data_sources').insert(source).execute()

    # Trigger fetch
    await fetch_and_store(person_id, request.source_type, request.username)

    return {'status': 'added', 'source': source}
```

---

## 7. MVP Implementation Steps

### Phase 1: Foundation (Week 1)
1. Create database tables (`data_sources`, `aggregated_profiles`)
2. Build `LinkedInFetcher` (uses existing `people` table data)
3. Build basic `ProfileAggregator`
4. API endpoint: GET `/profiles/{person_id}/aggregated`

### Phase 2: GitHub Integration (Week 2)
1. Build `GitHubFetcher` with GitHub API
2. Script to discover GitHub usernames from LinkedIn/people data
3. Add GitHub data to aggregation
4. API endpoint: POST `/profiles/{person_id}/sources` (add GitHub)

### Phase 3: DevPost Integration (Week 3)
1. Build `DevPostFetcher` with scraping
2. Add DevPost projects to aggregation
3. Frontend: Display unified profile

### Phase 4: Polish (Week 4)
1. Caching and cache invalidation
2. Background jobs for periodic refresh
3. Completeness scoring
4. Error handling and retry logic

---

## 8. Example: Complete Flow

```python
# Founder searches for "Software Engineer"
# System finds Maya Patel in results

# GET /api/v1/profiles/maya-id/aggregated

# Response:
{
    "person_id": "maya-id",
    "full_name": "Maya Patel",
    "headline": "CS @ UCSD | AI/ML Enthusiast",
    "location": "San Diego, CA",
    "current_title": null,
    "current_company": null,

    # From LinkedIn
    "experience": [],
    "education": [
        {
            "school": "UC San Diego",
            "degree": "BS",
            "field": "Computer Science",
            "end_year": 2026,
            "source": "linkedin"
        }
    ],

    # From GitHub
    "github_stats": {
        "username": "maya-codes",
        "profile_url": "https://github.com/maya-codes",
        "total_repos": 15,
        "total_stars": 47,
        "followers": 23,
        "most_used_languages": {
            "Python": 8,
            "JavaScript": 5,
            "TypeScript": 2
        }
    },
    "repositories": [
        {
            "name": "llm-router",
            "description": "Smart routing for LLM APIs",
            "url": "https://github.com/maya-codes/llm-router",
            "stars": 32,
            "language": "Python",
            "topics": ["llm", "api", "routing"]
        },
        // ... more repos
    ],

    # From DevPost
    "hackathon_projects": [
        {
            "name": "StudyBuddy AI",
            "tagline": "AI-powered study assistant",
            "hackathon_name": "SD Hacks 2024",
            "awards": ["Best AI Project"],
            "project_url": "https://devpost.com/software/studybuddy"
        }
    ],

    "skills": ["Python", "JavaScript", "Machine Learning", "React", "FastAPI"],

    "data_sources": ["linkedin", "github", "devpost"],
    "completeness_score": 0.9,
    "last_updated": "2026-02-11T10:30:00Z"
}
```

Founder sees:
- **Complete professional background** (LinkedIn)
- **Technical depth** (GitHub repos, languages)
- **Building experience** (hackathon projects)
- **All in one view** - no jumping between tabs

---

## 9. Key Advantages

1. **Simple**: Just fetch, normalize, merge
2. **Complete**: One place for all candidate data
3. **Fast**: Cached aggregated profiles
4. **Extensible**: Easy to add new sources
5. **Transparent**: Raw data always available

---

## 10. Future Enhancements

- Add resume parsing
- Add portfolio website scraping
- Add Twitter/X integration
- Smart deduplication (fuzzy matching)
- Conflict resolution (prefer newer data)
- Activity timeline (commits, posts, projects over time)
