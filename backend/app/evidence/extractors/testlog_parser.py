"""Parse test output logs to extract metrics."""

import re
from dataclasses import dataclass

from app.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class TestLogMetrics:
    """Metrics extracted from test logs."""

    tests_passed: bool
    total_tests: int
    passed_count: int
    failed_count: int
    skipped_count: int
    error_count: int
    failed_test_names: list[str]
    error_messages: list[str]
    duration_seconds: float


class TestLogParser:
    """Parse pytest/jest output to extract test metrics."""

    # Pytest patterns
    PYTEST_SUMMARY_PATTERN = re.compile(
        r"=+ (?:(\d+) passed)?(?:, )?(?:(\d+) failed)?(?:, )?(?:(\d+) skipped)?(?:, )?(?:(\d+) error)?.* in ([\d.]+)s"
    )
    PYTEST_FAILED_TEST_PATTERN = re.compile(r"FAILED (.+?) -")
    PYTEST_ERROR_PATTERN = re.compile(r"E\s+(.+)")

    # Jest patterns
    JEST_SUMMARY_PATTERN = re.compile(
        r"Tests:\s+(?:(\d+) failed, )?(?:(\d+) skipped, )?(?:(\d+) passed, )?(\d+) total"
    )
    JEST_TIME_PATTERN = re.compile(r"Time:\s+([\d.]+)\s*s")

    def parse(self, log_content: str) -> TestLogMetrics:
        """Parse test log output.

        Args:
            log_content: Raw test output log

        Returns:
            TestLogMetrics with extracted data
        """
        # Try pytest format first
        metrics = self._parse_pytest(log_content)
        if metrics:
            return metrics

        # Try jest format
        metrics = self._parse_jest(log_content)
        if metrics:
            return metrics

        # Fallback - try to extract any useful info
        return self._parse_generic(log_content)

    def _parse_pytest(self, log_content: str) -> TestLogMetrics | None:
        """Parse pytest output."""
        match = self.PYTEST_SUMMARY_PATTERN.search(log_content)
        if not match:
            return None

        passed = int(match.group(1) or 0)
        failed = int(match.group(2) or 0)
        skipped = int(match.group(3) or 0)
        errors = int(match.group(4) or 0)
        duration = float(match.group(5))

        total = passed + failed + skipped + errors
        tests_passed = failed == 0 and errors == 0

        # Extract failed test names
        failed_tests = self.PYTEST_FAILED_TEST_PATTERN.findall(log_content)

        # Extract error messages
        error_messages = self.PYTEST_ERROR_PATTERN.findall(log_content)[:10]  # Limit

        logger.info(
            "Pytest log parsed",
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration=duration,
        )

        return TestLogMetrics(
            tests_passed=tests_passed,
            total_tests=total,
            passed_count=passed,
            failed_count=failed,
            skipped_count=skipped,
            error_count=errors,
            failed_test_names=failed_tests,
            error_messages=error_messages,
            duration_seconds=duration,
        )

    def _parse_jest(self, log_content: str) -> TestLogMetrics | None:
        """Parse Jest output."""
        match = self.JEST_SUMMARY_PATTERN.search(log_content)
        if not match:
            return None

        failed = int(match.group(1) or 0)
        skipped = int(match.group(2) or 0)
        passed = int(match.group(3) or 0)
        total = int(match.group(4))

        # Extract duration
        time_match = self.JEST_TIME_PATTERN.search(log_content)
        duration = float(time_match.group(1)) if time_match else 0.0

        tests_passed = failed == 0

        logger.info(
            "Jest log parsed",
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration=duration,
        )

        return TestLogMetrics(
            tests_passed=tests_passed,
            total_tests=total,
            passed_count=passed,
            failed_count=failed,
            skipped_count=skipped,
            error_count=0,
            failed_test_names=[],
            error_messages=[],
            duration_seconds=duration,
        )

    def _parse_generic(self, log_content: str) -> TestLogMetrics:
        """Generic fallback parser."""
        # Look for common success/failure indicators
        log_lower = log_content.lower()

        tests_passed = (
            "all tests passed" in log_lower
            or "0 failed" in log_lower
            or ("passed" in log_lower and "failed" not in log_lower)
        )

        # Try to find any numbers
        numbers = re.findall(r"(\d+)\s+(?:tests?|specs?)", log_lower)
        total = int(numbers[0]) if numbers else 0

        return TestLogMetrics(
            tests_passed=tests_passed,
            total_tests=total,
            passed_count=total if tests_passed else 0,
            failed_count=0 if tests_passed else total,
            skipped_count=0,
            error_count=0,
            failed_test_names=[],
            error_messages=[],
            duration_seconds=0.0,
        )
