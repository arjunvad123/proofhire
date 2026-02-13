#!/usr/bin/env python3
"""
Import Greptile onboarding data - REST API Edition

This version uses Supabase REST API instead of SQLAlchemy.
NO DATABASE_URL password needed!

Company: Greptile
Role: Software Engineer (Generalist)
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.org_profiles_db import org_profiles_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


GREPTILE_JD = """
Software Engineer (Generalist) at Greptile (W24)
$140K - $180K • 0.75% - 1.25%
AI code review agent with complete context of your codebase
San Francisco
Full-time
US citizen/visa only
1+ years

About Greptile
Greptile reviews pull requests with complete context of the codebase. Thousands of teams use Greptile to catch more bugs and merge PRs faster.

We're a small, tight-knit in-person company based in San Francisco.

About the role
We want to build agents that autonomously validate code changes. Today that looks like AI that reviews pull requests in GitHub, catching bugs and enforcing standards. We're reviewing close to 1B lines of code a month now for over 1,000 companies.

Problems we're excited about
Coding standards can be idiosyncratic and are often poorly documented; can we build agents that learn them through osmosis like a new hire might?
Can we identify for each customer what types of PR feedback they do and don't care about, perhaps using some sample efficient RL, in order to increase signal-to-noise ratio?
Some bugs are best caught by running the code, potentially against discerning AI-generated E2E tests. Can we autonomously deploy feature branches and use agents to parallel try to break the application to detect bugs?

Trajectory
Went from 0 ---> XM in <12 Months and growing >25% MoM
1,500+ customers
Raised 30M+ led by Benchmark, along with continued support from YC, Paul Graham, Initialized, SV Angel, etc.

Team
We have assembled a small, talent dense team who have scaled critical functions at companies like Stripe, Google, Figma, LinkedIn, etc.

