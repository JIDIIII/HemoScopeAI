def create_model(num_classes: int = 2, pretrained: bool = False):
    """Build MobileNetV3-Small; pretrained weights download only when explicitly enabled."""
    try:
        from torch import nn
        from torchvision.models import MobileNet_V3_Small_Weights, mobilenet_v3_small
    except ImportError as exc:
        raise RuntimeError(
            'Install the ML training dependencies with: python -m pip install -e ".[train]"'
        ) from exc

    weights = MobileNet_V3_Small_Weights.DEFAULT if pretrained else None
    model = mobilenet_v3_small(weights=weights)
    input_features = model.classifier[-1].in_features
    model.classifier[-1] = nn.Linear(input_features, num_classes)
    return model
