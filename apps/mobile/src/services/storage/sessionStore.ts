import AsyncStorage from "@react-native-async-storage/async-storage";
import type { ResearchSession } from "@/types/session";

const STORAGE_KEY = "hemoscope.research-sessions.v1";

export function createLocalSessionId(): string {
  return (
    "local-" +
    Date.now().toString(36) +
    "-" +
    Math.random().toString(36).slice(2, 9)
  );
}

export async function listLocalSessions(): Promise<ResearchSession[]> {
  const raw = await AsyncStorage.getItem(STORAGE_KEY);
  if (!raw) return [];
  try {
    const value: unknown = JSON.parse(raw);
    if (!Array.isArray(value)) return [];
    return value as ResearchSession[];
  } catch {
    return [];
  }
}

export async function updateLocalSession(
  session: ResearchSession,
): Promise<void> {
  const existing = await listLocalSessions();
  const updated = [
    session,
    ...existing.filter((item) => item.sessionId !== session.sessionId),
  ].slice(0, 100);
  await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
}

export async function clearLocalSessions(): Promise<void> {
  await AsyncStorage.removeItem(STORAGE_KEY);
}
