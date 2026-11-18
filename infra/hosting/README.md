# Zero-dollar hosting path

## Recommended under a strict $0 budget: Render Free + Supabase Free Auth

The Android app does not need a separate web host. It calls the FastAPI service at `EXPO_PUBLIC_API_BASE_URL`; Supabase Auth handles sign-in. For a zero-dollar preview, Render Free is the simplest fit: Render documents free Docker web services, a Singapore region, managed TLS, and no credit card requirement. The included `render.yaml` builds the API with the existing `services/api/Dockerfile`, enables Supabase token checks, and keeps inference disabled. See [Render's free service limits](https://render.com/docs/free), [regions](https://render.com/docs/regions), [Docker Blueprint fields](https://render.com/docs/blueprint-spec), and [free Docker hosting](https://render.com/hosting/docker).

Render Free is suitable only for the no-model software flow. It has 512 MB RAM, sleeps after 15 minutes without traffic, takes about a minute to wake, and has an ephemeral filesystem. Free services can be restarted, and included monthly usage is capped. Do not add a payment method; Render documents suspension at included-usage limits when no payment method is present. These limits make it unsuitable for responsive production use or PyTorch inference. The API does not persist uploads, so its in-memory preview flow does not depend on a persistent disk.

### Deploy on Render

1. Create a Supabase Free project, preferably in Singapore. Disable public sign-ups and issue accounts only to approved users. Supabase Free includes Auth, but low-activity projects can pause after a week. See [Supabase pricing](https://supabase.com/pricing) and [free project pausing](https://supabase.com/docs/guides/platform/free-project-pausing).
2. In Render, create a Blueprint from this repository. Set the Blueprint file path to `infra/hosting/render.yaml`; the file configures a Docker web service on the Free plan in Singapore.
3. When prompted for `HEMOSCOPE_SUPABASE_URL` and `HEMOSCOPE_SUPABASE_PUBLISHABLE_KEY`, enter the Supabase project URL and publishable key. Never use the Supabase secret/service-role key. The project URL and publishable key are public configuration.
4. Deploy the Blueprint and wait for its `/health` check to pass. Render supplies an HTTPS service URL. Set the mobile build variables to `EXPO_PUBLIC_API_BASE_URL=<Render HTTPS URL>`, `EXPO_PUBLIC_AUTH_MODE=supabase`, and the same Supabase URL and publishable key.
5. Leave the Render plan at Free and keep a payment method off the account to preserve the no-charge behavior. If a usage limit is reached, expect the preview to be suspended until usage resets or the issue is resolved.

The API container protects `/quality`, `/analyze`, and `/session/*` with Supabase access-token validation when hosted auth is enabled; `/health` stays public. The API validates tokens server-side before parsing upload bodies. The hosted auth flow still needs live verification against the configured Supabase project before approved users send research images.

This profile intentionally sets `HEMOSCOPE_INFERENCE_PROVIDER=none`. It can host the software flow and return the API's explicit inconclusive/unavailable response, but it cannot classify an image. The frozen model bundle is absent from this checkout, and the normal API image does not install PyTorch. Do not claim real inference until the authorized model bundle is available and verified.

## Higher-capacity alternative: OCI Always Free

If Render's 512 MB cap blocks image processing, OCI Always Free offers a larger free VM: the published allowance includes up to 2 OCPUs and 12 GB RAM of Ampere A1 compute, 200 GB combined block storage, and 10 TB/month outbound transfer. Always Free compute must be in the tenancy's home region. Singapore is `ap-singapore-1`; choose it as the home region when creating a new tenancy if available and suitable. Free capacity can be unavailable. See [Always Free resources](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm) and [OCI regions](https://docs.oracle.com/en-us/iaas/Content/General/Concepts/regions.htm).

OCI is not the first choice when even a temporary card authorization is a blocker: account signup requires card details for identity verification and may create a temporary authorization hold, although Oracle says the card is not charged unless the account is upgraded. Keep the account unupgraded and provision only resources marked Always Free. Free VMs may be reclaimed after a seven-day period when CPU, network, and (for A1) memory use all stay under the published thresholds; capacity may also be unavailable. See the [OCI Free Tier FAQ](https://www.oracle.com/cloud/free/faq/) and [post-trial behavior](https://docs.oracle.com/en-us/iaas/Content/GSG/Tasks/signingup_topic-What_Happens_When_the_Promotion_Expires.htm).

The repository includes an ARM64 Docker Compose deployment with Caddy TLS in [`oci/`](oci/). It requires a hostname with DNS pointing to the VM and ports 80/443 open. It keeps port 8080 private, configures Supabase Auth, and disables model inference. Measure the actual workload and verify all model dependencies on ARM64 before considering this VM for real inference.

## Supabase Auth

Supabase Free is $0 and provides Auth, but low-activity free projects can pause after a week. Keep public sign-ups disabled and provision accounts only for approved users. See [Supabase pricing](https://supabase.com/pricing) and [free-project pausing](https://supabase.com/docs/guides/platform/free-project-pausing).

## Security and deployment gates

- No Supabase project, Render service, or OCI tenancy is configured here; no remote resources were created. Hosted authentication and TLS have not been verified against live services.
- Before inviting users, add and verify request-rate controls, set a privacy-safe logging and retention/deletion policy, and validate upload limits and timeouts under the selected host's memory cap. API upload byte and pixel limits are configured in `services/api/.env.example`.
- Keep the endpoint limited to approved, de-identified research material. This app is not a diagnostic device.
- `/health` is public and reports service/model availability only. Image endpoints reject requests without a valid Supabase user token when hosted auth is enabled.
- No OBS storage is needed by the current flow: image data is processed in memory and research history stays on the phone.

## Huawei Cloud remains a later provider

The container and mobile URL configuration are host-neutral. To move to Huawei later, deploy the same API image on ECS and set Huawei-specific server configuration there. The `modelarts` and `ecs` inference adapters in this repository are still scaffolds and do not make live requests. Implement and verify Huawei service authentication and request mapping before switching from `none`. Never store Huawei credentials in Expo.
