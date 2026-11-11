# Three-developer responsibilities

The assignments are role-based; they do not name contributors. Each owner keeps module changes within the assigned area and coordinates API changes before merging.

| Role | Primary ownership | First task | Branch recommendation |
| --- | --- | --- | --- |
| Developer 1 — AI/ML | ml/, dataset manifest, subject splits, preprocessing, training, evaluation, inference packaging, model card | Confirm C-NMC 2019 access and permitted use; inspect labels, subject keys, duplicates, and class balance before creating a split | feature/ai-pipeline |
| Developer 2 — Mobile | apps/mobile/, camera/gallery, crop UI, quality messaging, results, AsyncStorage history | Install the app on the target Android phone; verify camera/gallery permissions and complete field preview before implementing crop selection | feature/mobile-app |
| Developer 3 — Cloud/Hardware | services/api/, infra/, hardware/, Huawei IAM/OBS/ModelArts/ECS, security, integration | Confirm microscope and slide access, phone/adapter fit, Huawei region/quota/billing, and API request behavior | feature/backend-cloud |

## Integration expectations

- Freeze the request/response contract early. Change Pydantic schemas first, then regenerate packages/contracts/openapi.json and apps/mobile/src/types/api.generated.ts in the same change.
- Use the explicit analysis statuses and structured error envelope. Failed requests never become negative results.
- Keep Python training code out of the mobile bundle and Huawei secrets out of mobile environment variables.
- Run the API, mobile type check/lint, and contract drift check before integration.
- Keep research images and generated checkpoints out of Git.
- Use small handoffs that state the changed contract, implementation status, validation performed, and remaining TODOs.

No branches are created by this scaffold. The suggested names are local workflow guidance only.
