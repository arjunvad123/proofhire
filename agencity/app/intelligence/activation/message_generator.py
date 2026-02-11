"""
Activation Message Generator - Create personalized outreach messages.

The key is personalization:
- Mention their current role/company
- Reference why you're asking them specifically
- Be clear about the ask
- Make it easy for them to help
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ActivationMessageGenerator:
    """
    Generate personalized messages for network activation.

    Templates:
    1. Reverse Reference - "Who would you recommend?"
    2. Intro Request - "Can you introduce me to X?"
    3. Referral Request - "Can you post in your network?"
    4. Community Access - "Can you intro me to [community]?"
    """

    def generate_reverse_reference_message(
        self,
        person: dict,
        role_title: str,
        required_skills: list[str] = None,
        company_name: str = None,
        sender_name: str = None
    ) -> str:
        """
        Generate a "who would you recommend?" message.

        This is the highest-signal ask because:
        1. The person has already filtered for quality
        2. They'll only recommend people they'd vouch for
        3. Warm intro is built-in
        """
        first_name = self._get_first_name(person.get("full_name", ""))
        their_title = person.get("current_title", "")
        their_company = person.get("current_company", "")

        # Build personalized context
        context_lines = []

        # Personalize based on why we're asking them
        if their_title and any(kw in their_title.lower() for kw in ["ml", "machine learning", "ai", "data"]):
            context_lines.append(f"Given your experience in {their_title.split(' at ')[0] if ' at ' in their_title else their_title}, I thought you'd know some great people in this space.")
        elif their_company:
            context_lines.append(f"Given your experience at {their_company}, I thought you might know some talented folks.")
        else:
            context_lines.append("Given your experience in the industry, I thought you'd be a great person to ask.")

        # Build skills mention
        skills_mention = ""
        if required_skills:
            top_skills = required_skills[:3]
            skills_mention = f" with experience in {', '.join(top_skills)}"

        # Build the message
        message = f"""Hi {first_name},

Hope you're doing well! I'm building out our {role_title} team{f' at {company_name}' if company_name else ''} and wanted to reach out.

{context_lines[0]}

Quick ask: Who's the best {role_title}{skills_mention} you've ever worked with?

I'm not looking for people who are "officially looking" - often the best candidates aren't on the market. I'm more interested in someone you'd personally vouch for based on working with them.

If anyone comes to mind, I'd love an intro or even just a name to reach out to. Happy to share more context about the role if helpful.

Thanks!
{sender_name if sender_name else '[Your name]'}"""

        return message

    def generate_intro_request_message(
        self,
        recommender_name: str,
        recommended_name: str,
        recommended_context: str = None,
        role_title: str = None,
        sender_name: str = None
    ) -> str:
        """
        Generate a message to request an introduction.

        Sent after someone recommends a person.
        """
        first_name = self._get_first_name(recommender_name)
        rec_first_name = self._get_first_name(recommended_name)

        context_line = ""
        if recommended_context:
            context_line = f"\n\nYou mentioned: \"{recommended_context}\" - that's exactly what we're looking for."
        elif role_title:
            context_line = f"\n\n{rec_first_name} sounds like exactly what we need for our {role_title} role."

        message = f"""Hi {first_name},

Thanks so much for recommending {recommended_name}!{context_line}

Would you be open to making a quick intro? I can send you a short blurb about the opportunity that you can forward, or happy to jump on a quick call if that's easier.

No pressure at all - I know intros can be awkward. But if you think they'd be open to it, I'd really appreciate the connection.

Thanks again for thinking of them!

{sender_name if sender_name else '[Your name]'}"""

        return message

    def generate_referral_post_request(
        self,
        person: dict,
        role_title: str,
        community_type: str = "slack",  # slack, linkedin, email_list
        required_skills: list[str] = None,
        company_name: str = None,
        sender_name: str = None
    ) -> dict:
        """
        Generate a request for someone to post in their community.

        Returns both the ask message and a suggested post they can share.
        """
        first_name = self._get_first_name(person.get("full_name", ""))

        # Determine community reference
        community_refs = {
            "slack": "your Slack communities",
            "linkedin": "LinkedIn",
            "email_list": "your mailing lists",
            "discord": "your Discord servers"
        }
        community_ref = community_refs.get(community_type, "your communities")

        # Build skills string
        skills_str = ""
        if required_skills:
            skills_str = f" with experience in {', '.join(required_skills[:3])}"

        # The ask message
        ask_message = f"""Hi {first_name},

Quick favor to ask - I'm hiring a {role_title}{f' at {company_name}' if company_name else ''} and wondered if you'd be open to sharing in {community_ref}?

