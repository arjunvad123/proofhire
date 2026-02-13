"""
Skill Predictor - Auto-suggest skills and requirements for roles.

When a founder selects a role, automatically suggest:
- Required skills
- Preferred skills
- Years of experience
- Education preferences
- Company preferences

Usage:
    predictor = SkillPredictor()
    requirements = predictor.predict_requirements("ML Engineer")
    # Returns: {
    #   "required_skills": ["Python", "PyTorch", "Machine Learning"],
    #   "preferred_skills": ["TensorFlow", "MLOps"],
    #   "years_experience": 3,
    #   "education": "BS/MS in CS or related field"
    # }
"""

import logging
from typing import Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)


# =============================================================================
# ROLE REQUIREMENTS DATABASE
# =============================================================================

ROLE_REQUIREMENTS = {
    # Engineering Roles
    "ML Engineer": {
        "required_skills": ["Python", "PyTorch", "Machine Learning", "Deep Learning"],
        "preferred_skills": ["TensorFlow", "MLOps", "Kubernetes", "SQL", "Spark"],
        "years_experience": 3,
        "education": "BS/MS in CS, Math, or related field",
        "seniority_levels": ["Mid", "Senior", "Staff"],
        "remote_friendly": True,
        "salary_range": "$150k-$250k"
    },
    "Machine Learning Engineer": {
        "required_skills": ["Python", "PyTorch", "Machine Learning", "Deep Learning"],
        "preferred_skills": ["TensorFlow", "MLOps", "Kubernetes", "SQL", "Spark"],
        "years_experience": 3,
        "education": "BS/MS in CS, Math, or related field",
        "seniority_levels": ["Mid", "Senior", "Staff"],
        "remote_friendly": True,
        "salary_range": "$150k-$250k"
    },
    "Backend Engineer": {
        "required_skills": ["Python", "SQL", "REST APIs", "PostgreSQL"],
        "preferred_skills": ["Go", "Redis", "AWS", "Docker", "Kubernetes"],
        "years_experience": 2,
        "education": "BS in CS or related field",
        "seniority_levels": ["Junior", "Mid", "Senior"],
        "remote_friendly": True,
        "salary_range": "$120k-$200k"
    },
    "Senior Backend Engineer": {
        "required_skills": ["Python", "Go", "SQL", "System Design", "PostgreSQL"],
        "preferred_skills": ["Redis", "Kafka", "AWS", "Kubernetes", "Microservices"],
        "years_experience": 5,
        "education": "BS in CS or related field",
        "seniority_levels": ["Senior"],
        "remote_friendly": True,
        "salary_range": "$150k-$220k"
    },
    "Frontend Engineer": {
        "required_skills": ["React", "TypeScript", "JavaScript", "HTML/CSS"],
        "preferred_skills": ["Next.js", "Vue", "GraphQL", "Testing", "Tailwind"],
        "years_experience": 2,
        "education": "BS in CS or self-taught",
        "seniority_levels": ["Junior", "Mid", "Senior"],
        "remote_friendly": True,
        "salary_range": "$100k-$180k"
    },
    "Senior Frontend Engineer": {
        "required_skills": ["React", "TypeScript", "System Design", "Performance"],
        "preferred_skills": ["Next.js", "Vue", "GraphQL", "Testing", "State Management"],
        "years_experience": 5,
        "education": "BS in CS or self-taught",
        "seniority_levels": ["Senior"],
        "remote_friendly": True,
        "salary_range": "$140k-$200k"
    },
    "Fullstack Engineer": {
        "required_skills": ["React", "Node.js", "TypeScript", "SQL"],
        "preferred_skills": ["Python", "AWS", "Docker", "GraphQL", "PostgreSQL"],
        "years_experience": 3,
        "education": "BS in CS or related field",
        "seniority_levels": ["Mid", "Senior"],
        "remote_friendly": True,
        "salary_range": "$130k-$200k"
    },
    "DevOps Engineer": {
        "required_skills": ["AWS", "Docker", "Kubernetes", "CI/CD", "Linux"],
        "preferred_skills": ["Terraform", "Ansible", "Python", "Monitoring", "Security"],
        "years_experience": 3,
        "education": "BS in CS or related field",
        "seniority_levels": ["Mid", "Senior"],
        "remote_friendly": True,
        "salary_range": "$140k-$200k"
    },
    "SRE": {
        "required_skills": ["AWS", "Kubernetes", "Python", "Linux", "Monitoring"],
        "preferred_skills": ["Go", "Terraform", "Prometheus", "Grafana", "On-call"],
        "years_experience": 4,
        "education": "BS in CS or related field",
        "seniority_levels": ["Mid", "Senior"],
        "remote_friendly": True,
        "salary_range": "$150k-$220k"
    },
    "Site Reliability Engineer": {
        "required_skills": ["AWS", "Kubernetes", "Python", "Linux", "Monitoring"],
        "preferred_skills": ["Go", "Terraform", "Prometheus", "Grafana", "On-call"],
        "years_experience": 4,
        "education": "BS in CS or related field",
        "seniority_levels": ["Mid", "Senior"],
        "remote_friendly": True,
        "salary_range": "$150k-$220k"
    },
    "Data Engineer": {
        "required_skills": ["Python", "SQL", "Spark", "Airflow", "ETL"],
        "preferred_skills": ["dbt", "Snowflake", "Kafka", "AWS", "Data Modeling"],
        "years_experience": 3,
        "education": "BS in CS, Data Science, or related",
        "seniority_levels": ["Mid", "Senior"],
        "remote_friendly": True,
        "salary_range": "$140k-$200k"
    },
    "Data Scientist": {
        "required_skills": ["Python", "SQL", "Machine Learning", "Statistics"],
        "preferred_skills": ["R", "Deep Learning", "A/B Testing", "Pandas", "Visualization"],
        "years_experience": 2,
        "education": "MS in Stats, Math, CS, or related",
        "seniority_levels": ["Junior", "Mid", "Senior"],
        "remote_friendly": True,
        "salary_range": "$120k-$180k"
    },
    "iOS Engineer": {
        "required_skills": ["Swift", "iOS SDK", "Xcode", "UIKit"],
        "preferred_skills": ["SwiftUI", "Objective-C", "Core Data", "Testing"],
        "years_experience": 3,
        "education": "BS in CS or self-taught",
        "seniority_levels": ["Mid", "Senior"],
        "remote_friendly": True,
        "salary_range": "$130k-$190k"
    },
    "Android Engineer": {
        "required_skills": ["Kotlin", "Android SDK", "Android Studio"],
        "preferred_skills": ["Java", "Jetpack Compose", "Testing", "Coroutines"],
        "years_experience": 3,
        "education": "BS in CS or self-taught",
        "seniority_levels": ["Mid", "Senior"],
        "remote_friendly": True,
        "salary_range": "$130k-$190k"
    },
    "Security Engineer": {
        "required_skills": ["Security", "Python", "Linux", "Network Security"],
        "preferred_skills": ["AWS Security", "Penetration Testing", "SIEM", "Compliance"],
        "years_experience": 4,
        "education": "BS in CS or Security",
        "seniority_levels": ["Mid", "Senior"],
        "remote_friendly": True,
        "salary_range": "$150k-$220k"
    },

    # Product & Design
    "Product Manager": {
        "required_skills": ["Product Strategy", "User Research", "Roadmapping", "Agile"],
        "preferred_skills": ["SQL", "Data Analysis", "A/B Testing", "Technical Background"],
        "years_experience": 3,
        "education": "BS/MBA preferred",
        "seniority_levels": ["Mid", "Senior"],
        "remote_friendly": True,
        "salary_range": "$130k-$200k"
    },
    "Senior Product Manager": {
        "required_skills": ["Product Strategy", "Roadmapping", "Stakeholder Management", "Metrics"],
        "preferred_skills": ["SQL", "Technical Background", "0-to-1 Experience", "B2B"],
        "years_experience": 5,
        "education": "BS/MBA preferred",
        "seniority_levels": ["Senior"],
        "remote_friendly": True,
        "salary_range": "$160k-$230k"
    },
    "Product Designer": {
        "required_skills": ["Figma", "User Research", "Prototyping", "Visual Design"],
        "preferred_skills": ["Design Systems", "User Testing", "CSS", "Animation"],
        "years_experience": 3,
        "education": "Design degree or portfolio",
        "seniority_levels": ["Mid", "Senior"],
        "remote_friendly": True,
        "salary_range": "$120k-$180k"
    },
    "UX Designer": {
        "required_skills": ["User Research", "Wireframing", "Prototyping", "Figma"],
        "preferred_skills": ["User Testing", "Information Architecture", "Accessibility"],
        "years_experience": 2,
        "education": "Design degree or portfolio",
        "seniority_levels": ["Junior", "Mid", "Senior"],
        "remote_friendly": True,
        "salary_range": "$100k-$160k"
    },

    # Leadership
    "Engineering Manager": {
        "required_skills": ["People Management", "Technical Leadership", "Hiring", "1:1s"],
        "preferred_skills": ["Agile", "System Design", "Performance Reviews", "Strategy"],
        "years_experience": 6,
        "education": "BS in CS or related",
        "seniority_levels": ["Manager"],
        "remote_friendly": True,
        "salary_range": "$180k-$250k"
    },
    "VP Engineering": {
        "required_skills": ["Engineering Leadership", "Strategy", "Scaling Teams", "Executive Presence"],
        "preferred_skills": ["Public Company Experience", "M&A", "Board Presentation"],
        "years_experience": 12,
        "education": "BS/MS in CS",
        "seniority_levels": ["VP"],
        "remote_friendly": False,
        "salary_range": "$250k-$400k"
    },
    "CTO": {
        "required_skills": ["Technology Strategy", "Executive Leadership", "Board Presence"],
        "preferred_skills": ["Fundraising", "Public Speaking", "Previous Founder Experience"],
        "years_experience": 15,
        "education": "BS/MS in CS",
        "seniority_levels": ["C-Level"],
        "remote_friendly": False,
        "salary_range": "$300k-$500k+"
    },
}

