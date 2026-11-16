import { useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Animated,
  BackHandler,
  Platform,
  Image,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
  useWindowDimensions,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { Brand } from "../common/Brand";
import {
  AnimatedResearchArtwork,
  useReducedMotion,
} from "./AnimatedResearchArtwork";
const shield = require("../../../assets/research-shield.png");

const slides = [
  {
    title: "Welcome to HemoScope AI",
    description:
      "A guided smartphone microscopy research experience designed for clarity and responsible review.",
    artwork: require("../../../assets/microscope.png"),
  },
  {
    title: "Capture Clear Microscope Images",
    description:
      "Use guided imaging and immediate quality feedback to improve each microscope capture.",
    artwork: require("../../../assets/capture-focus.png"),
  },
  {
    title: "Select a Cell for AI Review",
    description:
      "Manually choose one complete white blood cell and submit it for research-level morphology screening.",
    artwork: require("../../../assets/cell-selection.png"),
  },
];

const noticeStep = slides.length;
const acknowledgment =
  "I understand that HemoScope is a research tool and does not provide a medical diagnosis.";

type WelcomeFlowProps = {
  onComplete: () => void | Promise<void>;
};

export default function WelcomeFlow({ onComplete }: WelcomeFlowProps) {
  const [step, setStep] = useState(0);
  const [checked, setChecked] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const savingRef = useRef(false);
  const { height } = useWindowDimensions();
  const reducedMotion = useReducedMotion();
  const reveal = useRef(new Animated.Value(1)).current;
  useEffect(() => {
    reveal.setValue(reducedMotion ? 1 : 0);
    const animation = Animated.timing(reveal, {
      toValue: 1,
      duration: 320,
      useNativeDriver: true,
    });
    animation.start();
    return () => animation.stop();
  }, [step, reducedMotion, reveal]);

  const compact = height < 730;
  const isNotice = step === noticeStep;
  const slide = slides[step];
  const disabled = saving || (isNotice && !checked);
  const continueLabel = isNotice ? "I Understand — Continue" : "Continue";

  useEffect(() => {
    if (Platform.OS === "web") return;
    const subscription = BackHandler.addEventListener(
      "hardwareBackPress",
      () => {
        if (savingRef.current) return true;
        if (step === 0) return false;

        setError("");
        setStep(step - 1);
        return true;
      },
    );

    return () => subscription.remove();
  }, [step]);

  function goBack() {
    setError("");
    setStep((current) => Math.max(0, current - 1));
  }

  async function goForward() {
    if (savingRef.current) return;

    if (!isNotice) {
      setStep(step + 1);
      return;
    }

    if (!checked) return;

    savingRef.current = true;
    setSaving(true);
    setError("");

    try {
      await onComplete();
    } catch {
      setError("Could not save your acknowledgment. Please try again.");
    } finally {
      savingRef.current = false;
      setSaving(false);
    }
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.screen}>
        <ScrollView
          key={step}
          style={styles.scroll}
          contentContainerStyle={[
            styles.content,
            compact && styles.contentCompact,
          ]}
        >
          <View style={{ alignSelf: "center" }}>
            <Brand width={158} />
          </View>

          <View
            accessible
            accessibilityLabel={`Welcome, step ${step + 1} of 4`}
            style={styles.progress}
          >
            {Array.from({ length: 4 }, (_, index) => (
              <View
                key={index}
                style={[styles.marker, index <= step && styles.activeMarker]}
              />
            ))}
          </View>

          {slide ? (
            <Animated.View
              style={[
                styles.intro,
                compact && styles.introCompact,
                {
                  opacity: reveal,
                  transform: [
                    {
                      translateY: reveal.interpolate({
                        inputRange: [0, 1],
                        outputRange: [12, 0],
                      }),
                    },
                  ],
                },
              ]}
            >
              <AnimatedResearchArtwork step={step} compact={compact} />
              <Text
                style={{
                  color: "#0F766E",
                  fontSize: 10,
                  letterSpacing: 1.4,
                  fontWeight: "600",
                  marginBottom: 12,
                }}
              >
                STEP {step + 1} OF 4
              </Text>
              <Text
                accessibilityRole="header"
                style={[styles.heading, styles.centeredHeading]}
              >
                {slide.title}
              </Text>
              <Text style={styles.description}>{slide.description}</Text>
            </Animated.View>
          ) : (
            <View style={styles.notice}>
              <Image source={shield} accessible={false} style={styles.shield} />

              <Text accessibilityRole="header" style={styles.heading}>
                Designed to assist research, not diagnose.
              </Text>

              <View style={styles.callout}>
                <Text style={styles.calloutText}>
                  HemoScope analyzes selected cell images and may flag
                  morphology for qualified review. It does not diagnose
                  leukemia, determine health status, or replace laboratory or
                  clinical evaluation.
                </Text>
                <Text style={[styles.calloutText, styles.materialNotice]}>
                  Use only approved, de-identified research or teaching
                  material.
                </Text>
              </View>

              <Pressable
                accessibilityRole="checkbox"
                accessibilityLabel={acknowledgment}
                accessibilityState={{ checked, disabled: saving }}
                disabled={saving}
                onPress={() => setChecked((current) => !current)}
                style={styles.checkboxRow}
              >
                <View style={[styles.checkbox, checked && styles.checkedBox]}>
                  {checked && <Text style={styles.checkmark}>✓</Text>}
                </View>
                <Text style={styles.checkboxLabel}>{acknowledgment}</Text>
              </Pressable>

              {!!error && (
                <Text accessibilityRole="alert" style={styles.error}>
                  {error}
                </Text>
              )}
            </View>
          )}
        </ScrollView>

        <View style={styles.footer}>
          {step > 0 && (
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Back"
              disabled={saving}
              onPress={goBack}
              style={({ pressed }) => [
                styles.button,
                styles.backButton,
                pressed && styles.pressed,
              ]}
            >
              <Text style={styles.backText}>← Back</Text>
            </Pressable>
          )}

          <Pressable
            accessibilityRole="button"
            accessibilityLabel={continueLabel}
            accessibilityState={{ disabled, busy: saving }}
            disabled={disabled}
            onPress={goForward}
            style={({ pressed }) => [
              styles.button,
              styles.continueButton,
              disabled && styles.disabledButton,
              pressed && styles.pressed,
            ]}
          >
            {saving ? (
              <ActivityIndicator color="#102A43" />
            ) : (
              <Text
                style={[styles.continueText, disabled && styles.disabledText]}
              >
                {isNotice ? "✓  " : "→  "}
                {continueLabel}
              </Text>
            )}
          </Pressable>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: "#FFFFFF" },
  screen: { flex: 1, width: "100%", maxWidth: 480, alignSelf: "center" },
  scroll: { flex: 1 },
  content: { paddingHorizontal: 24, paddingTop: 36, paddingBottom: 18 },
  contentCompact: { paddingTop: 24 },
  logo: { width: 156, height: 36, alignSelf: "center" },
  progress: {
    flexDirection: "row",
    justifyContent: "center",
    gap: 6,
    marginTop: 18,
  },
  marker: { width: 22, height: 4, borderRadius: 4, backgroundColor: "#D9E5E9" },
  activeMarker: { width: 30, backgroundColor: "#0F766E" },
  intro: { alignItems: "center", marginTop: 38 },
  introCompact: { marginTop: 23 },
  artwork: { width: "100%", maxWidth: 294, height: 253, marginBottom: 23 },
  artworkCompact: { maxWidth: 244, height: 202, marginBottom: 16 },
  heading: {
    color: "#102A43",
    fontSize: 24,
    fontWeight: "500",
    lineHeight: 29,
    letterSpacing: -0.6,
  },
  centeredHeading: { textAlign: "center", maxWidth: 326 },
  description: {
    color: "#51677B",
    fontSize: 14,
    lineHeight: 22,
    textAlign: "center",
    maxWidth: 298,
    marginTop: 13,
  },
  notice: { width: "100%", maxWidth: 352, alignSelf: "center", marginTop: 35 },
  shield: { width: 56, height: 56, marginBottom: 12 },
  callout: {
    marginTop: 20,
    borderRadius: 12,
    borderLeftWidth: 4,
    borderLeftColor: "#0F766E",
    backgroundColor: "#EEF7F6",
    padding: 16,
  },
  calloutText: { color: "#3D5F79", fontSize: 13, lineHeight: 20 },
  materialNotice: { marginTop: 8 },
  checkboxRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 10,
    minHeight: 48,
    paddingVertical: 12,
    marginTop: 7,
  },
  checkbox: {
    width: 22,
    height: 22,
    borderRadius: 6,
    borderWidth: 1.5,
    borderColor: "#8299AB",
    alignItems: "center",
    justifyContent: "center",
  },
  checkedBox: { backgroundColor: "#0F766E", borderColor: "#0F766E" },
  checkmark: { color: "#FFFFFF", fontSize: 15, fontWeight: "700" },
  checkboxLabel: { flex: 1, color: "#51677B", fontSize: 13, lineHeight: 19 },
  error: { color: "#A12834", fontSize: 13, lineHeight: 19, marginTop: 7 },
  footer: {
    flexDirection: "row",
    gap: 10,
    paddingHorizontal: 24,
    paddingTop: 8,
    paddingBottom: 16,
  },
  button: {
    minHeight: 48,
    paddingHorizontal: 12,
    paddingVertical: 11,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 12,
  },
  backButton: {
    minWidth: 84,
    borderWidth: 1,
    borderColor: "#D9E5E9",
    backgroundColor: "#FFFFFF",
  },
  backText: { color: "#102A43", fontSize: 14, fontWeight: "600" },
  continueButton: { flex: 1, backgroundColor: "#0F766E", elevation: 3 },
  continueText: {
    color: "#FFFFFF",
    fontSize: 14,
    fontWeight: "600",
    textAlign: "center",
  },
  disabledButton: { backgroundColor: "#D6E4E4", elevation: 0 },
  disabledText: { color: "#395657" },
  pressed: { opacity: 0.78 },
});
