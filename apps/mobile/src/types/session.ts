export type ResearchSession = {
  sessionId: string;
  imageId: string;
  capturedAt: string;
  qualityStatus: string;
  analysisStatus: string;
  modelVersion?: string;
  inferenceMode?: "real" | "simulated";
  modelLabel?: string;
  rawModelScore?: number;
  warning?: string;
};
