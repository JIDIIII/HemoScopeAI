# Huawei Cloud deployment

This document describes a deployment plan. The scaffold does not create Huawei resources and its OBS, ModelArts, and ECS provider adapters are not live integrations.

## Prerequisites and access

Before deployment, confirm the account, target region, account verification, service quota, budget owner, billing alerts, authorized data source, and laboratory approval. Use a scoped IAM identity for only the required services. Keep credentials in a protected server secret store or host environment, rotate them, and never copy them into an Expo variable or mobile bundle.

Use HTTPS, authentication, upload size and timeout limits, request rate controls, private network rules, non-content audit logs, and an approved retention/deletion policy before accepting research uploads.

## Path A: ModelArts

1. Confirm the region supports the required ModelArts inference workflow and that the project has permission, quota, and budget for the selected deployment resources.
2. Package a reviewed model checkpoint and its exact preprocessing/version metadata. Do not deploy unverified weights.
3. Configure the ModelArts real-time inference endpoint and backend-only IAM access.
4. Implement and test request signing/authentication, input/output mapping, timeout behavior, model version response, and error handling in the ModelArts adapter.
5. Set the HEMOSCOPE_INFERENCE_PROVIDER=modelarts and the service endpoint through protected environment configuration only.
6. Verify an accepted confirmed crop reaches the live model and record the actual model version and deployment evidence.
7. Remove or stop billable resources after the demonstration when no longer needed.

The repository adapter currently marks this boundary but does not perform ModelArts requests.

## Path B: ECS-hosted inference

1. Provision a minimal ECS instance only after budget and access approval.
2. Apply operating system updates, restrict inbound network access, configure HTTPS termination, and create a scoped runtime identity.
3. Install the API package and the separately reviewed ML inference dependencies. Place only the reviewed checkpoint on the server.
4. Implement the ECS inference adapter and configure HEMOSCOPE_INFERENCE_PROVIDER=ecs with its internal endpoint.
5. Keep OBS access private and server-side. Do not grant the phone direct bucket credentials.
6. Verify health, upload limits, model version, inference timeout, error path, and cleanup procedure.
7. Stop or delete the ECS and any attached resources when the demo is complete.

The repository ECS adapter is an interface scaffold, not a live client.

## OBS storage

The OBS adapter must use a private bucket, scoped IAM, encryption, object-key conventions without identifiers, and explicit retention/deletion. Use backend-mediated access or short-lived signed URLs only after security review. Do not expose a public bucket. The current adapter does not call the OBS SDK.

## Local development

Keep HEMOSCOPE_INFERENCE_PROVIDER=none and HEMOSCOPE_ENABLE_DEMO_MOCK=false by default. To verify API flow without a model, explicitly set HEMOSCOPE_ENABLE_DEMO_MOCK=true in a local backend environment. The response is marked simulated, has no model score, and is never live inference evidence.
