"""
Data Collector for Career Examples
Fetches real job descriptions and company examples for each career path.
"""

import asyncio
import json
from pathlib import Path
from typing import List, Dict, Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
import trafilatura


# ============================================
# Configuration
# ============================================

SEARCH_QUERIES = {
    "finance": [
        "FP&A analyst responsibilities Stripe",
        "financial analyst job description tech company",
        "investment banking analyst responsibilities",
        "quantitative analyst finance job description",
        "corporate finance analyst role description"
    ],
    "healthcare": [
        "health tech data scientist Tempus job description",
        "healthcare analytics engineer responsibilities",
        "medical AI research scientist job description",
        "bioinformatics analyst responsibilities",
        "clinical data analyst job description"
    ],
    "consultant": [
        "McKinsey business analyst responsibilities",
        "management consultant job description",
        "strategy consultant responsibilities",
        "technology consultant job description",
        "MBB consultant analyst role"
    ]
}

# Sample URLs (you can replace with actual search results)
EXAMPLE_URLS = {
    "finance": [
        "https://www.levels.fyi/blog/financial-planning-analysis-career-guide.html",
        "https://www.investopedia.com/articles/professionals/111715/career-advice-investment-banker-vs-corporate-finance.asp"
    ],
    "healthcare": [
        "https://www.healthcareitnews.com/news/what-does-healthcare-data-scientist-do",
        "https://www.aamc.org/career-development/explore-health-informatics-careers"
    ],
    "consultant": [
        "https://managementconsulted.com/consultant-job-description/",
        "https://www.themuse.com/advice/what-does-a-management-consultant-actually-do"
    ]
}


# ============================================
# HTTP Client with Retry Logic
# ============================================

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def fetch_url(url: str, client: httpx.AsyncClient) -> str:
    """
    Fetch URL content with retry logic.
    """
    response = await client.get(
        url,
        follow_redirects=True,
        timeout=30.0,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0"
        }
    )
    response.raise_for_status()
    return response.text


# ============================================
# Text Extraction
# ============================================

def extract_clean_text(html: str, url: str) -> Dict[str, Any]:
    """
    Extract clean article text from HTML using trafilatura.
    """
    # Extract main content
    text = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=True,
        no_fallback=False
    )

    if not text:
        print(f"⚠️  Warning: Could not extract text from {url}")
        return None

    # Extract metadata
    metadata = trafilatura.extract_metadata(html)

    return {
        "url": url,
        "title": metadata.title if metadata and metadata.title else "Unknown",
        "text": text,
        "author": metadata.author if metadata and metadata.author else None,
        "date": metadata.date if metadata and metadata.date else None,
    }


# ============================================
# Main Collection Logic
# ============================================

async def collect_examples_for_path(
    career_path: str,
    urls: List[str],
    output_file: Path
) -> None:
    """
    Collect examples for a specific career path.
    """
    print(f"\n📊 Collecting examples for: {career_path}")
    print(f"   URLs to process: {len(urls)}")

    examples = []

    async with httpx.AsyncClient() as client:
        for idx, url in enumerate(urls, 1):
            try:
                print(f"   [{idx}/{len(urls)}] Fetching: {url}")

                # Fetch HTML
                html = await fetch_url(url, client)

                # Extract clean text
                result = extract_clean_text(html, url)

                if result:
                    examples.append(result)
                    print(f"   ✓ Extracted {len(result['text'])} characters")

                # Be nice to servers
                await asyncio.sleep(1)

            except Exception as e:
                print(f"   ✗ Error fetching {url}: {e}")
                continue

    # Save to JSONL
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        for example in examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')

    print(f"   💾 Saved {len(examples)} examples to {output_file}")


async def collect_all_examples():
    """
    Collect examples for all career paths.
    """
    print("\n" + "="*60)
    print("🚀 Starting Career Examples Collection")
    print("="*60)

    data_dir = Path(__file__).parent / "data" / "company_examples"

    tasks = []
    for career_path, urls in EXAMPLE_URLS.items():
        output_file = data_dir / f"{career_path}.jsonl"
        tasks.append(collect_examples_for_path(career_path, urls, output_file))

    await asyncio.gather(*tasks)

    print("\n" + "="*60)
    print("✅ Collection Complete!")
    print("="*60)


# ============================================
# CLI Entry Point
# ============================================

if __name__ == "__main__":
    asyncio.run(collect_all_examples())
