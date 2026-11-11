# Hardware capture protocol

This protocol records a repeatable research setup. It is an engineering procedure, not a clinical acquisition standard.

## Record the setup

For each setup profile, note:

- Phone manufacturer/model and camera lens used.
- Microscope manufacturer/model, objective, and eyepiece.
- Adapter version, mounting position, and any alignment marks.
- Camera resolution and relevant capture settings.
- Slide material authorization and de-identification check.
- Operator role without a personal name in uploaded metadata.

## Capture steps

1. Confirm the slide is authorized for teaching or research use and has no visible identifiers.
2. Secure the phone adapter without loading fragile microscope optics.
3. Align the phone camera with the eyepiece and center the circular field.
4. Reduce vignetting by adjusting the mount; avoid excessive digital zoom.
5. Ask the qualified laboratory partner to select the smear region and focus the microscope.
6. Stabilize the phone and capture a complete field.
7. Repeat ten captures at a documented setup when measuring usable-capture rate.
8. Keep each field labeled as field-level research material. Do not infer that it represents the whole slide.

## Failure observations

| Failure | Possible signal | Action |
| --- | --- | --- |
| Defocus or motion | Weak high-frequency detail or directional blur | Stabilize, refocus, and recapture |
| Over/underexposure | Clipped highlights or very low intensity | Adjust illumination or exposure |
| Vignetting | Dark circular edge or off-center field | Recenter the phone and adjust the adapter |
| Stain or preparation artifact | Morphology is distorted or unassessable | Ask the laboratory reviewer; another capture may not fix it |
| Truncated cell | Cell touches crop boundary | Select another cell and confirm the full cell is visible |

## Device profile

Use hardware/device-profiles/ as a template location. Record observations and authorized test images outside the source repository unless data sharing has been approved. Calibration notes must identify the development threshold values and sample count used.
