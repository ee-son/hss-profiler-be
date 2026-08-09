import asyncio
from services.scraper import TwitterScraper
from services.rate_limit import RateLimitError
from services.predictor import predict_user
from services.cache import get_profile, save_profile, get_existing_language, get_profile_updated_at
from services.lang_detector import WrongLanguageError

async def profile_user(
    username: str,
    language: str,
    explain: bool = False,
    force_refresh: bool = False
):
    cached = get_profile(
        username=username,
        language=language
    )

    if cached:
        print(f"[CACHE] Using cached profile: {username}")

        last_updated = get_profile_updated_at(
            username=username,
            language=language
        )

        cached["last_updated"] = last_updated

        return cached

    existing_language = get_existing_language(username)

    if existing_language is not None and existing_language != language:
        raise WrongLanguageError(existing_language)
    
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

    except RateLimitError as e:
        raise RuntimeError(str(e))

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

    last_updated = get_profile_updated_at(
        username=username,
        language=language
    )

    result["last_updated"] = last_updated

    return result