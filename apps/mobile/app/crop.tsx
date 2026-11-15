import { router, useLocalSearchParams } from "expo-router";
import { useRef, useState } from "react";
import { Image, Text, View } from "react-native";
import { ActionButton } from "@/components/common/ActionButton";
import {
  CellCropSelector,
  type ConfirmedCrop,
} from "@/components/crop/CellCropSelector";
import { QualitySummaryCard } from "@/components/quality/QualitySummaryCard";
import { Screen } from "@/components/common/Screen";
import { analyzeConfirmedCrop, checkImageQuality } from "@/services/api/client";
import {
  createLocalSessionId,
  updateLocalSession,
} from "@/services/storage/sessionStore";
import { spacing, typography } from "@/theme";
import type { components } from "@/types/api.generated";
import { USE_MOCK_API } from "@/constants/api";
export default function CropScreen() {
  const params = useLocalSearchParams<{ uri?: string; sessionId?: string }>();
  const uri = typeof params.uri === "string" ? params.uri : undefined;
  const [sessionId] = useState(() =>
    typeof params.sessionId === "string"
      ? params.sessionId
      : createLocalSessionId(),
  );
  const [crop, setCrop] = useState<ConfirmedCrop>();
  const [quality, setQuality] =
    useState<components["schemas"]["QualityResponse"]>();
  const [busy, setBusy] = useState(false);
  const locked = useRef(false);
  const [error, setError] = useState<string>();
  const submit = async () => {
    if (!crop || locked.current) return;
    locked.current = true;
    setBusy(true);
    setError(undefined);
    setQuality(undefined);
    try {
      const checked = await checkImageQuality(crop);
      setQuality(checked);
      if (!checked.acceptable) {
        await updateLocalSession({
          sessionId,
          imageId: sessionId,
          capturedAt: new Date().toISOString(),
          qualityStatus: "rejected",
          analysisStatus: "recapture_required",
          inferenceMode: USE_MOCK_API ? "simulated" : undefined,
        }).catch(() =>
          setError(
            "The crop was rejected, and history could not be saved. Replace the crop or retake the field.",
          ),
        );
        return;
      }
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
          modelLabel: result.model_label ?? undefined,
          warning: result.warning,
          rawModelScore: result.raw_model_score ?? undefined,
        });
      } catch {
        storageWarning =
          "The result was received, but local history could not be saved.";
      }
      router.push({
        pathname: "/results",
        params: {
          cropUri: crop.uri,
          sessionId,
          qualityStatus: result.quality_status,
          saved: storageWarning ? "false" : "true",
          analysisStatus: result.analysis_status,
          modelLabel: result.model_label ?? "",
          modelVersion: result.model_version ?? "",
          inferenceMode: result.inference_mode ?? "",
          warning: result.warning,
          rawModelScore:
            result.raw_model_score == null
              ? ""
              : String(result.raw_model_score),
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
              setQuality(undefined);
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
            {quality ? <QualitySummaryCard result={quality} /> : null}
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
                setQuality(undefined);
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
