# Hosting and Huawei Cloud deployment

For a hard-$0 host outside Huawei Cloud, see [zero-dollar hosting options](../infra/hosting/README.md). The prepared first target is a Render Free service with Supabase Free Auth for the no-model preview; OCI Always Free is a higher-capacity alternative with account-verification and idle-reclamation caveats. Neither host is configured or provisioned in this repository.

The API container uses the runtime-provided `PORT` value and remains portable to another OCI-compatible host. Keep Huawei provider configuration separate from hosting configuration so the service can later run on Huawei ECS, or call a verified Huawei inference endpoint, without changing the mobile API URL contract. The Huawei adapter classes below remain scaffolds.

This document describes a deployment plan. The current scope keeps Huawei calls and remote storage disabled. The OBS, ModelArts, and ECS provider adapters are boundaries/configuration points, not live integrations. No OCI or Huawei resources have been created.

## Local mode (default)

Run the FastAPI backend locally with `HEMOSCOPE_INFERENCE_PROVIDER=none` and `HEMOSCOPE_ENABLE_DEMO_MOCK=false`. Health, upload validation, quality assessment, normalized crop extraction, and the mobile flow work without Huawei credentials. An accepted crop returns `analysis_status=inconclusive` and `inference_mode=unavailable` when no genuine model is configured; the response contains no label or score and says that no classification was performed. This is an operational fallback, not model inference evidence.

The mobile app includes a public software-flow sample. Its source, license, and limitations are recorded in `samples/public/README.md`. It is a neutrophil sample, not a B-ALL example and not a physical capture or quality-calibration set.

## Prerequisites and access

Before deployment, confirm the account, target region, account verification, service quota, budget owner, billing alerts, authorized data source, and laboratory approval. Use a scoped IAM identity for only the required services. Keep credentials in a protected server secret store or host environment, rotate them, and never copy them into an Expo variable or mobile bundle.

Use HTTPS, authentication, upload size and timeout limits, request rate controls, private network rules, non-content audit logs, and an approved retention/deletion policy before accepting research uploads.

## HTTPS and authentication

Local development may use HTTP only on a trusted private network. The mobile client and API support Supabase Auth email/password sessions. The API validates each Supabase access token with the project's `/auth/v1/user` endpoint before parsing `/quality`, `/analyze`, or `/session/{id}` requests; `/health` remains public. Local defaults keep auth disabled. Before remote upload access, configure `HEMOSCOPE_AUTH_MODE=supabase`, `HEMOSCOPE_SUPABASE_URL`, and `HEMOSCOPE_SUPABASE_PUBLISHABLE_KEY` on the API, and build the app with `EXPO_PUBLIC_AUTH_MODE=supabase` and matching project settings. Disable public sign-ups and issue accounts only to authorized users. The project URL and publishable key are public configuration; never use a Supabase secret or service-role key in the app or API. A remote endpoint must terminate TLS and retain the upload limits, privacy-safe logs, rate controls, and retention/deletion controls described here. See [the hosting guide](../infra/hosting/README.md) for the Render Blueprint and OCI Compose profile.

## Path A: ModelArts

1. Confirm the region supports the required ModelArts inference workflow and that the project has permission, quota, and budget for the selected deployment resources.
2. Package a reviewed model checkpoint and its exact preprocessing/version metadata. Do not deploy unverified weights.
3. Configure the ModelArts real-time inference endpoint and backend-only IAM access.
4. Implement and test request signing/authentication, input/output mapping, timeout behavior, model version response, and error handling in the ModelArts adapter.
5. Set the HEMOSCOPE_INFERENCE_PROVIDER=modelarts and the service endpoint through protected environment configuration only.
6. Verify an accepted confirmed crop reaches the live model and record the actual model version and deployment evidence.
7. Remove or stop billable resources after the demonstration when no longer needed.

The current repository adapter marks this boundary but does not perform ModelArts requests. After account setup, implement and validate the provider-specific authentication/request mapping before setting `HEMOSCOPE_INFERENCE_PROVIDER=modelarts`.

## Path B: ECS-hosted inference

1. Provision a minimal ECS instance only after budget and access approval.
2. Apply operating system updates, restrict inbound network access, configure HTTPS termination, and create a scoped runtime identity.
3. Install the API package and the separately reviewed ML inference dependencies. Place only the reviewed checkpoint on the server.
4. Implement the ECS inference adapter and configure HEMOSCOPE_INFERENCE_PROVIDER=ecs with its internal endpoint.
5. Keep OBS access private and server-side. Do not grant the phone direct bucket credentials.
6. Verify health, upload limits, model version, inference timeout, error path, and cleanup procedure.
7. Stop or delete the ECS and any attached resources when the demo is complete.

The repository ECS adapter is an interface scaffold, not a live client. After a Huawei account is available, select the endpoint and model-serving contract, implement the client, then configure `HEMOSCOPE_INFERENCE_PROVIDER=ecs` and the internal endpoint through protected server configuration.

## OBS storage

The OBS adapter must use a private bucket, scoped IAM, encryption, object-key conventions without identifiers, and explicit retention/deletion. Use backend-mediated access or short-lived signed URLs only after security review. Do not expose a public bucket. The current adapter does not call the OBS SDK, and local image processing does not require OBS.

## Local development

Keep `HEMOSCOPE_INFERENCE_PROVIDER=none` and `HEMOSCOPE_ENABLE_DEMO_MOCK=false` by default. Default no-model analysis returns an explicit inconclusive response so the mobile flow remains usable without pretending to classify. The optional `HEMOSCOPE_ENABLE_DEMO_MOCK=true` mode is marked simulated, has no model score, and is never live inference evidence.
