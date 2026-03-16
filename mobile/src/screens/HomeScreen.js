/**
 * HomeScreen — NAM SA'
 * Landing screen: logo, language selector, mode cards, voice CTA.
 * Everything fits on screen — no scrolling.
 */

import React, { useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Animated,
  Dimensions,
  Image,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useLanguage } from '../context/LanguageContext';
import { Colors, Typography, Spacing, BorderRadius, Shadows } from '../theme';

const { width: SCREEN_W } = Dimensions.get('window');

const MODES = [
  { id: 'Dictionary', icon: 'book-outline', titleKey: 'translate', subKey: 'translateSub', color: Colors.sky },
  { id: 'Dialogue', icon: 'mic-outline', titleKey: 'dialogue', subKey: 'dialogueSub', color: Colors.secondary },
  { id: 'Proverbs', icon: 'leaf-outline', titleKey: 'proverbs', subKey: 'proverbsSub', color: Colors.earth },
  { id: 'Tutor', icon: 'school-outline', titleKey: 'tutor', subKey: 'tutorSub', color: Colors.accent },
];

const CARD_W = (SCREEN_W - Spacing.lg * 2 - Spacing.sm) / 2;

export default function HomeScreen({ navigation }) {
  const insets = useSafeAreaInsets();
  const { lang, switchLanguage, t } = useLanguage();

  // Mic button pulse
  const pulseAnim = useRef(new Animated.Value(1)).current;
  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, { toValue: 1.08, duration: 1500, useNativeDriver: true }),
        Animated.timing(pulseAnim, { toValue: 1, duration: 1500, useNativeDriver: true }),
      ])
    ).start();
  }, []);

  return (
    <View style={[styles.container, { paddingTop: insets.top + Spacing.sm }]}>
      {/* === LANGUAGE SELECTOR === */}
      <View style={styles.langBar}>
        <TouchableOpacity
          style={[styles.langBtn, lang === 'fr' && styles.langBtnActive]}
          onPress={() => switchLanguage('fr')}
        >
          <Text style={[styles.langText, lang === 'fr' && styles.langTextActive]}>FR</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.langBtn, lang === 'en' && styles.langBtnActive]}
          onPress={() => switchLanguage('en')}
        >
          <Text style={[styles.langText, lang === 'en' && styles.langTextActive]}>EN</Text>
        </TouchableOpacity>
      </View>

      {/* === HERO === */}
      <View style={styles.heroSection}>
        <Image
          source={require('../../assets/playstore.png')}
          style={styles.logo}
          resizeMode="contain"
        />
        <Text style={styles.appName}>NAM SA'</Text>
        <Text style={styles.appSubtitle}>{t('appSubtitle')}</Text>
      </View>

      {/* === MODE GRID === */}
      <View style={styles.modeGrid}>
        {MODES.map((mode) => (
          <TouchableOpacity
            key={mode.id}
            style={[styles.modeCard, { borderLeftColor: mode.color }]}
            onPress={() => navigation.navigate(mode.id)}
            activeOpacity={0.7}
          >
            <Ionicons name={mode.icon} size={28} color={mode.color} />
            <Text style={styles.modeTitle}>{t(mode.titleKey)}</Text>
            <Text style={styles.modeSubtitle}>{t(mode.subKey)}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* === VOICE CTA === */}
      <View style={styles.ctaSection}>
        <Animated.View style={{ transform: [{ scale: pulseAnim }] }}>
          <TouchableOpacity
            style={styles.voiceButton}
            onPress={() => navigation.navigate('Dialogue')}
            activeOpacity={0.8}
          >
            <View style={styles.voiceButtonInner}>
              <Ionicons name="mic" size={32} color={Colors.textOnPrimary} />
            </View>
          </TouchableOpacity>
        </Animated.View>
        <Text style={styles.ctaText}>{t('tapToSpeak')}</Text>
        <TouchableOpacity
          onPress={() => navigation.navigate('Chat')}
          style={styles.chatLink}
          hitSlop={{ top: 8, bottom: 8, left: 16, right: 16 }}
        >
          <Ionicons name="chatbubble-ellipses-outline" size={16} color={Colors.textMuted} />
          <Text style={styles.chatLinkText}>{t('chatMode')}</Text>
        </TouchableOpacity>
      </View>
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
    paddingHorizontal: Spacing.lg,
  },

  // --- Language selector ---
  langBar: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: Spacing.xs,
    marginBottom: Spacing.sm,
  },
  langBtn: {
    paddingHorizontal: 14,
    paddingVertical: 7,
    borderRadius: BorderRadius.full,
    backgroundColor: Colors.card,
    ...Shadows.sm,
  },
  langBtnActive: { backgroundColor: Colors.primary },
  langText: { ...Typography.labelSmall, color: Colors.textSecondary },
  langTextActive: { color: Colors.textOnPrimary },

  // --- Hero ---
  heroSection: {
    alignItems: 'center',
    marginBottom: Spacing.lg,
  },
  logo: {
    width: 90,
    height: 90,
    marginBottom: Spacing.xs,
  },
  appName: {
    ...Typography.displayLarge,
    fontSize: 34,
    color: Colors.primary,
    textAlign: 'center',
  },
  appSubtitle: {
    ...Typography.bodyLarge,
    color: Colors.secondary,
    fontStyle: 'italic',
    marginTop: Spacing.xs,
  },

  // --- Mode Grid ---
  modeGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Spacing.sm,
  },
  modeCard: {
    width: CARD_W,
    backgroundColor: Colors.card,
    borderRadius: BorderRadius.lg,
    padding: Spacing.md,
    borderLeftWidth: 3,
    ...Shadows.sm,
  },
  modeTitle: {
    ...Typography.h3,
    color: Colors.textPrimary,
    marginTop: Spacing.xs,
  },
  modeSubtitle: {
    ...Typography.caption,
    color: Colors.textMuted,
    marginTop: 2,
  },

  // --- Voice CTA ---
  ctaSection: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  voiceButton: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: Colors.secondary,
    justifyContent: 'center',
    alignItems: 'center',
    ...Shadows.glow,
  },
  voiceButtonInner: {
    width: 84,
    height: 84,
    borderRadius: 42,
    backgroundColor: Colors.secondaryLight,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 3,
    borderColor: 'rgba(255,255,255,0.3)',
  },
  ctaText: {
    ...Typography.h3,
    color: Colors.textPrimary,
    marginTop: Spacing.md,
  },
  chatLink: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: Spacing.sm,
    paddingVertical: 6,
  },
  chatLinkText: {
    ...Typography.caption,
    color: Colors.textMuted,
  },
});