I know these posts can feel spammy, so no pressure at all. But referrals from trusted community members tend to attract much better candidates than job boards.

If you're open to it, I drafted a quick blurb you could share (feel free to edit however you'd like):

---

{self._generate_referral_post(role_title, required_skills, company_name, sender_name)}

---

Let me know if this would be helpful. Really appreciate it either way!

{sender_name if sender_name else '[Your name]'}"""

        return {
            "ask_message": ask_message,
            "suggested_post": self._generate_referral_post(role_title, required_skills, company_name, sender_name)
        }

    def _generate_referral_post(
        self,
        role_title: str,
        required_skills: list[str] = None,
        company_name: str = None,
        sender_name: str = None
    ) -> str:
        """Generate the actual referral post content."""
        skills_str = ""
        if required_skills:
            skills_str = f"\n\nLooking for someone with experience in: {', '.join(required_skills[:4])}"

        company_mention = f" at {company_name}" if company_name else " (early-stage startup)"

        return f"""My friend {sender_name if sender_name else '[Name]'} is hiring a {role_title}{company_mention} and asked me to share.

They're building [brief description of what the company does].{skills_str}

If you know anyone who might be interested, drop a comment or DM me and I can make an intro!"""

    def generate_community_access_request(
        self,
        person: dict,
        community_name: str,
        community_type: str = "slack",  # slack, discord, mailing_list, group
        reason: str = None,
        sender_name: str = None
    ) -> str:
        """
        Generate a request for access to a community.

        E.g., "Can you add me to that ML practitioners Slack?"
        """
        first_name = self._get_first_name(person.get("full_name", ""))

        reason_line = ""
        if reason:
            reason_line = f" {reason}"
        else:
            reason_line = " I'm trying to connect with more people in the space as we build out the team."

        type_refs = {
            "slack": "Slack workspace",
            "discord": "Discord server",
            "mailing_list": "mailing list",
            "group": "group"
        }
        type_ref = type_refs.get(community_type, "community")

        message = f"""Hi {first_name},

Hope you're doing well! I noticed you're part of the {community_name} {type_ref} and wondered if you'd be open to adding me?{reason_line}

Totally understand if it's invite-only or you'd prefer not to - no pressure at all.

Thanks!
{sender_name if sender_name else '[Your name]'}"""

        return message

    def generate_followup_message(
        self,
        person: dict,
        original_ask_type: str,
        days_since_ask: int = 7,
        sender_name: str = None
    ) -> str:
        """
        Generate a polite follow-up message.

        Only sent once, after reasonable time has passed.
        """
        first_name = self._get_first_name(person.get("full_name", ""))

        ask_refs = {
            "reverse_reference": "if anyone came to mind for the role",
            "intro_request": "about the introduction",
            "referral_post": "about sharing in your network",
            "community_access": "about the community access"
        }
        ask_ref = ask_refs.get(original_ask_type, "my earlier message")

        message = f"""Hi {first_name},

Just bumping this in case it got buried - no worries if you haven't had a chance to think about it yet, or if it's not something you can help with.

Let me know either way when you get a chance!

{sender_name if sender_name else '[Your name]'}"""

        return message

    def _get_first_name(self, full_name: str) -> str:
        """Extract first name from full name."""
        if not full_name:
            return "there"
        parts = full_name.strip().split()
        return parts[0] if parts else "there"


class IntroForwarderMessage:
    """
    Generate forwardable intro blurbs.

    When someone agrees to make an intro, give them a message
    they can simply forward.
    """

    @staticmethod
    def generate_forwardable_intro(
        candidate_name: str,
        role_title: str,
        company_description: str = None,
        what_makes_it_interesting: str = None,
        sender_name: str = None,
        sender_title: str = None
    ) -> str:
        """
        Generate a message the connector can forward to the candidate.

        This should be compelling to the candidate, not just convenient for us.
        """
        candidate_first = candidate_name.strip().split()[0] if candidate_name else "Hi"

        company_line = ""
        if company_description:
            company_line = f"\n\n{company_description}"

        interesting_line = ""
        if what_makes_it_interesting:
            interesting_line = f"\n\n{what_makes_it_interesting}"

        sender_sig = sender_name if sender_name else "[Name]"
        if sender_title:
            sender_sig += f", {sender_title}"

        return f"""Hi {candidate_first},

[Mutual connection] mentioned you'd be a great person to talk to about a {role_title} role I'm hiring for.{company_line}{interesting_line}

Would love to tell you more about it if you're open to a quick chat. No pressure if the timing isn't right - just thought it might be interesting based on what [mutual] said about your background.

Let me know if you'd be up for a 15-min call!

{sender_sig}"""
