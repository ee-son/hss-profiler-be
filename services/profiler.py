import asyncio
from services.scraper import TwitterScraper
from services.rate_limit import RateLimitError
from services.predictor import predict_user

async def profile_user(
    username: str,
    language: str,
    explain: bool = False
):
    scraper = TwitterScraper()
    await scraper.initialize()

    try:
        tweets = await asyncio.wait_for(
            scraper.scrape_user(
                username=username,
                language=language
            ),
            timeout=30
        )

    except asyncio.TimeoutError:
        raise RuntimeError(
            "Twitter is temporarily rate limited. Please try again in a few minutes."
        )

    except RateLimitError:
        raise RuntimeError(
            "Twitter rate limit exceeded. Please try again later."
        )

    return predict_user(
        username=username,
        tweets=tweets,
        language=language,
        explain=explain
    )