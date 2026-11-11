import { router, useLocalSearchParams } from "expo-router";
import { Image, Text, View } from "react-native";
import { ActionButton } from "@/components/common/ActionButton";
import { CellCropSelector } from "@/components/crop/CellCropSelector";
import { Screen } from "@/components/common/Screen";
import { colors, spacing, typography } from "@/theme";

export default function CropScreen() {
  const params = useLocalSearchParams<{ uri?: string }>();
  const uri = typeof params.uri === "string" ? params.uri : undefined;

  return (
    <Screen>
      <View style={{ gap: spacing.lg }}>
        <Text style={typography.body}>
          Choose one complete white blood cell and inspect the crop before any
          analysis request.
        </Text>
        {uri ? (
          <Image
            accessibilityLabel="Full microscope field to crop"
            source={{ uri }}
            resizeMode="contain"
            style={{
              width: "100%",
              height: 320,
              backgroundColor: colors.navy,
              borderRadius: 20,
            }}
          />
        ) : null}
        <CellCropSelector
          imageUri={uri}
          onCancel={() => router.back()}
          onConfirm={() => undefined}
        />
        <ActionButton
          label="Analysis is unavailable until crop selection is implemented"
          onPress={() => undefined}
          disabled
          variant="secondary"
        />
        <Text style={typography.caption}>
          A selected-cell crop is not yet produced by this scaffold. No AI
          request will be sent from this screen.
        </Text>
      </View>
    </Screen>
  );
}
