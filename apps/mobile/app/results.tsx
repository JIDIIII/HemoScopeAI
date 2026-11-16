import { router, useLocalSearchParams } from "expo-router";
import { Text, View } from "react-native";
import { ActionButton } from "@/components/common/ActionButton";
import { InfoCard } from "@/components/common/InfoCard";
import { Screen } from "@/components/common/Screen";
import { StatusPill } from "@/components/common/StatusPill";
import { spacing, typography } from "@/theme";
import type { components } from "@/types/api.generated";

type QualityRejectionReason = components["schemas"]["QualityRejectionReason"];

function readQualityReasons(value?: string): QualityRejectionReason[] {
  if (!value) return [];
  try {
    const parsed: unknown = JSON.parse(value);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(
      (item): item is QualityRejectionReason =>
        typeof item === "object" &&
        item !== null &&
        "code" in item &&
        typeof item.code === "string" &&
        "message" in item &&
        typeof item.message === "string" &&
        "instructions" in item &&
        typeof item.instructions === "string",
    );
  } catch {
    return [];
  }
}

export default function ResultsScreen() {
  const params = useLocalSearchParams<{
    analysisStatus?: string;
    modelLabel?: string;
    modelVersion?: string;
    inferenceMode?: string;
    warning?: string;
    requestId?: string;
    qualityReasons?: string;
  }>();
  const hasResult = typeof params.analysisStatus === "string";
  const simulated = params.inferenceMode === "simulated";
  const unavailable = params.inferenceMode === "unavailable";
  const qualityReasons = readQualityReasons(
    typeof params.qualityReasons === "string"
      ? params.qualityReasons
      : undefined,
  );

  return (
    <Screen>
      <View style={{ gap: spacing.lg }}>
        <InfoCard title={hasResult ? "Analysis response" : "No result yet"}>
          {simulated ? (
            <StatusPill label="SIMULATED DEVELOPMENT RESPONSE" tone="warning" />
          ) : null}
          {unavailable ? (
            <StatusPill label="MODEL NOT CONFIGURED" tone="warning" />
          ) : null}
          {qualityReasons.map((reason) => (
            <View key={reason.code} style={{ marginTop: spacing.sm }}>
              <Text style={typography.body}>{reason.message}</Text>
              <Text style={typography.caption}>{reason.instructions}</Text>
            </View>
          ))}
          <Text style={[typography.body, { marginTop: spacing.md }]}>
            {hasResult
              ? "Status: " + params.analysisStatus
              : "A result appears after a manually confirmed cell crop is submitted to an available inference service."}
          </Text>
          {params.modelLabel ? (
            <Text style={[typography.body, { marginTop: spacing.sm }]}>
              Morphology label: {params.modelLabel}
            </Text>
          ) : null}
          {unavailable ? (
            <Text style={[typography.body, { marginTop: spacing.sm }]}>
              No classification was performed because no local or cloud model is
              configured.
            </Text>
          ) : null}
          {params.modelVersion ? (
            <Text style={[typography.caption, { marginTop: spacing.sm }]}>
              Model version: {params.modelVersion}
            </Text>
          ) : null}
          {params.warning ? (
            <Text style={[typography.caption, { marginTop: spacing.sm }]}>
              {params.warning}
            </Text>
          ) : null}
          {params.requestId ? (
            <Text style={[typography.caption, { marginTop: spacing.sm }]}>
              Request ID: {params.requestId}
            </Text>
          ) : null}
        </InfoCard>
        <InfoCard title="Interpretation limits">
          <Text style={typography.body}>
            This is research and educational output for one selected cell. It
            cannot diagnose leukemia, rule out disease, or guide treatment.
            Review any concerning morphology with a qualified professional.
          </Text>
        </InfoCard>
        <ActionButton
          label="Capture another field"
          onPress={() => router.replace("/capture")}
        />
        <ActionButton
          label="View local history"
          onPress={() => router.push("/history")}
          variant="secondary"
        />
      </View>
    </Screen>
  );
}
