import { useCallback, useState } from "react";
import { useFocusEffect } from "expo-router";
import { Text, View } from "react-native";
import { InfoCard } from "@/components/common/InfoCard";
import { Screen } from "@/components/common/Screen";
import { StatusPill } from "@/components/common/StatusPill";
import { listLocalSessions } from "@/services/storage/sessionStore";
import { spacing, typography } from "@/theme";
import type { ResearchSession } from "@/types/session";

export default function HistoryScreen() {
  const [sessions, setSessions] = useState<ResearchSession[]>([]);
  const [loading, setLoading] = useState(true);

  useFocusEffect(
    useCallback(() => {
      let active = true;
      setLoading(true);
      listLocalSessions()
        .then((items) => {
          if (active) setSessions(items);
        })
        .catch(() => {
          if (active) setSessions([]);
        })
        .finally(() => {
          if (active) setLoading(false);
        });
      return () => {
        active = false;
      };
    }, []),
  );

  return (
    <Screen>
      <View style={{ gap: spacing.lg }}>
        <Text style={typography.body}>
          Session metadata stays on this device. Images, names, and patient
          identifiers are not included in these records.
        </Text>
        {loading ? (
          <Text style={typography.body}>Loading local history…</Text>
        ) : null}
        {!loading && sessions.length === 0 ? (
          <InfoCard title="No saved sessions">
            <Text style={typography.body}>
              A local record is created after an image quality check.
            </Text>
          </InfoCard>
        ) : null}
        {sessions.map((session) => (
          <InfoCard key={session.sessionId} title={session.imageId}>
            <Text style={typography.caption}>
              {new Date(session.capturedAt).toLocaleString()}
            </Text>
            <View
              style={{
                flexDirection: "row",
                gap: spacing.sm,
                marginTop: spacing.md,
              }}
            >
              <StatusPill
                label={"Quality: " + session.qualityStatus}
                tone="neutral"
              />
              <StatusPill
                label={"Analysis: " + session.analysisStatus}
                tone="neutral"
              />
            </View>
            {session.modelVersion ? (
              <Text style={[typography.caption, { marginTop: spacing.sm }]}>
                Model: {session.modelVersion}
              </Text>
            ) : null}
          </InfoCard>
        ))}
      </View>
    </Screen>
  );
}
