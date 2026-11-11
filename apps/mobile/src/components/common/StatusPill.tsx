import { StyleSheet, Text, View } from "react-native";
import { colors, radii, spacing, typography } from "@/theme";

type Props = { label: string; tone?: "success" | "warning" | "neutral" };

export function StatusPill({ label, tone = "neutral" }: Props) {
  const palette = {
    success: { background: "#DDF5F1", foreground: "#075D59" },
    warning: { background: "#FFF1D6", foreground: "#714500" },
    neutral: { background: colors.lightGray, foreground: colors.navy },
  }[tone];
  return (
    <View style={[styles.container, { backgroundColor: palette.background }]}>
      <Text
        style={[
          typography.caption,
          { color: palette.foreground, fontWeight: "700" },
        ]}
      >
        {label}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignSelf: "flex-start",
    borderRadius: radii.pill,
    paddingVertical: spacing.xs,
    paddingHorizontal: spacing.md,
  },
});
