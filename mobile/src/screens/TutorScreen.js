/**
 * TutorScreen — NAM SA'
 * Learning path: levels → topics → vocabulary cards with TTS.
 * Ghomala' translations fetched via API on demand.
 */

import React, { useState, useCallback } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, FlatList,
  ActivityIndicator, Dimensions,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useLanguage } from '../context/LanguageContext';
import { translate as apiTranslate } from '../services/api';
import { speak as ttsSpeak, stopSpeaking } from '../services/tts';
import { LEVELS } from '../data/vocabulary';
import { Colors, Typography, Spacing, BorderRadius, Shadows } from '../theme';

const { width: SCREEN_W } = Dimensions.get('window');
const CARD_W = (SCREEN_W - Spacing.lg * 2 - Spacing.sm) / 2;

export default function TutorScreen({ navigation }) {
  const insets = useSafeAreaInsets();
  const { lang, t } = useLanguage();

  const [selectedLevel, setSelectedLevel] = useState('basic');
  const [openTopic, setOpenTopic] = useState(null);
  const [ghomalaCache, setGhomalaCache] = useState({});
  const [translatingWord, setTranslatingWord] = useState(null);
  const [playingId, setPlayingId] = useState(null);

  const currentLevel = LEVELS.find((l) => l.id === selectedLevel);

  const translateWord = useCallback(async (word) => {
    const sourceText = lang === 'en' ? word.en : word.fr;
    const key = `${word.fr}_${word.en}`;
    if (ghomalaCache[key] && ghomalaCache[key] !== '…') return;
    setTranslatingWord(key);
    try {
      const result = await apiTranslate(sourceText, lang === 'en' ? 'en' : 'fr', 'bbj');
      const translation = result.translation?.trim();
      setGhomalaCache((prev) => ({ ...prev, [key]: translation || '?' }));
    } catch (err) {
      console.warn('Translate error:', sourceText, err.message);
      // Don't cache permanently — set temporary marker so user can retry
      setGhomalaCache((prev) => ({ ...prev, [key]: '…' }));
    }
    setTranslatingWord(null);
  }, [lang, ghomalaCache]);

  const playAudio = useCallback((text, ttsLang, id) => {
    if (playingId === id) { stopSpeaking(); setPlayingId(null); return; }
    ttsSpeak(text, ttsLang, {
      onStart: () => setPlayingId(id),
      onDone: () => setPlayingId(null),
      onError: () => setPlayingId(null),
    });
  }, [playingId]);

  // Render a word card
  const renderWordCard = (word, topicId, idx) => {
    const key = `${word.fr}_${word.en}`;
    const ghomala = ghomalaCache[key];
    const isTranslating = translatingWord === key;
    const wordLabel = lang === 'en' ? word.en : word.fr;

    return (
      <TouchableOpacity
        key={`${topicId}_${idx}`}
        style={styles.wordCard}
        onPress={() => !ghomala && translateWord(word)}
        activeOpacity={0.7}
      >
        <Text style={styles.wordEmoji}>{word.emoji}</Text>
        <Text style={styles.wordLabel}>{wordLabel}</Text>

        {isTranslating ? (
          <ActivityIndicator size="small" color={Colors.secondary} style={{ marginTop: 4 }} />
        ) : ghomala ? (
          <View style={styles.ghomalaRow}>
            <Text style={styles.ghomalaWord}>{ghomala}</Text>
            <TouchableOpacity
              onPress={() => playAudio(ghomala, 'bbj', `${topicId}_${idx}`)}
              hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
            >
              <Ionicons
                name={playingId === `${topicId}_${idx}` ? 'volume-high' : 'volume-medium-outline'}
                size={18} color={Colors.secondary}
              />
            </TouchableOpacity>
          </View>
        ) : (
          <Text style={styles.tapHint}>{t('tapToTranslate')}</Text>
        )}
      </TouchableOpacity>
    );
  };

  // Render a topic section
  const renderTopic = ({ item: topic }) => {
    const isOpen = openTopic === topic.id;
    return (
      <View style={styles.topicSection}>
        <TouchableOpacity
          style={[styles.topicHeader, isOpen && { borderBottomColor: currentLevel.color }]}
          onPress={() => setOpenTopic(isOpen ? null : topic.id)}
          activeOpacity={0.7}
        >
          <Text style={styles.topicEmoji}>{topic.emoji}</Text>
          <View style={{ flex: 1 }}>
            <Text style={styles.topicTitle}>{t(topic.titleKey)}</Text>
            <Text style={styles.topicCount}>{topic.words.length} {t('topicWords')}</Text>
          </View>
          <Ionicons
            name={isOpen ? 'chevron-up' : 'chevron-down'}
            size={20} color={Colors.textMuted}
          />
        </TouchableOpacity>

        {isOpen && (
          <View style={styles.wordsGrid}>
            {topic.words.map((word, idx) => renderWordCard(word, topic.id, idx))}
          </View>
        )}
      </View>
    );
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={22} color={Colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>{t('tutor')}</Text>
        <View style={{ width: 40 }} />
      </View>

      {/* Level Tabs */}
      <View style={styles.levelRow}>
        {LEVELS.map((level) => {
          const isActive = selectedLevel === level.id;
          return (
            <TouchableOpacity
              key={level.id}
              style={[styles.levelTab, isActive && { backgroundColor: level.color }]}
              onPress={() => { setSelectedLevel(level.id); setOpenTopic(null); }}
            >
              <Text style={styles.levelIcon}>{level.icon}</Text>
              <Text style={[styles.levelLabel, isActive && styles.levelLabelActive]}>
                {t(level.titleKey)}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>

      {/* Topics */}
      <FlatList
        data={currentLevel?.topics || []}
        renderItem={renderTopic}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.topicList}
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
  // Level tabs
  levelRow: {
    flexDirection: 'row', paddingHorizontal: Spacing.md, gap: Spacing.sm,
    marginBottom: Spacing.md,
  },
  levelTab: {
    flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    gap: 6, paddingVertical: 12, borderRadius: BorderRadius.full,
    backgroundColor: Colors.card, ...Shadows.sm,
  },
  levelIcon: { fontSize: 16 },
  levelLabel: { ...Typography.labelSmall, color: Colors.textSecondary },
  levelLabelActive: { color: Colors.textOnPrimary },
  // Topic list
  topicList: { paddingHorizontal: Spacing.md, paddingBottom: Spacing.xl },
  topicSection: { marginBottom: Spacing.md },
  topicHeader: {
    flexDirection: 'row', alignItems: 'center', gap: Spacing.sm,
    backgroundColor: Colors.card, borderRadius: BorderRadius.lg,
    padding: Spacing.md, borderBottomWidth: 3, borderBottomColor: 'transparent',
    ...Shadows.sm,
  },
  topicEmoji: { fontSize: 28 },
  topicTitle: { ...Typography.h3, color: Colors.textPrimary },
  topicCount: { ...Typography.caption, color: Colors.textMuted },
  // Words grid
  wordsGrid: {
    flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.sm,
    paddingTop: Spacing.sm, paddingHorizontal: Spacing.xs,
  },
  wordCard: {
    width: CARD_W, backgroundColor: Colors.warmWhite,
    borderRadius: BorderRadius.md, padding: Spacing.sm,
    alignItems: 'center', borderWidth: 1, borderColor: Colors.sand,
  },
  wordEmoji: { fontSize: 32, marginBottom: 4 },
  wordLabel: { ...Typography.label, color: Colors.textPrimary, textAlign: 'center' },
  ghomalaRow: {
    flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 4,
  },
  ghomalaWord: {
    ...Typography.body, color: Colors.primary, fontWeight: '600', textAlign: 'center',
  },
  tapHint: { ...Typography.caption, color: Colors.textMuted, fontStyle: 'italic', marginTop: 4 },
});
