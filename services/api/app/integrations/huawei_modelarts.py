from app.core.config import Settings
from app.services.inference import ConfiguredCloudAdapter


class HuaweiModelArtsAdapter(ConfiguredCloudAdapter):
    """ModelArts inference boundary; endpoint signing and request mapping remain TODO."""

    def __init__(self, settings: Settings) -> None:
        super().__init__("Huawei ModelArts")
        self.configured = bool(settings.huawei_modelarts_endpoint)
