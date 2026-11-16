import { useEffect, useMemo, useRef, useState } from "react";
import {
  Image,
  PanResponder,
  Text,
  View,
  type LayoutChangeEvent,
} from "react-native";
import { ActionButton } from "@/components/common/ActionButton";
import { colors, radii, spacing, typography } from "@/theme";

export type ConfirmedCrop = {
  uri: string;
  mimeType: string;
  fileName: string;
  bounds: { x: number; y: number; width: number; height: number };
};

type Point = { x: number; y: number };
type Selection = { x: number; y: number; width: number; height: number };
type ImageRect = { x: number; y: number; width: number; height: number };

type Props = {
  imageUri?: string;
  mimeType: string;
  fileName: string;
  busy?: boolean;
  onCancel: () => void;
  onConfirm: (crop: ConfirmedCrop) => void;
};

const MIN_CROP_PIXELS = 96;

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function selectionBetween(start: Point, end: Point): Selection {
  return {
    x: Math.min(start.x, end.x),
    y: Math.min(start.y, end.y),
    width: Math.abs(end.x - start.x),
    height: Math.abs(end.y - start.y),
  };
}

export function CellCropSelector({
  imageUri,
  mimeType,
  fileName,
  busy = false,
  onCancel,
  onConfirm,
}: Props) {
  const [sourceSize, setSourceSize] = useState<{
    width: number;
    height: number;
  }>();
  const [containerSize, setContainerSize] = useState({ width: 0, height: 0 });
  const [selection, setSelection] = useState<Selection>();
  const [imageLoadError, setImageLoadError] = useState(false);
  const dragStart = useRef<Point | undefined>(undefined);

  useEffect(() => {
    setSelection(undefined);
    setSourceSize(undefined);
    setImageLoadError(false);
    if (!imageUri) return;

    Image.getSize(
      imageUri,
      (width, height) => setSourceSize({ width, height }),
      () => {
        setSourceSize(undefined);
        setImageLoadError(true);
      },
    );
  }, [imageUri]);

  const onLayout = (event: LayoutChangeEvent) => {
    const { width, height } = event.nativeEvent.layout;
    setContainerSize({ width, height });
  };

  const imageRect = useMemo<ImageRect | undefined>(() => {
    if (
      !sourceSize ||
      sourceSize.width < 1 ||
      sourceSize.height < 1 ||
      containerSize.width < 1 ||
      containerSize.height < 1
    ) {
      return undefined;
    }
    const scale = Math.min(
      containerSize.width / sourceSize.width,
      containerSize.height / sourceSize.height,
    );
    const width = sourceSize.width * scale;
    const height = sourceSize.height * scale;
    return {
      x: (containerSize.width - width) / 2,
      y: (containerSize.height - height) / 2,
      width,
      height,
    };
  }, [containerSize, sourceSize]);

  const panResponder = useMemo(
    () =>
      PanResponder.create({
        onStartShouldSetPanResponder: () => Boolean(imageRect),
        onMoveShouldSetPanResponder: () => Boolean(imageRect),
        onPanResponderTerminationRequest: () => false,
        onPanResponderGrant: (event) => {
          if (!imageRect) return;
          const point = {
            x: clamp(
              event.nativeEvent.locationX,
              imageRect.x,
              imageRect.x + imageRect.width,
            ),
            y: clamp(
              event.nativeEvent.locationY,
              imageRect.y,
              imageRect.y + imageRect.height,
            ),
          };
          dragStart.current = point;
          setSelection({ x: point.x, y: point.y, width: 0, height: 0 });
        },
        onPanResponderMove: (event) => {
          if (!imageRect || !dragStart.current) return;
          const point = {
            x: clamp(
              event.nativeEvent.locationX,
              imageRect.x,
              imageRect.x + imageRect.width,
            ),
            y: clamp(
              event.nativeEvent.locationY,
              imageRect.y,
              imageRect.y + imageRect.height,
            ),
          };
          setSelection(selectionBetween(dragStart.current, point));
        },
        onPanResponderRelease: (event) => {
          if (!imageRect || !dragStart.current) return;
          const point = {
            x: clamp(
              event.nativeEvent.locationX,
              imageRect.x,
              imageRect.x + imageRect.width,
            ),
            y: clamp(
              event.nativeEvent.locationY,
              imageRect.y,
              imageRect.y + imageRect.height,
            ),
          };
          setSelection(selectionBetween(dragStart.current, point));
          dragStart.current = undefined;
        },
        onPanResponderTerminate: () => {
          dragStart.current = undefined;
          setSelection(undefined);
        },
      }),
    [imageRect],
  );

  const cropPixels = useMemo(() => {
    if (!selection || !imageRect || !sourceSize) return undefined;
    return {
      width: (selection.width / imageRect.width) * sourceSize.width,
      height: (selection.height / imageRect.height) * sourceSize.height,
    };
  }, [imageRect, selection, sourceSize]);

  const canConfirm =
    Boolean(selection && imageRect && sourceSize && cropPixels) &&
    (cropPixels?.width ?? 0) >= MIN_CROP_PIXELS &&
    (cropPixels?.height ?? 0) >= MIN_CROP_PIXELS;

  const confirmSelection = () => {
    if (!imageUri || !selection || !imageRect || !canConfirm) return;
    onConfirm({
      uri: imageUri,
      mimeType,
      fileName,
      bounds: {
        x: (selection.x - imageRect.x) / imageRect.width,
        y: (selection.y - imageRect.y) / imageRect.height,
        width: selection.width / imageRect.width,
        height: selection.height / imageRect.height,
      },
    });
  };

  return (
    <View style={{ gap: spacing.md }}>
      <Text style={typography.body}>
        Drag over one complete cell. Check the outline includes the whole cell
        and excludes neighboring cells before submitting.
      </Text>
      <View
        onLayout={onLayout}
        style={{
          width: "100%",
          height: 300,
          overflow: "hidden",
          borderRadius: radii.lg,
          backgroundColor: colors.navy,
        }}
      >
        {imageUri ? (
          <Image
            accessibilityLabel="Image used for single-cell crop selection"
            source={{ uri: imageUri }}
            resizeMode="contain"
            style={{ width: "100%", height: "100%" }}
          />
        ) : null}
        <View
          {...panResponder.panHandlers}
          style={{ position: "absolute", left: 0, top: 0, right: 0, bottom: 0 }}
        >
          {selection ? (
            <View
              pointerEvents="none"
              style={{
                position: "absolute",
                left: selection.x,
                top: selection.y,
                width: selection.width,
                height: selection.height,
                borderWidth: 2,
                borderColor: colors.teal,
                backgroundColor: "rgba(18, 188, 178, 0.18)",
              }}
            />
          ) : null}
        </View>
      </View>
      <Text style={typography.caption}>
        {imageLoadError
          ? "The image dimensions could not be read. Return to review and choose another image."
          : !sourceSize
            ? "Preparing the image for crop selection…"
            : canConfirm
              ? `Selected area: ${Math.round(cropPixels?.width ?? 0)} × ${Math.round(cropPixels?.height ?? 0)} source pixels.`
              : `Select at least ${MIN_CROP_PIXELS} × ${MIN_CROP_PIXELS} source pixels. Smaller selections will be rejected.`}
      </Text>
      <ActionButton
        label="Submit confirmed cell crop"
        onPress={confirmSelection}
        disabled={!canConfirm || busy}
        loading={busy}
      />
      <ActionButton
        label="Return to image review"
        onPress={onCancel}
        disabled={busy}
        variant="secondary"
      />
    </View>
  );
}
