from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

API_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="HEMOSCOPE_",
        env_file=API_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_version: str = "0.1.0"
    inference_provider: Literal["none", "local", "modelarts", "ecs"] = "none"
    enable_demo_mock: bool = False
    local_inference_bundle_dir: Path = (
        Path(__file__).resolve().parents[4]
        / "ml"
        / "artifacts"
        / "handoff"
        / "hemoscope-inference-handoff-v1"
    )
    local_inference_device: Literal["cpu"] = "cpu"
    max_upload_bytes: int = 10 * 1024 * 1024
    max_image_pixels: int = 40_000_000

    quality_min_field_width: int = 640
    quality_min_field_height: int = 480
    quality_min_crop_width: int = 96
    quality_min_crop_height: int = 96
    quality_min_laplacian_variance: float = 50.0
    quality_min_mean_brightness: float = 30.0
    quality_max_mean_brightness: float = 225.0
    quality_max_overexposed_fraction: float = 0.15
    quality_max_underexposed_fraction: float = 0.30

    huawei_region: str = ""
    huawei_obs_bucket: str = ""
    huawei_obs_endpoint: str = ""
    huawei_access_key_id: str = ""
    huawei_secret_access_key: str = ""
    huawei_modelarts_endpoint: str = ""
    huawei_ecs_inference_url: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
