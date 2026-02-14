"""
Company database service for Supabase.

Handles CRUD operations for companies, UMOs, roles, people, and data sources.
"""

import logging
from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

import httpx

from app.config import settings
from app.models.company import (
    Company,
    CompanyCreate,
    CompanyUpdate,
    CompanyUMO,
    CompanyUMOCreate,
    CompanyWithStats,
    DataSource,
    DataSourceCreate,
    DataSourceStatus,
    DataSourceType,
    Person,
    PersonCreate,
    PersonSource,
    Role,
    RoleCreate,
)

logger = logging.getLogger(__name__)


class CompanyDBService:
    """
    Service for managing company data in Supabase.

    Handles all database operations for the onboarding flow (Stage 0)
    and data import (Stage 1).
    """

    def __init__(self):
        self.base_url = settings.supabase_url
        self.api_key = settings.supabase_key
        self.headers = {
            "apikey": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    async def _request(
        self,
        method: str,
        table: str,
        data: dict | list | None = None,
        params: dict[str, Any] | None = None,
    ) -> list[dict] | dict | None:
        """Make a request to Supabase REST API."""
        url = f"{self.base_url}/rest/v1/{table}"

        async with httpx.AsyncClient() as client:
            try:
                if method == "GET":
                    response = await client.get(
                        url,
                        headers=self.headers,
                        params=params or {},
                        timeout=30.0,
                    )
                elif method == "POST":
                    response = await client.post(
                        url,
                        headers=self.headers,
                        json=data,
                        params=params or {},
                        timeout=30.0,
                    )
                elif method == "PATCH":
                    response = await client.patch(
                        url,
                        headers=self.headers,
                        json=data,
                        params=params or {},
                        timeout=30.0,
                    )
                elif method == "DELETE":
                    response = await client.delete(
                        url,
                        headers=self.headers,
                        params=params or {},
                        timeout=30.0,
                    )
                else:
                    raise ValueError(f"Unsupported method: {method}")

                response.raise_for_status()

                if response.status_code == 204:
                    return None

                return response.json()

            except httpx.HTTPError as e:
                logger.error(f"Supabase request failed: {e}")
                raise

    # =========================================================================
    # COMPANY OPERATIONS
    # =========================================================================

    async def create_company(self, data: CompanyCreate) -> Company:
        """Create a new company."""
        company_id = uuid4()
        now = datetime.utcnow().isoformat()

        company_data = {
            "id": str(company_id),
            "name": data.name,
            "domain": data.domain,
            "stage": data.stage.value if data.stage else None,
            "industry": data.industry,
            "tech_stack": data.tech_stack,
            "team_size": data.team_size,
            "founder_email": data.founder_email,
            "founder_name": data.founder_name,
            "pinecone_namespace": f"company_{company_id}",
            "linkedin_imported": False,
            "existing_db_imported": False,
            "onboarding_complete": False,
            "people_count": 0,
            "roles_count": 0,
            "created_at": now,
            "updated_at": now,
        }

        result = await self._request("POST", "companies", company_data)

        if result and isinstance(result, list) and len(result) > 0:
            return self._dict_to_company(result[0])

        raise Exception("Failed to create company")

    async def get_company(self, company_id: UUID) -> Optional[Company]:
        """Get a company by ID."""
        params = {"id": f"eq.{company_id}"}
        result = await self._request("GET", "companies", params=params)

        if result and isinstance(result, list) and len(result) > 0:
            return self._dict_to_company(result[0])

        return None

    async def update_company(self, company_id: UUID, data: CompanyUpdate | dict) -> Optional[Company]:
        """Update a company."""
        # Handle both CompanyUpdate and dict
        if isinstance(data, dict):
            update_data = {k: v for k, v in data.items() if v is not None}
        else:
            update_data = {k: v for k, v in data.model_dump().items() if v is not None}

        if "stage" in update_data and update_data["stage"]:
            if hasattr(update_data["stage"], "value"):
                update_data["stage"] = update_data["stage"].value

        update_data["updated_at"] = datetime.utcnow().isoformat()

        params = {"id": f"eq.{company_id}"}
        result = await self._request("PATCH", "companies", update_data, params)

        if result and isinstance(result, list) and len(result) > 0:
            return self._dict_to_company(result[0])

        return None

    async def get_company_with_stats(self, company_id: UUID) -> Optional[CompanyWithStats]:
        """Get a company with all related data."""
        company = await self.get_company(company_id)
        if not company:
            return None

        # Get UMO
        umo = await self.get_company_umo(company_id)

        # Get roles
        roles = await self.get_roles(company_id)

        # Get recent imports
        imports = await self.get_data_sources(company_id, limit=5)

        # Count people
        people_count = await self.count_people(company_id)

        # Exclude people_count and roles_count from company to avoid duplicates
        company_data = company.model_dump(exclude={"people_count", "roles_count"})

        return CompanyWithStats(
            **company_data,
            umo=umo,
            roles=roles,
            recent_imports=imports,
            people_count=people_count,
            roles_count=len(roles),
        )

    def _dict_to_company(self, data: dict) -> Company:
        """Convert dict to Company model."""
        from app.models.company import CompanyStage

        stage = None
        if data.get("stage"):
            try:
                stage = CompanyStage(data["stage"])
            except ValueError:
                pass

        return Company(
            id=UUID(data["id"]),
            name=data["name"],
            domain=data.get("domain"),
            stage=stage,
            industry=data.get("industry"),
            tech_stack=data.get("tech_stack") or [],
            team_size=data.get("team_size"),
            founder_email=data["founder_email"],
            founder_name=data["founder_name"],
            founder_linkedin_url=data.get("founder_linkedin_url"),
            linkedin_imported=data.get("linkedin_imported", False),
            existing_db_imported=data.get("existing_db_imported", False),
            onboarding_complete=data.get("onboarding_complete", False),
            pinecone_namespace=data.get("pinecone_namespace"),
            people_count=data.get("people_count", 0),
            roles_count=data.get("roles_count", 0),
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")) if data.get("created_at") else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00")) if data.get("updated_at") else datetime.utcnow(),
        )

    # =========================================================================
    # UMO OPERATIONS
    # =========================================================================

    async def create_or_update_umo(self, company_id: UUID, data: CompanyUMOCreate) -> CompanyUMO:
        """Create or update a company's UMO."""
        existing = await self.get_company_umo(company_id)

        now = datetime.utcnow().isoformat()

        # Generate UMO text for embedding
        umo_text = self._generate_umo_text(data)

        umo_data = {
            "company_id": str(company_id),
            "preferred_backgrounds": data.preferred_backgrounds,
            "must_have_traits": data.must_have_traits,
            "anti_patterns": data.anti_patterns,
            "culture_values": data.culture_values,
            "work_style": data.work_style,
            "ideal_candidate_description": data.ideal_candidate_description,
            "umo_text": umo_text,
            "updated_at": now,
        }

        if existing:
            # Update
            params = {"company_id": f"eq.{company_id}"}
            result = await self._request("PATCH", "company_umos", umo_data, params)
        else:
            # Create
            umo_data["id"] = str(uuid4())
            umo_data["created_at"] = now
            result = await self._request("POST", "company_umos", umo_data)

        if result and isinstance(result, list) and len(result) > 0:
            return self._dict_to_umo(result[0])

        raise Exception("Failed to create/update UMO")

    async def get_company_umo(self, company_id: UUID) -> Optional[CompanyUMO]:
        """Get a company's UMO."""
        params = {"company_id": f"eq.{company_id}"}
        result = await self._request("GET", "company_umos", params=params)

        if result and isinstance(result, list) and len(result) > 0:
            return self._dict_to_umo(result[0])

        return None

    def _generate_umo_text(self, data: CompanyUMOCreate) -> str:
        """Generate text representation of UMO for embedding."""
        parts = []

        if data.ideal_candidate_description:
            parts.append(f"Ideal candidate: {data.ideal_candidate_description}")

        if data.preferred_backgrounds:
            parts.append(f"Preferred backgrounds: {', '.join(data.preferred_backgrounds)}")

        if data.must_have_traits:
            parts.append(f"Must have: {', '.join(data.must_have_traits)}")

        if data.anti_patterns:
            parts.append(f"Avoid: {', '.join(data.anti_patterns)}")

        if data.culture_values:
            parts.append(f"Culture values: {', '.join(data.culture_values)}")

        if data.work_style:
            parts.append(f"Work style: {data.work_style}")

        return "\n".join(parts)

    def _dict_to_umo(self, data: dict) -> CompanyUMO:
        """Convert dict to CompanyUMO model."""
        return CompanyUMO(
            id=UUID(data["id"]),
            company_id=UUID(data["company_id"]),
            preferred_backgrounds=data.get("preferred_backgrounds") or [],
            must_have_traits=data.get("must_have_traits") or [],
            anti_patterns=data.get("anti_patterns") or [],
            culture_values=data.get("culture_values") or [],
            work_style=data.get("work_style"),
            ideal_candidate_description=data.get("ideal_candidate_description"),
            umo_text=data.get("umo_text"),
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")) if data.get("created_at") else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00")) if data.get("updated_at") else datetime.utcnow(),
        )

    # =========================================================================
    # ROLE OPERATIONS
    # =========================================================================

    async def create_role(self, company_id: UUID, data: RoleCreate) -> Role:
        """Create a new role."""
        role_id = uuid4()
        now = datetime.utcnow().isoformat()

        role_data = {
            "id": str(role_id),
            "company_id": str(company_id),
            "title": data.title,
            "level": data.level.value if data.level else None,
            "department": data.department,
            "required_skills": data.required_skills,
            "preferred_skills": data.preferred_skills,
            "years_experience_min": data.years_experience_min,
            "years_experience_max": data.years_experience_max,
            "description": data.description,
            "location": data.location,
            "salary_min": data.salary_min,
            "salary_max": data.salary_max,
            "status": "active",
            "created_at": now,
            "updated_at": now,
        }

        result = await self._request("POST", "roles", role_data)

        if result and isinstance(result, list) and len(result) > 0:
            return self._dict_to_role(result[0])

        raise Exception("Failed to create role")

    async def get_roles(self, company_id: UUID) -> list[Role]:
        """Get all roles for a company."""
        params = {
            "company_id": f"eq.{company_id}",
            "order": "created_at.desc",
        }
        result = await self._request("GET", "roles", params=params)

        if result and isinstance(result, list):
            return [self._dict_to_role(r) for r in result]

        return []

    def _dict_to_role(self, data: dict) -> Role:
        """Convert dict to Role model."""
        from app.models.company import RoleLevel, RoleStatus

        level = None
        if data.get("level"):
            try:
                level = RoleLevel(data["level"])
            except ValueError:
                pass

        status = RoleStatus.ACTIVE
        if data.get("status"):
            try:
                status = RoleStatus(data["status"])
            except ValueError:
                pass

        return Role(
            id=UUID(data["id"]),
            company_id=UUID(data["company_id"]),
            title=data["title"],
            level=level,
            department=data.get("department"),
            required_skills=data.get("required_skills") or [],
            preferred_skills=data.get("preferred_skills") or [],
            years_experience_min=data.get("years_experience_min"),
            years_experience_max=data.get("years_experience_max"),
            description=data.get("description"),
            location=data.get("location"),
            salary_min=data.get("salary_min"),
            salary_max=data.get("salary_max"),
            status=status,
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")) if data.get("created_at") else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00")) if data.get("updated_at") else datetime.utcnow(),
        )

    # =========================================================================
    # PERSON OPERATIONS
    # =========================================================================

    async def create_person(self, company_id: UUID, data: PersonCreate) -> Person:
        """Create a new person."""
        person_id = uuid4()
        now = datetime.utcnow().isoformat()

        person_data = {
            "id": str(person_id),
            "company_id": str(company_id),
            "email": data.email,
            "linkedin_url": data.linkedin_url,
            "github_url": data.github_url,
            "full_name": data.full_name,
            "first_name": data.first_name,
            "last_name": data.last_name,
            "headline": data.headline,
            "location": data.location,
            "current_company": data.current_company,
            "current_title": data.current_title,
            "status": "unknown",
            "trust_score": 0.5,
            "is_from_network": False,
            "is_from_existing_db": False,
            "is_from_people_search": False,
            "first_seen": now,
            "created_at": now,
            "updated_at": now,
        }

        result = await self._request("POST", "people", person_data)

        if result and isinstance(result, list) and len(result) > 0:
            return self._dict_to_person(result[0])

        raise Exception("Failed to create person")

    async def find_person_by_email(self, company_id: UUID, email: str) -> Optional[Person]:
        """Find a person by email within a company's namespace."""
        params = {
            "company_id": f"eq.{company_id}",
            "email": f"eq.{email}",
        }
        result = await self._request("GET", "people", params=params)

        if result and isinstance(result, list) and len(result) > 0:
            return self._dict_to_person(result[0])

        return None

    async def find_person_by_linkedin(self, company_id: UUID, linkedin_url: str) -> Optional[Person]:
        """Find a person by LinkedIn URL within a company's namespace."""
        params = {
            "company_id": f"eq.{company_id}",
            "linkedin_url": f"eq.{linkedin_url}",
        }
        result = await self._request("GET", "people", params=params)

        if result and isinstance(result, list) and len(result) > 0:
            return self._dict_to_person(result[0])

        return None

    async def update_person(self, person_id: UUID, updates: dict) -> Optional[Person]:
        """Update a person."""
        updates["updated_at"] = datetime.utcnow().isoformat()
        params = {"id": f"eq.{person_id}"}
        result = await self._request("PATCH", "people", updates, params)

        if result and isinstance(result, list) and len(result) > 0:
            return self._dict_to_person(result[0])

        return None

    async def get_people(
        self,
        company_id: UUID,
        limit: int = 50,
        offset: int = 0,
        filters: dict = None
    ) -> list[Person]:
        """Get people for a company with optional filters.
        
        Automatically handles pagination for large result sets.
        Supabase has a max limit of 1000 per request, so we paginate
        when requesting more than that.
        """
        # Supabase max limit per request
        SUPABASE_MAX_LIMIT = 1000
        
        # If limit is within Supabase's max, make a single request
        if limit <= SUPABASE_MAX_LIMIT:
            params = {
                "company_id": f"eq.{company_id}",
                "limit": limit,
                "offset": offset,
                "order": "created_at.desc",
            }

            # Apply additional filters
            if filters:
                if filters.get("is_from_network") is True:
                    params["is_from_network"] = "eq.true"
                elif filters.get("is_from_network") is False:
                    params["is_from_network"] = "eq.false"

                if filters.get("is_from_existing_db") is True:
                    params["is_from_existing_db"] = "eq.true"

                if filters.get("is_from_people_search") is True:
                    params["is_from_people_search"] = "eq.true"

            result = await self._request("GET", "people", params=params)

            if result and isinstance(result, list):
                return [self._dict_to_person(p) for p in result]

            return []
        
        # For large limits, paginate through results
        all_people = []
        current_offset = offset
        remaining = limit
        
        while remaining > 0:
            batch_size = min(remaining, SUPABASE_MAX_LIMIT)
            
            params = {
                "company_id": f"eq.{company_id}",
                "limit": batch_size,
                "offset": current_offset,
                "order": "created_at.desc",
            }

            # Apply additional filters
            if filters:
                if filters.get("is_from_network") is True:
                    params["is_from_network"] = "eq.true"
                elif filters.get("is_from_network") is False:
                    params["is_from_network"] = "eq.false"

                if filters.get("is_from_existing_db") is True:
                    params["is_from_existing_db"] = "eq.true"

                if filters.get("is_from_people_search") is True:
                    params["is_from_people_search"] = "eq.true"

            result = await self._request("GET", "people", params=params)
            
            if not result or not isinstance(result, list) or len(result) == 0:
                # No more results
                break
            
            batch_people = [self._dict_to_person(p) for p in result]
            all_people.extend(batch_people)
            
            # If we got fewer results than requested, we've hit the end
            if len(result) < batch_size:
                break
            
            current_offset += batch_size
            remaining -= len(result)
        
        return all_people

    async def count_people(self, company_id: UUID) -> int:
        """Count people in a company's namespace."""
        # Use Supabase's count feature via headers
        url = f"{self.base_url}/rest/v1/people"
        headers = {
            **self.headers,
            "Prefer": "count=exact",
        }
        params = {
            "company_id": f"eq.{company_id}",
            "select": "id",
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    url,
                    headers=headers,
                    params=params,
                    timeout=30.0,
                )
                # Count is in the Content-Range header
                content_range = response.headers.get("content-range", "")
                if "/" in content_range:
                    return int(content_range.split("/")[1])
                return 0
            except Exception as e:
                logger.error(f"Failed to count people: {e}")
                return 0

    def _dict_to_person(self, data: dict) -> Person:
        """Convert dict to Person model."""
        from app.models.company import PersonStatus

        status = PersonStatus.UNKNOWN
        if data.get("status"):
            try:
                status = PersonStatus(data["status"])
            except ValueError:
                pass

        return Person(
            id=UUID(data["id"]),
            company_id=UUID(data["company_id"]),
            email=data.get("email"),
            linkedin_url=data.get("linkedin_url"),
            github_url=data.get("github_url"),
            full_name=data["full_name"],
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            headline=data.get("headline"),
            location=data.get("location"),
            current_company=data.get("current_company"),
            current_title=data.get("current_title"),
            status=status,
            trust_score=data.get("trust_score", 0.5),
            relevance_score=data.get("relevance_score"),
            is_from_network=data.get("is_from_network", False),
            is_from_existing_db=data.get("is_from_existing_db", False),
            is_from_people_search=data.get("is_from_people_search", False),
            pinecone_id=data.get("pinecone_id"),
            first_seen=datetime.fromisoformat(data["first_seen"].replace("Z", "+00:00")) if data.get("first_seen") else datetime.utcnow(),
            last_enriched=datetime.fromisoformat(data["last_enriched"].replace("Z", "+00:00")) if data.get("last_enriched") else None,
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")) if data.get("created_at") else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00")) if data.get("updated_at") else datetime.utcnow(),
        )

    # =========================================================================
    # DATA SOURCE OPERATIONS
    # =========================================================================

    async def create_data_source(self, company_id: UUID, data: DataSourceCreate) -> DataSource:
        """Create a new data source."""
        source_id = uuid4()
        now = datetime.utcnow().isoformat()

        source_data = {
            "id": str(source_id),
            "company_id": str(company_id),
            "type": data.type.value,
            "name": data.name,
            "status": "pending",
            "total_records": 0,
            "records_matched": 0,
            "records_created": 0,
            "records_failed": 0,
            "created_at": now,
        }

        result = await self._request("POST", "data_sources", source_data)

        if result and isinstance(result, list) and len(result) > 0:
            return self._dict_to_data_source(result[0])

        raise Exception("Failed to create data source")

    async def update_data_source(self, source_id: UUID, updates: dict) -> Optional[DataSource]:
        """Update a data source."""
        params = {"id": f"eq.{source_id}"}
        result = await self._request("PATCH", "data_sources", updates, params)

        if result and isinstance(result, list) and len(result) > 0:
            return self._dict_to_data_source(result[0])

        return None

    async def get_data_sources(self, company_id: UUID, limit: int = 10) -> list[DataSource]:
        """Get data sources for a company."""
        params = {
            "company_id": f"eq.{company_id}",
            "limit": limit,
            "order": "created_at.desc",
        }
        result = await self._request("GET", "data_sources", params=params)

        if result and isinstance(result, list):
            return [self._dict_to_data_source(s) for s in result]

        return []

    def _dict_to_data_source(self, data: dict) -> DataSource:
        """Convert dict to DataSource model."""
        return DataSource(
            id=UUID(data["id"]),
            company_id=UUID(data["company_id"]),
            type=DataSourceType(data["type"]),
            name=data.get("name"),
            file_url=data.get("file_url"),
            file_name=data.get("file_name"),
            total_records=data.get("total_records", 0),
            records_matched=data.get("records_matched", 0),
            records_created=data.get("records_created", 0),
            records_failed=data.get("records_failed", 0),
            status=DataSourceStatus(data["status"]),
            error_message=data.get("error_message"),
            imported_at=datetime.fromisoformat(data["imported_at"].replace("Z", "+00:00")) if data.get("imported_at") else None,
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")) if data.get("created_at") else datetime.utcnow(),
        )

    # =========================================================================
    # PERSON SOURCE (Junction) OPERATIONS
    # =========================================================================

    async def create_person_source(
        self,
        person_id: UUID,
        source_id: UUID,
        original_data: Optional[dict] = None,
        connected_on: Optional[datetime] = None,
        connection_strength: Optional[float] = None,
    ) -> PersonSource:
        """Create a person-source relationship."""
        ps_id = uuid4()
        now = datetime.utcnow().isoformat()

        ps_data = {
            "id": str(ps_id),
            "person_id": str(person_id),
            "source_id": str(source_id),
            "original_data": original_data,
            "connected_on": connected_on.isoformat() if connected_on else None,
            "connection_strength": connection_strength,
            "created_at": now,
        }

        result = await self._request("POST", "person_sources", ps_data)

        if result and isinstance(result, list) and len(result) > 0:
            return PersonSource(
                id=UUID(result[0]["id"]),
                person_id=person_id,
                source_id=source_id,
                original_data=original_data,
                connected_on=connected_on,
                connection_strength=connection_strength,
            )

        raise Exception("Failed to create person source")


    # =========================================================================
    # ACTIVATION REQUEST OPERATIONS (Intelligence System)
    # =========================================================================

    async def create_activation_request(
        self,
        company_id: UUID,
        target_person_id: UUID,
        template_type: str,
        message_content: str,
        metadata: dict = None
    ) -> dict:
        """Create an activation request."""
        request_id = uuid4()
        now = datetime.utcnow().isoformat()

        request_data = {
            "id": str(request_id),
            "company_id": str(company_id),
            "target_person_id": str(target_person_id),
            "template_type": template_type,
            "message_content": message_content,
            "metadata": metadata or {},
            "status": "pending",
            "created_at": now,
        }

        result = await self._request("POST", "activation_requests", request_data)

        if result and isinstance(result, list) and len(result) > 0:
            return result[0]

        return None

    async def get_activation_requests(
        self,
        company_id: UUID,
        status: str = None,
        limit: int = 100
    ) -> list[dict]:
        """Get activation requests for a company."""
        params = {
            "company_id": f"eq.{company_id}",
            "limit": limit,
            "order": "created_at.desc",
        }

        if status:
            params["status"] = f"eq.{status}"

        result = await self._request("GET", "activation_requests", params=params)

        if result and isinstance(result, list):
            return result

        return []

    async def update_activation_request(
        self,
        request_id: UUID,
        status: str = None,
        sent_at: datetime = None,
        responded_at: datetime = None
    ) -> dict:
        """Update an activation request."""
        updates = {}

        if status:
            updates["status"] = status
        if sent_at:
            updates["sent_at"] = sent_at.isoformat()
        if responded_at:
            updates["responded_at"] = responded_at.isoformat()

        if not updates:
            return None

        params = {"id": f"eq.{request_id}"}
        result = await self._request("PATCH", "activation_requests", updates, params)

        if result and isinstance(result, list) and len(result) > 0:
            return result[0]

        return None

    # =========================================================================
    # RECOMMENDATION OPERATIONS (Intelligence System)
    # =========================================================================

    async def create_recommendation(
        self,
        company_id: UUID,
        recommender_id: UUID,
        recommended_name: str,
        activation_request_id: UUID = None,
        recommended_linkedin: str = None,
        recommended_email: str = None,
        recommended_context: str = None,
        recommended_current_company: str = None,
        recommended_current_title: str = None
    ) -> dict:
        """Create a recommendation."""
        rec_id = uuid4()
        now = datetime.utcnow().isoformat()

        rec_data = {
            "id": str(rec_id),
            "company_id": str(company_id),
            "recommender_id": str(recommender_id),
            "activation_request_id": str(activation_request_id) if activation_request_id else None,
            "recommended_name": recommended_name,
            "recommended_linkedin": recommended_linkedin,
            "recommended_email": recommended_email,
            "recommended_context": recommended_context,
            "recommended_current_company": recommended_current_company,
            "recommended_current_title": recommended_current_title,
            "status": "new",
            "created_at": now,
        }

        result = await self._request("POST", "recommendations", rec_data)

        if result and isinstance(result, list) and len(result) > 0:
            return result[0]

        return None

    async def get_recommendations(
        self,
        company_id: UUID,
        status: str = None,
        limit: int = 100
    ) -> list[dict]:
        """Get recommendations for a company."""
        params = {
            "company_id": f"eq.{company_id}",
            "limit": limit,
            "order": "created_at.desc",
        }

        if status:
            params["status"] = f"eq.{status}"

        result = await self._request("GET", "recommendations", params=params)

        if result and isinstance(result, list):
            return result

        return []

    async def update_recommendation(
        self,
        recommendation_id: UUID,
        status: str = None
    ) -> dict:
        """Update a recommendation."""
        if not status:
            return None

        updates = {"status": status}
        params = {"id": f"eq.{recommendation_id}"}
        result = await self._request("PATCH", "recommendations", updates, params)

        if result and isinstance(result, list) and len(result) > 0:
            return result[0]

        return None

    async def get_person(self, company_id: UUID, person_id: UUID) -> Optional[dict]:
        """Get a person by ID."""
        params = {
            "company_id": f"eq.{company_id}",
            "id": f"eq.{person_id}",
        }
        result = await self._request("GET", "people", params=params)

        if result and isinstance(result, list) and len(result) > 0:
            return result[0]

        return None


# Global instance
company_db = CompanyDBService()
