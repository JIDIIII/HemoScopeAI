import { Text, View } from "react-native";
import { colors, radii, spacing, typography } from "@/theme";

export type ConfirmedCrop = {
  uri: string;
  mimeType: string;
  fileName: string;
  bounds: { x: number; y: number; width: number; height: number };
};

type Props = {
  imageUri?: string;
  onCancel: () => void;
  onConfirm: (crop: ConfirmedCrop) => void;
};

export function CellCropSelector({ imageUri, onCancel, onConfirm }: Props) {
  void imageUri;
  void onCancel;
  void onConfirm;
  return (
    <View
      accessibilityRole="summary"
      style={{
        borderWidth: 1,
        borderStyle: "dashed",
        borderColor: colors.teal,
        borderRadius: radii.lg,
        padding: spacing.lg,
        backgroundColor: colors.white,
        gap: spacing.sm,
      }}
    >
      <Text style={typography.sectionTitle}>Manual crop selector — TODO</Text>
      <Text style={typography.body}>
        The component contract carries a confirmed crop file and normalized
        bounds. Drag, resize, border checks, and crop preview are not
        implemented yet; analysis stays disabled until they are.
      </Text>
    </View>
  );
}
