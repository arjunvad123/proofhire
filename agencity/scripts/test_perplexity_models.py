"""Compare Perplexity sonar vs sonar-pro, and test identity conflation with common names."""

import asyncio
import httpx
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

from app.config import settings

API_KEY = settings.perplexity_api_key


async def call_perplexity(model: str, query: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a technical recruiter researcher. Provide factual, verifiable information only.",
                    },
                    {"role": "user", "content": query},
                ],
                "temperature": 0.2,
                "max_tokens": 1000,
            },
            timeout=45.0,
        )
        if response.status_code == 200:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            citations = data.get("citations", [])
            return content, citations
        else:
            return f"ERROR {response.status_code}: {response.text[:300]}", []


async def run():
    # Test 1: A common name that would cause conflation
    query = """Research "Aarush Agrawal" who works as a Software Development Engineer at Amazon in San Francisco.
Their LinkedIn is https://www.linkedin.com/in/aarush-agrawal-

Find their GitHub profile, technical skills, and any open source work.
Only report findings you can verify belong to THIS specific person."""

    for model in ["sonar", "sonar-pro"]:
        print(f"\n{'='*80}")
        print(f"MODEL: {model}")
        print(f"{'='*80}")
        content, citations = await call_perplexity(model, query)
        print(content[:1200])
        if citations:
            print(f"\n--- CITATIONS ({len(citations)}) ---")
            for c in citations[:5]:
                print(f"  {c}")
        print()


if __name__ == "__main__":
    asyncio.run(run())
