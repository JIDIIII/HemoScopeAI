import { useCallback, useState } from "react";
import { router, useFocusEffect } from "expo-router";
import { Alert, Pressable, ScrollView, Text, View } from "react-native";
import {
  Database,
  CheckCircle2,
  CircleAlert,
  Trash2,
  Clock3,
  ChevronRight,
  Microscope,
} from "lucide-react-native";
import { Screen } from "@/components/common/Screen";
import { StatusPill } from "@/components/common/StatusPill";
import {
  listLocalSessions,
  clearLocalSessions,
  deleteLocalSession,
} from "@/services/storage/sessionStore";
import { colors, typography } from "@/theme";
import type { ResearchSession } from "@/types/session";
export default function HistoryScreen() {
  const [sessions, setSessions] = useState<ResearchSession[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");
  const [newest, setNewest] = useState(true);
  useFocusEffect(
    useCallback(() => {
      let active = true;
      setLoading(true);
      listLocalSessions()
        .then((items) => {
          if (active) {
            setSessions(items);
            setError("");
          }
        })
        .catch(() => {
          if (active)
            setError(
              "Could not load local history. Reopen this screen to retry.",
            );
        })
        .finally(() => {
          if (active) setLoading(false);
        });
      return () => {
        active = false;
      };
    }, []),
  );
  const remove = (id?: string) =>
    Alert.alert(
      id ? "Delete this session?" : "Clear all sessions?",
      "Only local research metadata will be removed.",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Delete",
          style: "destructive",
          onPress: () => {
            void (id ? deleteLocalSession(id) : clearLocalSessions())
              .then(() => listLocalSessions())
              .then(setSessions)
              .catch(() => setError("Could not delete history. Please retry."));
          },
        },
      ],
    );
  const visible = sessions
    .filter((s) => filter === "all" || s.analysisStatus === filter)
    .sort(
      (a, b) => (newest ? -1 : 1) * a.capturedAt.localeCompare(b.capturedAt),
    );
  return (
    <Screen>
      <View
        style={{
          flexDirection: "row",
          justifyContent: "flex-end",
          marginTop: -8,
        }}
      >
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Clear all research sessions"
          onPress={() => remove()}
          style={{
            padding: 9,
            borderWidth: 1,
            borderColor: colors.border,
            borderRadius: 11,
          }}
        >
          <Trash2 size={19} color={colors.navy} />
        </Pressable>
      </View>
      <View style={{ flexDirection: "row", gap: 8 }}>
        {[
          { label: "Total Sessions", count: sessions.length, icon: Database },
          {
            label: "Completed",
            count: sessions.filter((s) =>
              ["analysis_complete", "review_required"].includes(
                s.analysisStatus,
              ),
            ).length,
            icon: CheckCircle2,
          },
          {
            label: "For Review",
            count: sessions.filter(
              (s) => s.analysisStatus === "review_required",
            ).length,
            icon: CircleAlert,
          },
        ].map(({ label, count, icon: Icon }) => (
          <View
            key={label}
            style={{
              flex: 1,
              padding: 12,
              borderRadius: 15,
              borderWidth: 1,
              borderColor: colors.border,
              gap: 9,
            }}
          >
            <Text style={{ fontSize: 9, color: colors.muted }}>{label}</Text>
            <Text
              style={{ fontSize: 23, color: colors.navy, fontWeight: "600" }}
            >
              {count}
            </Text>
            <Icon size={18} color="#3B9D98" style={{ alignSelf: "flex-end" }} />
          </View>
        ))}
      </View>
      <View style={{ flexDirection: "row", gap: 6 }}>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={{ gap: 5 }}
        >
          {[
            ["all", "All"],
            ["review_required", "Review Required"],
            ["analysis_complete", "Analysis Complete"],
            ["inconclusive", "Inconclusive"],
            ["recapture_required", "Recapture"],
          ].map(([key, label]) => (
            <Pressable
              key={key}
              accessibilityRole="button"
              accessibilityState={{ selected: filter === key }}
              onPress={() => setFilter(key)}
              style={{
                padding: 9,
                borderWidth: 1,
                borderColor: colors.border,
                borderRadius: 8,
                backgroundColor: filter === key ? colors.navy : "white",
              }}
            >
              <Text
                style={{
                  fontSize: 9,
                  color: filter === key ? "white" : colors.muted,
                }}
              >
                {label}
              </Text>
            </Pressable>
          ))}
        </ScrollView>
        <Pressable
          accessibilityRole="button"
          onPress={() => setNewest(!newest)}
          style={{
            flexDirection: "row",
            alignItems: "center",
            gap: 4,
            padding: 7,
            borderWidth: 1,
            borderColor: colors.border,
            borderRadius: 8,
          }}
        >
          <Clock3 size={14} color={colors.navy} />
          <Text style={{ fontSize: 9, color: colors.navy }}>
            {newest ? "Newest" : "Oldest"}
          </Text>
        </Pressable>
      </View>
      <View style={{ flexDirection: "row", justifyContent: "space-between" }}>
        <Text style={typography.sectionTitle}>Saved Sessions</Text>
        <Text style={typography.caption}>{visible.length} results</Text>
      </View>
      {loading ? (
        <Text style={typography.caption}>Loading local history…</Text>
      ) : null}
      {error ? (
        <Text accessibilityRole="alert" style={typography.error}>
          {error}
        </Text>
      ) : null}
      {!loading && !error && !visible.length ? (
        <Text style={typography.body}>
          No sessions to show. Start a new capture to create a research session.
        </Text>
      ) : null}
      {visible.map((session) => (
        <View
          key={session.sessionId}
          style={{
            flexDirection: "row",
            borderWidth: 1,
            borderColor: colors.border,
            borderRadius: 17,
            overflow: "hidden",
          }}
        >
          <Pressable
            accessibilityRole="button"
            disabled={session.analysisStatus === "not_started"}
            onPress={() =>
              router.push({
                pathname: "/results",
                params: {
                  analysisStatus: session.analysisStatus,
                  modelVersion: session.modelVersion ?? "",
                  modelLabel: session.modelLabel ?? "",
                  inferenceMode: session.inferenceMode ?? "",
                  warning: session.warning ?? "",
                  rawModelScore:
                    session.rawModelScore == null
                      ? ""
                      : String(session.rawModelScore),
                },
              })
            }
            style={{
              flex: 1,
              flexDirection: "row",
              padding: 12,
              gap: 10,
              alignItems: "center",
            }}
          >
            <View
              style={{
                width: 48,
                height: 64,
                backgroundColor: colors.pale,
                borderRadius: 12,
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <Microscope color={colors.teal} size={27} />
            </View>
            <View style={{ flex: 1, gap: 4 }}>
              <Text
                numberOfLines={1}
                style={{ fontSize: 11, color: colors.navy, fontWeight: "600" }}
              >
                {session.imageId}
              </Text>
              <Text style={{ fontSize: 9, color: colors.muted }}>
                {new Date(session.capturedAt).toLocaleString()}
              </Text>
              {session.inferenceMode === "simulated" ? (
                <Text
                  style={{ fontSize: 9, color: colors.teal, fontWeight: "700" }}
                >
                  DEMO · SIMULATED
                </Text>
              ) : null}
              <StatusPill
                label={"Quality: " + session.qualityStatus}
                  tone={session.qualityStatus === "accepted" ? "success" : "warning"}
              />
              <Text style={{ fontSize: 10, color: colors.teal }}>
                {session.analysisStatus.replaceAll("_", " ")}
              </Text>
              {session.modelVersion ? (
                <Text style={{ fontSize: 8, color: colors.muted }}>
                  {session.modelVersion}
                </Text>
              ) : null}
            </View>
            <ChevronRight size={16} color={colors.navy} />
          </Pressable>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={"Delete session " + session.imageId}
            onPress={() => remove(session.sessionId)}
            style={{
              borderLeftWidth: 1,
              borderColor: colors.border,
              padding: 10,
              justifyContent: "center",
              backgroundColor: "#FAFCFD",
            }}
          >
            <Trash2 size={15} color={colors.muted} />
          </Pressable>
        </View>
      ))}
      <Text style={typography.caption}>
        Only metadata is saved. Research images and patient identifiers are not
        stored in history.
      </Text>
    </Screen>
  );
}
