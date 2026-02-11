"""
Reverse Reference Generator - Ask network for recommendations.

The most powerful move: "Who's the best ML engineer you've ever worked with?"

Why reverse reference beats API search:
1. Your network has already filtered for quality
2. They've seen the person's actual work (not just resume)
3. Warm intro is built-in (they recommended them)
4. Trust transfers through the relationship
"""

import logging
from typing import Optional
from uuid import UUID

from app.services.company_db import CompanyDBService
from .message_generator import ActivationMessageGenerator

logger = logging.getLogger(__name__)


class ReverseReferenceGenerator:
    """
    Generate "reverse reference" requests for network members.

    Instead of searching for candidates, we ask our network:
    "Who would YOU recommend for this role?"
    """

    def __init__(self, company_id: UUID):
        self.company_id = company_id
        self.db = CompanyDBService()
        self.message_gen = ActivationMessageGenerator()

    def _to_dict(self, obj) -> dict:
        """Convert a Pydantic model or object to a dict."""
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        elif hasattr(obj, "dict"):
            return obj.dict()
        elif isinstance(obj, dict):
            return obj
        else:
            return dict(obj)

    async def generate_activation_requests(
        self,
        role_title: str,
        required_skills: list[str] = None,
        target_person_ids: list[UUID] = None,
        limit: int = 50
    ) -> list[dict]:
        """
        Generate personalized activation requests.

        Args:
            role_title: The role we're hiring for (e.g., "ML Engineer")
            required_skills: Skills to highlight
            target_person_ids: Specific people to ask (or None for auto-select)
            limit: Max number of requests to generate

        Returns:
            List of activation request dicts ready to send/save
        """
        # Get best people to ask
        if target_person_ids:
            targets = await self._get_specific_people(target_person_ids)
        else:
            targets = await self._select_best_targets(role_title, limit)

        requests = []

        for person in targets:
            # Generate personalized message
            message = self.message_gen.generate_reverse_reference_message(
                person=person,
                role_title=role_title,
                required_skills=required_skills
            )

            # Calculate priority score
            priority = self._calculate_ask_priority(person, role_title)

            request = {
                "target_person_id": person.get("id"),
                "target_name": person.get("full_name"),
                "target_title": person.get("current_title"),
                "target_company": person.get("current_company"),
                "target_linkedin": person.get("linkedin_url"),
                "template_type": "reverse_reference",
                "role_asked_about": role_title,
                "skills_mentioned": required_skills or [],
                "message_content": message,
                "priority_score": priority,
                "ask_reason": self._get_ask_reason(person, role_title),
                "status": "pending"
            }

            requests.append(request)

        # Sort by priority
        requests.sort(key=lambda x: x["priority_score"], reverse=True)

        logger.info(f"Generated {len(requests)} reverse reference requests for {role_title}")

        return requests

    async def _select_best_targets(
        self,
        role_title: str,
        limit: int
    ) -> list[dict]:
        """
        Select the best people in network to ask for recommendations.

        Priority order:
        1. People currently in relevant roles (they know peers)
        2. People at companies known for this role (Google for ML, etc.)
        3. People with long tenure (more connections)
        4. Recruiters (they know who's looking)
        """
        # Get all network connections
        all_people_raw = await self.db.get_people(
            self.company_id,
            limit=10000,
            filters={"is_from_network": True}
        )
        all_people = [self._to_dict(p) for p in all_people_raw]

        scored_people = []

        role_lower = role_title.lower()

        # Role-specific keywords for matching
        role_keywords = self._get_role_keywords(role_title)

        for person in all_people:
            score = 0.0
            reasons = []

            title = (person.get("current_title") or "").lower()
            company = (person.get("current_company") or "").lower()

            # 1. Currently in relevant role (highest signal - they know peers)
            if any(kw in title for kw in role_keywords["primary"]):
                score += 0.4
                reasons.append(f"Currently works as {person.get('current_title')}")

            # 2. At a company known for this role
            if any(c in company for c in role_keywords["top_companies"]):
                score += 0.3
                reasons.append(f"Works at {person.get('current_company')}")

            # 3. Senior/lead role (more connections)
            if any(level in title for level in ["senior", "staff", "principal", "lead", "director", "head"]):
                score += 0.15
                reasons.append("Senior level (broader network)")

            # 4. Recruiter (knows who's looking)
            if any(kw in title for kw in ["recruit", "talent", "sourcer"]):
                score += 0.25
                reasons.append("Recruiter (knows who's looking)")

            # 5. Manager/director (has team knowledge)
            if any(kw in title for kw in ["manager", "director", "vp", "head of"]):
                score += 0.1
                reasons.append("Manager (knows team dynamics)")

            if score > 0:
                person["ask_score"] = score
                person["ask_reasons"] = reasons
                scored_people.append(person)

        # Sort by score and return top N
        scored_people.sort(key=lambda x: x["ask_score"], reverse=True)

        return scored_people[:limit]

    async def _get_specific_people(self, person_ids: list[UUID]) -> list[dict]:
        """Get specific people by ID."""
        people = []
        for pid in person_ids:
            person = await self.db.get_person(self.company_id, pid)
            if person:
                people.append(self._to_dict(person))
        return people

    def _get_role_keywords(self, role_title: str) -> dict:
        """Get relevant keywords for a role."""
        role_lower = role_title.lower()

        # Default keywords
        keywords = {
            "primary": role_lower.split(),
            "secondary": [],
            "top_companies": []
        }

        # Role-specific mappings
        role_mappings = {
            "ml engineer": {
                "primary": ["machine learning", "ml ", " ml", "deep learning", "ai engineer"],
                "secondary": ["data scientist", "research engineer", "applied scientist"],
                "top_companies": ["google", "meta", "openai", "anthropic", "deepmind", "nvidia", "microsoft", "amazon"]
            },
            "machine learning engineer": {
                "primary": ["machine learning", "ml ", " ml", "deep learning", "ai engineer"],
                "secondary": ["data scientist", "research engineer", "applied scientist"],
                "top_companies": ["google", "meta", "openai", "anthropic", "deepmind", "nvidia", "microsoft", "amazon"]
            },
            "data scientist": {
                "primary": ["data scientist", "data science", "analytics"],
                "secondary": ["ml engineer", "machine learning", "statistician"],
                "top_companies": ["google", "meta", "netflix", "airbnb", "uber", "linkedin"]
            },
            "software engineer": {
                "primary": ["software engineer", "software developer", "swe", "backend", "frontend", "fullstack"],
                "secondary": ["developer", "programmer", "engineer"],
                "top_companies": ["google", "meta", "apple", "amazon", "microsoft", "stripe", "airbnb"]
            },
            "backend engineer": {
                "primary": ["backend", "back-end", "server", "api engineer"],
                "secondary": ["software engineer", "platform engineer"],
                "top_companies": ["stripe", "datadog", "mongodb", "snowflake", "cloudflare"]
            },
            "frontend engineer": {
                "primary": ["frontend", "front-end", "ui engineer", "react", "web developer"],
                "secondary": ["software engineer", "full stack"],
                "top_companies": ["airbnb", "stripe", "figma", "vercel", "notion"]
            },
        }

        # Check for matches
        for role_pattern, mapping in role_mappings.items():
            if role_pattern in role_lower or role_lower in role_pattern:
                return mapping

        return keywords

    def _calculate_ask_priority(self, person: dict, role_title: str) -> float:
        """Calculate priority for asking this person."""
        return person.get("ask_score", 0.5)

    def _get_ask_reason(self, person: dict, role_title: str) -> str:
        """Get human-readable reason for asking this person."""
        reasons = person.get("ask_reasons", [])
        if reasons:
            return "; ".join(reasons[:2])  # Top 2 reasons
        return "Network connection"

    async def save_activation_requests(
        self,
        requests: list[dict]
    ) -> list[dict]:
        """
        Save activation requests to database.

        Args:
            requests: List of request dicts from generate_activation_requests

        Returns:
            List of saved requests with IDs
        """
        saved = []

        for request in requests:
            # Save to activation_requests table
            record = await self.db.create_activation_request(
                company_id=self.company_id,
                target_person_id=request["target_person_id"],
                template_type=request["template_type"],
                message_content=request["message_content"],
                metadata={
                    "role_asked_about": request["role_asked_about"],
                    "skills_mentioned": request["skills_mentioned"],
                    "priority_score": request["priority_score"],
                    "ask_reason": request["ask_reason"]
                }
            )

            if record:
                saved.append({
                    **request,
                    "id": record.get("id"),
                    "created_at": record.get("created_at")
                })

        logger.info(f"Saved {len(saved)} activation requests")

        return saved

    async def get_pending_requests(self) -> list[dict]:
        """Get all pending activation requests."""
        requests = await self.db.get_activation_requests(
            company_id=self.company_id,
            status="pending"
        )
        return [self._to_dict(r) for r in requests]

    async def mark_request_sent(self, request_id: UUID) -> dict:
        """Mark an activation request as sent."""
        return await self.db.update_activation_request(
            request_id=request_id,
            status="sent"
        )

    async def mark_request_responded(
        self,
        request_id: UUID,
        had_recommendation: bool = False
    ) -> dict:
        """Mark an activation request as responded to."""
        status = "responded_with_rec" if had_recommendation else "responded_no_rec"
        return await self.db.update_activation_request(
            request_id=request_id,
            status=status
        )


