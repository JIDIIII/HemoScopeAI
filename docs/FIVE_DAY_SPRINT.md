# HemoScope AI five-day sprint

This scaffold establishes the repository foundation. The milestones below plan future work; they are not claims that the five days have been completed. The project outline contains a seven-day plan, while this document follows the five-day schedule requested for the project.

## Day 1 — Foundation

- Initialize the monorepo and role-based module boundaries.
- Start the Expo mobile app and FastAPI backend.
- Agree the Pydantic, OpenAPI, and TypeScript API contract.
- Connect mobile image selection to the API in a development workflow.
- Check cloud region, IAM access, billing controls, microscope access, phone, and adapter feasibility.

**Checkpoint:** app sends an image to the API; hardware and Huawei access have a documented go/fallback decision.

## Day 2 — Baseline

- Prepare the C-NMC 2019 manifest and subject-separated train/validation/test split.
- Perform an initial MobileNetV3-Small training and evaluation run using approved data.
- Implement capture, full-field preview, and manual single-cell crop.
- Record the phone, microscope, objective, eyepiece, adapter, and capture settings.

**Checkpoint:** a baseline has measured validation results and the app can preview and confirm one complete cell crop.

## Day 3 — Quality and Cloud

- Calibrate OpenCV quality checks on representative fields and crops.
- Implement actionable rejection and retake states.
- Connect ModelArts inference or the Huawei ECS fallback.
- Return model version and uncertainty/inconclusive state through the shared contract.

**Checkpoint:** poor images are rejected before inference and an accepted crop reaches a genuine Huawei-hosted model.

## Day 4 — Integration

- Test capture on the physical Android phone.
- Run field quality review and manual cell selection.
- Upload the confirmed crop over HTTPS to the live endpoint.
- Display the real cloud result, model version, and warning in the app.
- Save non-identifying research session metadata locally.

**Checkpoint:** the real device-to-cloud workflow has a repeatable end-to-end test record.

## Day 5 — Validation and Handoff

- Run regression checks for capture, quality rejection, crop, inference, history, and errors.
- Record evaluation metrics with denominators and limitations.
- Produce an Android build, deployment notes, architecture diagram, and model card.
- Rehearse the demonstration and document unresolved risks.

**Checkpoint:** the team can repeat the demonstration and hand over source, build, model evidence, setup notes, and known limitations.

## Foundation completed by this scaffold

The mobile navigation and camera/gallery selection path, backend health and quality routes, quality-gate test cases, OpenAPI/type generation, ML training interfaces, CI configuration, and role documentation are present. Manual crop generation, trained weights, cloud APIs, authenticated deployment, and physical phone validation remain future sprint work.
