import type { components } from "../../types/api.generated";
type Analysis = components["schemas"]["AnalysisResponse"];
export const resultCopy = {
  recapture_required: {
    title: "Recapture required",
    guidance:
      "The crop was rejected. Refocus, adjust illumination, or select a complete cell and retry.",
  },
  inconclusive: {
    title: "Inconclusive",
    guidance:
      "The model could not give a reliable morphology label. Ask a qualified reviewer to inspect the cell.",
  },
  review_required: {
    title: "Qualified review required",
    guidance:
      "The selected cell has been flagged for qualified morphology review. This is not a diagnosis.",
  },
  analysis_complete: {
    title: "Selected-cell analysis complete",
    guidance:
      "Analysis covers only this selected cell. It does not rule out disease elsewhere in the field or slide.",
  },
  error: {
    title: "Analysis failed",
    guidance:
      "No interpretable result is available. Check the connection and retry. Failure is not a negative finding.",
  },
} as const;
export function validateAnalysis(value: unknown): Analysis {
  const result = value as Analysis;
  if (
    !result ||
    !Object.hasOwn(resultCopy, result.analysis_status) ||
    typeof result.analysis_id !== "string" ||
    typeof result.request_id !== "string" ||
    !result.request_id ||
    typeof result.warning !== "string" ||
    !["accepted", "rejected"].includes(result.quality_status) ||
    (result.inference_mode != null &&
      !["real", "simulated", "unavailable"].includes(result.inference_mode)) ||
    (result.model_label != null && typeof result.model_label !== "string") ||
    (result.model_version != null &&
      typeof result.model_version !== "string") ||
    (result.all_score != null &&
      (!Number.isFinite(result.all_score) ||
        result.all_score < 0 ||
        result.all_score > 1)) ||
    (result.decision_policy_version != null &&
      typeof result.decision_policy_version !== "string") ||
    (result.raw_model_score != null && !Number.isFinite(result.raw_model_score))
  )
    throw new Error(
      "The service returned an invalid result. No classification can be displayed.",
    );
  if (
    result.inference_mode === "unavailable" &&
    (result.analysis_status !== "inconclusive" ||
      result.quality_status !== "accepted" ||
      result.model_label != null ||
      result.raw_model_score != null ||
      result.model_version != null)
  )
    throw new Error(
      "An unavailable model cannot provide a classification or score.",
    );
  if (
    (result.analysis_status === "recapture_required" &&
      result.quality_status !== "rejected") ||
    (result.quality_status === "rejected" &&
      !["recapture_required", "error"].includes(result.analysis_status))
  )
    throw new Error(
      "The service returned contradictory crop quality and analysis status. No classification can be displayed.",
    );
  if (
    ["analysis_complete", "review_required"].includes(result.analysis_status) &&
    (result.quality_status !== "accepted" ||
      !result.model_version ||
      !result.inference_mode)
  )
    throw new Error(
      "The service returned incomplete model metadata or a rejected crop. No classification can be displayed.",
    );
  if (
    result.inference_mode === "real" &&
    (!result.model_version ||
      result.all_score == null ||
      !result.decision_policy_version)
  )
    throw new Error(
      "The service returned a real model result without its score and policy version.",
    );
  return result;
}
