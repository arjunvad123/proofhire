"""Tests for evidence extractors."""

import pytest

from app.evidence.extractors.diff_extractor import DiffExtractor
from app.evidence.extractors.testlog_parser import TestLogParser
from app.evidence.extractors.coverage_parser import CoverageParser
from app.evidence.extractors.writeup_extractor import WriteupExtractor


class TestDiffExtractor:
    """Tests for DiffExtractor."""

    def setup_method(self):
        self.extractor = DiffExtractor()

    def test_extracts_files_changed(self):
        """Should extract changed files from diff."""
        diff = """diff --git a/app/service.py b/app/service.py
index 123456..789abc 100644
--- a/app/service.py
+++ b/app/service.py
@@ -1,3 +1,4 @@
+# Fixed the bug
 def process():
     pass
"""
        metrics = self.extractor.extract(diff)

        assert "app/service.py" in metrics.files_changed
        assert metrics.lines_added == 1
        assert metrics.lines_removed == 0

    def test_identifies_test_files(self):
        """Should identify test files."""
        diff = """diff --git a/tests/test_service.py b/tests/test_service.py
index 123456..789abc 100644
--- a/tests/test_service.py
+++ b/tests/test_service.py
@@ -1,3 +1,10 @@
+def test_new_case():
+    assert True
"""
        metrics = self.extractor.extract(diff)

        assert "tests/test_service.py" in metrics.test_files_changed
        assert metrics.test_added is True
        assert metrics.tests_added_count >= 1

    def test_detects_skipped_tests(self):
        """Should detect skipped test additions."""
        diff = """diff --git a/tests/test_service.py b/tests/test_service.py
+@pytest.mark.skip
+def test_flaky():
+    pass
"""
        metrics = self.extractor.extract(diff)

        assert metrics.skipped_tests_added == 1


class TestTestLogParser:
    """Tests for TestLogParser."""

    def setup_method(self):
        self.parser = TestLogParser()

    def test_parses_pytest_output(self):
        """Should parse pytest summary."""
        log = """
============================= test session starts ==============================
collected 10 items

tests/test_service.py ..........                                        [100%]

============================== 8 passed, 1 failed, 1 skipped in 2.34s ==============================
"""
        metrics = self.parser.parse(log)

        assert metrics.total_tests == 10
        assert metrics.passed_count == 8
        assert metrics.failed_count == 1
        assert metrics.skipped_count == 1
        assert metrics.duration_seconds == 2.34
        assert metrics.tests_passed is False

    def test_parses_all_passed(self):
        """Should detect all tests passed."""
        log = """
============================== 5 passed in 1.00s ==============================
"""
        metrics = self.parser.parse(log)

        assert metrics.tests_passed is True
        assert metrics.passed_count == 5

    def test_handles_jest_output(self):
        """Should parse Jest output."""
        log = """
Test Suites: 2 passed, 2 total
Tests:       1 failed, 9 passed, 10 total
Time:        3.456 s
"""
        metrics = self.parser.parse(log)

        assert metrics.total_tests == 10
        assert metrics.passed_count == 9
        assert metrics.failed_count == 1


class TestCoverageParser:
    """Tests for CoverageParser."""

    def setup_method(self):
        self.parser = CoverageParser()

    def test_parses_cobertura_xml(self):
        """Should parse Cobertura format XML."""
        xml = """<?xml version="1.0"?>
<coverage line-rate="0.85" branch-rate="0.70">
    <packages>
        <package name="app">
            <classes>
                <class name="service.py" filename="app/service.py">
                    <lines>
                        <line number="1" hits="1"/>
                        <line number="2" hits="1"/>
                        <line number="3" hits="0"/>
                        <line number="4" hits="1"/>
                    </lines>
                </class>
            </classes>
        </package>
    </packages>
</coverage>
"""
        metrics = self.parser.parse(xml)

        assert metrics.line_coverage_percent == 85.0
        assert metrics.branch_coverage_percent == 70.0
        assert metrics.lines_covered == 3
        assert metrics.lines_total == 4

    def test_identifies_uncovered_lines(self):
        """Should identify uncovered lines."""
        xml = """<?xml version="1.0"?>
<coverage line-rate="0.75">
    <packages>
        <package name="app">
            <classes>
                <class filename="app/service.py">
                    <lines>
                        <line number="1" hits="1"/>
                        <line number="2" hits="0"/>
                    </lines>
                </class>
            </classes>
        </package>
    </packages>
</coverage>
"""
        metrics = self.parser.parse(xml)

        assert "app/service.py" in metrics.uncovered_files
        assert 2 in metrics.uncovered_files["app/service.py"]


class TestWriteupExtractor:
    """Tests for WriteupExtractor."""

    def setup_method(self):
        self.extractor = WriteupExtractor()

    def test_extracts_word_count(self):
        """Should count words correctly."""
        writeup = "This is a test writeup with some words in it."
        metrics = self.extractor.extract(writeup)

        assert metrics.word_count == 10

    def test_identifies_root_cause_section(self):
        """Should identify root cause discussion."""
        writeup = """## Root Cause

The bug was caused by an off-by-one error in the loop condition.
The comparison used > instead of >= which caused valid requests to be blocked.
"""
        metrics = self.extractor.extract(writeup)

        assert metrics.has_root_cause is True
        assert "root_cause" in metrics.sections

    def test_identifies_tradeoffs_section(self):
        """Should identify tradeoffs discussion."""
        writeup = """## Tradeoffs

I considered using a different data structure but decided against it
because the current approach is simpler and the performance is adequate.
"""
        metrics = self.extractor.extract(writeup)

        assert metrics.has_tradeoffs is True

    def test_identifies_monitoring_section(self):
        """Should identify monitoring discussion."""
        writeup = """## Monitoring

To detect this in production, we should add metrics tracking the rate
of blocked requests and alert if it exceeds a threshold.
"""
        metrics = self.extractor.extract(writeup)

        assert metrics.has_monitoring is True

    def test_checks_prompts_answered(self):
        """Should check which prompts were answered."""
        writeup = """## What was the bug?

The root cause was an off-by-one error. The condition checked > instead of >=.

## What did you change?

I changed the comparison operator from > to >= in the rate limiting check.
"""
        metrics = self.extractor.extract(writeup)

        # Should identify both prompts as answered
        assert len(metrics.prompts_answered) >= 2
