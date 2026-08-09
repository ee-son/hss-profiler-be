import os
import secrets


def check_admin_key(api_key: str | None) -> bool:
    admin_api_key = os.getenv("ADMIN_API_KEY")

    if not admin_api_key:
        return False

    if not api_key:
        return False

    return secrets.compare_digest(
        api_key,
        admin_api_key
    )
