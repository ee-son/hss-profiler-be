import asyncio
from services.scraper import TwitterScraper
from services.rate_limit import RateLimitError
from services.predictor import predict_user
from services.cache import get_profile, save_profile

async def profile_user(
    username: str,
    language: str,
    explain: bool = False
):
    cached = get_profile(
        username=username,
        language=language
    )

    if cached:
        print(f"[CACHE] Using cached profile: {username}")
        return cached
    
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

    result = predict_user(
        username=username,
        tweets=tweets,
        language=language,
        explain=explain
    )

    save_profile(
        username=username,
        language=language,
        result=result
    )

    return result