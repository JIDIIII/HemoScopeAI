export const colors = {
  navy: "#0B172A",
  teal: "#0E9997",
  white: "#FFFFFF",
  background: "#F3F6F8",
  lightGray: "#E9EEF2",
  muted: "#64748B",
  border: "#DCE4E9",
  error: "#A43737",
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 20,
  xl: 28,
  xxl: 40,
};

export const radii = {
  md: 14,
  lg: 20,
  pill: 999,
};

export const typography = {
  eyebrow: {
    color: colors.teal,
    fontSize: 12,
    fontWeight: "800" as const,
    letterSpacing: 1.4,
  },
  title: {
    color: colors.navy,
    fontSize: 30,
    lineHeight: 36,
    fontWeight: "800" as const,
  },
  sectionTitle: {
    color: colors.navy,
    fontSize: 17,
    lineHeight: 22,
    fontWeight: "700" as const,
  },
  body: {
    color: colors.navy,
    fontSize: 15,
    lineHeight: 23,
  },
  caption: {
    color: colors.muted,
    fontSize: 12,
    lineHeight: 18,
  },
  button: {
    color: colors.white,
    fontSize: 15,
    fontWeight: "700" as const,
  },
  error: {
    color: colors.error,
    fontSize: 14,
    lineHeight: 21,
  },
};
