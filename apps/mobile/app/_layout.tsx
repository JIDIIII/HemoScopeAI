import { Stack } from "expo-router";
import { StatusBar } from "react-native";
import { useReducedMotion } from "@/hooks/useReducedMotion";

export default function RootLayout() {
  const reducedMotion = useReducedMotion();
  const sectionAnimation = reducedMotion ? "none" : "slide_from_right";

  return (
    <>
      <StatusBar barStyle="dark-content" backgroundColor="#FFFFFF" />
      <Stack
        screenOptions={{
          headerShown: false,
          contentStyle: { backgroundColor: "#FFFFFF" },
          animation: reducedMotion ? "none" : "slide_from_right",
          animationTypeForReplace: "push",
          gestureEnabled: !reducedMotion,
        }}
      >
        <Stack.Screen name="index" options={{ animation: "none" }} />
        <Stack.Screen
          name="onboarding"
          options={{ animation: sectionAnimation }}
        />
        <Stack.Screen name="(tabs)" options={{ animation: sectionAnimation }} />
      </Stack>
    </>
  );
}
