// Expo Router decodes route parameters again in useLocalSearchParams. Local
// Expo Go file paths contain percent escapes that must reach Android unchanged.
const PREFIX = "image-uri:";

export function imageUriParam(uri: string): string {
  // JSON escapes protect percent signs from URL decoding at every route hop.
  return PREFIX + JSON.stringify(uri).replace(/%/g, "\\u0025");
}

export function readImageUri(value: unknown): string | undefined {
  if (typeof value !== "string" || !value) return undefined;
  if (!value.startsWith(PREFIX)) return value; // Existing open routes/deep links.
  try {
    const uri: unknown = JSON.parse(value.slice(PREFIX.length));
    return typeof uri === "string" && uri ? uri : undefined;
  } catch {
    return undefined;
  }
}
