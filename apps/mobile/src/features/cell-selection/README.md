# Cell selection

`CellCropSelector` provides drag/resize bounds constrained to the displayed image, generates a separate JPEG with Expo ImageManipulator, previews it and requires explicit complete-cell confirmation. `geometry.ts` maps normalized bounds to original pixels and rejects invalid bounds. The original URI remains on the crop screen for replacement. The user, not this component, verifies that one complete white blood cell is present. Device gesture/orientation verification is pending.