class RecommendationTracker:
    """
    Track recommendations received from the network.

    When a network member recommends someone, we:
    1. Store the recommendation
    2. Generate an intro request message
    3. Track the pipeline: recommendation -> intro -> contacted -> converted
    """

    def __init__(self, company_id: UUID):
        self.company_id = company_id
        self.db = CompanyDBService()
        self.message_gen = ActivationMessageGenerator()

    async def record_recommendation(
        self,
        recommender_id: UUID,
        activation_request_id: UUID = None,
        recommended_name: str = None,
        recommended_linkedin: str = None,
        recommended_email: str = None,
        recommended_context: str = None,
        recommended_current_company: str = None,
        recommended_current_title: str = None
    ) -> dict:
        """
        Record a recommendation from a network member.

        Args:
            recommender_id: ID of the person who made the recommendation
            activation_request_id: The request that triggered this (if any)
            recommended_name: Name of the recommended person
            recommended_linkedin: Their LinkedIn URL
            recommended_email: Their email (if provided)
            recommended_context: Why they were recommended
            recommended_current_company: Their current company
            recommended_current_title: Their current title

        Returns:
            The saved recommendation with intro message
        """
        # Get recommender details
        recommender = await self.db.get_person(self.company_id, recommender_id)
        recommender_name = recommender.get("full_name") if recommender else "your connection"

        # Generate intro request message
        intro_message = self.message_gen.generate_intro_request_message(
            recommender_name=recommender_name,
            recommended_name=recommended_name,
            recommended_context=recommended_context
        )

        # Save to database
        recommendation = await self.db.create_recommendation(
            company_id=self.company_id,
            recommender_id=recommender_id,
            activation_request_id=activation_request_id,
            recommended_name=recommended_name,
            recommended_linkedin=recommended_linkedin,
            recommended_email=recommended_email,
            recommended_context=recommended_context,
            recommended_current_company=recommended_current_company,
            recommended_current_title=recommended_current_title
        )

        if recommendation:
            recommendation["intro_request_message"] = intro_message

        logger.info(f"Recorded recommendation: {recommended_name} from {recommender_name}")

        return recommendation

    async def get_recommendations(
        self,
        status: str = None
    ) -> list[dict]:
        """Get all recommendations, optionally filtered by status."""
        recommendations = await self.db.get_recommendations(
            company_id=self.company_id,
            status=status
        )
        return recommendations

    async def update_recommendation_status(
        self,
        recommendation_id: UUID,
        status: str
    ) -> dict:
        """
        Update recommendation status.

        Statuses:
        - new: Just received
        - intro_requested: Asked for intro
        - intro_made: Intro was made
        - contacted: We reached out
        - responded: They responded
        - converted: They joined the pipeline
        - declined: They said no
        """
        return await self.db.update_recommendation(
            recommendation_id=recommendation_id,
            status=status
        )

    async def get_recommendation_stats(self) -> dict:
        """Get statistics on recommendations."""
        all_recs = await self.get_recommendations()

        by_status = {}
        for rec in all_recs:
            status = rec.get("status", "new")
            by_status[status] = by_status.get(status, 0) + 1

        # Calculate conversion funnel
        total = len(all_recs)
        intro_requested = by_status.get("intro_requested", 0) + by_status.get("intro_made", 0) + by_status.get("contacted", 0) + by_status.get("responded", 0) + by_status.get("converted", 0)
        intro_made = by_status.get("intro_made", 0) + by_status.get("contacted", 0) + by_status.get("responded", 0) + by_status.get("converted", 0)
        contacted = by_status.get("contacted", 0) + by_status.get("responded", 0) + by_status.get("converted", 0)
        responded = by_status.get("responded", 0) + by_status.get("converted", 0)
        converted = by_status.get("converted", 0)

        return {
            "total_recommendations": total,
            "by_status": by_status,
            "funnel": {
                "recommendations": total,
                "intro_requested": intro_requested,
                "intro_made": intro_made,
                "contacted": contacted,
                "responded": responded,
                "converted": converted
            },
            "conversion_rates": {
                "rec_to_intro_request": intro_requested / total if total > 0 else 0,
                "intro_request_to_made": intro_made / intro_requested if intro_requested > 0 else 0,
                "intro_to_contact": contacted / intro_made if intro_made > 0 else 0,
                "contact_to_response": responded / contacted if contacted > 0 else 0,
                "response_to_convert": converted / responded if responded > 0 else 0
            }
        }
