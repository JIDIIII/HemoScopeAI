import { CameraView, useCameraPermissions } from "expo-camera";
import * as ImagePicker from "expo-image-picker";
import { router } from "expo-router";
import { useRef, useState } from "react";
import { ActivityIndicator, Text, View } from "react-native";
import { ActionButton } from "@/components/common/ActionButton";
import { InfoCard } from "@/components/common/InfoCard";
import { Screen } from "@/components/common/Screen";
import { createLocalSessionId } from "@/services/storage/sessionStore";
import { colors, spacing, typography } from "@/theme";
import type { CameraView as CameraViewType } from "expo-camera";

export default function CaptureScreen() {
  const cameraRef = useRef<CameraViewType>(null);
  const [permission, requestPermission] = useCameraPermissions();
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | undefined>();

  const openReview = (
    uri: string,
    mimeType = "image/jpeg",
    fileName = "field.jpg",
  ) => {
    const sessionId = createLocalSessionId();
    router.push({
      pathname: "/review",
      params: { uri, mimeType, fileName, sessionId },
    });
  };

  const captureField = async () => {
    setMessage(undefined);
    setBusy(true);
    try {
      const photo = await cameraRef.current?.takePictureAsync({ quality: 1 });
      if (!photo?.uri) {
        setMessage(
          "The camera did not return an image. Try again or import a file.",
        );
        return;
      }
      openReview(photo.uri);
    } catch {
      setMessage(
        "Camera capture failed. Check permission or choose an image from the gallery.",
      );
    } finally {
      setBusy(false);
    }
  };

  const importField = async () => {
    setMessage(undefined);
    setBusy(true);
    try {
      const permissionResult =
        await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (!permissionResult.granted) {
        setMessage("Gallery permission is needed to choose a research image.");
        return;
      }
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ["images"],
        quality: 1,
        allowsEditing: false,
      });
      if (result.canceled) return;
      const asset = result.assets[0];
      if (!asset?.uri) {
        setMessage("The selected item did not contain an image.");
        return;
      }
      openReview(
        asset.uri,
        asset.mimeType ?? "image/jpeg",
        asset.fileName ?? "imported-field.jpg",
      );
    } catch {
      setMessage("The gallery could not open. Check permission or try again.");
    } finally {
      setBusy(false);
    }
  };

  if (!permission) {
    return (
      <Screen>
        <View
          style={{ flex: 1, alignItems: "center", justifyContent: "center" }}
        >
          <ActivityIndicator color={colors.teal} />
          <Text style={[typography.body, { marginTop: spacing.md }]}>
            Checking camera permission…
          </Text>
        </View>
      </Screen>
    );
  }

  return (
    <Screen>
      <View style={{ flex: 1, gap: spacing.md }}>
        <Text style={typography.body}>
          Capture a complete microscope field. Review focus and exposure before
          selecting a cell.
        </Text>
        {permission.granted ? (
          <CameraView
            ref={cameraRef}
            facing="back"
            style={{
              flex: 1,
              minHeight: 320,
              borderRadius: 20,
              overflow: "hidden",
            }}
          />
        ) : (
          <InfoCard title="Camera permission is required">
            <Text style={typography.body}>
              Allow camera access to capture a field. Gallery import remains
              available if camera permission is denied.
            </Text>
            <ActionButton
              label="Request camera permission"
              onPress={requestPermission}
              style={{ marginTop: spacing.md }}
            />
          </InfoCard>
        )}

        {message ? (
          <Text accessibilityRole="alert" style={typography.error}>
            {message}
          </Text>
        ) : null}
        <View style={{ gap: spacing.sm }}>
          <ActionButton
            label="Capture microscope field"
            onPress={captureField}
            disabled={!permission.granted || busy}
            loading={busy}
          />
          <ActionButton
            label="Choose image from gallery"
            onPress={importField}
            variant="secondary"
            disabled={busy}
            loading={busy}
          />
        </View>
        <Text style={typography.caption}>
          Accepted image formats are JPEG, PNG, and WebP. Patient identifiers
          must not appear in the image.
        </Text>
      </View>
    </Screen>
  );
}
