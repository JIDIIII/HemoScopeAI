#!/usr/bin/env python3
"""Check required scaffold paths and safety exclusions without opening images."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "README.md",
    "apps/mobile/app/_layout.tsx",
    "apps/mobile/app/onboarding.tsx",
    "apps/mobile/app/setup.tsx",
    "apps/mobile/app/capture.tsx",
    "apps/mobile/app/review.tsx",
    "apps/mobile/app/crop.tsx",
    "apps/mobile/app/results.tsx",
    "apps/mobile/app/history.tsx",
    "apps/mobile/app/settings.tsx",
    "apps/mobile/package.json",
    "services/api/app/main.py",
    "services/api/app/core/security.py",
    "services/api/app/services/image_quality.py",
    "services/api/app/services/image_preprocessing.py",
    "services/api/tests/test_analyze.py",
    "ml/src/train.py",
    "packages/contracts/openapi.json",
    "docs/ARCHITECTURE.md",
    "docs/API_CONTRACT.md",
    "docs/FIVE_DAY_SPRINT.md",
    "docs/SAFETY_AND_LIMITATIONS.md",
    "docs/DEPLOYMENT.md",
    ".github/workflows/ci.yml",
]
FORBIDDEN_SUFFIXES = {".pt", ".pth", ".onnx", ".ckpt"}


def main() -> int:
    missing = [path for path in REQUIRED if not (ROOT / path).is_file()]
    unexpected_artifacts = [
        path
        for path in (ROOT / "ml" / "artifacts").rglob("*")
        if path.is_file() and path.suffix.lower() in FORBIDDEN_SUFFIXES
    ]
    if missing or unexpected_artifacts:
        if missing:
            print("Missing required files:")
            print("\n".join(f"- {path}" for path in missing))
        if unexpected_artifacts:
            print("Unexpected model artifacts:")
            print("\n".join(f"- {path.relative_to(ROOT)}" for path in unexpected_artifacts))
        return 1
    print(f"Structure verified: {len(REQUIRED)} required paths present; no model weights found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
