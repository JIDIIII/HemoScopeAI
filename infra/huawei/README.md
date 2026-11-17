# Huawei Cloud infrastructure

Planned path: Expo mobile app to authenticated HTTPS FastAPI, with a private OBS bucket and ModelArts real-time inference. Use backend-hosted PyTorch inference on ECS if ModelArts account access, region, quota, resource pool, or budget is unavailable. The team does not yet have a Huawei Cloud account configured, so the selected provider remains `none`.

The repository contains configuration boundaries and disabled adapter classes only. No billable resource is provisioned and no adapter currently makes a live Huawei API request. The backend defaults to local image validation and quality assessment; accepted images without a configured model receive an explicit inconclusive response. Follow docs/DEPLOYMENT.md for prerequisites, least-privilege IAM, private storage, endpoint validation, and cleanup.

Store access keys and tokens outside source control in a protected server environment. Example environment files contain blanks only. Never put Huawei credentials in EXPO_PUBLIC_ variables.

## Provider switch preparation

The backend provider setting is `HEMOSCOPE_INFERENCE_PROVIDER=none|local|modelarts|ecs`. `none` is the no-model local mode. `local` loads the ignored, versioned handoff bundle from `ml/artifacts/handoff/hemoscope-inference-handoff-v1` and runs CPU inference after the crop-quality gate; it requires the optional `local-inference` Python extra. This is for local development and is not packaged into the API Docker image. Set endpoint and server-side credentials only after cloud adapters are implemented and verified against the account's region and service contract. `modelarts` and `ecs` remain scaffolds and fail closed with `model_unavailable` instead of returning a prediction.

Do not enable OBS upload by default. The existing private-storage interface and blank environment settings are preparation only; remote persistence, access control, and retention must be implemented before storing images.
