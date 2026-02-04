"""Parse coverage reports to extract metrics."""

import xml.etree.ElementTree as ET
from dataclasses import dataclass

from app.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class CoverageMetrics:
    """Metrics extracted from coverage reports."""

    line_coverage_percent: float
    branch_coverage_percent: float | None
    lines_covered: int
    lines_total: int
    uncovered_files: dict[str, list[int]]  # file -> uncovered line numbers


class CoverageParser:
    """Parse coverage.xml (Cobertura format) to extract metrics."""

    def parse(self, xml_content: str) -> CoverageMetrics:
        """Parse coverage XML.

        Args:
            xml_content: Raw coverage.xml content

        Returns:
            CoverageMetrics with extracted data
        """
        try:
            root = ET.fromstring(xml_content)
            return self._parse_cobertura(root)
        except ET.ParseError as e:
            logger.error("Failed to parse coverage XML", error=str(e))
            return CoverageMetrics(
                line_coverage_percent=0.0,
                branch_coverage_percent=None,
                lines_covered=0,
                lines_total=0,
                uncovered_files={},
            )

    def _parse_cobertura(self, root: ET.Element) -> CoverageMetrics:
        """Parse Cobertura format coverage.xml."""
        # Get overall coverage from root attributes
        line_rate = float(root.get("line-rate", "0"))
        branch_rate = root.get("branch-rate")

        line_coverage_percent = line_rate * 100
        branch_coverage_percent = float(branch_rate) * 100 if branch_rate else None

        # Count lines
        lines_covered = 0
        lines_total = 0
        uncovered_files: dict[str, list[int]] = {}

        for package in root.findall(".//package"):
            for cls in package.findall(".//class"):
                filename = cls.get("filename", "unknown")
                file_uncovered = []

                for line in cls.findall(".//line"):
                    lines_total += 1
                    hits = int(line.get("hits", "0"))

                    if hits > 0:
                        lines_covered += 1
                    else:
                        line_number = int(line.get("number", "0"))
                        file_uncovered.append(line_number)

                if file_uncovered:
                    uncovered_files[filename] = file_uncovered

        logger.info(
            "Coverage parsed",
            line_coverage=round(line_coverage_percent, 1),
            lines_covered=lines_covered,
            lines_total=lines_total,
        )

        return CoverageMetrics(
            line_coverage_percent=round(line_coverage_percent, 2),
            branch_coverage_percent=round(branch_coverage_percent, 2) if branch_coverage_percent else None,
            lines_covered=lines_covered,
            lines_total=lines_total,
            uncovered_files=uncovered_files,
        )

    def compute_delta(
        self,
        current: CoverageMetrics,
        baseline: CoverageMetrics,
    ) -> float:
        """Compute coverage delta from baseline.

        Returns:
            Percentage point change (positive = improvement)
        """
        return current.line_coverage_percent - baseline.line_coverage_percent
