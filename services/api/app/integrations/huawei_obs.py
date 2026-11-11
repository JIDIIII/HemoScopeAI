from typing import Protocol

from app.core.config import Settings
from app.core.errors import APIError


class PrivateObjectStorage(Protocol):
    async def store_private_object(self, object_key: str, content: bytes, content_type: str) -> str:
        """Store content in a private bucket and return a non-public object identifier."""
        ...


class HuaweiOBSAdapter:
    """OBS adapter boundary; IAM signing and the OBS SDK client are not wired yet."""

    def __init__(self, settings: Settings) -> None:
        self._configured = bool(
            settings.huawei_obs_bucket
            and settings.huawei_obs_endpoint
            and settings.huawei_access_key_id
            and settings.huawei_secret_access_key
        )

    async def store_private_object(self, object_key: str, content: bytes, content_type: str) -> str:
        del object_key, content, content_type
        if not self._configured:
            raise APIError(503, "obs_not_configured", "Private OBS storage is not configured.")
        raise APIError(
            503,
            "obs_adapter_incomplete",
            "OBS credentials are present, but the provider SDK adapter is not implemented.",
        )