Responsibilities (in order of how much time you'll likely spend on each):
Solve some of our hardest and most interesting problems, including LLM memory, multi-language codebase indexing, semantic search for large codebases, and much more.
Design, implement, test, and deploy full features
Get user feedback to iterate the features

Qualifications:
B.S. Computer Science or equivalent degree, undergraduate or higher
1+ years of software or DevOps engineering experience
Experience with JavaScript/TypeScript

You will like this role if:
You want to work on a product that thousands of developers rely on
The chaos of high growth and things breaking is exciting to you
You like being in an office every day around other smart people who are excited about what they're building
You love solving very hard problems.
You specifically prefer working in-person over working remote

Technology
Backend: Node, TypeScript, AWS ECS/Lambda, Postgres Frontend: NextJS
"""


async def import_greptile():
    """Import Greptile onboarding data using REST API."""
    logger.info("=" * 60)
    logger.info("Importing Greptile Onboarding Data (REST API)")
    logger.info("=" * 60)

    # Step 1: Create or get profile
    logger.info("\n1. Creating/getting organization profile for Greptile...")
    profile = await org_profiles_db.get_or_create_profile(
        slack_workspace_id="T_GREPTILE_DEMO",
        slack_workspace_name="Greptile Demo Workspace",
    )
    logger.info(f"✓ Profile ID: {profile['id']}")

    # Step 2: Import company data
    logger.info("\n2. Importing company data...")
    updated_profile = await org_profiles_db.import_onboarding_data(
        profile_id=profile["id"],
        company_name="Greptile",
        company_hq_location="San Francisco, CA",
        company_size=15,  # Small, tight-knit team (10-20 employees)
        product_description="AI code review agent with complete context of your codebase. Reviews PRs for 1,000+ companies.",
        tech_stack=["Node", "TypeScript", "AWS ECS", "Lambda", "Postgres", "NextJS"],
        hiring_priorities=[
            "1+ years experience",
            "JavaScript/TypeScript expert",
            "In-person SF only",
            "Loves hard problems",
        ],
    )
    logger.info(f"✓ Updated profile: {updated_profile['company_name']}")

    # Step 3: Add hiring priorities for the role
    logger.info("\n3. Adding hiring priorities for Software Engineer role...")
    priority = await org_profiles_db.add_hiring_priority(
        org_profile_id=profile["id"],
        role_title="Software Engineer (Generalist)",
        must_haves=[
            "1+ years of software or DevOps engineering experience",
            "Experience with JavaScript/TypeScript",
            "B.S. Computer Science or equivalent",
            "US citizen/visa",
            "In-person in San Francisco",
        ],
        nice_to_haves=[
            "Experience with LLM memory",
            "Multi-language codebase indexing",
            "Semantic search for large codebases",
            "Experience at Stripe, Google, Figma, LinkedIn",
        ],
        dealbreakers=[
            "Remote-only candidates",
            "Less than 1 year experience",
            "Not interested in AI/LLMs",
        ],
        specific_work="Build agents that autonomously validate code changes. Design, implement, test, and deploy full features. Get user feedback to iterate.",
        success_criteria="Ship features that help 1,000+ companies catch bugs faster. Solve hard problems in LLM memory, codebase indexing, and semantic search.",
    )
    logger.info(f"✓ Added hiring priority: {priority['role_title']}")

    # Step 4: Add knowledge entries based on "You will like this role if"
    logger.info("\n4. Adding knowledge entries...")

    await org_profiles_db.add_knowledge(
        org_profile_id=profile["id"],
        category="cultural_fit",
        content="Thrives in chaos of high growth, loves solving very hard problems, prefers in-person work over remote.",
        source="job_description",
        confidence=0.95,
    )
    logger.info("✓ Added cultural fit knowledge")

    await org_profiles_db.add_knowledge(
        org_profile_id=profile["id"],
        category="technical_challenge",
        content="Excited about LLM memory, multi-language codebase indexing, and semantic search for large codebases.",
        source="job_description",
        confidence=0.95,
    )
    logger.info("✓ Added technical challenge knowledge")

    await org_profiles_db.add_knowledge(
        org_profile_id=profile["id"],
        category="company_trajectory",
        content="Went from 0 to XM in <12 months, growing >25% MoM. 1,500+ customers. Raised 30M+ led by Benchmark.",
        source="job_description",
        confidence=1.0,
    )
    logger.info("✓ Added company trajectory knowledge")

    # Step 5: Mark complete
    logger.info("\n5. Marking onboarding complete...")
    final_profile = await org_profiles_db.mark_onboarding_complete(profile["id"])
    logger.info(f"✓ Onboarding complete: {final_profile.get('onboarding_complete')}")

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("✓ Greptile Import Complete!")
    logger.info("=" * 60)
    logger.info(f"Profile ID: {final_profile['id']}")
    logger.info(f"Company: {final_profile.get('company_name')}")
    logger.info(f"Location: {final_profile.get('company_hq_location')}")
    logger.info(f"Tech Stack: {', '.join(final_profile.get('tech_stack', []))}")
    logger.info(f"Onboarding: {'Complete' if final_profile.get('onboarding_complete') else 'Incomplete'}")

    # Fetch and display knowledge
    knowledge_entries = await org_profiles_db.get_knowledge(profile["id"])
    logger.info(f"\nKnowledge Entries: {len(knowledge_entries)}")
    for entry in knowledge_entries:
        logger.info(f"  - [{entry['category']}] {entry['content'][:60]}...")

    # Fetch and display hiring priorities
    priorities = await org_profiles_db.get_hiring_priorities(profile["id"])
    logger.info(f"\nHiring Priorities: {len(priorities)}")
    for priority in priorities:
        logger.info(f"  - {priority['role_title']}")
        logger.info(f"    Must-haves: {len(priority.get('must_haves', []))}")
        logger.info(f"    Nice-to-haves: {len(priority.get('nice_to_haves', []))}")


async def main():
    try:
        await import_greptile()
    except Exception as e:
        logger.error(f"✗ Import failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
