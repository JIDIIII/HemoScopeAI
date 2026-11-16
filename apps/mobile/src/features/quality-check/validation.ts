import type { components } from "../../types/api.generated";
type Quality = components["schemas"]["QualityResponse"];
export function validateQuality(value: unknown): Quality {
  const result = value as Quality;
  if (
    !result ||
    typeof result.acceptable !== "boolean" ||
    result.quality_status !== (result.acceptable ? "accepted" : "rejected") ||
    !result.measurements ||
    ![
      result.measurements.width,
      result.measurements.height,
      result.measurements.blur_score,
      result.measurements.mean_brightness,
    ].every(Number.isFinite) ||
    !Array.isArray(result.rejection_reasons) ||
    !result.rejection_reasons.every(
      (r) =>
        r &&
        typeof r.code === "string" &&
        typeof r.message === "string" &&
        typeof r.instructions === "string",
    ) ||
    !Array.isArray(result.actionable_instructions) ||
    !result.actionable_instructions.every((s) => typeof s === "string")
  )
    throw new Error(
      "The service returned invalid quality data. Retry before continuing.",
    );
  return result;
}
