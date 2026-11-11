import type { ReactNode } from "react";
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  type ViewStyle,
} from "react-native";
import { colors, radii, spacing, typography } from "@/theme";

type Props = {
  label: string;
  onPress: () => void;
  disabled?: boolean;
  loading?: boolean;
  variant?: "primary" | "secondary";
  style?: ViewStyle;
  icon?: ReactNode;
};

export function ActionButton({
  label,
  onPress,
  disabled = false,
  loading = false,
  variant = "primary",
  style,
  icon,
}: Props) {
  const secondary = variant === "secondary";
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ disabled: disabled || loading, busy: loading }}
      disabled={disabled || loading}
      onPress={onPress}
      style={({ pressed }) => [
        styles.button,
        secondary ? styles.secondary : styles.primary,
        (disabled || loading) && styles.disabled,
        pressed && !disabled && !loading && styles.pressed,
        style,
      ]}
    >
      {loading ? (
        <ActivityIndicator color={secondary ? colors.navy : colors.white} />
      ) : (
        <>
          {icon}
          <Text style={[typography.button, secondary && styles.secondaryText]}>
            {label}
          </Text>
        </>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    minHeight: 52,
    paddingHorizontal: spacing.lg,
    borderRadius: radii.md,
    alignItems: "center",
    justifyContent: "center",
    flexDirection: "row",
    gap: spacing.sm,
  },
  primary: { backgroundColor: colors.teal },
  secondary: {
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: colors.border,
  },
  secondaryText: { color: colors.navy },
  disabled: { opacity: 0.52 },
  pressed: { opacity: 0.82 },
});
