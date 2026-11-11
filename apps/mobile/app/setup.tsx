import { Link, router } from "expo-router";
import { Text, View } from "react-native";
import { ActionButton } from "@/components/common/ActionButton";
import { InfoCard } from "@/components/common/InfoCard";
import { Screen } from "@/components/common/Screen";
import { colors, spacing, typography } from "@/theme";

const setupSteps = [
  "Secure the adjustable phone adapter around the microscope eyepiece.",
  "Center the circular field and reduce vignetting without heavy digital zoom.",
  "Use an authorized, de-identified slide selected by the laboratory partner.",
  "Stabilize the phone, focus through the microscope, and check illumination.",
];

export default function SetupScreen() {
  return (
    <Screen>
      <View style={{ gap: spacing.lg }}>
        <View style={{ gap: spacing.sm }}>
          <Text style={typography.eyebrow}>BEFORE YOU CAPTURE</Text>
          <Text style={typography.title}>Set up the microscope</Text>
          <Text style={typography.body}>
            Keep the same phone, microscope, objective, adapter, and capture
            settings during a comparison session.
          </Text>
        </View>
        <InfoCard title="Quick setup checklist">
          <View style={{ gap: spacing.md }}>
            {setupSteps.map((step, index) => (
              <View
                key={step}
                style={{ flexDirection: "row", gap: spacing.sm }}
              >
                <Text style={[typography.body, { color: colors.teal }]}>
                  {String(index + 1).padStart(2, "0")}
                </Text>
                <Text style={[typography.body, { flex: 1 }]}>{step}</Text>
              </View>
            ))}
          </View>
        </InfoCard>
        <ActionButton
          label="Open camera or choose an image"
          onPress={() => router.push("/capture")}
        />
        <View style={{ flexDirection: "row", gap: spacing.lg }}>
          <Link
            href="/history"
            style={{ color: colors.teal, fontWeight: "700" }}
          >
            Local history
          </Link>
          <Link
            href="/settings"
            style={{ color: colors.teal, fontWeight: "700" }}
          >
            Settings
          </Link>
        </View>
        <Text style={typography.caption}>
          Hardware checklist is available offline. One field does not represent
          the full slide.
        </Text>
      </View>
    </Screen>
  );
}
