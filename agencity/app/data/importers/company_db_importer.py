"""
Company Database CSV importer.

Imports a company's existing candidate/contact database from a CSV file.
Flexible format that accepts various column names.
"""

import csv
import io
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.models.company import (
    DataSourceCreate,
    DataSourceStatus,
    DataSourceType,
    ImportResult,
    PersonCreate,
)
from app.services.company_db import company_db
from app.data.entity_resolver import EntityResolver

logger = logging.getLogger(__name__)


class CompanyDBImporter:
    """
    Imports a company's existing database from CSV.

    Flexible format - tries to match common column names:
    - name, full_name, fullname -> full_name
    - email, email_address -> email
    - linkedin, linkedin_url -> linkedin_url
    - company, current_company, employer -> current_company
    - title, position, job_title, current_title -> current_title
    - location, city -> location
    - skills -> skills (stored in notes for now)
    - notes, comments -> notes
    """

    # Column name mappings (supports various naming conventions)
    COLUMN_MAP = {
        # Name variants
        "name": "full_name",
        "full_name": "full_name",
        "fullname": "full_name",
        "full name": "full_name",
        "candidate name": "full_name",
        "candidate": "full_name",
        # Email variants
        "email": "email",
        "email_address": "email",
        "email address": "email",
        "e-mail": "email",
        # LinkedIn variants
        "linkedin": "linkedin_url",
        "linkedin_url": "linkedin_url",
        "linkedin url": "linkedin_url",
        "linkedin profile": "linkedin_url",
        "profile": "linkedin_url",
        "url": "linkedin_url",
        # GitHub variants
        "github": "github_url",
        "github_url": "github_url",
        "github url": "github_url",
        # Company variants
        "company": "current_company",
        "current_company": "current_company",
        "current company": "current_company",
        "employer": "current_company",
        "organization": "current_company",
        # Title variants
        "title": "current_title",
        "position": "current_title",
        "job_title": "current_title",
        "job title": "current_title",
        "current_title": "current_title",
        "current title": "current_title",
        "role": "current_title",
        # Location variants
        "location": "location",
        "city": "location",
        "region": "location",
        # Other
        "skills": "skills",
        "notes": "notes",
        "comments": "notes",
        "headline": "headline",
        "first_name": "first_name",
        "first name": "first_name",
        "last_name": "last_name",
        "last name": "last_name",
    }

    async def import_csv(
        self,
        company_id: UUID,
        csv_content: str,
        filename: str = "database.csv",
    ) -> ImportResult:
        """
        Import a company's database CSV file.

        Args:
            company_id: The company to import into
            csv_content: The CSV file content as a string
            filename: Original filename for tracking

        Returns:
            ImportResult with stats about the import
        """
        # Create data source record
        source = await company_db.create_data_source(
            company_id,
            DataSourceCreate(
                type=DataSourceType.COMPANY_DATABASE,
                name=filename,
            ),
        )

        # Update status to processing
        await company_db.update_data_source(
            source.id,
            {"status": DataSourceStatus.PROCESSING.value},
        )

        # Parse CSV
        records = self._parse_csv(csv_content)
        total_records = len(records)

        logger.info(f"Parsed {total_records} records from {filename}")

        # Import each record
        resolver = EntityResolver(company_id)
        records_created = 0
        records_matched = 0
        records_failed = 0
        errors = []

        for record in records:
            try:
                # Skip records without a name
                full_name = record.get("full_name")
                if not full_name:
                    continue

                # Build headline from skills if available
                headline = record.get("headline")
                if not headline and record.get("skills"):
                    headline = record.get("skills")[:200]  # Limit length

                # Create PersonCreate
                person_data = PersonCreate(
                    email=record.get("email"),
                    linkedin_url=record.get("linkedin_url"),
                    github_url=record.get("github_url"),
                    full_name=full_name,
                    first_name=record.get("first_name"),
                    last_name=record.get("last_name"),
                    headline=headline,
                    location=record.get("location"),
                    current_company=record.get("current_company"),
                    current_title=record.get("current_title"),
                )

                # Resolve or create
                person, was_created = await resolver.resolve_or_create(
                    person_data,
                    is_from_existing_db=True,
                )

                if was_created:
                    records_created += 1
                else:
                    records_matched += 1

                # Create person-source relationship
                await company_db.create_person_source(
                    person_id=person.id,
                    source_id=source.id,
                    original_data=record,
                )

            except Exception as e:
                records_failed += 1
                name = record.get("full_name", "Unknown")
                errors.append(f"Failed to import {name}: {str(e)}")
                logger.error(f"Failed to import record: {e}")

        # Update data source with results
        await company_db.update_data_source(
            source.id,
            {
                "status": DataSourceStatus.COMPLETED.value,
                "total_records": total_records,
                "records_created": records_created,
                "records_matched": records_matched,
                "records_failed": records_failed,
                "imported_at": datetime.utcnow().isoformat(),
                "error_message": "\n".join(errors[:10]) if errors else None,
            },
        )

        # Update company people count
        people_count = await company_db.count_people(company_id)
        await company_db.update_company(
            company_id,
            {"people_count": people_count},
        )

        logger.info(
            f"Import complete: {records_created} created, "
            f"{records_matched} matched, {records_failed} failed"
        )

        return ImportResult(
            source_id=source.id,
            status=DataSourceStatus.COMPLETED,
            total_records=total_records,
            records_created=records_created,
            records_matched=records_matched,
            records_failed=records_failed,
            errors=errors[:10],
        )

    def _parse_csv(self, csv_content: str) -> list[dict]:
        """
        Parse CSV content into a list of normalized dictionaries.

        Handles various column naming conventions.
        """
        records = []

        # Clean content
        csv_content = csv_content.strip()
        if csv_content.startswith("\ufeff"):
            csv_content = csv_content[1:]

        # Parse CSV
        reader = csv.DictReader(io.StringIO(csv_content))

        for row in reader:
            try:
                # Normalize column names
                normalized = {}
                for key, value in row.items():
                    if key is None:
                        continue

                    # Normalize the key
                    key_lower = key.lower().strip()
                    mapped_key = self.COLUMN_MAP.get(key_lower)

                    if mapped_key:
                        # Clean the value
                        clean_value = value.strip() if value else None
                        if clean_value:
                            # Don't overwrite if we already have a value
                            if mapped_key not in normalized or not normalized[mapped_key]:
                                normalized[mapped_key] = clean_value

                # Build full_name from first/last if not present
                if not normalized.get("full_name"):
                    first = normalized.get("first_name", "")
                    last = normalized.get("last_name", "")
                    full = f"{first} {last}".strip()
                    if full:
                        normalized["full_name"] = full

                # Skip empty records
                if not normalized.get("full_name") and not normalized.get("email"):
                    continue

                records.append(normalized)

            except Exception as e:
                logger.warning(f"Failed to parse row: {e}")
                continue

        return records
