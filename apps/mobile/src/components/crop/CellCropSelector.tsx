import { useEffect, useRef, useState } from "react";
import { Image, PanResponder, Pressable, Text, View } from "react-native";
import { Move, RotateCcw, Focus, Check } from "lucide-react-native";
import { ImageManipulator, SaveFormat } from "expo-image-manipulator";
import { ActionButton } from "@/components/common/ActionButton";
import {
  moveCrop,
  resizeFromCorner,
  type CropCorner,
  pixelCrop,
  type Bounds,
} from "@/features/cell-selection/geometry";
import { colors, spacing, typography } from "@/theme";
export type ConfirmedCrop = {
  uri: string;
  mimeType: string;
  fileName: string;
  bounds: Bounds;
};
type Props = {
  imageUri?: string;
  onCancel: () => void;
  onConfirm: (crop: ConfirmedCrop) => void;
};
const initial: Bounds = { x: 0.3, y: 0.3, width: 0.4, height: 0.4 };
export function CellCropSelector({ imageUri, onCancel, onConfirm }: Props) {
  const [size, setSize] = useState<{ width: number; height: number }>();
  const [layoutWidth, setLayoutWidth] = useState(300);
  const [bounds, setBounds] = useState(initial);
  const [preview, setPreview] = useState<ConfirmedCrop>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();
  const start = useRef(initial);
  useEffect(() => {
    let active = true;
    setSize(undefined);
    setPreview(undefined);
    setBounds(initial);
    setError(undefined);
    if (imageUri)
      Image.getSize(imageUri, (width, height) => {
          if (active) setSize({ width, height });
        }, () => {
          if (active)
            setError(
              "Cannot open this image. Return to capture and choose another file.",
            );
        });
    return () => {
      active = false;
    };
  }, [imageUri]);
  const scale = size
    ? Math.min(layoutWidth / size.width, 360 / size.height)
    : 1;
  const width = size ? size.width * scale : layoutWidth;
  const height = size ? size.height * scale : 300;
  const thumbScale = size
    ? Math.min(
        70 / (bounds.width * size.width),
        70 / (bounds.height * size.height),
      )
    : 1;
  const responder = (corner?: CropCorner) =>
    PanResponder.create({
      onStartShouldSetPanResponder: () => !busy,
      onMoveShouldSetPanResponder: () => !busy,
      onPanResponderGrant: () => {
        start.current = bounds;
        setPreview(undefined);
      },
      onPanResponderMove: (_, gesture) =>
        setBounds(
          corner
            ? resizeFromCorner(
                start.current,
                gesture.dx / width,
                gesture.dy / height,
                corner,
              )
            : moveCrop(start.current, gesture.dx / width, gesture.dy / height),
        ),
      onPanResponderTerminationRequest: () => false,
    });
  const move = responder();
  const makePreview = async () => {
    if (!imageUri || !size) return;
    setBusy(true);
    setError(undefined);
    try {
      const context = ImageManipulator.manipulate(imageUri);
      context.crop(pixelCrop(bounds, size.width, size.height));
      const rendered = await context.renderAsync();
      const file = await rendered.saveAsync({
        format: SaveFormat.JPEG,
        compress: 1,
      });
      setPreview({
        uri: file.uri,
        mimeType: "image/jpeg",
        fileName: "confirmed-cell.jpg",
        bounds,
      });
    } catch {
      setError(
        "Could not create the crop. Adjust the selection and retry; the original field is preserved.",
      );
    } finally {
      setBusy(false);
    }
  };
  return (
    <View
      style={{ gap: spacing.md }}
      onLayout={(event) => setLayoutWidth(event.nativeEvent.layout.width)}
    >
      <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
        <Move size={14} color={colors.muted} />
        <Text style={[typography.caption, { flex: 1, fontSize: 10 }]}>
          Drag and resize selection
        </Text>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Reset cell selection"
          disabled={busy}
          onPress={() => {
            setBounds(initial);
            setPreview(undefined);
          }}
          style={{ flexDirection: "row", gap: 5, padding: 7 }}
        >
          <RotateCcw size={14} color={colors.teal} />
          <Text style={{ fontSize: 10, color: colors.teal }}>Reset</Text>
        </Pressable>
      </View>
      {imageUri && size ? (
        <View
          style={{
            width,
            height,
            alignSelf: "center",
            backgroundColor: colors.pale,
          }}
        >
          <Image
            source={{ uri: imageUri }}
            style={{ width, height }}
            resizeMode="contain"
            accessibilityLabel="Original field with movable cell selection"
          />
          <View
            pointerEvents="none"
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              right: 0,
              height: bounds.y * height,
              backgroundColor: "#102D4733",
            }}
          />
          <View
            pointerEvents="none"
            style={{
              position: "absolute",
              top: (bounds.y + bounds.height) * height,
              bottom: 0,
              left: 0,
              right: 0,
              backgroundColor: "#102D4733",
            }}
          />
          <View
            pointerEvents="none"
            style={{
              position: "absolute",
              top: bounds.y * height,
              height: bounds.height * height,
              left: 0,
              width: bounds.x * width,
              backgroundColor: "#102D4733",
            }}
          />
          <View
            pointerEvents="none"
            style={{
              position: "absolute",
              top: bounds.y * height,
              height: bounds.height * height,
              left: (bounds.x + bounds.width) * width,
              right: 0,
              backgroundColor: "#102D4733",
            }}
          />
          <View
            {...move.panHandlers}
            accessibilityLabel="Drag cell selection"
            style={{
              position: "absolute",
              left: bounds.x * width,
              top: bounds.y * height,
              width: bounds.width * width,
              height: bounds.height * height,
              borderWidth: 2,
              borderColor: colors.white,
            }}
          >
            <View
              pointerEvents="none"
              style={{
                position: "absolute",
                top: -27,
                alignSelf: "center",
                paddingHorizontal: 8,
                paddingVertical: 4,
                backgroundColor: colors.teal,
                borderRadius: 4,
              }}
            >
              <Text style={{ color: "white", fontSize: 8, fontWeight: "700" }}>
                1 CELL
              </Text>
            </View>
            <View
              pointerEvents="none"
              style={{
                position: "absolute",
                top: "50%",
                width: "100%",
                height: 1,
                backgroundColor: "#FFFFFF88",
              }}
            />
            <View
              pointerEvents="none"
              style={{
                position: "absolute",
                left: "50%",
                height: "100%",
                width: 1,
                backgroundColor: "#FFFFFF88",
              }}
            />
            {(
              [
                "topLeft",
                "topRight",
                "bottomLeft",
                "bottomRight",
              ] as CropCorner[]
            ).map((corner) => (
              <View
                key={corner}
                {...responder(corner).panHandlers}
                accessibilityLabel={"Resize " + corner}
                style={{
                  position: "absolute",
                  width: 30,
                  height: 30,
                  alignItems: "center",
                  justifyContent: "center",
                  ...(corner.startsWith("top")
                    ? { top: -16 }
                    : { bottom: -16 }),
                  ...(corner.endsWith("Left") ? { left: -16 } : { right: -16 }),
                }}
              >
                <View
                  style={{
                    width: 15,
                    height: 15,
                    borderRadius: 8,
                    backgroundColor: "white",
                    borderWidth: 2,
                    borderColor: colors.teal,
                  }}
                />
              </View>
            ))}
          </View>
        </View>
      ) : null}
      <View
        style={{
          flexDirection: "row",
          gap: 11,
          padding: 13,
          borderWidth: 1,
          borderColor: colors.border,
          borderRadius: 14,
          backgroundColor: colors.pale,
        }}
      >
        <Focus size={23} color={colors.teal} />
        <View style={{ flex: 1 }}>
          <Text style={{ fontSize: 11, fontWeight: "600", color: colors.navy }}>
            Position around one complete cell
          </Text>
          <Text style={[typography.caption, { fontSize: 10 }]}>
            Include the entire cell, avoid cut edges, and keep only one cell as
            the primary subject.
          </Text>
        </View>
      </View>
      {size && imageUri ? (
        <>
          <View
            style={{ flexDirection: "row", justifyContent: "space-between" }}
          >
            <Text style={typography.sectionTitle}>Selected Cell Preview</Text>
            <Text style={typography.eyebrow}>LIVE</Text>
          </View>
          <View
            style={{
              borderWidth: 1,
              borderColor: colors.border,
              borderRadius: 15,
              padding: 12,
              flexDirection: "row",
              gap: 12,
              alignItems: "center",
            }}
          >
            <View
              style={{
                width: bounds.width * size.width * thumbScale,
                height: bounds.height * size.height * thumbScale,
                overflow: "hidden",
                borderRadius: 10,
                backgroundColor: colors.pale,
              }}
            >
              <Image
                source={{ uri: imageUri }}
                style={{
                  position: "absolute",
                  width: size.width * thumbScale,
                  height: size.height * thumbScale,
                  left: -bounds.x * size.width * thumbScale,
                  top: -bounds.y * size.height * thumbScale,
                }}
              />
            </View>
            <View style={{ flex: 1 }}>
              <Text
                style={{ fontSize: 12, color: colors.navy, fontWeight: "600" }}
              >
                Manual selection
              </Text>
              <Text style={[typography.caption, { color: colors.teal }]}>
                Crop {Math.round(bounds.width * size.width)} ×{" "}
                {Math.round(bounds.height * size.height)} px
              </Text>
              <Text style={[typography.caption, { fontSize: 9 }]}>
                Confirm that the whole white blood cell is visible.
              </Text>
            </View>
          </View>
        </>
      ) : null}
      {error ? (
        <Text accessibilityRole="alert" style={typography.error}>
          {error}
        </Text>
      ) : null}
      <ActionButton
        label="Preview selected crop"
        onPress={makePreview}
        loading={busy}
        disabled={!size || busy}
      />
      {preview ? (
        <>
          <Image
            source={{ uri: preview.uri }}
            resizeMode="contain"
            style={{ width: "100%", height: 220, backgroundColor: colors.navy }}
            accessibilityLabel="Actual cropped image for confirmation"
          />
          <Text style={typography.body}>
            Confirm that exactly one complete white blood cell is visible, with
            no cell edge cut off. If uncertain, adjust the box or choose another
            field.
          </Text>
          <ActionButton
            label="Confirm Cell Selection"
            icon={<Check size={19} color="white" />}
            onPress={() => onConfirm(preview)}
            disabled={busy}
          />
        </>
      ) : null}
      <ActionButton
        label="Return to field review"
        onPress={onCancel}
        variant="secondary"
        disabled={busy}
      />
    </View>
  );
}
