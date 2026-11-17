# Huawei Cloud infrastructure

Planned path: Expo mobile app to authenticated HTTPS FastAPI, with a private OBS bucket and ModelArts real-time inference. Use backend-hosted PyTorch inference on ECS if ModelArts account access, region, quota, resource pool, or budget is unavailable. The team does not yet have a Huawei Cloud account configured, so the selected provider remains `none`.

The repository contains configuration boundaries and disabled adapter classes only. No billable resource is provisioned and no adapter currently makes a live Huawei API request. The backend defaults to local image validation and quality assessment; accepted images without a configured model receive an explicit inconclusive response. Follow docs/DEPLOYMENT.md for prerequisites, least-privilege IAM, private storage, endpoint validation, and cleanup.

Store access keys and tokens outside source control in a protected server environment. Example environment files contain blanks only. Never put Huawei credentials in EXPO_PUBLIC_ variables.

## Provider switch preparation

The backend provider setting is `HEMOSCOPE_INFERENCE_PROVIDER=none|modelarts|ecs`. Set the endpoint and required server-side credentials only after the corresponding adapter has been implemented and verified against the account's region and service contract. `modelarts` and `ecs` are not live in this scaffold and currently fail closed with a structured `model_unavailable` error instead of returning a prediction. `none` is the supported local mode.

Do not enable OBS upload by default. The existing private-storage interface and blank environment settings are preparation only; remote persistence, access control, and retention must be implemented before storing images.
