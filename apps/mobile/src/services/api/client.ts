import { API_BASE_URL } from "@/constants/api";
import type { components } from "@/types/api.generated";

type QualityResponse = components["schemas"]["QualityResponse"];
type HealthResponse = components["schemas"]["HealthResponse"];
type ErrorResponse = components["schemas"]["ErrorResponse"];
type AnalysisResponse = components["schemas"]["AnalysisResponse"];

export type ImageUpload = {
  uri: string;
  mimeType: string;
  fileName: string;
};

async function parseError(response: Response): Promise<Error> {
  try {
    const payload = (await response.json()) as ErrorResponse;
    return new Error(payload.error.message);
  } catch {
    return new Error("Request failed with status " + response.status + ".");
  }
}

async function request(
  url: string,
  init?: RequestInit,
  timeoutMs = 15000,
): Promise<Response> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...init, signal: controller.signal });
  } catch (cause) {
    if (cause instanceof Error && cause.name === "AbortError") {
      throw new Error(
        "The request timed out. Check the network and try again.",
      );
    }
    throw new Error(
      "The backend could not be reached. Check the API URL and network.",
    );
  } finally {
    clearTimeout(timeout);
  }
}

export async function getHealth(): Promise<HealthResponse> {
  const response = await request(API_BASE_URL + "/health");
  if (!response.ok) throw await parseError(response);
  return (await response.json()) as HealthResponse;
}

export async function checkImageQuality(
  image: ImageUpload,
): Promise<QualityResponse> {
  const body = new FormData();
  const safeExtension =
    image.mimeType === "image/png"
      ? "png"
      : image.mimeType === "image/webp"
        ? "webp"
        : "jpg";
  body.append("image", {
    uri: image.uri,
    name: "research-field." + safeExtension,
    type: image.mimeType,
  } as unknown as Blob);
  const response = await request(API_BASE_URL + "/quality", {
    method: "POST",
    body,
  });
  if (!response.ok) throw await parseError(response);
  return (await response.json()) as QualityResponse;
}

export async function analyzeConfirmedCrop(input: {
  cellCrop: ImageUpload;
  researchSessionId?: string;
}): Promise<AnalysisResponse> {
  const body = new FormData();
  const safeExtension =
    input.cellCrop.mimeType === "image/png"
      ? "png"
      : input.cellCrop.mimeType === "image/webp"
        ? "webp"
        : "jpg";
  body.append("cell_crop", {
    uri: input.cellCrop.uri,
    name: "confirmed-cell." + safeExtension,
    type: input.cellCrop.mimeType,
  } as unknown as Blob);
  body.append("crop_confirmed", "true");
  if (input.researchSessionId) {
    body.append("research_session_id", input.researchSessionId);
  }
  const response = await request(API_BASE_URL + "/analyze", {
    method: "POST",
    body,
  });
  if (!response.ok) throw await parseError(response);
  return (await response.json()) as AnalysisResponse;
}
