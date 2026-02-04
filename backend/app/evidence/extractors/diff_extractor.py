"""Extract evidence from git diffs."""

import re
from dataclasses import dataclass

from app.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class DiffMetrics:
    """Metrics extracted from a diff."""

    files_changed: list[str]
    lines_added: int
    lines_removed: int
    test_files_changed: list[str]
    test_added: bool
    tests_added_count: int
    skipped_tests_added: int


class DiffExtractor:
    """Extract metrics from git diff patches."""

    # Patterns for test files
    TEST_FILE_PATTERNS = [
        r"test_.*\.py$",
        r".*_test\.py$",
        r"tests/.*\.py$",
        r".*\.test\.(js|ts|tsx)$",
        r".*\.spec\.(js|ts|tsx)$",
        r"__tests__/.*\.(js|ts|tsx)$",
    ]

    # Patterns for test functions
    TEST_FUNCTION_PATTERNS = [
        r"^\+\s*def test_",  # Python
        r"^\+\s*async def test_",  # Python async
        r"^\+\s*it\(",  # JavaScript/Jest
        r"^\+\s*test\(",  # JavaScript/Jest
        r"^\+\s*describe\(",  # JavaScript/Jest
    ]

    # Patterns for skipped tests
    SKIP_PATTERNS = [
        r"^\+.*@pytest\.mark\.skip",
        r"^\+.*@unittest\.skip",
        r"^\+.*\.skip\(",
        r"^\+.*xfail",
    ]

    def extract(self, diff_content: str) -> DiffMetrics:
        """Extract metrics from a unified diff.

        Args:
            diff_content: Raw unified diff content

        Returns:
            DiffMetrics with extracted data
        """
        files_changed = []
        test_files_changed = []
        lines_added = 0
        lines_removed = 0
        tests_added_count = 0
        skipped_tests_added = 0

        current_file = None

        for line in diff_content.split("\n"):
            # Track current file
            if line.startswith("diff --git"):
                match = re.search(r"b/(.+)$", line)
                if match:
                    current_file = match.group(1)
                    files_changed.append(current_file)

                    # Check if it's a test file
                    if self._is_test_file(current_file):
                        test_files_changed.append(current_file)

            # Count added/removed lines
            elif line.startswith("+") and not line.startswith("+++"):
                lines_added += 1

                # Check for test function additions
                if any(re.match(pattern, line) for pattern in self.TEST_FUNCTION_PATTERNS):
                    tests_added_count += 1

                # Check for skip additions
                if any(re.search(pattern, line) for pattern in self.SKIP_PATTERNS):
                    skipped_tests_added += 1

            elif line.startswith("-") and not line.startswith("---"):
                lines_removed += 1

        test_added = tests_added_count > 0 or len(test_files_changed) > 0

        logger.info(
            "Diff extracted",
            files_changed=len(files_changed),
            test_files=len(test_files_changed),
            lines_added=lines_added,
            lines_removed=lines_removed,
            tests_added=tests_added_count,
        )

        return DiffMetrics(
            files_changed=files_changed,
            lines_added=lines_added,
            lines_removed=lines_removed,
            test_files_changed=test_files_changed,
            test_added=test_added,
            tests_added_count=tests_added_count,
            skipped_tests_added=skipped_tests_added,
        )

    def _is_test_file(self, filepath: str) -> bool:
        """Check if a file path is a test file."""
        return any(
            re.search(pattern, filepath)
            for pattern in self.TEST_FILE_PATTERNS
        )
