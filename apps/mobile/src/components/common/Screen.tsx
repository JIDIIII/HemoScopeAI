import type { PropsWithChildren } from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { router, usePathname, type Href } from "expo-router";
import {
  ArrowLeft,
  Home,
  ScanLine,
  History,
  Settings,
} from "lucide-react-native";
import { Brand } from "./Brand";
import { colors, typography } from "@/theme";
const pages: Record<string, [string, string]> = {
  "/capture": ["Capture Microscope Image", ""],
  "/review": [
    "Image Quality Review",
    "Confirming suitability for further analysis",
  ],
  "/crop": ["Select White Blood Cell", "Choose one complete cell for analysis"],
  "/results": ["Cell Analysis Result", "Cell-level morphology screening"],
  "/setup": ["Capture Guide", "Prepare your microscope and phone"],
  "/history": ["Research History", "Locally saved, non-identifying sessions"],
  "/settings": ["Settings", "Application and research information"],
};
export function Screen({ children }: PropsWithChildren) {
  const path = usePathname();
  const main = ["/dashboard", "/history", "/settings"].includes(path);
  const page = pages[path];
  return (
    <SafeAreaView
      style={styles.safeArea}
      edges={["top", "bottom", "left", "right"]}
    >
      <View style={styles.frame}>
        <ScrollView
          contentContainerStyle={styles.content}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          {main ? (
            <View style={styles.brandRow}>
              <Brand />
              {path === "/dashboard" ? (
                <Pressable
                  accessibilityRole="button"
                  accessibilityLabel="Settings"
                  onPress={() => router.push("/settings")}
                  style={styles.back}
                >
                  <Settings color={colors.navy} size={20} />
                </Pressable>
              ) : null}
            </View>
          ) : null}
          {page ? (
            <View style={styles.heading}>
              {!main ? (
                <Pressable
                  accessibilityRole="button"
                  accessibilityLabel="Back"
                  onPress={() =>
                    router.canGoBack()
                      ? router.back()
                      : router.replace("/dashboard")
                  }
                  style={styles.back}
                >
                  <ArrowLeft size={20} color={colors.navy} />
                </Pressable>
              ) : null}
              <View style={{ flex: 1 }}>
                <Text style={[typography.title, { fontSize: 21 }]}>
                  {page[0]}
                </Text>
                {page[1] ? (
                  <Text style={[typography.caption, { marginTop: 3 }]}>
                    {page[1]}
                  </Text>
                ) : null}
              </View>
            </View>
          ) : null}
          {children}
        </ScrollView>
        {main ? (
          <View style={styles.tabs}>
            {[
              { label: "Home", href: "/dashboard", icon: Home },
              { label: "Capture", href: "/capture", icon: ScanLine },
              { label: "History", href: "/history", icon: History },
              { label: "Settings", href: "/settings", icon: Settings },
            ].map(({ label, href, icon: Icon }) => (
              <Pressable
                key={href}
                accessibilityRole="tab"
                accessibilityState={{ selected: path === href }}
                onPress={() => router.navigate(href as Href)}
                style={[styles.tab, path === href && styles.selected]}
              >
                <Icon
                  size={21}
                  color={path === href ? colors.teal : colors.muted}
                />
                <Text
                  style={{
                    fontSize: 10,
                    color: path === href ? colors.teal : colors.muted,
                  }}
                >
                  {label}
                </Text>
              </Pressable>
            ))}
          </View>
        ) : null}
      </View>
    </SafeAreaView>
  );
}
const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: colors.white },
  frame: { flex: 1, width: "100%", maxWidth: 520, alignSelf: "center" },
  content: {
    flexGrow: 1,
    paddingHorizontal: 24,
    paddingTop: 24,
    paddingBottom: 28,
    gap: 18,
  },
  brandRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 0,
  },
  heading: {
    flexDirection: "row",
    gap: 11,
    alignItems: "center",
    marginBottom: 0,
  },
  back: {
    width: 40,
    height: 40,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: "center",
    justifyContent: "center",
  },
  demo: {
    backgroundColor: colors.pale,
    padding: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderStyle: "dashed",
    borderColor: colors.border,
  },
  tabs: {
    flexDirection: "row",
    borderTopWidth: 1,
    borderColor: colors.border,
    paddingHorizontal: 14,
  },
  tab: {
    flex: 1,
    paddingVertical: 10,
    alignItems: "center",
    gap: 5,
    borderTopWidth: 2,
    borderColor: "transparent",
  },
  selected: { borderColor: colors.teal },
});
