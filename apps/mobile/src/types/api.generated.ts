/* Generated from packages/contracts/openapi.json. Do not edit by hand. */
export interface components {
  schemas: {
    "AnalysisResponse": {
      "analysis_id": string;
      "analysis_status": components["schemas"]["AnalysisStatus"];
      "inference_mode"?: (components["schemas"]["InferenceMode"]) | (null);
      "model_label"?: (string) | (null);
      "model_version"?: (string) | (null);
      "quality_status": components["schemas"]["QualityStatus"];
      "raw_model_score"?: (number) | (null);
      "research_session_id"?: (string) | (null);
      "warning": string;
    };
    "AnalysisStatus": "recapture_required" | "inconclusive" | "review_required" | "analysis_complete" | "error";
    "CaptureMetadata": {
      "capture_sequence_index"?: (number) | (null);
      "objective_magnification"?: (number) | (null);
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
      "inference_mode": string;
      "model_available": boolean;
      "model_version"?: (string) | (null);
      "service_status": string;
    };
    "InferenceMode": "real" | "simulated";
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
