import { router } from "expo-router";
import { Text, View } from "react-native";
import { ActionButton } from "@/components/common/ActionButton";
import { InfoCard } from "@/components/common/InfoCard";
import { Screen } from "@/components/common/Screen";
import { colors, spacing, typography } from "@/theme";

export default function OnboardingScreen() {
  return (
    <Screen>
      <View style={{ gap: spacing.lg }}>
        <View style={{ gap: spacing.sm }}>
          <Text style={typography.eyebrow}>HEMOSCOPE AI</Text>
          <Text style={typography.title}>Guided microscope imaging</Text>
          <Text style={typography.body}>
            A research prototype for capturing a microscope field, checking
            image quality, and preparing a manually selected cell for screening.
          </Text>
        </View>

        <InfoCard title="Research and education only">
          <Text style={typography.body}>
            This prototype does not diagnose leukemia, rule out disease, or
            recommend treatment. A result for one selected cell does not
            represent an entire smear. Any concerning finding needs qualified
            review.
          </Text>
        </InfoCard>

        <InfoCard title="Use authorized material">
          <Text style={typography.body}>
            Use only approved, de-identified teaching or research images. Do not
            capture patient names, slide labels, or other identifying details.
          </Text>
        </InfoCard>

        <ActionButton
          label="I understand — continue"
          onPress={() => router.push("/setup")}
        />
        <Text style={[typography.caption, { color: colors.muted }]}>
          HemoScope AI is not a medical diagnostic device.
        </Text>
      </View>
    </Screen>
  );
}
