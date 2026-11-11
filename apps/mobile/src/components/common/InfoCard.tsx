import type { PropsWithChildren } from "react";
import { StyleSheet, Text, View } from "react-native";
import { colors, radii, spacing, typography } from "@/theme";

type Props = PropsWithChildren<{ title: string }>;

export function InfoCard({ title, children }: Props) {
  return (
    <View style={styles.card}>
      <Text style={typography.sectionTitle}>{title}</Text>
      <View style={{ marginTop: spacing.md }}>{children}</View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.white,
    borderRadius: radii.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.lg,
  },
});