# Skill categories for suggestions
SKILL_CATEGORIES = {
    "languages": ["Python", "JavaScript", "TypeScript", "Go", "Java", "Kotlin", "Swift", "Rust", "C++"],
    "frontend": ["React", "Vue", "Angular", "Next.js", "Svelte", "Tailwind", "CSS"],
    "backend": ["Node.js", "Django", "FastAPI", "Spring", "Rails", "GraphQL", "REST"],
    "data": ["SQL", "PostgreSQL", "MongoDB", "Redis", "Elasticsearch", "Snowflake"],
    "ml": ["PyTorch", "TensorFlow", "Scikit-learn", "Pandas", "NumPy", "MLOps"],
    "devops": ["AWS", "GCP", "Azure", "Docker", "Kubernetes", "Terraform", "CI/CD"],
    "tools": ["Git", "Jira", "Figma", "Notion", "Slack"],
}


class RoleRequirements(BaseModel):
    """Predicted requirements for a role."""
    role_title: str
    required_skills: list[str]
    preferred_skills: list[str]
    years_experience: int
    education: str
    seniority_levels: list[str]
    remote_friendly: bool
    salary_range: str
    confidence: float  # How confident we are in these predictions


class SkillPredictor:
    """
    Predict skills and requirements for roles.

    Uses:
    1. Role database (industry standards)
    2. Company history (past hires)
    3. Role title parsing (extract level, domain)
    """

    def __init__(self):
        pass

    def predict_requirements(
        self,
        role_title: str,
        company_context: dict = {}
    ) -> RoleRequirements:
        """
        Predict requirements for a role.

        Args:
            role_title: The role to predict for
            company_context: Optional company info for customization

        Returns:
            RoleRequirements with predicted skills, experience, etc.
        """
        # Try exact match first
        if role_title in ROLE_REQUIREMENTS:
            reqs = ROLE_REQUIREMENTS[role_title]
            return RoleRequirements(
                role_title=role_title,
                confidence=0.95,
                **reqs
            )

        # Try fuzzy match
        role_lower = role_title.lower()
        for known_role, reqs in ROLE_REQUIREMENTS.items():
            if known_role.lower() in role_lower or role_lower in known_role.lower():
                return RoleRequirements(
                    role_title=role_title,
                    confidence=0.8,
                    **reqs
                )

        # Fall back to parsing
        return self._parse_role_title(role_title)

    def _parse_role_title(self, role_title: str) -> RoleRequirements:
        """Parse a role title to infer requirements."""
        role_lower = role_title.lower()

        # Detect seniority
        seniority = "Mid"
        years = 3
        if "senior" in role_lower or "sr" in role_lower:
            seniority = "Senior"
            years = 5
        elif "staff" in role_lower:
            seniority = "Staff"
            years = 7
        elif "principal" in role_lower:
            seniority = "Principal"
            years = 10
        elif "lead" in role_lower:
            seniority = "Lead"
            years = 6
        elif "junior" in role_lower or "jr" in role_lower:
            seniority = "Junior"
            years = 1
        elif "manager" in role_lower or "director" in role_lower:
            seniority = "Manager"
            years = 8

        # Detect domain
        required_skills = []
        preferred_skills = []

        if any(kw in role_lower for kw in ["ml", "machine learning", "ai"]):
            required_skills = ["Python", "Machine Learning", "PyTorch"]
            preferred_skills = ["TensorFlow", "Deep Learning", "MLOps"]
        elif any(kw in role_lower for kw in ["backend", "server", "api"]):
            required_skills = ["Python", "SQL", "REST APIs"]
            preferred_skills = ["Go", "AWS", "Docker"]
        elif any(kw in role_lower for kw in ["frontend", "ui", "web"]):
            required_skills = ["React", "TypeScript", "CSS"]
            preferred_skills = ["Next.js", "Testing", "GraphQL"]
        elif any(kw in role_lower for kw in ["fullstack", "full stack"]):
            required_skills = ["React", "Node.js", "SQL"]
            preferred_skills = ["TypeScript", "AWS", "Docker"]
        elif any(kw in role_lower for kw in ["devops", "sre", "platform", "infra"]):
            required_skills = ["AWS", "Kubernetes", "Docker", "Linux"]
            preferred_skills = ["Terraform", "Python", "Monitoring"]
        elif any(kw in role_lower for kw in ["data engineer"]):
            required_skills = ["Python", "SQL", "ETL"]
            preferred_skills = ["Spark", "Airflow", "dbt"]
        elif any(kw in role_lower for kw in ["data scientist", "data science"]):
            required_skills = ["Python", "SQL", "Statistics"]
            preferred_skills = ["Machine Learning", "Visualization"]
        elif any(kw in role_lower for kw in ["product manager", "pm"]):
            required_skills = ["Product Strategy", "Roadmapping"]
            preferred_skills = ["SQL", "Technical Background"]
        elif any(kw in role_lower for kw in ["design", "ux", "ui"]):
            required_skills = ["Figma", "User Research"]
            preferred_skills = ["Prototyping", "Design Systems"]
        else:
            # Generic engineering
            required_skills = ["Problem Solving", "Communication"]
            preferred_skills = ["Relevant Domain Experience"]

        return RoleRequirements(
            role_title=role_title,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            years_experience=years,
            education="BS in relevant field",
            seniority_levels=[seniority],
            remote_friendly=True,
            salary_range="Market rate",
            confidence=0.5
        )

    def suggest_skills(
        self,
        partial_skill: str,
        category: Optional[str] = None,
        limit: int = 5
    ) -> list[str]:
        """
        Suggest skills based on partial input.

        Args:
            partial_skill: What user has typed
            category: Optional category filter
            limit: Max suggestions

        Returns:
            List of skill suggestions
        """
        partial_lower = partial_skill.lower()
        suggestions = []

        # Search by category if specified
        if category and category in SKILL_CATEGORIES:
            skills = SKILL_CATEGORIES[category]
        else:
            # Search all categories
            skills = []
            for cat_skills in SKILL_CATEGORIES.values():
                skills.extend(cat_skills)

        for skill in skills:
            if partial_lower in skill.lower():
                suggestions.append(skill)
                if len(suggestions) >= limit:
                    break

        return suggestions

    def get_related_skills(self, skill: str, limit: int = 5) -> list[str]:
        """Get skills related to a given skill."""
        skill_lower = skill.lower()

        # Find which category this skill belongs to
        for category, skills in SKILL_CATEGORIES.items():
            for s in skills:
                if skill_lower == s.lower():
                    # Return other skills from same category
                    return [other for other in skills if other.lower() != skill_lower][:limit]

        return []

    def get_all_roles(self) -> list[str]:
        """Get all known roles."""
        return list(ROLE_REQUIREMENTS.keys())

    def get_roles_by_skill(self, skill: str) -> list[str]:
        """Get roles that require or prefer a skill."""
        matching_roles = []

        for role, reqs in ROLE_REQUIREMENTS.items():
            all_skills = reqs["required_skills"] + reqs["preferred_skills"]
            if any(skill.lower() in s.lower() for s in all_skills):
                matching_roles.append(role)

        return matching_roles
