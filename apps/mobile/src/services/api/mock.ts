import type { components } from "../../types/api.generated";
export type MockScenario =
  | "analysis_complete"
  | "inconclusive"
  | "review_required"
  | "recapture_required"
  | "error"
  | "offline"
  | "timeout"
  | "invalid_file";
export const mockScenarios: MockScenario[] = [
  "analysis_complete",
  "inconclusive",
  "review_required",
  "recapture_required",
  "error",
  "offline",
  "timeout",
  "invalid_file",
];
let scenario: MockScenario = "inconclusive";
export const setMockScenario = (value: MockScenario) => {
  scenario = value;
};
export const getMockScenario = () => scenario;
export async function mockRequest(path: string): Promise<unknown> {
  await new Promise((resolve) => setTimeout(resolve, 350));
  if (scenario === "offline")
    throw new Error("SIMULATED: Backend offline. Check the network and retry.");
  if (scenario === "timeout")
    throw new Error("SIMULATED: Request timed out. Retry with the same crop.");
  if (scenario === "error")
    throw new Error("SIMULATED: Server error. No classification was produced.");
  if (path === "/health")
    return {
      api_version: "mock-v1",
      inference_mode: "simulated",
      model_available: false,
      model_version: "MOCK-NOT-A-MODEL",
      service_status: "development_mock",
    };
  if (scenario === "invalid_file")
    throw new Error(
      "SIMULATED: Invalid image. Choose a JPEG, PNG, or WebP image.",
    );
  if (path === "/quality") {
    const rejected = scenario === "recapture_required";
    return {
      acceptable: !rejected,
      quality_status: rejected ? "rejected" : "accepted",
      measurements: {
        width: 512,
        height: 512,
        file_format: "JPEG",
        blur_score: rejected ? 2 : 200,
        mean_brightness: 128,
        overexposed_fraction: 0,
        underexposed_fraction: 0,
      },
      rejection_reasons: rejected
        ? [
            {
              code: "blur",
              message: "SIMULATED: Image is out of focus.",
              instructions:
                "Refocus the microscope, stabilize the phone, and retake.",
            },
          ]
        : [],
      actionable_instructions: [],
    } satisfies components["schemas"]["QualityResponse"];
  }
  return {
    analysis_id: "mock-" + Date.now(),
    request_id: "mock-request-" + Date.now(),
    analysis_status: scenario,
    inference_mode: "simulated",
    model_label:
      scenario === "review_required" ? "Simulated morphology flag" : null,
    model_version: "MOCK-NOT-A-MODEL",
    quality_status: scenario === "recapture_required" ? "rejected" : "accepted",
    raw_model_score: null,
    warning:
      "SIMULATED DEVELOPMENT RESPONSE. No image measurements or model inference were performed. Research use only.",
  };
}
