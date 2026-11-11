# Huawei Cloud infrastructure

Planned path: Expo mobile app to authenticated HTTPS FastAPI, with a private OBS bucket and ModelArts real-time inference. Use backend-hosted PyTorch inference on ECS if ModelArts account access, region, quota, resource pool, or budget is unavailable.

The repository contains configuration boundaries and disabled adapter classes only. No billable resource is provisioned and no adapter currently makes a live Huawei API request. Follow docs/DEPLOYMENT.md for prerequisites, least-privilege IAM, private storage, endpoint validation, and cleanup.

Store access keys and tokens outside source control in a protected server environment. Example environment files contain blanks only. Never put Huawei credentials in EXPO_PUBLIC_ variables.
