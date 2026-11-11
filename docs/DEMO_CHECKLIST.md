# HemoScope AI demo checklist

## Before the demonstration

- Confirm permission for the microscope, adapter, slides, and images.
- Remove slide labels, patient names, and identifying material from view.
- Check phone, microscope, objective, adapter, lighting, Wi-Fi, and API base URL.
- Confirm whether the backend has a real model. If only the development mock is enabled, label every result as simulated and do not present it as model evidence.
- Verify that quality rejection stops analysis and that model_unavailable stays an error/inconclusive state.
- Prepare current limitations and any measured results with their denominators.

## Scaffold demonstration

- Start the API and show GET /health.
- Open the Expo app and acknowledge the research disclaimer.
- Show microscope setup instructions.
- Use a physical phone to capture a field or select an approved image.
- Show the preview and quality request/response.
- If quality rejects the image, show its reason and retake instruction.
- State that drag-and-resize crop and genuine inference are not yet implemented in this scaffold.

## Never claim

- Do not say the app diagnoses leukemia or can rule it out.
- Do not treat a single cell or field as a whole-slide negative result.
- Do not describe a simulated response as real inference.
- Do not show unmeasured accuracy or fabricated model output.
- Do not display identifiable slide or patient information.
