import { router, useLocalSearchParams } from "expo-router";
import { useRef, useState } from "react";
import { Image, Text, View } from "react-native";
import { ActionButton } from "@/components/common/ActionButton";
import {
  CellCropSelector,
  type ConfirmedCrop,
} from "@/components/crop/CellCropSelector";
import { DemoControls } from "@/components/common/DemoControls";
import { Screen } from "@/components/common/Screen";
import { analyzeConfirmedCrop } from "@/services/api/client";
import {
  createLocalSessionId,
  updateLocalSession,
} from "@/services/storage/sessionStore";
import { imageUriParam, readImageUri } from "@/services/navigation/imageUri";
import { spacing, typography } from "@/theme";
export default function CropScreen() {
  const params = useLocalSearchParams<{ uri?: string; sessionId?: string }>();
  const uri = readImageUri(params.uri);
  const [sessionId] = useState(() =>
    typeof params.sessionId === "string"
      ? params.sessionId
      : createLocalSessionId(),
  );
  const [crop, setCrop] = useState<ConfirmedCrop>();
  const [busy, setBusy] = useState(false);
  const locked = useRef(false);
  const [error, setError] = useState<string>();
  const submit = async () => {
    if (!crop || locked.current) return;
    locked.current = true;
    setBusy(true);
    setError(undefined);
    try {
      // /analyze applies crop-specific quality limits before inference.
      // /quality is reserved for the original full-field image.
      const result = await analyzeConfirmedCrop({
        cellCrop: crop,
        researchSessionId: sessionId,
      });
      let storageWarning = "";
      try {
        await updateLocalSession({
          sessionId,
          imageId: sessionId,
          capturedAt: new Date().toISOString(),
          qualityStatus: result.quality_status,
          analysisStatus: result.analysis_status,
          modelVersion: result.model_version ?? undefined,
          inferenceMode: result.inference_mode ?? undefined,
          allScore: result.all_score ?? undefined,
          decisionPolicyVersion: result.decision_policy_version ?? undefined,
          warning: result.warning,
        });
      } catch {
        storageWarning =
          "The result was received, but local history could not be saved.";
      }
      router.push({
        pathname: "/results",
        params: {
          cropUri: imageUriParam(crop.uri),
          sessionId,
          qualityStatus: result.quality_status,
          saved: storageWarning ? "false" : "true",
          analysisStatus: result.analysis_status,
          modelVersion: result.model_version ?? "",
          inferenceMode: result.inference_mode ?? "",
          warning: result.warning,
          allScore: result.all_score == null ? "" : String(result.all_score),
          decisionPolicyVersion: result.decision_policy_version ?? "",
          requestId: result.request_id,
          qualityReasons: JSON.stringify(result.rejection_reasons ?? []),
          storageWarning,
        },
      });
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Analysis failed. No result is available. Retry with this crop.",
      );
    } finally {
      locked.current = false;
      setBusy(false);
    }
  };
  return (
    <Screen>
      <View style={{ gap: spacing.lg }}>
        {!busy ? (
          <DemoControls
            onChange={() => {
              setError(undefined);
            }}
          />
        ) : null}
        {!uri ? (
          <>
            <Text style={typography.error}>No field selected.</Text>
            <ActionButton
              label="Return to capture"
              onPress={() => router.replace("/capture")}
            />
          </>
        ) : !crop ? (
          <CellCropSelector
            imageUri={uri}
            onCancel={() => router.back()}
            onConfirm={(value) => {
              setCrop(value);
              setError(undefined);
            }}
          />
        ) : (
          <>
            <Image
              source={{ uri: crop.uri }}
              style={{ width: "100%", height: 280 }}
              resizeMode="contain"
              accessibilityLabel="Confirmed cell crop to upload"
            />
            <Text style={typography.body}>
              Only this confirmed crop will be sent for analysis. Its quality is
              checked before inference.
            </Text>
            {error ? (
              <Text accessibilityRole="alert" style={typography.error}>
                {error} No negative finding can be inferred.
              </Text>
            ) : null}
            <ActionButton
              label={
                error ? "Retry crop analysis" : "Check crop quality and analyze"
              }
              onPress={submit}
              loading={busy}
              disabled={busy}
            />
            <ActionButton
              label="Replace crop from original field"
              onPress={() => {
                setCrop(undefined);
                setError(undefined);
              }}
              disabled={busy}
              variant="secondary"
            />
            <ActionButton
              label="Retake field"
              onPress={() => router.replace("/capture")}
              disabled={busy}
              variant="secondary"
            />
          </>
        )}
        <Text style={typography.caption}>
          Research use only. One selected cell cannot diagnose or rule out
          disease. Concerning morphology needs qualified review.
        </Text>
      </View>
    </Screen>
  );
}
