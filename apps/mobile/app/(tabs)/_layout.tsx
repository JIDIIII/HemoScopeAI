import { Tabs } from "expo-router";
import { Easing } from "react-native";
import { BottomMenu } from "@/components/common/BottomMenu";
import { useReducedMotion } from "@/hooks/useReducedMotion";

export default function MainTabs() {
  const reducedMotion = useReducedMotion();
  return (
    <Tabs
      initialRouteName="dashboard"
      backBehavior="history"
      tabBar={(props) => <BottomMenu {...props} />}
      screenOptions={{
        headerShown: false,
        lazy: false,
        animation: reducedMotion ? "none" : "fade",
        transitionSpec: {
          animation: "timing",
          config: {
            duration: reducedMotion ? 0 : 300,
            easing: Easing.inOut(Easing.cubic),
          },
        },
        sceneStyle: { backgroundColor: "#FFFFFF" },
      }}
    >
      <Tabs.Screen name="dashboard" />
      <Tabs.Screen name="history" />
      <Tabs.Screen name="settings" />
    </Tabs>
  );
}
