import { useState } from "react";
import { Text, TextInput, View } from "react-native";
import { router, Stack } from "expo-router";
import { ActionButton } from "@/components/common/ActionButton";
import { Brand } from "@/components/common/Brand";
import { Screen } from "@/components/common/Screen";
import { colors, typography } from "@/theme";
import {
  isSupabaseAuthConfigured,
  signInWithPassword,
} from "@/services/auth/supabase";

export default function SignInScreen() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const signIn = async () => {
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      await signInWithPassword(email, password);
      router.replace("/dashboard");
    } catch {
      setError(
        isSupabaseAuthConfigured
          ? "Sign-in failed. Check your email and password, then try again."
          : "This app build is missing its Supabase Auth configuration.",
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <Stack.Screen options={{ headerShown: false }} />
      <Screen>
        <Brand />
        <View style={{ gap: 9 }}>
          <Text style={typography.title}>Sign in to HemoScope AI</Text>
          <Text style={typography.body}>
            Use an account issued by the project owner. Uploads are sent only to
            the configured research API.
          </Text>
        </View>
        <View style={{ gap: 8 }}>
          <Text style={[typography.caption, { color: colors.navy }]}>Email</Text>
          <TextInput
            accessibilityLabel="Email"
            autoCapitalize="none"
            autoComplete="email"
            autoCorrect={false}
            keyboardType="email-address"
            onChangeText={setEmail}
            placeholder="name@example.org"
            placeholderTextColor={colors.muted}
            style={inputStyle}
            textContentType="emailAddress"
            value={email}
          />
        </View>
        <View style={{ gap: 8 }}>
          <Text style={[typography.caption, { color: colors.navy }]}>Password</Text>
          <TextInput
            accessibilityLabel="Password"
            autoCapitalize="none"
            autoComplete="password"
            onChangeText={setPassword}
            onSubmitEditing={() => void signIn()}
            placeholder="Password"
            placeholderTextColor={colors.muted}
            secureTextEntry
            style={inputStyle}
            textContentType="password"
            value={password}
          />
        </View>
        {error ? <Text style={typography.error}>{error}</Text> : null}
        <ActionButton
          label="Sign In"
          loading={busy}
          disabled={!email.trim() || !password}
          onPress={() => void signIn()}
        />
        <Text style={typography.caption}>
          Accounts are provisioned by the project owner. HemoScope AI is for
          research and education only, not medical diagnosis.
        </Text>
      </Screen>
    </>
  );
}

const inputStyle = {
  minHeight: 50,
  borderWidth: 1,
  borderColor: colors.border,
  borderRadius: 13,
  paddingHorizontal: 14,
  color: colors.navy,
  backgroundColor: colors.white,
} as const;
