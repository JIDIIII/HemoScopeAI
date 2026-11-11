from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class PreprocessingMetadata:
    image_size: int = 224
    color_space: str = "RGB"
    resize: str = "bilinear-square"
    mean: tuple[float, float, float] = (0.485, 0.456, 0.406)
    standard_deviation: tuple[float, float, float] = (0.229, 0.224, 0.225)
    interpolation: str = "PIL bilinear"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_transforms(image_size: int = 224, training: bool = False):
    try:
        from torchvision import transforms
    except ImportError as exc:
        raise RuntimeError(
            'Install the ML training dependencies with: python -m pip install -e ".[train]"'
        ) from exc

    steps = [transforms.Resize((image_size, image_size))]
    if training:
        steps.extend(
            [
                transforms.RandomHorizontalFlip(p=0.5),
                transforms.RandomRotation(degrees=5),
            ]
        )
    steps.extend(
        [
            transforms.ToTensor(),
            transforms.Normalize(
                mean=(0.485, 0.456, 0.406),
                std=(0.229, 0.224, 0.225),
            ),
        ]
    )
    return transforms.Compose(steps)
