export const colors = {
  navy: "#102D47",
  primaryButton: "#172941",
  primaryButtonDisabled: "#59708A",
  teal: "#107D78",
  aqua: "#25D9CF",
  white: "#FFFFFF",
  background: "#FFFFFF",
  lightGray: "#F1F6F7",
  muted: "#7185A1",
  border: "#D6E5E9",
  error: "#A43737",
  mint: "#DEF4F1",
  pale: "#EEF8F7",
};
export const spacing = { xs: 4, sm: 8, md: 12, lg: 20, xl: 28, xxl: 40 };
export const radii = { md: 13, lg: 17, pill: 999 };
export const typography = {
  eyebrow: {
    color: colors.teal,
    fontSize: 10,
    fontWeight: "700" as const,
    letterSpacing: 1.4,
  },
  title: {
    color: colors.navy,
    fontSize: 24,
    lineHeight: 30,
    fontWeight: "400" as const,
    letterSpacing: -0.7,
  },
  sectionTitle: {
    color: colors.navy,
    fontSize: 17,
    lineHeight: 24,
    fontWeight: "500" as const,
  },
  body: { color: colors.navy, fontSize: 14, lineHeight: 22 },
  caption: { color: colors.muted, fontSize: 11, lineHeight: 17 },
  button: { color: colors.white, fontSize: 13, fontWeight: "600" as const },
  error: { color: colors.error, fontSize: 13, lineHeight: 20 },
};
