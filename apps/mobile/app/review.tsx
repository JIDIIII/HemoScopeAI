import { router, useLocalSearchParams } from "expo-router";
import { useState } from "react";
import { Image, Text, View } from "react-native";
import { ActionButton } from "@/components/common/ActionButton";
import { InfoCard } from "@/components/common/InfoCard";
import { Screen } from "@/components/common/Screen";
import { QualitySummaryCard } from "@/components/quality/QualitySummaryCard";
import { checkImageQuality } from "@/services/api/client";
import {
  createLocalSessionId,
  updateLocalSession,
} from "@/services/storage/sessionStore";
import { colors, spacing, typography } from "@/theme";
import type { components } from "@/types/api.generated";

type QualityResponse = components["schemas"]["QualityResponse"];

export default function ReviewScreen() {
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
    typeof params.sessionId === "string"
      ? params.sessionId
      : createLocalSessionId();
  const [quality, setQuality] = useState<QualityResponse | undefined>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | undefined>();

  const runQualityCheck = async () => {
    if (!uri) {
      setError(
        "The image preview is unavailable. Capture or import the image again.",
      );
      return;
    }
    setBusy(true);
    setError(undefined);
    try {
      const result = await checkImageQuality({ uri, mimeType, fileName });
      setQuality(result);
      await updateLocalSession({
        sessionId,
        imageId: sessionId,
        capturedAt: new Date().toISOString(),
        qualityStatus: result.quality_status,
        analysisStatus: "not_started",
      });
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "The quality service could not be reached. No classification was started.",
      );
    } finally {
      setBusy(false);
    }
  };

  if (!uri) {
    return (
      <Screen>
        <InfoCard title="No image selected">
          <Text style={typography.body}>
            Return to capture and choose a valid microscope image.
          </Text>
          <ActionButton
            label="Return to capture"
            onPress={() => router.replace("/capture")}
            style={{ marginTop: spacing.md }}
          />
        </InfoCard>
      </Screen>
    );
  }

  const accepted = quality?.acceptable === true;
  return (
    <Screen>
      <View style={{ gap: spacing.lg }}>
        <Text style={typography.body}>
          Check the full field before manually selecting one cell.
        </Text>
        <Image
          accessibilityLabel="Selected microscope field preview"
          source={{ uri }}
          resizeMode="contain"
          style={{
            width: "100%",
            height: 300,
            backgroundColor: colors.navy,
            borderRadius: 20,
          }}
        />
        {quality ? <QualitySummaryCard result={quality} /> : null}
        {error ? (
          <Text accessibilityRole="alert" style={typography.error}>
            {error}
          </Text>
        ) : null}
        <ActionButton
          label={quality ? "Check quality again" : "Check image quality"}
          onPress={runQualityCheck}
          loading={busy}
          disabled={busy}
        />
        {accepted ? (
          <ActionButton
            label="Continue to manual cell selection"
            onPress={() =>
              router.push({
                pathname: "/crop",
                params: { uri, mimeType, fileName, sessionId },
              })
            }
          />
        ) : null}
        {!accepted ? (
          <ActionButton
            label="Retake or choose another image"
            variant="secondary"
            onPress={() => router.replace("/capture")}
          />
        ) : null}
        <Text style={typography.caption}>
          Development quality limits need calibration on representative
          microscope images. Passing these checks does not confirm biological
          suitability.
        </Text>
      </View>
    </Screen>
  );
}
