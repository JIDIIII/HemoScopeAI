import { router, useLocalSearchParams } from "expo-router";
import { useState } from "react";
import { Text, View } from "react-native";
import {
  CellCropSelector,
  type ConfirmedCrop,
} from "@/components/crop/CellCropSelector";
import { Screen } from "@/components/common/Screen";
import { analyzeConfirmedCrop } from "@/services/api/client";
import { updateLocalSession } from "@/services/storage/sessionStore";
import { spacing, typography } from "@/theme";

export default function CropScreen() {
  const params = useLocalSearchParams<{
    uri?: string;
    mimeType?: string;
    fileName?: string;
    sessionId?: string;
  }>();
  const uri = typeof params.uri === "string" ? params.uri : undefined;
  const mimeType =
    typeof params.mimeType === "string" ? params.mimeType : "image/jpeg";
  const fileName =
    typeof params.fileName === "string" ? params.fileName : "field.jpg";
  const sessionId =
    typeof params.sessionId === "string" ? params.sessionId : undefined;
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();

  const submitCrop = async (crop: ConfirmedCrop) => {
    setBusy(true);
    setError(undefined);
    try {
      const result = await analyzeConfirmedCrop({
        cellCrop: {
          uri: crop.uri,
          mimeType: crop.mimeType,
          fileName: crop.fileName,
        },
        cropBounds: crop.bounds,
      });
      if (sessionId) {
        await updateLocalSession({
          sessionId,
          imageId: sessionId,
          capturedAt: new Date().toISOString(),
          qualityStatus: result.quality_status,
          analysisStatus: result.analysis_status,
          modelVersion: result.model_version ?? undefined,
        });
      }
      router.replace({
        pathname: "/results",
        params: {
          analysisStatus: result.analysis_status,
          modelLabel: result.model_label ?? undefined,
          modelVersion: result.model_version ?? undefined,
          inferenceMode: result.inference_mode ?? undefined,
          warning: result.warning,
          requestId: result.request_id,
          qualityReasons: JSON.stringify(result.rejection_reasons),
        },
      });
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "The analysis service could not be reached. No classification was started.",
      );
    } finally {
      setBusy(false);
    }
  };

  if (!uri) {
    return (
      <Screen>
        <Text style={typography.body}>
          The image preview is unavailable. Return to capture and choose an
          image again.
        </Text>
      </Screen>
    );
  }

  return (
    <Screen>
      <View style={{ gap: spacing.lg }}>
        <CellCropSelector
          imageUri={uri}
          mimeType={mimeType}
          fileName={fileName}
          busy={busy}
          onCancel={() => router.back()}
          onConfirm={submitCrop}
        />
        {error ? (
          <Text accessibilityRole="alert" style={typography.error}>
            {error}
          </Text>
        ) : null}
        <Text style={typography.caption}>
          An accepted image with no configured model will return an inconclusive
          status. It will not be assigned a made-up label or score.
        </Text>
      </View>
    </Screen>
  );
}
