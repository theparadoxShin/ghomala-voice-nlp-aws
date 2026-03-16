/**
 * DictionaryScreen — NAM SA'
 * Google Translate-style interface: 2 text boxes, language picker modal, TTS via device Speech.
 */

import React, { useState, useCallback } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, TextInput,
  ActivityIndicator, Platform, KeyboardAvoidingView, Modal, Pressable,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useLanguage } from '../context/LanguageContext';
import { translate as apiTranslate } from '../services/api';
import { speak as ttsSpeak, stopSpeaking } from '../services/tts';
import { Colors, Typography, Spacing, BorderRadius, Shadows } from '../theme';

const LANGUAGES = [
  { code: 'fr', label: 'Français', speech: 'fr-FR' },
  { code: 'en', label: 'English', speech: 'en-US' },
  { code: 'bbj', label: "Ghomala'", speech: 'fr-FR' },
];

export default function DictionaryScreen({ navigation }) {
  const insets = useSafeAreaInsets();
  const { t, lang } = useLanguage();

  const [sourceLang, setSourceLang] = useState('fr');
  const [targetLang, setTargetLang] = useState('bbj');
  const [sourceText, setSourceText] = useState('');
  const [translatedText, setTranslatedText] = useState('');
  const [loading, setLoading] = useState(false);
  const [speaking, setSpeaking] = useState(null); // 'src' | 'tgt' | null
  const [pickerTarget, setPickerTarget] = useState(null); // 'source' | 'target' | null

  const handleSwap = () => {
    setSourceLang(targetLang);
    setTargetLang(sourceLang);
    setSourceText(translatedText);
    setTranslatedText(sourceText);
  };

  const selectLanguage = (code) => {
    if (pickerTarget === 'source') {
      if (code === targetLang) setTargetLang(sourceLang);
      setSourceLang(code);
    } else {
      if (code === sourceLang) setSourceLang(targetLang);
      setTargetLang(code);
    }
    setPickerTarget(null);
  };

  const handleTranslate = useCallback(async () => {
    if (!sourceText.trim()) return;
    setLoading(true);
    try {
      const result = await apiTranslate(sourceText.trim(), sourceLang, targetLang);
      setTranslatedText(result.translation || '');
    } catch (err) {
      console.warn('Translate error:', err.message);
      setTranslatedText(
        err.message?.includes('429')
          ? (lang === 'en' ? 'Too many requests, please wait...' : 'Trop de requêtes, patientez...')
          : t('error')
      );
    }
    setLoading(false);
  }, [sourceText, sourceLang, targetLang, t]);

  const speak = (text, langCode, id) => {
    if (speaking) { stopSpeaking(); setSpeaking(null); return; }
    ttsSpeak(text, langCode, {
      onStart: () => setSpeaking(id),
      onDone: () => setSpeaking(null),
      onError: () => setSpeaking(null),
    });
  };

  const getLangLabel = (code) => LANGUAGES.find((l) => l.code === code)?.label || code;

  return (
    <KeyboardAvoidingView
      style={[styles.container, { paddingTop: insets.top }]}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={22} color={Colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>{t('translate')}</Text>
        <View style={{ width: 40 }} />
      </View>

      {/* Language Selector Row */}
      <View style={styles.langRow}>
        <TouchableOpacity
          style={styles.langPill}
          onPress={() => setPickerTarget('source')}
        >
          <Text style={styles.langPillText}>{getLangLabel(sourceLang)}</Text>
          <Ionicons name="chevron-down" size={14} color={Colors.textSecondary} />
        </TouchableOpacity>

        <TouchableOpacity onPress={handleSwap} style={styles.swapBtn}>
          <Ionicons name="swap-horizontal" size={26} color={Colors.secondary} />
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.langPill}
          onPress={() => setPickerTarget('target')}
        >
          <Text style={styles.langPillText}>{getLangLabel(targetLang)}</Text>
          <Ionicons name="chevron-down" size={14} color={Colors.textSecondary} />
        </TouchableOpacity>
      </View>

      {/* Source Text Box */}
      <View style={styles.textBox}>
        <TextInput
          style={styles.textInput}
          value={sourceText}
          onChangeText={(txt) => {
            setSourceText(txt);
            if (!txt.trim()) setTranslatedText('');
          }}
          placeholder={t('typeMessage')}
          placeholderTextColor={Colors.textMuted}
          multiline
          maxLength={1000}
          returnKeyType="done"
          blurOnSubmit
          onSubmitEditing={handleTranslate}
        />
        <View style={styles.textActions}>
          {sourceText.length > 0 && (
            <>
              <TouchableOpacity onPress={() => speak(sourceText, sourceLang, 'src')}>
                <Ionicons
                  name={speaking === 'src' ? 'volume-high' : 'volume-medium-outline'}
                  size={22}
                  color={Colors.accent}
                />
              </TouchableOpacity>
              <TouchableOpacity
                onPress={() => { setSourceText(''); setTranslatedText(''); }}
              >
                <Ionicons name="close-circle" size={22} color={Colors.textMuted} />
              </TouchableOpacity>
            </>
          )}
        </View>
      </View>

      {/* Translate Button */}
      <TouchableOpacity
        style={[styles.translateBtn, !sourceText.trim() && styles.translateBtnDisabled]}
        onPress={handleTranslate}
        disabled={!sourceText.trim() || loading}
      >
        {loading ? (
          <ActivityIndicator color={Colors.textOnPrimary} />
        ) : (
          <>
            <Ionicons name="language" size={20} color={Colors.textOnPrimary} />
            <Text style={styles.translateBtnText}>{t('translateAction')}</Text>
          </>
        )}
      </TouchableOpacity>

      {/* Translation Result Box */}
      <View style={[styles.textBox, styles.resultBox]}>
        <Text
          style={[
            styles.resultText,
            !translatedText && styles.placeholderResultText,
          ]}
          selectable
        >
          {translatedText || t('noTranslation')}
        </Text>
        {translatedText.length > 0 && (
          <View style={styles.textActions}>
            <TouchableOpacity onPress={() => speak(translatedText, targetLang, 'tgt')}>
              <Ionicons
                name={speaking === 'tgt' ? 'volume-high' : 'volume-medium-outline'}
                size={24}
                color={Colors.primary}
              />
            </TouchableOpacity>
          </View>
        )}
      </View>

      {/* Bottom padding */}
      <View style={{ height: insets.bottom + Spacing.md }} />

      {/* Language Picker Modal */}
      <Modal
        visible={pickerTarget !== null}
        transparent
        animationType="fade"
        onRequestClose={() => setPickerTarget(null)}
      >
        <Pressable style={styles.modalOverlay} onPress={() => setPickerTarget(null)}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>
              {pickerTarget === 'source' ? t('from') : t('to')}
            </Text>
            {LANGUAGES.map((lang) => {
              const isSelected =
                pickerTarget === 'source'
                  ? sourceLang === lang.code
                  : targetLang === lang.code;
              return (
                <TouchableOpacity
                  key={lang.code}
                  style={[styles.modalOption, isSelected && styles.modalOptionActive]}
                  onPress={() => selectLanguage(lang.code)}
                >
                  <Text style={[
                    styles.modalOptionText,
                    isSelected && styles.modalOptionTextActive,
                  ]}>
                    {lang.label}
                  </Text>
                  {isSelected && (
                    <Ionicons name="checkmark" size={20} color={Colors.primary} />
                  )}
                </TouchableOpacity>
              );
            })}
          </View>
        </Pressable>
      </Modal>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background, paddingHorizontal: Spacing.lg },
  // Header
  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingVertical: Spacing.sm,
  },
  backBtn: {
    width: 40, height: 40, borderRadius: 20,
    backgroundColor: Colors.card, justifyContent: 'center', alignItems: 'center',
    ...Shadows.sm,
  },
  headerTitle: { ...Typography.h2, color: Colors.primary },
  // Language row
  langRow: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    gap: Spacing.md, marginVertical: Spacing.md,
  },
  langPill: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    backgroundColor: Colors.card, paddingHorizontal: 16, paddingVertical: 10,
    borderRadius: BorderRadius.full, ...Shadows.sm,
  },
  langPillText: { ...Typography.label, color: Colors.textPrimary },
  swapBtn: {
    width: 44, height: 44, borderRadius: 22,
    backgroundColor: Colors.sand, justifyContent: 'center', alignItems: 'center',
  },
  // Text boxes
  textBox: {
    backgroundColor: Colors.card, borderRadius: BorderRadius.lg,
    padding: Spacing.md, minHeight: 120, borderWidth: 1,
    borderColor: Colors.sand, ...Shadows.sm,
  },
  textInput: {
    ...Typography.bodyLarge, color: Colors.textPrimary, flex: 1,
    minHeight: 80, textAlignVertical: 'top',
  },
  textActions: {
    flexDirection: 'row', justifyContent: 'flex-end', gap: Spacing.md, marginTop: Spacing.xs,
  },
  resultBox: { marginTop: Spacing.md, backgroundColor: Colors.warmWhite, flex: 1 },
  resultText: { ...Typography.bodyLarge, color: Colors.primary, lineHeight: 28 },
  placeholderResultText: { color: Colors.textMuted, fontStyle: 'italic' },
  // Translate button
  translateBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    gap: Spacing.xs, backgroundColor: Colors.primary, borderRadius: BorderRadius.full,
    paddingVertical: 14, marginTop: Spacing.md, ...Shadows.md,
  },
  translateBtnDisabled: { backgroundColor: Colors.stone },
  translateBtnText: { ...Typography.label, color: Colors.textOnPrimary },
  // Modal
  modalOverlay: {
    flex: 1, backgroundColor: Colors.overlay,
    justifyContent: 'center', alignItems: 'center',
  },
  modalContent: {
    backgroundColor: Colors.card, borderRadius: BorderRadius.xl,
    padding: Spacing.lg, width: '75%', ...Shadows.lg,
  },
  modalTitle: {
    ...Typography.h3, color: Colors.textPrimary,
    textAlign: 'center', marginBottom: Spacing.md,
  },
  modalOption: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingVertical: 14, paddingHorizontal: Spacing.md,
    borderRadius: BorderRadius.md, marginBottom: Spacing.xs,
  },
  modalOptionActive: { backgroundColor: Colors.sand },
  modalOptionText: { ...Typography.bodyLarge, color: Colors.textPrimary },
  modalOptionTextActive: { color: Colors.primary, fontWeight: '600' },
});
