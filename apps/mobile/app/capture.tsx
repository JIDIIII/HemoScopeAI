import { CameraView, useCameraPermissions } from "expo-camera";
import { Asset } from "expo-asset";
import * as ImagePicker from "expo-image-picker";
import { router, useFocusEffect, useLocalSearchParams } from "expo-router";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Linking,
  Pressable,
  Text,
  View,
} from "react-native";
import {
  Camera,
  Images,
  ClipboardList,
  ChevronDown,
  Focus,
} from "lucide-react-native";
import { validateImageInput } from "@/features/capture/validation";
import { ActionButton } from "@/components/common/ActionButton";
import { InfoCard } from "@/components/common/InfoCard";
import { Screen } from "@/components/common/Screen";
import { createLocalSessionId } from "@/services/storage/sessionStore";
import { colors, typography } from "@/theme";
import publicSampleImage from "../assets/samples/white_blood_cell_on_blood_smear_unstained.jpg";
export default function CaptureScreen() {
  const cameraRef = useRef<CameraView>(null);
  const [permission, requestPermission] = useCameraPermissions();
  const [busy, setBusy] = useState(false);
  const [focused, setFocused] = useState(true);
  const [cameraReady, setCameraReady] = useState(false);
  const [message, setMessage] = useState<string>();
  const [guideOpen, setGuideOpen] = useState(false);
  const params = useLocalSearchParams<{ import?: string }>();
  const imported = useRef(false);
  useFocusEffect(
    useCallback(() => {
      setFocused(true);
      return () => {
        setFocused(false);
        setCameraReady(false);
      };
    }, []),
  );
  const openReview = useCallback(
    (uri: string, mimeType = "image/jpeg", fileName = "field.jpg") => {
      router.push({
        pathname: "/review",
        params: { uri, mimeType, fileName, sessionId: createLocalSessionId() },
      });
    },
    [],
  );
  const capture = async () => {
    setBusy(true);
    setMessage(undefined);
    try {
      const photo = await cameraRef.current?.takePictureAsync({ quality: 1 });
      if (!photo?.uri)
        throw new Error(
          "The camera did not return an image. Retry or import a file.",
        );
      openReview(photo.uri);
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Camera capture failed. Try again.",
      );
    } finally {
      setBusy(false);
    }
  };
  const importField = useCallback(async () => {
    setBusy(true);
    setMessage(undefined);
    try {
      const allowed = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (!allowed.granted) {
        setMessage(
          "Gallery permission is needed. Enable photo access in device settings.",
        );
        return;
      }
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ["images"],
        quality: 1,
        allowsEditing: false,
      });
      if (result.canceled) return;
      const asset = result.assets[0];
      if (!asset?.uri)
        throw new Error("The selected item did not contain an image.");
      openReview(
        asset.uri,
        validateImageInput(asset),
        asset.fileName ?? "imported-field.jpg",
      );
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "The gallery could not open. Try again.",
      );
    } finally {
      setBusy(false);
    }
  }, [openReview]);
  useEffect(() => {
    if (params.import === "true" && !imported.current) {
      imported.current = true;
      void importField();
    }
  }, [params.import, importField]);
  const openPermissions = () => {
    void (
      permission?.canAskAgain ? requestPermission() : Linking.openSettings()
    ).catch(() =>
      setMessage(
        "Could not open permissions. Allow camera access from device settings.",
      ),
    );
  };
  const openPublicSample = async () => {
    setMessage(undefined);
    setBusy(true);
    try {
      const asset = Asset.fromModule(publicSampleImage);
      await asset.downloadAsync();
      const sampleUri = asset.localUri ?? asset.uri;
      if (!sampleUri) throw new Error("Sample unavailable");
      openReview(sampleUri, "image/jpeg", "public-sample-white-blood-cell.jpg");
    } catch {
      setMessage("The bundled sample could not be opened. Try gallery import.");
    } finally {
      setBusy(false);
    }
  };
  return (
    <Screen>
      <Pressable
        accessibilityRole="button"
        accessibilityState={{ expanded: guideOpen }}
        onPress={() => setGuideOpen(!guideOpen)}
        style={{
          borderWidth: 1,
          borderColor: colors.border,
          borderRadius: 16,
          padding: 14,
          flexDirection: "row",
          alignItems: "center",
          gap: 12,
        }}
      >
        <View
          style={{
            backgroundColor: colors.mint,
            padding: 10,
            borderRadius: 12,
          }}
        >
          <ClipboardList size={21} color={colors.teal} />
        </View>
        <View style={{ flex: 1 }}>
          <Text style={{ color: colors.navy, fontSize: 13, fontWeight: "600" }}>
            Microscope setup
          </Text>
          <Text style={typography.caption}>3 quick checks before capture</Text>
        </View>
        <ChevronDown size={18} color={colors.navy} />
      </Pressable>
      {guideOpen ? (
        <Text style={typography.caption}>
          1. Secure and center the phone over the eyepiece.{"\n"}2. Stabilize
          the mount and focus the microscope.{"\n"}3. Balance illumination; use
          approved, de-identified material.
        </Text>
      ) : null}
      {!permission ? (
        <ActivityIndicator color={colors.teal} />
      ) : permission.granted && focused ? (
        <CameraView
          ref={cameraRef}
          facing="back"
          onCameraReady={() => setCameraReady(true)}
          onMountError={() => {
            setCameraReady(false);
            setMessage("Camera could not start. Retry or import an image.");
          }}
          style={{ height: 380, borderRadius: 24, overflow: "hidden" }}
        >
          <View
            pointerEvents="none"
            style={{ flex: 1, alignItems: "center", justifyContent: "center" }}
          >
            <Focus size={86} strokeWidth={1} color="#DDF5F1" />
            <Text
              style={{
                position: "absolute",
                bottom: 18,
                color: "white",
                fontSize: 10,
                backgroundColor: "#102D4799",
                borderRadius: 8,
                padding: 8,
              }}
            >
              Center field and adjust focus
            </Text>
          </View>
        </CameraView>
      ) : (
        <InfoCard title="Camera access">
          <Text style={typography.body}>
            Allow camera access to capture a microscope field. Gallery import
            remains available.
          </Text>
          <ActionButton
            label={
              permission.canAskAgain
                ? "Allow camera access"
                : "Open device settings"
            }
            onPress={openPermissions}
            style={{ marginTop: 14 }}
          />
        </InfoCard>
      )}
      {message ? (
        <Text accessibilityRole="alert" style={typography.error}>
          {message}
        </Text>
      ) : null}
      <Text style={[typography.caption, { textAlign: "center" }]}>
        Center the microscope field and adjust focus before capturing.
      </Text>
      <View
        style={{
          flexDirection: "row",
          justifyContent: "space-around",
          alignItems: "center",
          paddingVertical: 8,
        }}
      >
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Choose image from gallery"
          disabled={busy}
          onPress={importField}
          style={{ alignItems: "center", gap: 7, padding: 12 }}
        >
          <Images size={24} color={colors.navy} />
          <Text style={typography.caption}>Gallery</Text>
        </Pressable>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Capture microscope field"
          accessibilityState={{
            disabled: !permission?.granted || !cameraReady || busy,
          }}
          disabled={!permission?.granted || !cameraReady || busy}
          onPress={capture}
          style={{
            width: 74,
            height: 74,
            borderRadius: 40,
            borderWidth: 2,
            borderColor: colors.navy,
            padding: 5,
            opacity: !cameraReady || busy ? 0.5 : 1,
          }}
        >
          <View
            style={{
              flex: 1,
              borderRadius: 40,
              backgroundColor: colors.teal,
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            {busy ? (
              <ActivityIndicator color="white" />
            ) : (
              <Camera size={25} color="white" />
            )}
          </View>
        </Pressable>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Capture guide"
          onPress={() => router.push("/setup")}
          style={{ alignItems: "center", gap: 7, padding: 12 }}
        >
          <ClipboardList size={24} color={colors.navy} />
          <Text style={typography.caption}>Guide</Text>
        </Pressable>
      </View>
      <Text style={[typography.caption, { fontSize: 10, textAlign: "center" }]}>
        JPEG, PNG or WebP · Approved research material only
      </Text>
      <ActionButton
        label="Try public sample image"
        onPress={openPublicSample}
        variant="secondary"
        disabled={busy}
      />
      <Text style={typography.caption}>
        The public sample exercises the software flow. It is not a team
        microscope capture, B-ALL example, or clinical result.
      </Text>
    </Screen>
  );
}
