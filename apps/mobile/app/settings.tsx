import { useState } from "react";
import { Alert, Image, Text, View } from "react-native";
import { router } from "expo-router";
import Constants from "expo-constants";
import {
  Info,
  ShieldCheck,
  FlaskConical,
  Camera,
  ScanLine,
  Cloud,
  CircleAlert,
  Trash2,
  LogOut,
} from "lucide-react-native";
import { Screen } from "@/components/common/Screen";
import { MenuRow } from "@/components/common/MenuRow";
import { getHealth } from "@/services/api/client";
import { clearLocalSessions } from "@/services/storage/sessionStore";
import { USE_MOCK_API, USE_SUPABASE_AUTH } from "@/constants/api";
import { colors, typography } from "@/theme";
import { signOut } from "@/services/auth/supabase";
export default function SettingsScreen() {
  const [connection, setConnection] = useState(
    USE_MOCK_API
      ? "Demo mode · no live inference"
      : "Live endpoint · tap to check",
  );
  const [busy, setBusy] = useState(false);
  const check = async () => {
    if (busy) return;
    setBusy(true);
    setConnection("Checking connection…");
    try {
      const health = await getHealth();
      setConnection(
        `${health.service_status} · ${health.model_available ? "model available" : "model unavailable"} · ${health.inference_mode}`,
      );
    } catch (error) {
      setConnection(
        error instanceof Error ? error.message : "Connection failed",
      );
    } finally {
      setBusy(false);
    }
  };
  const clear = () =>
    Alert.alert(
      "Clear local history?",
      "Saved session metadata will be removed from this device.",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Clear",
          style: "destructive",
          onPress: () => {
            void clearLocalSessions()
              .then(() => Alert.alert("History cleared"))
              .catch(() =>
                Alert.alert("Could not clear history", "Please try again."),
              );
          },
        },
      ],
    );
  const group = {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 16,
    overflow: "hidden" as const,
  };
  return (
    <Screen>
      <View
        style={{
          backgroundColor: colors.mint,
          borderWidth: 1,
          borderColor: "#C2E8E3",
          padding: 17,
          borderRadius: 17,
          flexDirection: "row",
          alignItems: "center",
          gap: 14,
        }}
      >
        <View
          style={{
            borderWidth: 1,
            borderColor: "#BEE6DF",
            borderRadius: 12,
            padding: 8,
          }}
        >
          <Image
            source={require("../assets/brand/symbol.png")}
            style={{ width: 24, height: 32 }}
            resizeMode="contain"
          />
        </View>
        <Text style={{ color: colors.navy, fontSize: 13, fontWeight: "600" }}>
          HemoScope
        </Text>
      </View>
      <Text style={[typography.eyebrow, { color: colors.muted, marginTop: 5 }]}>
        APPLICATION
      </Text>
      <View style={group}>
        <MenuRow
          icon={Info}
          title="App version"
          subtitle={`Research prototype ${Constants.expoConfig?.version ?? "0.1.0"}`}
        />
        <MenuRow
          icon={ShieldCheck}
          title="Research disclaimer"
          subtitle="Review usage limitations"
          onPress={() => router.push("/onboarding")}
        />
        <MenuRow
          icon={FlaskConical}
          title="About HemoScope AI"
          subtitle="Project purpose and technology"
          onPress={() =>
            Alert.alert(
              "HemoScope AI",
              "A guided microscopy research companion. Capture, review quality, confirm one cell, and request cloud-assisted morphology screening. Not a medical diagnostic device.",
            )
          }
        />
      </View>
      <Text style={[typography.eyebrow, { color: colors.muted }]}>
        CAPTURE & ANALYSIS
      </Text>
      <View style={group}>
        <MenuRow
          icon={Camera}
          title="Capture instructions"
          subtitle="Microscope setup guidance"
          onPress={() => router.push("/setup")}
        />
        <MenuRow
          icon={ScanLine}
          title="Image quality guidance"
          subtitle="Focus, exposure and dimensions"
          onPress={() =>
            Alert.alert(
              "Image quality guidance",
              "Stabilize the phone, refocus the microscope and balance illumination. Use JPEG, PNG or WebP without identifiers. The service checks dimensions and quality; passing engineering checks does not guarantee biological suitability.",
            )
          }
        />
        <MenuRow
          icon={Cloud}
          title="Service connection"
          subtitle={connection}
          onPress={check}
        />
        <MenuRow
          icon={CircleAlert}
          title="Analysis limitations"
          subtitle="Cell-level morphology only"
          onPress={() =>
            Alert.alert(
              "Analysis limitations",
              "One selected cell cannot diagnose or rule out disease. Inconclusive and failed analyses are not negative findings. Concerning morphology needs qualified review.",
            )
          }
        />
      </View>
      <Text style={[typography.eyebrow, { color: colors.muted }]}>
        RESEARCH DATA
      </Text>
      <View style={group}>
        <MenuRow
          icon={Trash2}
          title="Clear local history"
          subtitle="Remove saved metadata from this device"
          onPress={clear}
        />
      </View>
      {USE_SUPABASE_AUTH ? (
        <>
          <Text style={[typography.eyebrow, { color: colors.muted }]}>ACCOUNT</Text>
          <View style={group}>
            <MenuRow
              icon={LogOut}
              title="Sign out"
              subtitle="End this device's HemoScope session"
              onPress={() => {
                void signOut().then(() => router.replace("/signin"));
              }}
            />
          </View>
        </>
      ) : null}
    </Screen>
  );
}
