import { router, useLocalSearchParams } from "expo-router";
import { useState } from "react";
import { Image, Pressable, Text, View } from "react-native";
import {
  Activity,
  ChevronDown,
  CircleAlert,
  ShieldCheck,
  Database,
  Camera,
  History,
  ScanLine,
  Check,
} from "lucide-react-native";
import { ActionButton } from "@/components/common/ActionButton";
import { Screen } from "@/components/common/Screen";
import { resultCopy } from "@/features/analysis/result";
import { updateLocalSession } from "@/services/storage/sessionStore";
import { colors, typography } from "@/theme";
export default function ResultsScreen() {
  const params = useLocalSearchParams<{
    analysisStatus?: string;
    modelLabel?: string;
    modelVersion?: string;
    inferenceMode?: string;
    warning?: string;
    rawModelScore?: string;
    storageWarning?: string;
    cropUri?: string;
    sessionId?: string;
    qualityStatus?: string;
    saved?: string;
  }>();
  const status =
    typeof params.analysisStatus === "string" &&
    Object.hasOwn(resultCopy, params.analysisStatus)
      ? (params.analysisStatus as keyof typeof resultCopy)
      : undefined;
  const copy = status ? resultCopy[status] : undefined;
  const showModel =
    status === "review_required" || status === "analysis_complete";
  const [details, setDetails] = useState(false);
  const [saved, setSaved] = useState(params.saved === "true");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(params.storageWarning ?? "");
  const save = async () => {
    if (!params.sessionId || !status || busy) return;
    setBusy(true);
    try {
      await updateLocalSession({
        sessionId: params.sessionId,
        imageId: params.sessionId,
        capturedAt: new Date().toISOString(),
        analysisStatus: status,
        qualityStatus: params.qualityStatus ?? "accepted",
        inferenceMode:
          params.inferenceMode === "simulated"
            ? "simulated"
            : params.inferenceMode === "real"
              ? "real"
              : undefined,
        modelVersion: params.modelVersion,
        modelLabel: params.modelLabel,
        warning: params.warning,
        rawModelScore:
          params.rawModelScore && Number.isFinite(Number(params.rawModelScore))
            ? Number(params.rawModelScore)
            : undefined,
      });
      setSaved(true);
      setError("");
    } catch {
      setError(
        "Could not save this session. Your result remains available; please retry.",
      );
    } finally {
      setBusy(false);
    }
  };
  return (
    <Screen>
      <View
        style={{
          flexDirection: "row",
          gap: 12,
          alignItems: "center",
          padding: 10,
          borderWidth: 1,
          borderColor: colors.border,
          borderRadius: 15,
        }}
      >
        {params.cropUri ? (
          <Image
            source={{ uri: params.cropUri }}
            style={{ width: 64, height: 64, borderRadius: 11 }}
            resizeMode="contain"
            accessibilityLabel="Confirmed selected cell"
          />
        ) : (
          <View
            style={{
              width: 54,
              height: 60,
              borderRadius: 11,
              backgroundColor: colors.pale,
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <ScanLine color={colors.teal} size={26} />
          </View>
        )}
        <View style={{ gap: 4, flex: 1 }}>
          <Text style={typography.eyebrow}>SELECTED CELL</Text>
          <Text style={{ fontSize: 11, color: colors.navy, fontWeight: "600" }}>
            {params.cropUri
              ? "Manual crop confirmed"
              : "Saved research metadata"}
          </Text>
          <Text style={{ fontSize: 10, color: colors.muted }}>
            {params.qualityStatus
              ? "Image quality: " + params.qualityStatus
              : "Cell-level analysis"}
          </Text>
        </View>
      </View>
      <View
        style={{
          backgroundColor: colors.pale,
          borderWidth: 1,
          borderColor: "#C4E6E3",
          borderRadius: 20,
          padding: 20,
          gap: 15,
          overflow: "hidden",
        }}
      >
        {params.inferenceMode === "simulated" ? (
          <View
            style={{
              alignSelf: "flex-end",
              backgroundColor: "#385463",
              paddingHorizontal: 9,
              paddingVertical: 4,
              borderRadius: 5,
            }}
          >
            <Text style={{ color: "white", fontSize: 8, letterSpacing: 0.6 }}>
              SIMULATED DEMO DATA
            </Text>
          </View>
        ) : null}
        <View
          style={{
            width: 43,
            height: 43,
            backgroundColor: "white",
            borderRadius: 13,
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <CircleAlert color="#24B8B4" size={24} />
        </View>
        <Text style={[typography.eyebrow, { letterSpacing: 0.6 }]}>
          {copy?.title.toUpperCase() ?? "NO RESULT"}
        </Text>
        <Text style={[typography.sectionTitle, { fontSize: 18 }]}>
          {status === "review_required"
            ? "Morphology Flagged for Review"
            : (copy?.title ?? "No result available")}
        </Text>
        <Text style={typography.caption}>
          {copy?.guidance ??
            "Confirm a cell crop and submit it to receive a result."}
        </Text>
        {showModel && params.modelLabel ? (
          <Text style={typography.caption}>
            Morphology label: {params.modelLabel}
          </Text>
        ) : null}
      </View>
      <View
        style={{
          borderWidth: 1,
          borderColor: colors.border,
          borderRadius: 15,
          overflow: "hidden",
        }}
      >
        <Pressable
          accessibilityRole="button"
          accessibilityState={{ expanded: details }}
          onPress={() => setDetails(!details)}
          style={{
            flexDirection: "row",
            alignItems: "center",
            gap: 12,
            padding: 13,
          }}
        >
          <View
            style={{
              padding: 9,
              backgroundColor: colors.pale,
              borderRadius: 12,
            }}
          >
            <Activity color={colors.teal} size={20} />
          </View>
          <View style={{ flex: 1 }}>
            <Text
              style={{ color: colors.navy, fontSize: 12, fontWeight: "600" }}
            >
              Technical Details
            </Text>
            <Text style={{ color: colors.muted, fontSize: 9, marginTop: 4 }}>
              Model and processing information
            </Text>
          </View>
          <ChevronDown color={colors.navy} size={18} />
        </Pressable>
        {details ? (
          <View style={{ padding: 16, paddingTop: 0, gap: 7 }}>
            <Text style={typography.caption}>
              Model version: {params.modelVersion || "Not available"}
            </Text>
            <Text style={typography.caption}>
              Inference mode: {params.inferenceMode || "Not available"}
            </Text>
            {showModel && params.rawModelScore ? (
              <Text style={typography.caption}>
                Raw model score: {params.rawModelScore}. This is not a
                calibrated probability or patient risk.
              </Text>
            ) : null}
            {params.warning ? (
              <Text style={typography.caption}>{params.warning}</Text>
            ) : null}
          </View>
        ) : null}
      </View>
      <View
        style={{
          backgroundColor: colors.pale,
          padding: 14,
          borderRadius: 15,
          flexDirection: "row",
          gap: 10,
        }}
      >
        <ShieldCheck color="#527D94" size={21} />
        <Text style={[typography.caption, { flex: 1, color: "#486E88" }]}>
          <Text style={{ fontWeight: "600" }}>
            Research and educational use only.{" "}
          </Text>
          AI-generated morphology information is not a medical diagnosis. It
          cannot rule out disease. Concerning findings require qualified review.
        </Text>
      </View>
      {error ? (
        <Text accessibilityRole="alert" style={typography.error}>
          {error}
        </Text>
      ) : null}
      {params.sessionId ? (
        <ActionButton
          label={saved ? "Research Session Saved" : "Save Research Session"}
          icon={
            saved ? (
              <Check size={19} color="white" />
            ) : (
              <Database size={19} color="white" />
            )
          }
          onPress={save}
          disabled={saved || busy}
          loading={busy}
        />
      ) : null}
      <View style={{ flexDirection: "row", gap: 9 }}>
        <ActionButton
          label="New Capture"
          icon={<Camera color={colors.navy} size={17} />}
          onPress={() => router.replace("/capture")}
          variant="secondary"
          style={{ flex: 1 }}
        />
        <ActionButton
          label="View History"
          icon={<History color={colors.navy} size={17} />}
          onPress={() => router.navigate("/history")}
          variant="secondary"
          style={{ flex: 1 }}
        />
      </View>
    </Screen>
  );
}
