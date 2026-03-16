/**
 * ProverbsScreen — NAM SA'
 * Browse Bamiléké proverbs by category.
 * Translate to Ghomala', listen (TTS), or ask NAM SA' about a proverb.
 */

import React, { useState, useCallback } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, FlatList, ScrollView,
  ActivityIndicator, Dimensions,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useLanguage } from '../context/LanguageContext';
import { translate as apiTranslate } from '../services/api';
import { speak as ttsSpeak, stopSpeaking } from '../services/tts';
import { PROVERB_CATEGORIES } from '../data/proverbs';
import { Colors, Typography, Spacing, BorderRadius, Shadows } from '../theme';

const { width: SCREEN_W } = Dimensions.get('window');

export default function ProverbsScreen({ navigation }) {
  const insets = useSafeAreaInsets();
  const { lang, t } = useLanguage();

  const [selectedCat, setSelectedCat] = useState(PROVERB_CATEGORIES[0].id);
  const [expandedProverb, setExpandedProverb] = useState(null);
  const [ghomalaTranslations, setGhomalaTranslations] = useState({});
  const [translating, setTranslating] = useState(null);
  const [playingId, setPlayingId] = useState(null);

  const currentCategory = PROVERB_CATEGORIES.find((c) => c.id === selectedCat);

  const translateToGhomala = useCallback(async (proverbId, text) => {
    setTranslating(proverbId);
    try {
      const result = await apiTranslate(text, lang === 'en' ? 'en' : 'fr', 'bbj');
      setGhomalaTranslations((prev) => ({ ...prev, [proverbId]: result.translation || '' }));
    } catch {
      setGhomalaTranslations((prev) => ({ ...prev, [proverbId]: '...' }));
    }
    setTranslating(null);
  }, [lang]);

  const playAudio = useCallback((text, ttsLang, id) => {
    if (playingId === id) { stopSpeaking(); setPlayingId(null); return; }
    ttsSpeak(text, ttsLang, {
      onStart: () => setPlayingId(id),
      onDone: () => setPlayingId(null),
      onError: () => setPlayingId(null),
    });
  }, [playingId]);

  const askAboutProverb = useCallback((proverb) => {
    const question = lang === 'en'
      ? `Tell me more about this Bamiléké proverb and its cultural context: "${proverb.en}"`
      : `Parle-moi de ce proverbe Bamiléké et de son contexte culturel : "${proverb.fr}"`;
    navigation.navigate('Chat', { initialMessage: question });
  }, [lang, navigation]);

  const renderProverb = ({ item }) => {
    const isExpanded = expandedProverb === item.id;
    const ghomala = ghomalaTranslations[item.id];
    const proverbText = lang === 'en' ? item.en : item.fr;
    const meaningText = lang === 'en' ? item.meaningEn : item.meaningFr;

    return (
      <TouchableOpacity
        style={[styles.proverbCard, isExpanded && styles.proverbCardExpanded]}
        onPress={() => setExpandedProverb(isExpanded ? null : item.id)}
        activeOpacity={0.7}
      >
        {/* Proverb text */}
        <Text style={styles.proverbText}>« {proverbText} »</Text>

        {isExpanded && (
          <View style={styles.proverbDetails}>
            {/* Meaning */}
            <View style={styles.meaningBox}>
              <Text style={styles.meaningLabel}>{t('proverbMeaning')}</Text>
              <Text style={styles.meaningText}>{meaningText}</Text>
            </View>

            {/* Ghomala' translation */}
            {ghomala ? (
              <View style={styles.ghomalaBox}>
                <Text style={styles.ghomalaLabel}>Ghomala'</Text>
                <Text style={styles.ghomalaText}>{ghomala}</Text>
                <TouchableOpacity
                  style={styles.actionBtn}
                  onPress={() => playAudio(ghomala, 'bbj', `${item.id}_gh`)}
                >
                  <Ionicons
                    name={playingId === `${item.id}_gh` ? 'volume-high' : 'volume-medium-outline'}
                    size={18} color={Colors.secondary}
                  />
                  <Text style={styles.actionBtnText}>{t('listen')}</Text>
                </TouchableOpacity>
              </View>
            ) : (
              <TouchableOpacity
                style={styles.translateGhomalaBtn}
                onPress={() => translateToGhomala(item.id, proverbText)}
                disabled={translating === item.id}
              >
                {translating === item.id ? (
                  <ActivityIndicator size="small" color={Colors.secondary} />
                ) : (
                  <>
                    <Ionicons name="language" size={18} color={Colors.secondary} />
                    <Text style={styles.translateGhomalaBtnText}>{t('translateToGhomala')}</Text>
                  </>
                )}
              </TouchableOpacity>
            )}

            {/* Action buttons */}
            <View style={styles.actionRow}>
              <TouchableOpacity
                style={styles.actionBtn}
                onPress={() => playAudio(proverbText, lang === 'en' ? 'en' : 'fr', `${item.id}_orig`)}
              >
                <Ionicons
                  name={playingId === `${item.id}_orig` ? 'volume-high' : 'volume-medium-outline'}
                  size={18} color={Colors.accent}
                />
                <Text style={styles.actionBtnText}>{t('listen')}</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.actionBtn, styles.askBtn]}
                onPress={() => askAboutProverb(item)}
              >
                <Ionicons name="chatbubble-outline" size={18} color={Colors.primary} />
                <Text style={[styles.actionBtnText, { color: Colors.primary }]}>{t('askAbout')}</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}
      </TouchableOpacity>
    );
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={22} color={Colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>{t('proverbs')}</Text>
        <View style={{ width: 40 }} />
      </View>

      {/* Category Tabs */}
      <ScrollView
        horizontal showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.catRow}
      >
        {PROVERB_CATEGORIES.map((cat) => {
          const isActive = selectedCat === cat.id;
          return (
            <TouchableOpacity
              key={cat.id}
              style={[styles.catTab, isActive && { backgroundColor: cat.color }]}
              onPress={() => { setSelectedCat(cat.id); setExpandedProverb(null); }}
            >
              <Text style={styles.catEmoji}>{cat.emoji}</Text>
              <Text style={[styles.catLabel, isActive && styles.catLabelActive]}>{t(cat.titleKey)}</Text>
            </TouchableOpacity>
          );
        })}
      </ScrollView>

      {/* Proverbs List */}
      <FlatList
        data={currentCategory?.proverbs || []}
        renderItem={renderProverb}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
      />

      <View style={{ height: insets.bottom }} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  // Header
  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: Spacing.md, paddingVertical: Spacing.sm,
  },
  backBtn: {
    width: 40, height: 40, borderRadius: 20,
    backgroundColor: Colors.card, justifyContent: 'center', alignItems: 'center', ...Shadows.sm,
  },
  headerTitle: { ...Typography.h2, color: Colors.primary },
  // Category tabs
  catRow: { paddingHorizontal: Spacing.md, gap: Spacing.sm, paddingBottom: Spacing.md },
  catTab: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    paddingHorizontal: 14, paddingVertical: 10,
    borderRadius: BorderRadius.full, backgroundColor: Colors.card, ...Shadows.sm,
  },
  catEmoji: { fontSize: 18 },
  catLabel: { ...Typography.labelSmall, color: Colors.textSecondary },
  catLabelActive: { color: Colors.textOnPrimary },
  // Proverb list
  listContent: { paddingHorizontal: Spacing.md, paddingBottom: Spacing.xl },
  proverbCard: {
    backgroundColor: Colors.card, borderRadius: BorderRadius.lg,
    padding: Spacing.md, marginBottom: Spacing.md,
    borderLeftWidth: 3, borderLeftColor: Colors.secondary, ...Shadows.sm,
  },
  proverbCardExpanded: { borderLeftColor: Colors.primary, ...Shadows.md },
  proverbText: {
    ...Typography.bodyLarge, color: Colors.textPrimary,
    fontStyle: 'italic', lineHeight: 26,
  },
  // Details
  proverbDetails: { marginTop: Spacing.md },
  meaningBox: {
    backgroundColor: Colors.backgroundAlt, borderRadius: BorderRadius.md,
    padding: Spacing.sm, marginBottom: Spacing.sm,
  },
  meaningLabel: { ...Typography.labelSmall, color: Colors.textMuted, marginBottom: 4 },
  meaningText: { ...Typography.body, color: Colors.textSecondary },
  ghomalaBox: {
    backgroundColor: Colors.sand, borderRadius: BorderRadius.md,
    padding: Spacing.sm, marginBottom: Spacing.sm,
  },
  ghomalaLabel: { ...Typography.labelSmall, color: Colors.earth, marginBottom: 4 },
  ghomalaText: { ...Typography.bodyLarge, color: Colors.primary, fontWeight: '600' },
  translateGhomalaBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    backgroundColor: Colors.sand, borderRadius: BorderRadius.full,
    paddingHorizontal: 14, paddingVertical: 10, alignSelf: 'flex-start',
    marginBottom: Spacing.sm,
  },
  translateGhomalaBtnText: { ...Typography.labelSmall, color: Colors.secondary },
  // Actions
  actionRow: { flexDirection: 'row', gap: Spacing.sm, marginTop: Spacing.xs },
  actionBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 4,
    paddingHorizontal: 12, paddingVertical: 8, borderRadius: BorderRadius.full,
    backgroundColor: Colors.backgroundAlt,
  },
  askBtn: { backgroundColor: Colors.sand },
  actionBtnText: { ...Typography.caption, color: Colors.accent },
});
