import { Stack } from "expo-router";
import { StatusBar } from "react-native";
import { colors } from "@/theme";

export default function RootLayout() {
  return (
    <>
      <StatusBar barStyle="dark-content" backgroundColor={colors.background} />
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: colors.background },
          headerTintColor: colors.navy,
          headerTitleStyle: { fontWeight: "700" },
          contentStyle: { backgroundColor: colors.background },
        }}
      >
        <Stack.Screen name="index" options={{ headerShown: false }} />
        <Stack.Screen name="onboarding" options={{ title: "Research use" }} />
        <Stack.Screen name="setup" options={{ title: "Microscope setup" }} />
        <Stack.Screen name="capture" options={{ title: "Capture field" }} />
        <Stack.Screen name="review" options={{ title: "Image quality" }} />
        <Stack.Screen name="crop" options={{ title: "Select one cell" }} />
        <Stack.Screen name="results" options={{ title: "Analysis result" }} />
        <Stack.Screen name="history" options={{ title: "Local history" }} />
        <Stack.Screen name="settings" options={{ title: "Settings" }} />
      </Stack>
    </>
  );
}
