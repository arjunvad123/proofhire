"""LLM prompts for various tasks.

All prompts are carefully designed to:
1. Produce schema-compliant JSON output
2. Avoid quality judgments (only factual observations)
3. Require citations for any claims
"""

WRITEUP_TAGGING_PROMPT = '''You are analyzing a candidate's technical writeup from a coding simulation.

Your task is to identify which TOPICS are present in the writeup. You are NOT judging quality - only identifying what topics the candidate addressed.

For each topic found, you MUST provide a direct quote from the text as evidence.

## Topics to look for:

1. **root_cause_identified** - The candidate explains what caused the bug/issue
2. **tradeoff_discussed** - The candidate discusses alternative approaches or tradeoffs
3. **monitoring_considered** - The candidate mentions how to monitor/detect the issue
4. **testing_mentioned** - The candidate discusses their testing approach
5. **edge_cases_mentioned** - The candidate discusses edge cases they considered

## Output Format

Return a JSON object with this exact structure:
{{
  "tags": [
    {{
      "tag": "root_cause_identified",
      "confidence": 0.9,
      "evidence_quote": "The exact quote from the writeup",
      "start_char": 0,
      "end_char": 50
    }}
  ],
  "word_count": 150,
  "sections_identified": ["root cause", "fix description"]
}}

## Guidelines

- Only include tags where you find clear evidence
- The evidence_quote must be a DIRECT quote from the text
- Confidence should be 0.7-1.0 (only include if confident)
- Do NOT make quality judgments - just identify presence of topics

## Writeup to analyze:

{writeup}

Return ONLY the JSON object, no other text.'''

WRITEUP_SUMMARY_PROMPT = '''Summarize this technical writeup from a coding simulation.

## Guidelines:
- Keep summary under 500 characters
- Extract 3-5 key points
- Assess technical depth as "shallow", "moderate", or "deep"
- Be objective and factual

## Output Format

Return a JSON object:
{{
  "summary": "Brief summary here",
  "key_points": ["Point 1", "Point 2", "Point 3"],
  "technical_depth": "moderate"
}}

## Writeup:

{writeup}

Return ONLY the JSON object, no other text.'''

INTERVIEW_QUESTIONS_PROMPT = '''Generate interview questions for a candidate based on unproven claims from their coding simulation.

The goal is to help the interviewer probe areas where the simulation evidence was insufficient.

## Context

These claims could NOT be proven from the simulation evidence:
{claims}

Company context (what they value):
{com}

## Guidelines

- Questions should be open-ended, not yes/no
- Focus on understanding the candidate's thought process
- Tailor questions to the company's priorities
- Maximum 5 questions

## Output Format

Return a JSON object:
{{
  "questions": [
    {{
      "question": "The interview question",
      "rationale": "Why this question is relevant",
      "dimension": "The skill dimension this probes"
    }}
  ]
}}

Return ONLY the JSON object, no other text.'''
