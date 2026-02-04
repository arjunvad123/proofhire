"""Extract evidence from candidate writeups."""

import re
from dataclasses import dataclass

from app.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class WriteupMetrics:
    """Metrics extracted from candidate writeup."""

    word_count: int
    prompts_answered: list[str]
    sections: dict[str, str]
    has_root_cause: bool
    has_tradeoffs: bool
    has_monitoring: bool


class WriteupExtractor:
    """Extract metrics and structure from candidate writeups."""

    # Expected prompts/sections in writeups
    EXPECTED_PROMPTS = [
        "root cause",
        "what was the bug",
        "why did this happen",
        "what did you change",
        "tradeoffs",
        "alternative approaches",
        "monitoring",
        "how would you detect",
    ]

    # Section header patterns
    SECTION_PATTERNS = [
        (r"#+\s*root\s*cause", "root_cause"),
        (r"#+\s*what\s*(?:was\s*)?(?:the\s*)?bug", "root_cause"),
        (r"#+\s*(?:the\s*)?fix", "fix_description"),
        (r"#+\s*changes?", "fix_description"),
        (r"#+\s*tradeoffs?", "tradeoffs"),
        (r"#+\s*alternatives?", "tradeoffs"),
        (r"#+\s*monitoring", "monitoring"),
        (r"#+\s*(?:how\s*to\s*)?detect", "monitoring"),
        (r"#+\s*testing", "testing"),
    ]

    def extract(self, writeup_text: str) -> WriteupMetrics:
        """Extract metrics from a writeup.

        Args:
            writeup_text: Raw writeup markdown/text

        Returns:
            WriteupMetrics with extracted data
        """
        # Basic metrics
        word_count = len(writeup_text.split())

        # Extract sections
        sections = self._extract_sections(writeup_text)

        # Check which prompts were answered
        prompts_answered = self._check_prompts_answered(writeup_text, sections)

        # Check for key content
        has_root_cause = self._has_content_type(writeup_text, sections, "root_cause")
        has_tradeoffs = self._has_content_type(writeup_text, sections, "tradeoffs")
        has_monitoring = self._has_content_type(writeup_text, sections, "monitoring")

        logger.info(
            "Writeup extracted",
            word_count=word_count,
            prompts_answered=len(prompts_answered),
            has_root_cause=has_root_cause,
            has_tradeoffs=has_tradeoffs,
            has_monitoring=has_monitoring,
        )

        return WriteupMetrics(
            word_count=word_count,
            prompts_answered=prompts_answered,
            sections=sections,
            has_root_cause=has_root_cause,
            has_tradeoffs=has_tradeoffs,
            has_monitoring=has_monitoring,
        )

    def _extract_sections(self, text: str) -> dict[str, str]:
        """Extract named sections from markdown text."""
        sections: dict[str, str] = {}
        lines = text.split("\n")

        current_section = None
        current_content: list[str] = []

        for line in lines:
            # Check if this line is a section header
            is_header = False
            for pattern, section_name in self.SECTION_PATTERNS:
                if re.match(pattern, line, re.IGNORECASE):
                    # Save previous section
                    if current_section:
                        sections[current_section] = "\n".join(current_content).strip()

                    current_section = section_name
                    current_content = []
                    is_header = True
                    break

            if not is_header and current_section:
                current_content.append(line)

        # Save last section
        if current_section:
            sections[current_section] = "\n".join(current_content).strip()

        return sections

    def _check_prompts_answered(
        self,
        text: str,
        sections: dict[str, str],
    ) -> list[str]:
        """Check which expected prompts were answered."""
        answered = []
        text_lower = text.lower()

        for prompt in self.EXPECTED_PROMPTS:
            prompt_lower = prompt.lower()

            # Check if prompt topic is mentioned with substantial content
            if prompt_lower in text_lower:
                # Find the mention and check if followed by content
                idx = text_lower.find(prompt_lower)
                if idx >= 0:
                    # Check next 200 chars have substantial content
                    following = text_lower[idx : idx + 200]
                    if len(following.split()) >= 10:
                        answered.append(prompt)

        # Also check section coverage
        section_to_prompt = {
            "root_cause": "root cause",
            "fix_description": "what did you change",
            "tradeoffs": "tradeoffs",
            "monitoring": "monitoring",
        }

        for section, prompt in section_to_prompt.items():
            if section in sections and len(sections[section]) > 50:
                if prompt not in answered:
                    answered.append(prompt)

        return answered

    def _has_content_type(
        self,
        text: str,
        sections: dict[str, str],
        content_type: str,
    ) -> bool:
        """Check if writeup has substantial content of a type."""
        # Check if section exists with content
        if content_type in sections:
            return len(sections[content_type]) > 50

        # Fallback: check for keywords
        text_lower = text.lower()
        keywords = {
            "root_cause": ["root cause", "because", "the bug was", "issue was"],
            "tradeoffs": ["tradeoff", "trade-off", "alternatively", "instead of", "considered"],
            "monitoring": ["monitor", "alert", "detect", "log", "metric", "observ"],
        }

        type_keywords = keywords.get(content_type, [])
        return any(kw in text_lower for kw in type_keywords)
