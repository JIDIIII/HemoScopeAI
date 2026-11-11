import { router, useLocalSearchParams } from "expo-router";
import { Text, View } from "react-native";
import { ActionButton } from "@/components/common/ActionButton";
import { InfoCard } from "@/components/common/InfoCard";
import { Screen } from "@/components/common/Screen";
import { StatusPill } from "@/components/common/StatusPill";
import { spacing, typography } from "@/theme";

export default function ResultsScreen() {
  const params = useLocalSearchParams<{
    analysisStatus?: string;
    modelLabel?: string;
    modelVersion?: string;
    inferenceMode?: string;
    warning?: string;
  }>();
  const hasResult = typeof params.analysisStatus === "string";
  const simulated = params.inferenceMode === "simulated";

  return (
    <Screen>
      <View style={{ gap: spacing.lg }}>
        <InfoCard
          title={hasResult ? "Selected-cell screening result" : "No result yet"}
        >
          {simulated ? (
            <StatusPill label="SIMULATED DEVELOPMENT RESPONSE" tone="warning" />
          ) : null}
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
