import { useEffect, useState } from "react";
import { ActivityIndicator, StatusBar, View } from "react-native";
import { Stack, router, useSegments } from "expo-router";
import { colors } from "@/theme";
import { USE_SUPABASE_AUTH } from "@/constants/api";
import {
  hasStoredSession,
  isSupabaseAuthConfigured,
  subscribeToAuth,
} from "@/services/auth/supabase";

export default function RootLayout() {
  const segments = useSegments();
  const [authReady, setAuthReady] = useState(!USE_SUPABASE_AUTH);
  const [signedIn, setSignedIn] = useState(false);

  useEffect(() => {
    if (!USE_SUPABASE_AUTH) return;
    let active = true;
    const unsubscribe = subscribeToAuth((value) => {
      if (active) setSignedIn(value);
    });
    void hasStoredSession().then((value) => {
      if (active) {
        setSignedIn(value);
        setAuthReady(true);
      }
    }).catch(() => {
      if (active) {
        setSignedIn(false);
        setAuthReady(true);
      }
    });
    if (!isSupabaseAuthConfigured) setAuthReady(true);
    return () => {
      active = false;
      unsubscribe();
    };
  }, []);

  useEffect(() => {
    if (!USE_SUPABASE_AUTH || !authReady) return;
    const publicRoute = segments[0] === "signin" || segments[0] === "onboarding";
    if (!signedIn && !publicRoute) router.replace("/signin");
    if (signedIn && segments[0] === "signin") router.replace("/dashboard");
  }, [authReady, segments, signedIn]);

  if (USE_SUPABASE_AUTH && !authReady) {
    return (
      <View
        style={{
          flex: 1,
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: colors.white,
        }}
      >
        <ActivityIndicator color={colors.teal} />
      </View>
    );
  }

  return (
    <>
      <StatusBar barStyle="dark-content" backgroundColor="#FFFFFF" />
      <Stack
        screenOptions={{
          headerShown: false,
          contentStyle: { backgroundColor: "#FFFFFF" },
        }}
      />
    </>
  );
}
