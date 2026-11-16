import { router } from "expo-router";
import { LinearGradient } from "expo-linear-gradient";
import {
  Camera,
  ImagePlus,
  Microscope,
  History,
  FlaskConical,
} from "lucide-react-native";
import { Alert, Pressable, Text, View } from "react-native";
import { Screen } from "@/components/common/Screen";
import { ActionButton } from "@/components/common/ActionButton";
import { MenuRow } from "@/components/common/MenuRow";
import { colors, typography } from "@/theme";
export default function DashboardScreen() {
  return (
    <Screen>
      <Text style={[typography.title, { fontSize: 22, marginTop: -7 }]}>
        Your microscopy research companion.
      </Text>
      <LinearGradient
        colors={["#102B46", "#13766E"]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={{
          padding: 23,
          borderRadius: 24,
          minHeight: 242,
          overflow: "hidden",
          justifyContent: "center",
          gap: 13,
        }}
      >
        <View
          style={{
            position: "absolute",
            width: 180,
            height: 180,
            borderRadius: 100,
            borderWidth: 24,
            borderColor: "#ffffff08",
            top: -40,
            right: -65,
          }}
        />
        <View
          style={{
            borderRadius: 20,
            backgroundColor: "#ffffff20",
            alignSelf: "flex-start",
            paddingHorizontal: 9,
            paddingVertical: 5,
          }}
        >
          <Text
            style={{
              fontSize: 9,
              letterSpacing: 0.7,
              color: colors.white,
              fontWeight: "700",
            }}
          >
            AI-ASSISTED RESEARCH
          </Text>
        </View>
        <Text
          style={{
            fontSize: 25,
            lineHeight: 29,
            color: colors.white,
            letterSpacing: -0.7,
          }}
        >
          Explore Cellular{"\n"}Morphology with AI
        </Text>
        <Text
          style={{
            fontSize: 12,
            lineHeight: 20,
            color: "#BDD9DD",
            maxWidth: 255,
          }}
        >
          Capture microscope images, verify quality, and analyze a selected cell
          with guided cloud-assisted AI.
        </Text>
      </LinearGradient>
      <View style={{ flexDirection: "row", gap: 9 }}>
        <ActionButton
          label="Start New Scan"
          icon={<Camera size={18} color="white" />}
          onPress={() => router.push("/capture")}
          style={{ flex: 1 }}
        />
        <ActionButton
          label="Import Image"
          icon={<ImagePlus size={18} color={colors.navy} />}
          variant="secondary"
          onPress={() =>
            router.push({ pathname: "/capture", params: { import: "true" } })
          }
          style={{ flex: 1 }}
        />
      </View>
      <View
        style={{
          flexDirection: "row",
          justifyContent: "space-between",
          marginTop: 8,
        }}
      >
        <Text style={typography.sectionTitle}>Quick access</Text>
        <Text style={typography.caption}>Research tools</Text>
      </View>
      <View
        style={{
          borderWidth: 1,
          borderColor: colors.border,
          borderRadius: 17,
          overflow: "hidden",
        }}
      >
        <MenuRow
          icon={Microscope}
          title="Capture Guide"
          subtitle="Prepare your microscope and phone"
          onPress={() => router.push("/setup")}
        />
      </View>
      <View style={{ flexDirection: "row", gap: 10 }}>
        {[
          {
            title: "Recent Sessions",
            description: "Review saved analyses",
            icon: History,
            action: () => router.push("/history"),
          },
          {
            title: "Technology",
            description: "How HemoScope works",
            icon: FlaskConical,
            action: () =>
              Alert.alert(
                "How HemoScope works",
                "Capture a field, check image quality, manually confirm one complete cell, and submit its crop for morphology screening. Research use only; qualified review is required.",
              ),
          },
        ].map(({ title, description, icon: Icon, action }) => (
          <Pressable
            accessibilityRole="button"
            key={title}
            onPress={action}
            style={{
              flex: 1,
              padding: 16,
              minHeight: 125,
              borderWidth: 1,
              borderColor: colors.border,
              borderRadius: 17,
              gap: 10,
            }}
          >
            <View
              style={{
                backgroundColor: colors.pale,
                width: 38,
                height: 38,
                borderRadius: 12,
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <Icon size={21} color={colors.teal} />
            </View>
            <Text
              style={{ color: colors.navy, fontWeight: "600", fontSize: 12 }}
            >
              {title}
            </Text>
            <Text style={[typography.caption, { fontSize: 10 }]}>
              {description}
            </Text>
          </Pressable>
        ))}
      </View>
    </Screen>
  );
}
