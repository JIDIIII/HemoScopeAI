import { Text, View } from "react-native";
import {
  CheckCircle2,
  CircleAlert,
  Focus,
  Lightbulb,
  Maximize2,
  FileImage,
} from "lucide-react-native";
import { colors, typography } from "@/theme";
import type { components } from "@/types/api.generated";
export function QualitySummaryCard({
  result,
}: {
  result: components["schemas"]["QualityResponse"];
}) {
  const accepted = result.acceptable;
  const checks = [
    {
      name: "Focus & sharpness",
      detail: "Edge detail and clarity",
      icon: Focus,
      match: /blur|focus/i,
    },
    {
      name: "Exposure",
      detail: "Illumination balance",
      icon: Lightbulb,
      match: /expos|bright|dark/i,
    },
    {
      name: "Image dimensions",
      detail: `${result.measurements.width} × ${result.measurements.height} px`,
      icon: Maximize2,
      match: /dimension|small|size|resolution/i,
    },
    {
      name: "File validity",
      detail: "Supported image format",
      icon: FileImage,
      match: /file|format|invalid|decode/i,
    },
  ];
  return (
    <View style={{ gap: 9 }}>
      <View
        style={{
          backgroundColor: accepted ? colors.mint : "#FFF4E9",
          borderColor: accepted ? "#B9E5E0" : "#EED7BE",
          borderWidth: 1,
          padding: 14,
          borderRadius: 15,
          flexDirection: "row",
          gap: 12,
          marginBottom: 3,
        }}
      >
        <View
          style={{
            backgroundColor: "white",
            width: 38,
            height: 38,
            borderRadius: 12,
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          {accepted ? (
            <CheckCircle2 size={21} color={colors.teal} />
          ) : (
            <CircleAlert size={21} color="#A66B28" />
          )}
        </View>
        <View style={{ flex: 1 }}>
          <Text style={typography.body}>
            {accepted ? "Image Quality Accepted" : "Recapture Required"}
          </Text>
          <Text style={[typography.caption, { fontSize: 10, marginTop: 3 }]}>
            {accepted
              ? "This image passed the current engineering quality checks."
              : "This image needs attention before analysis. Follow the guidance below."}
          </Text>
        </View>
      </View>
      {checks.map(({ name, detail, icon: Icon, match }) => {
        const failed = result.rejection_reasons.some((r) => match.test(r.code));
        return (
          <View
            key={name}
            style={{
              borderWidth: 1,
              borderColor: colors.border,
              padding: 10,
              borderRadius: 13,
              flexDirection: "row",
              gap: 10,
              alignItems: "center",
            }}
          >
            <View
              style={{
                width: 33,
                height: 33,
                alignItems: "center",
                justifyContent: "center",
                backgroundColor: colors.lightGray,
                borderRadius: 9,
              }}
            >
              <Icon size={18} color="#577C96" />
            </View>
            <View style={{ flex: 1 }}>
              <Text
                style={{ fontSize: 11, fontWeight: "600", color: colors.navy }}
              >
                {name}
              </Text>
              <Text style={{ fontSize: 9, color: colors.muted, marginTop: 4 }}>
                {detail}
              </Text>
            </View>
            <View
              style={{
                borderRadius: 14,
                backgroundColor: accepted
                  ? colors.mint
                  : failed
                    ? "#FFF0E0"
                    : colors.lightGray,
                paddingHorizontal: 8,
                paddingVertical: 4,
              }}
            >
              <Text
                style={{
                  fontSize: 9,
                  fontWeight: "600",
                  color: accepted ? colors.teal : colors.muted,
                }}
              >
                {accepted ? "Passed" : failed ? "Retake" : "See review"}
              </Text>
            </View>
          </View>
        );
      })}
      {result.rejection_reasons.map((r) => (
        <Text key={r.code} style={typography.error}>
          {r.message} {r.instructions}
        </Text>
      ))}
      {result.actionable_instructions
        .filter(
          (item) =>
            !result.rejection_reasons.some((r) => r.instructions === item),
        )
        .map((item, i) => (
          <Text key={i} style={typography.caption}>
            {item}
          </Text>
        ))}
    </View>
  );
}
