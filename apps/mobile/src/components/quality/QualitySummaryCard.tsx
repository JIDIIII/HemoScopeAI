import { Text, View } from "react-native";
import { InfoCard } from "@/components/common/InfoCard";
import { StatusPill } from "@/components/common/StatusPill";
import { spacing, typography } from "@/theme";
import type { components } from "@/types/api.generated";

type QualityResponse = components["schemas"]["QualityResponse"];

export function QualitySummaryCard({ result }: { result: QualityResponse }) {
  const accepted = result.acceptable;
  return (
    <InfoCard title={accepted ? "Quality checks passed" : "Recapture required"}>
      <StatusPill
        label={accepted ? "Accepted for cell selection" : "Image rejected"}
        tone={accepted ? "success" : "warning"}
      />
      <View style={{ gap: spacing.sm, marginTop: spacing.md }}>
        <Text style={typography.body}>
          Focus score: {result.measurements.blur_score.toFixed(1)}
        </Text>
        <Text style={typography.body}>
          Brightness: {result.measurements.mean_brightness.toFixed(1)} / 255
        </Text>
        <Text style={typography.body}>
          Image size: {result.measurements.width} × {result.measurements.height}
        </Text>
        {result.rejection_reasons.map((reason) => (
          <Text key={reason.code} style={typography.error}>
            {reason.message} {reason.instructions}
          </Text>
        ))}
      </View>
    </InfoCard>
  );
}
