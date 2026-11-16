from app.core.config import Settings
from app.services.inference import ConfiguredCloudAdapter


class HuaweiECSInferenceAdapter(ConfiguredCloudAdapter):
    """ECS-hosted inference boundary; deployment-specific client remains TODO."""

    def __init__(self, settings: Settings) -> None:
        super().__init__("Huawei ECS")
        self.configured = bool(settings.huawei_ecs_inference_url)
