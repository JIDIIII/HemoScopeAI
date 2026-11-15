export type Bounds = { x: number; y: number; width: number; height: number };
const clamp = (value: number, min: number, max: number) =>
  Math.max(min, Math.min(value, max));
export function moveCrop(start: Bounds, dx: number, dy: number): Bounds {
  return {
    ...start,
    x: clamp(start.x + dx, 0, 1 - start.width),
    y: clamp(start.y + dy, 0, 1 - start.height),
  };
}
export function resizeCrop(start: Bounds, dx: number, dy: number): Bounds {
  return {
    ...start,
    width: clamp(start.width + dx, 0.05, 1 - start.x),
    height: clamp(start.height + dy, 0.05, 1 - start.y),
  };
}
export function pixelCrop(bounds: Bounds, width: number, height: number) {
  if (
    ![width, height].every((n) => Number.isInteger(n) && n > 0) ||
    !Object.values(bounds).every(Number.isFinite) ||
    bounds.x < 0 ||
    bounds.y < 0 ||
    bounds.width <= 0 ||
    bounds.height <= 0 ||
    bounds.x + bounds.width > 1.000001 ||
    bounds.y + bounds.height > 1.000001
  )
    throw new Error("Select a valid region inside the image.");
  const originX = Math.min(width - 1, Math.floor(bounds.x * width));
  const originY = Math.min(height - 1, Math.floor(bounds.y * height));
  return {
    originX,
    originY,
    width: Math.max(
      1,
      Math.min(width - originX, Math.round(bounds.width * width)),
    ),
    height: Math.max(
      1,
      Math.min(height - originY, Math.round(bounds.height * height)),
    ),
  };
}

export type CropCorner = "topLeft" | "topRight" | "bottomLeft" | "bottomRight";
export function resizeFromCorner(
  start: Bounds,
  dx: number,
  dy: number,
  corner: CropCorner,
): Bounds {
  const left = corner === "topLeft" || corner === "bottomLeft";
  const top = corner === "topLeft" || corner === "topRight";
  const x = left
    ? clamp(start.x + dx, 0, start.x + start.width - 0.05)
    : start.x;
  const y = top
    ? clamp(start.y + dy, 0, start.y + start.height - 0.05)
    : start.y;
  const right = left
    ? start.x + start.width
    : clamp(start.x + start.width + dx, start.x + 0.05, 1);
  const bottom = top
    ? start.y + start.height
    : clamp(start.y + start.height + dy, start.y + 0.05, 1);
  return { x, y, width: right - x, height: bottom - y };
}
