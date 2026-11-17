/* Generated from packages/contracts/openapi.json. Do not edit by hand. */
export interface components {
  schemas: {
    "AnalysisResponse": {
      "actionable_instructions"?: Array<string>;
      "all_score"?: (number) | (null);
      "analysis_id": string;
      "analysis_status": components["schemas"]["AnalysisStatus"];
      "decision_policy_version"?: (string) | (null);
      "inference_mode"?: (components["schemas"]["InferenceMode"]) | (null);
      "model_label"?: (string) | (null);
      "model_version"?: (string) | (null);
      "quality_status": components["schemas"]["QualityStatus"];
      "raw_model_score"?: (number) | (null);
      "rejection_reasons"?: Array<components["schemas"]["QualityRejectionReason"]>;
      "request_id": string;
      "research_session_id"?: (string) | (null);
      "warning": string;
    };
    "AnalysisStatus": "recapture_required" | "inconclusive" | "review_required" | "analysis_complete" | "error";
    "CaptureMetadata": {
      "capture_profile_id"?: (string) | (null);
      "capture_sequence_index"?: (number) | (null);
      "objective_magnification"?: (number) | (null);
    };
    "CropBounds": {
      "height": number;
      "width": number;
      "x": number;
      "y": number;
    };
    "ErrorDetail": {
      "code": string;
      "details"?: (Record<string, unknown>) | (null);
      "message": string;
      "request_id": string;
    };
    "ErrorResponse": {
      "error": components["schemas"]["ErrorDetail"];
    };
    "HealthResponse": {
      "api_version": string;
      "inference_mode": components["schemas"]["InferenceMode"];
      "model_available": boolean;
      "model_version"?: (string) | (null);
      "service_status": string;
    };
    "InferenceMode": "real" | "simulated" | "unavailable";
    "QualityMeasurements": {
      "blur_score": number;
      "file_format": string;
      "height": number;
      "mean_brightness": number;
      "overexposed_fraction": number;
      "underexposed_fraction": number;
      "width": number;
    };
    "QualityRejectionReason": {
      "code": string;
      "instructions": string;
      "message": string;
    };
    "QualityResponse": {
      "acceptable": boolean;
      "actionable_instructions": Array<string>;
      "measurements": components["schemas"]["QualityMeasurements"];
      "quality_status": components["schemas"]["QualityStatus"];
      "rejection_reasons": Array<components["schemas"]["QualityRejectionReason"]>;
    };
    "QualityStatus": "accepted" | "rejected";
    "SessionMetadata": {
      "analysis_status"?: (components["schemas"]["AnalysisStatus"]) | (null);
      "created_at": string;
      "model_version"?: (string) | (null);
      "quality_status"?: (components["schemas"]["QualityStatus"]) | (null);
      "session_id": string;
    };
  };
}
