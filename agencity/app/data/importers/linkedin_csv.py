"""
LinkedIn Connections CSV importer.

Parses LinkedIn's "Connections.csv" export format and imports
people into the company's database.
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
    LinkedInConnection,
    PersonCreate,
)
from app.services.company_db import company_db
from app.data.entity_resolver import EntityResolver

logger = logging.getLogger(__name__)


class LinkedInImporter:
    """
    Imports LinkedIn connections from CSV export.

    Expected CSV format (LinkedIn's export):
    First Name,Last Name,URL,Email Address,Company,Position,Connected On

    Example row:
    Oliver,Fichte,https://www.linkedin.com/in/oliver-fichte,ofichte21@gmail.com,Stealth Startup,Founder,10 Feb 2026
    """

    # Column name mappings (LinkedIn uses these exact names)
    COLUMN_MAP = {
        "first name": "first_name",
        "last name": "last_name",
        "url": "linkedin_url",
        "email address": "email",
        "company": "company",
        "position": "position",
        "connected on": "connected_on",
    }

    async def import_csv(
        self,
        company_id: UUID,
        csv_content: str,
        filename: str = "Connections.csv",
    ) -> ImportResult:
        """
        Import a LinkedIn connections CSV file.

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
                type=DataSourceType.LINKEDIN_EXPORT,
                name=filename,
            ),
        )

        # Update status to processing
        await company_db.update_data_source(
            source.id,
            {"status": DataSourceStatus.PROCESSING.value},
        )

        # Parse CSV
        connections = self._parse_csv(csv_content)
        total_records = len(connections)

        logger.info(f"Parsed {total_records} connections from {filename}")

        # Import each connection
        resolver = EntityResolver(company_id)
        records_created = 0
        records_matched = 0
        records_failed = 0
        errors = []

        for conn in connections:
            try:
                # Create PersonCreate from connection
                person_data = PersonCreate(
                    email=conn.email,
                    linkedin_url=conn.linkedin_url,
                    full_name=conn.full_name,
                    first_name=conn.first_name,
                    last_name=conn.last_name,
                    current_company=conn.company,
                    current_title=conn.position,
                )

                # Resolve or create
                person, was_created = await resolver.resolve_or_create(
                    person_data,
                    is_from_network=True,
                )

                if was_created:
                    records_created += 1
                else:
                    records_matched += 1

                # Create person-source relationship
                await company_db.create_person_source(
                    person_id=person.id,
                    source_id=source.id,
                    original_data={
                        "first_name": conn.first_name,
                        "last_name": conn.last_name,
                        "email": conn.email,
                        "linkedin_url": conn.linkedin_url,
                        "company": conn.company,
                        "position": conn.position,
                        "connected_on": conn.connected_on.isoformat() if conn.connected_on else None,
                    },
                    connected_on=conn.connected_on,
                    connection_strength=self._calculate_connection_strength(conn.connected_on),
                )

            except Exception as e:
                records_failed += 1
                errors.append(f"Failed to import {conn.full_name}: {str(e)}")
                logger.error(f"Failed to import connection: {e}")

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
            errors=errors[:10],  # Limit errors in response
        )

    def _parse_csv(self, csv_content: str) -> list[LinkedInConnection]:
        """
        Parse CSV content into LinkedInConnection objects.

        Handles LinkedIn's specific CSV format with potential encoding issues.
        """
        connections = []

        # LinkedIn CSV sometimes has BOM or weird encoding
        csv_content = csv_content.strip()
        if csv_content.startswith("\ufeff"):
            csv_content = csv_content[1:]

        # LinkedIn exports have a "Notes:" section at the TOP - skip until we find the header
        lines = csv_content.split("\n")
        clean_lines = []
        found_header = False

        for line in lines:
            # Look for the header line
            if not found_header:
                if line.lower().startswith("first name,"):
                    found_header = True
                    clean_lines.append(line)
                continue

            # After header, collect data lines (stop at empty lines)
            if line.strip() == "":
                continue
            clean_lines.append(line)

        csv_content = "\n".join(clean_lines)

        # Parse CSV
        reader = csv.DictReader(io.StringIO(csv_content))

        for row in reader:
            try:
                # Normalize column names (LinkedIn uses Title Case)
                normalized = {}
                for key, value in row.items():
                    if key is None:
                        continue
                    normalized_key = self.COLUMN_MAP.get(key.lower().strip(), key.lower().strip())
                    normalized[normalized_key] = value.strip() if value else None

                # Parse connected_on date
                connected_on = self._parse_date(normalized.get("connected_on"))

                # Build full name
                first_name = normalized.get("first_name") or ""
                last_name = normalized.get("last_name") or ""
                full_name = f"{first_name} {last_name}".strip()

                if not full_name:
                    continue  # Skip rows without names

                conn = LinkedInConnection(
                    first_name=first_name,
                    last_name=last_name,
                    full_name=full_name,
                    linkedin_url=normalized.get("linkedin_url"),
                    email=normalized.get("email"),
                    company=normalized.get("company"),
                    position=normalized.get("position"),
                    connected_on=connected_on,
                )

                connections.append(conn)

            except Exception as e:
                logger.warning(f"Failed to parse row: {e}")
                continue

        return connections

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """
        Parse LinkedIn's date format.

        LinkedIn uses formats like:
        - "10 Feb 2026"
        - "10 February 2026"
        """
        if not date_str:
            return None

        date_str = date_str.strip()

        formats = [
            "%d %b %Y",  # "10 Feb 2026"
            "%d %B %Y",  # "10 February 2026"
            "%Y-%m-%d",  # ISO format fallback
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        return None

    def _calculate_connection_strength(self, connected_on: Optional[datetime]) -> float:
        """
        Calculate connection strength based on recency.

        More recent connections are considered stronger.
        """
        if not connected_on:
            return 0.5  # Default for unknown dates

        now = datetime.utcnow()
        days_ago = (now - connected_on).days

        if days_ago < 30:
            return 0.9  # Very recent
        elif days_ago < 90:
            return 0.8
        elif days_ago < 180:
            return 0.7
        elif days_ago < 365:
            return 0.6
        elif days_ago < 730:  # 2 years
            return 0.5
        else:
            return 0.4  # Older connections
