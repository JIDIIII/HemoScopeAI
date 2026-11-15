export function validateImageInput(input: {
  mimeType?: string | null;
  fileName?: string | null;
  fileSize?: number;
  width: number;
  height: number;
}): string {
  const extension = input.fileName?.split(".").pop()?.toLowerCase();
  const mime =
    input.mimeType ??
    (
      {
        jpg: "image/jpeg",
        jpeg: "image/jpeg",
        png: "image/png",
        webp: "image/webp",
      } as Record<string, string>
    )[extension ?? ""];
  if (!mime || !["image/jpeg", "image/png", "image/webp"].includes(mime))
    throw new Error("Unsupported image format. Choose JPEG, PNG, or WebP.");
  if (input.fileSize != null && input.fileSize > 10 * 1024 * 1024)
    throw new Error("This image exceeds 10 MB. Choose a smaller image.");
  if (
    !Number.isFinite(input.width) ||
    !Number.isFinite(input.height) ||
    input.width <= 0 ||
    input.height <= 0
  )
    throw new Error(
      "This file has invalid image dimensions. Choose another image.",
    );
  return mime;
}
