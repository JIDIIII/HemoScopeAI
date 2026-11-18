import { router, useLocalSearchParams } from "expo-router";
import { ScanLine } from "lucide-react-native";
import { useState } from "react";
import { Image, Text, View } from "react-native";
import { ActionButton } from "@/components/common/ActionButton";
import { InfoCard } from "@/components/common/InfoCard";
import { DemoControls } from "@/components/common/DemoControls";
import { Screen } from "@/components/common/Screen";
import { QualitySummaryCard } from "@/components/quality/QualitySummaryCard";
import { checkImageQuality } from "@/services/api/client";
import {
  createLocalSessionId,
  updateLocalSession,
} from "@/services/storage/sessionStore";
import { colors, spacing, typography } from "@/theme";
import type { components } from "@/types/api.generated";
import { imageUriParam, readImageUri } from "@/services/navigation/imageUri";
import { USE_MOCK_API } from "@/constants/api";

type QualityResponse = components["schemas"]["QualityResponse"];

export default function ReviewScreen() {
  const params = useLocalSearchParams<{
    uri?: string;
    mimeType?: string;
    fileName?: string;
    sessionId?: string;
  }>();
  const uri = readImageUri(params.uri);
  const mimeType =
    typeof params.mimeType === "string" ? params.mimeType : "image/jpeg";
  const fileName =
    typeof params.fileName === "string" ? params.fileName : "field.jpg";
  const [sessionId] = useState(() =>
    typeof params.sessionId === "string"
      ? params.sessionId
      : createLocalSessionId(),
  );
  const [quality, setQuality] = useState<QualityResponse | undefined>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | undefined>();
  const [preview, setPreview] = useState<{
    uri: string;
    status: "loaded" | "failed";
  }>();
  const previewReady = preview?.uri === uri && preview?.status === "loaded";
  const previewFailed = preview?.uri === uri && preview?.status === "failed";

  const runQualityCheck = async () => {
    if (!uri || !previewReady) {
      setError(
        "The image preview is unavailable. Capture or import the image again.",
      );
      return;
    }
    setBusy(true);
    setQuality(undefined);
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
        inferenceMode: USE_MOCK_API ? "simulated" : undefined,
      }).catch(() =>
        setError(
          "Quality review completed, but local history could not be saved.",
        ),
      );
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

  const accepted = !busy && quality?.acceptable === true;
  return (
    <Screen>
      <View style={{ gap: spacing.lg }}>
        {!busy ? (
          <DemoControls
            onChange={() => {
              setQuality(undefined);
              setError(undefined);
            }}
          />
        ) : null}
        <Image
          key={uri}
          accessibilityLabel="Selected microscope field preview"
          source={{ uri }}
          onLoad={() => setPreview({ uri, status: "loaded" })}
          onError={() => {
            setPreview({ uri, status: "failed" });
            setQuality(undefined);
            setError(undefined);
          }}
          resizeMode="contain"
          style={{
            width: "100%",
            height: 220,
            backgroundColor: colors.pale,
            borderRadius: 20,
          }}
        />
        {!previewReady ? (
          <Text
            accessibilityRole={previewFailed ? "alert" : undefined}
            style={previewFailed ? typography.error : typography.caption}
          >
            {previewFailed
              ? "This image could not be opened. Choose it again from the gallery. No image was uploaded."
              : "Loading image preview…"}
          </Text>
        ) : null}
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
          disabled={busy || !previewReady}
        />
        {accepted ? (
          <ActionButton
            label="Continue to Cell Selection"
            icon={<ScanLine size={19} color="white" />}
            onPress={() =>
              router.push({
                pathname: "/crop",
                params: {
                  uri: imageUriParam(uri),
                  mimeType,
                  fileName,
                  sessionId,
                },
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
