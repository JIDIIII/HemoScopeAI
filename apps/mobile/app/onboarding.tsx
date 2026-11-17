import { Stack, router } from "expo-router";
import WelcomeFlow from "../src/components/onboarding/WelcomeFlow";

export default function OnboardingScreen() {
  return (
    <>
      <Stack.Screen options={{ headerShown: false }} />
      <WelcomeFlow onComplete={() => router.replace("/dashboard")} />
    </>
  );
}
