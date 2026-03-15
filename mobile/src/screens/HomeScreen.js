/**
 * HomeScreen — NAM SA'
 * Landing screen with logo, sun animation, mode selector and voice CTA.
 * Adapts to all screen sizes (small phones to tablets).
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Animated,
  Dimensions,
  Image,
  ScrollView,
  Platform,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { Colors, Typography, Spacing, BorderRadius, Shadows } from '../theme';

const { width: SCREEN_W, height: SCREEN_H } = Dimensions.get('window');
const isSmallScreen = SCREEN_H < 700;
const isTablet = SCREEN_W >= 768;

// Conversation modes
const MODES = [
  {
    id: 'tutor',
    iconName: 'book-outline',
    iconSet: 'Ionicons',
    title: 'Tuteur',
    subtitle: 'Apprendre le Ghomala\'',
    color: Colors.accent,
  },
  {
    id: 'conversation',
    iconName: 'chatbubbles-outline',
    iconSet: 'Ionicons',
    title: 'Dialogue',
    subtitle: 'Conversation libre',
    color: Colors.secondary,
  },
  {
    id: 'proverb',
    iconName: 'leaf-outline',
    iconSet: 'Ionicons',
    title: 'Proverbes',
    subtitle: 'Sagesse Bamiléké',
    color: Colors.earth,
  },
  {
    id: 'translate',
    iconName: 'swap-horizontal',
    iconSet: 'Ionicons',
    title: 'Traduire',
    subtitle: 'FR ↔ Ghomala\'',
    color: Colors.sky,
  },
];

const ModeIcon = ({ mode, size = 24, color }) => {
  if (mode.iconSet === 'MaterialCommunityIcons') {
    return <MaterialCommunityIcons name={mode.iconName} size={size} color={color} />;
  }
  return <Ionicons name={mode.iconName} size={size} color={color} />;
};

export default function HomeScreen({ navigation }) {
  const insets = useSafeAreaInsets();
  const [selectedMode, setSelectedMode] = useState('tutor');

  // Animations
  const sunRotate = useRef(new Animated.Value(0)).current;
  const fadeIn = useRef(new Animated.Value(0)).current;
  const slideUp = useRef(new Animated.Value(30)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    // Sun glow pulse
    Animated.loop(
      Animated.sequence([
        Animated.timing(sunRotate, {
          toValue: 1,
          duration: 8000,
          useNativeDriver: true,
        }),
        Animated.timing(sunRotate, {
          toValue: 0,
          duration: 8000,
          useNativeDriver: true,
        }),
      ])
    ).start();

    // Entrance animations
    Animated.parallel([
      Animated.timing(fadeIn, {
        toValue: 1,
        duration: 800,
        useNativeDriver: true,
      }),
      Animated.timing(slideUp, {
        toValue: 0,
        duration: 800,
        useNativeDriver: true,
      }),
    ]).start();

    // Voice button pulse
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.08,
          duration: 1500,
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 1500,
          useNativeDriver: true,
        }),
      ])
    ).start();
  }, []);

  const sunOpacity = sunRotate.interpolate({
    inputRange: [0, 0.5, 1],
    outputRange: [0.6, 1, 0.6],
  });

  const startConversation = () => {
    navigation.navigate('Conversation', { mode: selectedMode });
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        bounces={true}
      >
        {/* === HERO SECTION === */}
        <Animated.View
          style={[
            styles.heroSection,
            {
              opacity: fadeIn,
              transform: [{ translateY: slideUp }],
            },
          ]}
        >
          {/* Sun glow background */}
          <Animated.View style={[styles.sunGlow, { opacity: sunOpacity }]} />

          {/* Logo */}
          <Image
            source={require('../../assets/logo.png')}
            style={styles.logo}
            resizeMode="contain"
          />

          {/* App name */}
          <Text style={styles.appName}>NAM SA'</Text>
          <Text style={styles.appSubtitle}>Le soleil s'est levé</Text>
          <Text style={styles.appDescription}>
            Préservons le Ghomala' ensemble
          </Text>
        </Animated.View>

        {/* === MODE SELECTOR === */}
        <View style={styles.modeSection}>
          <Text style={styles.sectionTitle}>Choisir un mode</Text>
          <View style={styles.modeGrid}>
            {MODES.map((mode) => (
              <TouchableOpacity
                key={mode.id}
                style={[
                  styles.modeCard,
                  selectedMode === mode.id && styles.modeCardActive,
                  selectedMode === mode.id && { borderColor: mode.color },
                ]}
                onPress={() => setSelectedMode(mode.id)}
                activeOpacity={0.7}
              >
                <ModeIcon mode={mode} size={28} color={selectedMode === mode.id ? mode.color : Colors.textSecondary} />
                <Text
                  style={[
                    styles.modeTitle,
                    selectedMode === mode.id && { color: mode.color },
                  ]}
                >
                  {mode.title}
                </Text>
                <Text style={styles.modeSubtitle}>{mode.subtitle}</Text>
                {selectedMode === mode.id && (
                  <View style={[styles.modeIndicator, { backgroundColor: mode.color }]} />
                )}
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* === VOICE CTA === */}
        <View style={styles.ctaSection}>
          <Animated.View style={{ transform: [{ scale: pulseAnim }] }}>
            <TouchableOpacity
              style={styles.voiceButton}
              onPress={startConversation}
              activeOpacity={0.8}
            >
              <View style={styles.voiceButtonInner}>
                <Ionicons name="mic" size={32} color={Colors.textOnPrimary} />
              </View>
            </TouchableOpacity>
          </Animated.View>
          <Text style={styles.ctaText}>Appuie pour parler</Text>
          <Text style={styles.ctaSubtext}>
            {MODES.find((m) => m.id === selectedMode)?.subtitle}
          </Text>
        </View>

        {/* === QUICK PHRASES === */}
        <View style={styles.phrasesSection}>
          <Text style={styles.sectionTitle}>Essaie de dire...</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            {[
              'Comment dit-on bonjour ?',
              'Apprends-moi à compter',
              'Un proverbe Bamiléké',
              'Comment me présenter ?',
              'Les mots de la famille',
            ].map((phrase, i) => (
              <TouchableOpacity
                key={i}
                style={styles.phraseChip}
                onPress={() =>
                  navigation.navigate('Conversation', {
                    mode: selectedMode,
                    initialMessage: phrase,
                  })
                }
              >
                <Text style={styles.phraseText}>{phrase}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>

        {/* Bottom spacing */}
        <View style={{ height: insets.bottom + 20 }} />
      </ScrollView>
    </View>
  );
}

// ============================================================================
// STYLES — Responsive for all screen sizes
// ============================================================================
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: Spacing.lg,
  },

  // --- Hero ---
  heroSection: {
    alignItems: 'center',
    paddingTop: isSmallScreen ? Spacing.md : Spacing.xl,
    paddingBottom: Spacing.lg,
    position: 'relative',
  },
  sunGlow: {
    position: 'absolute',
    top: isSmallScreen ? -40 : -60,
    width: isTablet ? 400 : 280,
    height: isTablet ? 400 : 280,
    borderRadius: 200,
    backgroundColor: Colors.secondaryLight,
    opacity: 0.15,
  },
  logo: {
    width: isSmallScreen ? 100 : isTablet ? 180 : 140,
    height: isSmallScreen ? 100 : isTablet ? 180 : 140,
    marginBottom: Spacing.md,
  },
  appName: {
    ...Typography.displayLarge,
    fontSize: isSmallScreen ? 32 : isTablet ? 48 : 40,
    color: Colors.primary,
    textAlign: 'center',
  },
  appSubtitle: {
    ...Typography.bodyLarge,
    color: Colors.secondary,
    fontStyle: 'italic',
    marginTop: Spacing.xs,
  },
  appDescription: {
    ...Typography.body,
    color: Colors.textMuted,
    marginTop: Spacing.xs,
  },

  // --- Mode Selector ---
  modeSection: {
    marginTop: Spacing.lg,
  },
  sectionTitle: {
    ...Typography.label,
    color: Colors.textSecondary,
    textTransform: 'uppercase',
    marginBottom: Spacing.md,
  },
  modeGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Spacing.sm,
  },
  modeCard: {
    width: (SCREEN_W - Spacing.lg * 2 - Spacing.sm) / 2,
    backgroundColor: Colors.card,
    borderRadius: BorderRadius.lg,
    padding: Spacing.md,
    borderWidth: 2,
    borderColor: 'transparent',
    position: 'relative',
    overflow: 'hidden',
    ...Shadows.sm,
  },
  modeCardActive: {
    backgroundColor: Colors.warmWhite,
    ...Shadows.md,
  },
  modeIcon: {
    marginBottom: Spacing.xs,
  },
  modeTitle: {
    ...Typography.h3,
    color: Colors.textPrimary,
  },
  modeSubtitle: {
    ...Typography.caption,
    color: Colors.textMuted,
    marginTop: 2,
  },
  modeIndicator: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    height: 3,
    borderBottomLeftRadius: BorderRadius.lg,
    borderBottomRightRadius: BorderRadius.lg,
  },

  // --- Voice CTA ---
  ctaSection: {
    alignItems: 'center',
    marginTop: Spacing.xl,
    paddingVertical: Spacing.lg,
  },
  voiceButton: {
    width: isSmallScreen ? 90 : isTablet ? 130 : 110,
    height: isSmallScreen ? 90 : isTablet ? 130 : 110,
    borderRadius: 100,
    backgroundColor: Colors.secondary,
    justifyContent: 'center',
    alignItems: 'center',
    ...Shadows.glow,
  },
  voiceButtonInner: {
    width: isSmallScreen ? 75 : isTablet ? 110 : 92,
    height: isSmallScreen ? 75 : isTablet ? 110 : 92,
    borderRadius: 100,
    backgroundColor: Colors.secondaryLight,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 3,
    borderColor: 'rgba(255,255,255,0.3)',
  },
  ctaText: {
    ...Typography.h2,
    color: Colors.textPrimary,
    marginTop: Spacing.md,
  },
  ctaSubtext: {
    ...Typography.body,
    color: Colors.textMuted,
    marginTop: Spacing.xs,
  },

  // --- Quick Phrases ---
  phrasesSection: {
    marginTop: Spacing.xl,
    marginBottom: Spacing.lg,
  },
  phraseChip: {
    backgroundColor: Colors.card,
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm + 2,
    borderRadius: BorderRadius.full,
    marginRight: Spacing.sm,
    borderWidth: 1,
    borderColor: Colors.sand,
    ...Shadows.sm,
  },
  phraseText: {
    ...Typography.body,
    color: Colors.primary,
  },
});
