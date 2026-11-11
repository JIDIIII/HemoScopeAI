import { useState } from "react";
import { Alert, Text, View } from "react-native";
import { ActionButton } from "@/components/common/ActionButton";
import { InfoCard } from "@/components/common/InfoCard";
import { Screen } from "@/components/common/Screen";
import { getHealth } from "@/services/api/client";
import { clearLocalSessions } from "@/services/storage/sessionStore";
import { API_BASE_URL } from "@/constants/api";
import { spacing, typography } from "@/theme";
import type { components } from "@/types/api.generated";

type HealthResponse = components["schemas"]["HealthResponse"];

export default function SettingsScreen() {
  const [health, setHealth] = useState<HealthResponse | undefined>();
  const [message, setMessage] = useState<string | undefined>();
  const [busy, setBusy] = useState(false);

  const checkBackend = async () => {
    setBusy(true);
    setMessage(undefined);
    try {
      setHealth(await getHealth());
    } catch (cause) {
      setHealth(undefined);
      setMessage(
        cause instanceof Error ? cause.message : "Backend connection failed.",
      );
    } finally {
      setBusy(false);
    }
  };

  const clearHistory = () => {
    Alert.alert(
      "Clear local history?",
      "This removes saved session metadata from this device.",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Clear",
          style: "destructive",
          onPress: () => {
            void clearLocalSessions().then(() =>
              setMessage("Local history cleared."),
            );
          },
        },
      ],
    );
  };

  return (
    <Screen>
      <View style={{ gap: spacing.lg }}>
        <InfoCard title="API connection">
          <Text style={typography.body}>Base URL: {API_BASE_URL}</Text>
          <Text style={[typography.caption, { marginTop: spacing.sm }]}>
            Set EXPO_PUBLIC_API_BASE_URL in apps/mobile/.env before starting
            Expo. Android phones need the computer&apos;s LAN address, not
            localhost.
          </Text>
          <ActionButton
            label="Check backend health"
            onPress={checkBackend}
            loading={busy}
            disabled={busy}
            style={{ marginTop: spacing.md }}
          />
          {health ? (
            <Text style={[typography.caption, { marginTop: spacing.md }]}>
              Service: {health.service_status}; model available:{" "}
              {health.model_available ? "yes" : "no"}; mode:{" "}
              {health.inference_mode}
            </Text>
          ) : null}
          {message ? (
            <Text
              accessibilityRole="alert"
              style={[typography.caption, { marginTop: spacing.md }]}
            >
              {message}
            </Text>
          ) : null}
        </InfoCard>
        <InfoCard title="Local data">
          <Text style={typography.body}>
            History stores a local random image ID, timestamp, quality state,
            analysis state, and model version. It does not store patient names.
          </Text>
          <ActionButton
            label="Clear local history"
            onPress={clearHistory}
            variant="secondary"
            style={{ marginTop: spacing.md }}
          />
        </InfoCard>
        <InfoCard title="Research use only">
          <Text style={typography.body}>
            HemoScope AI is not a medical diagnostic device. A failed or
            inconclusive analysis must never be interpreted as a negative
            result.
          </Text>
        </InfoCard>
      </View>
    </Screen>
  );
}
