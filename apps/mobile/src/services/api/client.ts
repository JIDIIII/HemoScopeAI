import { API_BASE_URL, USE_MOCK_API } from "@/constants/api";
import { mockRequest } from "./mock";
import { validateAnalysis } from "@/features/analysis/result";
import { validateQuality } from "@/features/quality-check/validation";
import type { components } from "@/types/api.generated";
import { Platform } from "react-native";
import { File } from "expo-file-system";
import {
  AuthSessionError,
  getSupabaseAccessToken,
} from "@/services/auth/supabase";

type QualityResponse = components["schemas"]["QualityResponse"];
type HealthResponse = components["schemas"]["HealthResponse"];
type ErrorResponse = components["schemas"]["ErrorResponse"];
type AnalysisResponse = components["schemas"]["AnalysisResponse"];
type CropBounds = components["schemas"]["CropBounds"];

export type ImageUpload = {
  uri: string;
  mimeType: string;
  fileName: string;
};

async function appendImage(
  body: FormData,
  field: string,
  image: ImageUpload,
  name: string,
): Promise<void> {
  if (Platform.OS === "web") {
    // Browser FormData requires binary data; the native URI descriptor becomes
    // the literal string "[object Object]" when appended in a browser.
    const response = await fetch(image.uri);
    if (!response.ok)
      throw new Error("Cannot open this image. Choose it again.");
    body.append(field, await response.blob(), name);
  } else {
    // SDK 57's fetch requires binary file parts, not the legacy { uri } descriptor.
    // Read before requesting so a missing local file is an image error.
    try {
      const bytes = await new File(image.uri).arrayBuffer();
      // Expo fetch accepts byte-backed file parts. React Native's global Blob
      // cannot construct a blob from ArrayBuffer, so supply its supported bytes()
      // interface directly, with a safe filename and the validated media type.
      body.append(field, {
        name,
        type: image.mimeType,
        bytes: async () => new Uint8Array(bytes),
      } as unknown as Blob);
    } catch {
      throw new Error("Cannot open this image. Choose it again.");
    }
  }
}

async function parseError(response: Response): Promise<Error> {
  try {
    const payload = (await response.json()) as ErrorResponse;
    const requestId = payload.error.request_id;
    return new Error(
      requestId
        ? `${payload.error.message} (Request ID: ${requestId})`
        : payload.error.message,
    );
  } catch {
    return new Error("Request failed with status " + response.status + ".");
  }
}

async function request(
  url: string,
  init?: RequestInit,
  timeoutMs = 15000,
  authenticated = false,
): Promise<Response> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    if (USE_MOCK_API)
      return new Response(
        JSON.stringify(await mockRequest(url.replace(API_BASE_URL, ""))),
        { headers: { "Content-Type": "application/json" } },
      );
    const headers = new Headers(init?.headers);
    if (authenticated) {
      const accessToken = await getSupabaseAccessToken();
      if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
    }
    const response = await fetch(url, {
      ...init,
      headers,
      signal: controller.signal,
    });
    // Consume the body while the timeout is active, including slow body downloads.
    const body = await response.text();
    return new Response(body, {
      status: response.status,
      headers: response.headers,
    });
  } catch (cause) {
    if (USE_MOCK_API) throw cause;
    if (cause instanceof AuthSessionError) throw cause;
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
  await appendImage(body, "image", image, "research-field." + safeExtension);
  const response = await request(API_BASE_URL + "/quality", {
    method: "POST",
    body,
  }, 15000, true);
  if (!response.ok) throw await parseError(response);
  return validateQuality(await response.json());
}

export async function analyzeConfirmedCrop(input: {
  cellCrop: ImageUpload;
  // Only provide bounds when uploading a source field, never an extracted crop.
  cropBounds?: CropBounds;
  researchSessionId?: string;
}): Promise<AnalysisResponse> {
  const body = new FormData();
  const safeExtension =
    input.cellCrop.mimeType === "image/png"
      ? "png"
      : input.cellCrop.mimeType === "image/webp"
        ? "webp"
        : "jpg";
  await appendImage(
    body,
    "cell_crop",
    input.cellCrop,
    "confirmed-cell." + safeExtension,
  );
  body.append("crop_confirmed", "true");
  if (input.cropBounds) {
    body.append("crop_bounds", JSON.stringify(input.cropBounds));
  }
  // Local history IDs (including legacy local-... IDs) are not backend UUIDs.
  // This optional field must be omitted unless it satisfies the API contract.
  if (
    input.researchSessionId &&
    /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(
      input.researchSessionId,
    )
  ) {
    body.append("research_session_id", input.researchSessionId);
  }
  const response = await request(API_BASE_URL + "/analyze", {
    method: "POST",
    body,
  }, 15000, true);
  if (!response.ok) throw await parseError(response);
  return validateAnalysis(await response.json());
}
