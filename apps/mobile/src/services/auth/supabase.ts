import AsyncStorage from "@react-native-async-storage/async-storage";
import { USE_SUPABASE_AUTH } from "@/constants/api";

const SESSION_KEY = "hemoscope.supabase.session.v1";
const SUPABASE_URL = (process.env.EXPO_PUBLIC_SUPABASE_URL ?? "").replace(
  /\/+$/,
  "",
);
const SUPABASE_PUBLISHABLE_KEY =
  process.env.EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY ?? "";

type StoredSession = {
  access_token: string;
  refresh_token: string;
  expires_at: number;
};

type AuthResponse = StoredSession & {
  expires_in: number;
};

type AuthListener = (signedIn: boolean) => void;
const listeners = new Set<AuthListener>();
let refreshInFlight: Promise<string> | null = null;

export class AuthSessionError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "AuthSessionError";
  }
}

class SupabaseRequestError extends Error {
  constructor(readonly status: number) {
    super("Supabase authentication request failed.");
    this.name = "SupabaseRequestError";
  }
}

export const isSupabaseAuthConfigured =
  USE_SUPABASE_AUTH &&
  SUPABASE_URL.startsWith("https://") &&
  SUPABASE_PUBLISHABLE_KEY.length > 0;

export function subscribeToAuth(listener: AuthListener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function notifyAuthListeners(signedIn: boolean): void {
  for (const listener of listeners) listener(signedIn);
}

async function readSession(): Promise<StoredSession | null> {
  const stored = await AsyncStorage.getItem(SESSION_KEY);
  if (!stored) return null;
  try {
    const value = JSON.parse(stored) as Partial<StoredSession>;
    if (
      typeof value.access_token === "string" &&
      typeof value.refresh_token === "string" &&
      typeof value.expires_at === "number"
    ) {
      return value as StoredSession;
    }
  } catch {
    // Remove malformed local session data rather than passing it to the API.
  }
  await AsyncStorage.removeItem(SESSION_KEY);
  return null;
}

async function writeSession(payload: AuthResponse): Promise<StoredSession> {
  const session: StoredSession = {
    access_token: payload.access_token,
    refresh_token: payload.refresh_token,
    expires_at:
      payload.expires_at ?? Math.floor(Date.now() / 1000) + payload.expires_in,
  };
  await AsyncStorage.setItem(SESSION_KEY, JSON.stringify(session));
  notifyAuthListeners(true);
  return session;
}

async function authRequest(
  grant: "password" | "refresh_token",
  body: Record<string, string>,
): Promise<AuthResponse> {
  if (!isSupabaseAuthConfigured) {
    throw new AuthSessionError(
      "Supabase sign-in is not configured for this app build.",
    );
  }
  const response = await fetch(
    `${SUPABASE_URL}/auth/v1/token?grant_type=${grant}`,
    {
      method: "POST",
      headers: {
        apikey: SUPABASE_PUBLISHABLE_KEY,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    },
  );
  if (!response.ok) {
    throw new SupabaseRequestError(response.status);
  }
  const payload = (await response.json()) as Partial<AuthResponse>;
  if (
    typeof payload.access_token !== "string" ||
    typeof payload.refresh_token !== "string" ||
    typeof payload.expires_in !== "number"
  ) {
    throw new Error("Supabase returned an invalid authentication response.");
  }
  return payload as AuthResponse;
}

export async function hasStoredSession(): Promise<boolean> {
  if (!USE_SUPABASE_AUTH || !isSupabaseAuthConfigured) return false;
  return (await readSession()) !== null;
}

export async function signInWithPassword(
  email: string,
  password: string,
): Promise<void> {
  const payload = await authRequest("password", {
    email: email.trim(),
    password,
  });
  await writeSession(payload);
}

async function refreshAccessToken(session: StoredSession): Promise<string> {
  const payload = await authRequest("refresh_token", {
    refresh_token: session.refresh_token,
  });
  const refreshed = await writeSession(payload);
  return refreshed.access_token;
}

export async function getSupabaseAccessToken(): Promise<string | null> {
  if (!USE_SUPABASE_AUTH) return null;
  if (!isSupabaseAuthConfigured) {
    throw new AuthSessionError(
      "Supabase sign-in is not configured for this app build.",
    );
  }
  const session = await readSession();
  if (!session) throw new AuthSessionError("Sign in to continue.");
  if (session.expires_at > Math.floor(Date.now() / 1000) + 60) {
    return session.access_token;
  }
  if (!refreshInFlight) {
    refreshInFlight = refreshAccessToken(session)
      .catch(async (error: unknown) => {
        if (
          error instanceof SupabaseRequestError &&
          [400, 401, 403].includes(error.status)
        ) {
          await AsyncStorage.removeItem(SESSION_KEY);
          notifyAuthListeners(false);
          throw new AuthSessionError("Your sign-in expired. Sign in again.");
        }
        throw new AuthSessionError(
          "Could not refresh your sign-in. Check the network and try again.",
        );
      })
      .finally(() => {
        refreshInFlight = null;
      });
  }
  try {
    return await refreshInFlight;
  } catch (error) {
    if (error instanceof AuthSessionError) throw error;
    throw new AuthSessionError("Could not refresh your sign-in. Try again.");
  }
}

export async function signOut(): Promise<void> {
  const session = await readSession();
  if (session && isSupabaseAuthConfigured) {
    try {
      await fetch(`${SUPABASE_URL}/auth/v1/logout`, {
        method: "POST",
        headers: {
          apikey: SUPABASE_PUBLISHABLE_KEY,
          Authorization: `Bearer ${session.access_token}`,
        },
      });
    } catch {
      // Clear the local session even when the user is offline.
    }
  }
  await AsyncStorage.removeItem(SESSION_KEY);
  notifyAuthListeners(false);
}
