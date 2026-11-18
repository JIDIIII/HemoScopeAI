import type { ComponentProps } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { Tabs, router } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Home, History, Settings, Plus } from "lucide-react-native";
import { colors } from "@/theme";

type Props = Parameters<NonNullable<ComponentProps<typeof Tabs>["tabBar"]>>[0];
const items: Record<string, { label: string; icon: typeof Home }> = {
  dashboard: { label: "Home", icon: Home },
  history: { label: "History", icon: History },
  settings: { label: "Settings", icon: Settings },
};
export function BottomMenu({ state, navigation }: Props) {
  const insets = useSafeAreaInsets();
  return (
    <View
      style={[
        styles.navigation,
        { paddingBottom: insets.bottom + 12 },
      ]}
    >
      <View style={styles.tabs}>
        {state.routes.map((route, index) => {
          const selected = state.index === index;
          const { label, icon: Icon } = items[route.name];
          return (
            <Pressable
              key={route.key}
              accessibilityRole="tab"
              accessibilityState={{ selected }}
              onPress={() => {
                const event = navigation.emit({
                  type: "tabPress",
                  target: route.key,
                  canPreventDefault: true,
                });
                if (!selected && !event.defaultPrevented)
                  navigation.navigate(route.name);
              }}
              onLongPress={() =>
                navigation.emit({ type: "tabLongPress", target: route.key })
              }
              style={({ pressed }) => [styles.tab, pressed && styles.pressed]}
            >
              <Icon size={21} color={selected ? colors.white : "#B8C5D0"} />
              <Text
                style={{
                  fontSize: 10,
                  color: selected ? colors.white : "#B8C5D0",
                }}
              >
                {label}
              </Text>
            </Pressable>
          );
        })}
      </View>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Start new scan"
        onPress={() => router.push("/capture")}
        style={({ pressed }) => [
          styles.captureButton,
          pressed && styles.pressed,
        ]}
      >
        <View style={styles.captureInner}>
          <Plus size={26} color={colors.white} />
        </View>
      </Pressable>
    </View>
  );
}
const styles = StyleSheet.create({
  navigation: {
    width: "100%",
    maxWidth: 520,
    alignSelf: "center",
    backgroundColor: colors.white,
    flexDirection: "row",
    alignItems: "center",
    gap: 20,
    paddingHorizontal: 30,
    paddingTop: 10,
    paddingBottom: 12,
  },
  tabs: {
    flex: 1,
    flexDirection: "row",
    backgroundColor: colors.primaryButton,
    borderRadius: 28,
    paddingHorizontal: 10,
    boxShadow: "0px 7px 16px rgba(23, 41, 65, 0.22)",
  },
  tab: {
    flex: 1,
    minHeight: 56,
    justifyContent: "center",
    alignItems: "center",
    gap: 4,
  },
  captureButton: {
    width: 56,
    height: 56,
    borderRadius: 28,
    borderWidth: 3,
    borderColor: colors.primaryButton,
    backgroundColor: colors.white,
    padding: 4,
    boxShadow: "0px 7px 16px rgba(23, 41, 65, 0.22)",
  },
  captureInner: {
    flex: 1,
    borderRadius: 24,
    backgroundColor: colors.primaryButton,
    alignItems: "center",
    justifyContent: "center",
  },
  pressed: { opacity: 0.8 },
});
