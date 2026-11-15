import { Image, View } from "react-native";
// Display the supplied artboard at its measured ink bounds without altering the original asset.
export function Brand({ width = 158 }: { width?: number }) {
  const scale = width / 4190;
  return (
    <View
      accessible
      accessibilityLabel="HemoScope"
      style={{ width, height: 953 * scale, overflow: "hidden" }}
    >
      <Image
        source={require("../../../assets/brand/wordmark-source.png")}
        style={{
          position: "absolute",
          width: 6337 * scale,
          height: 4320 * scale,
          left: -970 * scale,
          top: -1727 * scale,
        }}
      />
    </View>
  );
}
