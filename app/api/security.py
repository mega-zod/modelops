from hmac import compare_digest

from fastapi import Header, HTTPException, status

from app.core.config import get_settings


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Protect operational endpoints when a key is configured or in production."""
    settings = get_settings()
    expected_key = settings.api_access_key

    if expected_key is None:
        if settings.app_env.lower() == "production":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="MODEL_OPS_API_KEY must be configured in production.",
            )
        return

    if x_api_key is None or not compare_digest(x_api_key, expected_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid X-API-Key header is required.",
        )
