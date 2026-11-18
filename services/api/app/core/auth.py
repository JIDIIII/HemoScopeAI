import httpx
from fastapi import Request

from app.core.config import Settings
from app.core.errors import APIError


async def verify_supabase_access_token(request: Request, settings: Settings) -> str:
    """Ask Supabase Auth to validate a user token; never trust decoded client claims."""
    authorization = request.headers.get("authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise APIError(401, "authentication_required", "Sign in before uploading an image.")

    try:
        async with httpx.AsyncClient(timeout=settings.supabase_auth_timeout_seconds) as client:
            response = await client.get(
                f"{settings.supabase_url}/auth/v1/user",
                headers={
                    "apikey": settings.supabase_publishable_key,
                    "Authorization": f"Bearer {token.strip()}",
                },
            )
    except httpx.HTTPError as exc:
        raise APIError(
            503,
            "authentication_provider_unavailable",
            "Sign-in could not be verified right now. Try again shortly.",
        ) from exc

    if response.status_code in {400, 401, 403}:
        raise APIError(401, "authentication_required", "Your sign-in expired. Sign in again.")
    if response.status_code != 200:
        raise APIError(
            503,
            "authentication_provider_unavailable",
            "Sign-in could not be verified right now. Try again shortly.",
        )

    try:
        user = response.json()
    except ValueError as exc:
        raise APIError(
            503,
            "authentication_provider_unavailable",
            "Sign-in could not be verified right now. Try again shortly.",
        ) from exc
    user_id = user.get("id") if isinstance(user, dict) else None
    if not isinstance(user_id, str) or not user_id:
        raise APIError(
            503,
            "authentication_provider_unavailable",
            "Sign-in could not be verified right now. Try again shortly.",
        )
    return user_id
