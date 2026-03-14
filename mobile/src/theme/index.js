/**
 * NAM SA' Design Theme
 * "Le soleil s'est levé" — Colors from the official logo
 *
 * Color Palette:
 * - Maroon (#7A2E1E)   : Primary — text & headings from logo
 * - Sun Gold (#E8A020)  : Secondary — sun rays, CTAs, active states
 * - Forest Green (#2D7A3A) : Accent — leaves, success states
 * - Sky Blue (#A8D8EA)  : Background — sky, calm surfaces
 * - Terracotta (#A0522D): Earth — warm surfaces, cards
 * - Cream (#FFF8F0)     : Surface — main backgrounds
 */

export const Colors = {
  // === PRIMARY — Dark Maroon (from "NAM SA'" text) ===
  primary: '#7A2E1E',
  primaryLight: '#9E4A3A',
  primaryDark: '#5C1A10',

  // === SECONDARY — Sun Gold (from sun illustration) ===
  secondary: '#E8A020',
  secondaryLight: '#F5C04A',
  secondaryDark: '#C88010',

  // === ACCENT — Forest Green (from banana leaves) ===
  accent: '#2D7A3A',
  accentLight: '#4AA55A',
  accentDark: '#1B5A28',

  // === SKY — Light Blue (from sky background) ===
  sky: '#A8D8EA',
  skyLight: '#C8E8F5',
  skyDark: '#7ABCD5',

  // === EARTH — Terracotta (from ground) ===
  earth: '#A0522D',
  earthLight: '#C87A50',
  earthDark: '#7A3A1A',

  // === NEUTRALS ===
  cream: '#FFF8F0',
  warmWhite: '#FFFDF9',
  sand: '#F5E6D0',
  stone: '#D4C4B0',
  bark: '#6B5A4A',
  charcoal: '#2C2420',
  
  // === SEMANTIC ===
  success: '#2D7A3A',
  error: '#D04040',
  warning: '#E8A020',
  info: '#5A9EC8',

  // === TEXT ===
  textPrimary: '#2C2420',
  textSecondary: '#6B5A4A',
  textMuted: '#9A8A7A',
  textOnPrimary: '#FFFFFF',
  textOnSecondary: '#2C2420',
  textOnAccent: '#FFFFFF',

  // === BACKGROUNDS ===
  background: '#FFF8F0',
  backgroundAlt: '#F5E6D0',
  card: '#FFFFFF',
  cardElevated: '#FFFDF9',
  overlay: 'rgba(44, 36, 32, 0.6)',

  // === VOICE UI ===
  voiceActive: '#E8A020',
  voiceInactive: '#D4C4B0',
  voiceWave: '#2D7A3A',
  voicePulse: 'rgba(232, 160, 32, 0.3)',
};

export const Typography = {
  // Display — for hero text, app name
  displayLarge: {
    fontSize: 36,
    fontWeight: '800',
    letterSpacing: -0.5,
    lineHeight: 44,
  },
  displayMedium: {
    fontSize: 28,
    fontWeight: '700',
    letterSpacing: -0.3,
    lineHeight: 36,
  },
  // Headings
  h1: { fontSize: 24, fontWeight: '700', lineHeight: 32 },
  h2: { fontSize: 20, fontWeight: '600', lineHeight: 28 },
  h3: { fontSize: 18, fontWeight: '600', lineHeight: 24 },
  // Body
  bodyLarge: { fontSize: 17, fontWeight: '400', lineHeight: 26 },
  body: { fontSize: 15, fontWeight: '400', lineHeight: 22 },
  bodySmall: { fontSize: 13, fontWeight: '400', lineHeight: 18 },
  // Labels
  label: { fontSize: 14, fontWeight: '600', lineHeight: 20, letterSpacing: 0.3 },
  labelSmall: { fontSize: 12, fontWeight: '600', lineHeight: 16, letterSpacing: 0.5 },
  // Caption
  caption: { fontSize: 12, fontWeight: '400', lineHeight: 16 },
};

export const Spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
  xxxl: 64,
};

export const BorderRadius = {
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  full: 9999,
};

export const Shadows = {
  sm: {
    shadowColor: '#2C2420',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 2,
  },
  md: {
    shadowColor: '#2C2420',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.12,
    shadowRadius: 12,
    elevation: 4,
  },
  lg: {
    shadowColor: '#2C2420',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.16,
    shadowRadius: 24,
    elevation: 8,
  },
  glow: {
    shadowColor: '#E8A020',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.4,
    shadowRadius: 20,
    elevation: 8,
  },
};
