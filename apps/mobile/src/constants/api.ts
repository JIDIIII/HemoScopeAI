export const API_BASE_URL = (
  process.env.EXPO_PUBLIC_API_BASE_URL ?? "http://localhost:8000"
).replace(/\/+$/, "");

// Never silently switch a failed live request to a simulated response.
export const USE_MOCK_API =
  __DEV__ && process.env.EXPO_PUBLIC_API_MODE === "mock";

export const USE_SUPABASE_AUTH =
  process.env.EXPO_PUBLIC_AUTH_MODE === "supabase";
