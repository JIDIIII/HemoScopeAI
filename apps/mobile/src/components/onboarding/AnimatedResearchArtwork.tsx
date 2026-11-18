import { useEffect, useRef } from "react";
import { Animated, Easing, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { Microscope, Focus, ScanLine } from "lucide-react-native";
import { useReducedMotion } from "@/hooks/useReducedMotion";
export { useReducedMotion } from "@/hooks/useReducedMotion";

export function AnimatedResearchArtwork({
  step,
  compact,
}: {
  step: number;
  compact: boolean;
}) {
  const reduced = useReducedMotion();
  const orbit = useRef(new Animated.Value(0)).current;
  const float = useRef(new Animated.Value(0)).current;
  const size = compact ? 210 : 260;
  const ring = size * 0.84;
  const Icon = [Microscope, Focus, ScanLine][step] ?? Microscope;
  useEffect(() => {
    if (reduced) {
      orbit.setValue(0);
      float.setValue(0);
      return;
    }
    const rotation = Animated.loop(
      Animated.timing(orbit, {
        toValue: 1,
        duration: 14000,
        easing: Easing.linear,
        useNativeDriver: true,
        isInteraction: false,
      }),
    );
    const hover = Animated.loop(
      Animated.sequence([
        Animated.timing(float, {
          toValue: 1,
          duration: 2000,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
          isInteraction: false,
        }),
        Animated.timing(float, {
          toValue: 0,
          duration: 2000,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
          isInteraction: false,
        }),
      ]),
    );
    rotation.start();
    hover.start();
    return () => {
      rotation.stop();
      hover.stop();
    };
  }, [reduced, orbit, float]);
  return (
    <View
      accessible={false}
      style={{
        width: size,
        height: size,
        alignItems: "center",
        justifyContent: "center",
        marginBottom: 24,
      }}
    >
      <View
        style={{
          position: "absolute",
          width: ring,
          height: ring,
          borderRadius: ring / 2,
          borderWidth: 1,
          borderStyle: "dashed",
          borderColor: "#BDDEDD",
        }}
      />
      <View
        style={{
          position: "absolute",
          top: 14,
          right: 10,
          width: 27,
          height: 27,
          borderWidth: 5,
          borderColor: "#8ACFC9",
          backgroundColor: "#DAF1EE",
          borderRadius: 20,
        }}
      />
      <View
        style={{
          position: "absolute",
          bottom: 12,
          left: 4,
          width: 37,
          height: 37,
          borderWidth: 5,
          borderColor: "#8ACFC9",
          backgroundColor: "#DAF1EE",
          borderRadius: 22,
        }}
      />
      <Animated.View
        pointerEvents="none"
        style={{
          position: "absolute",
          width: ring,
          height: ring,
          transform: [
            {
              rotate: orbit.interpolate({
                inputRange: [0, 1],
                outputRange: ["0deg", "360deg"],
              }),
            },
          ],
        }}
      >
        <View
          style={{
            position: "absolute",
            left: ring / 2 - 6,
            top: -6,
            width: 12,
            height: 12,
            borderRadius: 8,
            borderWidth: 3,
            borderColor: "#B5DEDA",
            backgroundColor: "white",
          }}
        />
        <View
          style={{
            position: "absolute",
            left: ring / 2 - 5,
            bottom: -5,
            width: 10,
            height: 10,
            borderRadius: 6,
            backgroundColor: "#B5DEDA",
          }}
        />
      </Animated.View>
      <Animated.View
        style={{
          transform: [
            {
              translateY: float.interpolate({
                inputRange: [0, 1],
                outputRange: [3, -5],
              }),
            },
            {
              rotate: float.interpolate({
                inputRange: [0, 1],
                outputRange: ["-4deg", "-1deg"],
              }),
            },
          ],
          boxShadow: "0px 18px 35px rgba(16,125,120,0.22)",
          borderRadius: 34,
        }}
      >
        <LinearGradient
          colors={["#102D47", "#117D75"]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={{
            width: size * 0.51,
            height: size * 0.51,
            borderRadius: 34,
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <Icon size={size * 0.21} color="white" strokeWidth={2} />
        </LinearGradient>
      </Animated.View>
    </View>
  );
}
