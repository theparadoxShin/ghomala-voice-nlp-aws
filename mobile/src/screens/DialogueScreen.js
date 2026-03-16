/**
 * DialogueScreen — NAM SA'
 * Live conversation interface: text chat + voice.
 * Text → /api/chat. Voice → WebSocket /ws/live.
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, FlatList, TextInput,
  Dimensions, Platform, KeyboardAvoidingView, ActivityIndicator,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useLanguage } from '../context/LanguageContext';
import { sendChat } from '../services/api';
import { speak as ttsSpeak, stopSpeaking } from '../services/tts';
import { Colors, Typography, Spacing, BorderRadius, Shadows } from '../theme';

const { width: SCREEN_W } = Dimensions.get('window');

export default function DialogueScreen({ navigation, route }) {
  const insets = useSafeAreaInsets();
  const { t, lang } = useLanguage();

  const initialMessage = route?.params?.initialMessage || null;

  const [messages, setMessages] = useState([]);
  const [textInput, setTextInput] = useState('');
  const [sending, setSending] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [playingMsgId, setPlayingMsgId] = useState(null);
  const [initialSent, setInitialSent] = useState(false);

  const flatListRef = useRef(null);

  // Welcome message
  useEffect(() => {
    const welcomeText = lang === 'en'
      ? "Hello! I'm NAM SA', your guide to the Ghomala' language. Type or speak to start a conversation!"
      : "Salut ! Je suis NAM SA', ton guide pour la langue Ghomala'. Écris ou parle pour commencer !";
    setMessages([{ id: 'welcome', role: 'assistant', text: welcomeText, timestamp: new Date() }]);
  }, [lang]);

  // Auto-send initial message (e.g. from ProverbsScreen)
  useEffect(() => {
    if (initialMessage && !initialSent && messages.length > 0) {
      setInitialSent(true);
      handleSend(initialMessage);
    }
  }, [initialMessage, initialSent, messages.length]);

  // Send text message
  const handleSend = useCallback(async (text) => {
    if (!text?.trim() || sending) return;
    const trimmed = text.trim();
    setTextInput('');

    const userMsg = { id: Date.now().toString(), role: 'user', text: trimmed, timestamp: new Date() };
    setMessages((prev) => [...prev, userMsg]);
    setSending(true);

    try {
      const response = await sendChat(trimmed, 'conversation', sessionId);
      setSessionId(response.session_id);
      const assistantMsg = {
        id: (Date.now() + 1).toString(), role: 'assistant',
        text: response.response, timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(), role: 'assistant',
          text: lang === 'en' ? 'Connection error. Please try again.' : 'Erreur de connexion. Réessaie.',
          timestamp: new Date(), isError: true,
        },
      ]);
    }
    setSending(false);
  }, [sending, sessionId, lang]);

  // TTS playback via Cloud TTS
  const handlePlayTTS = useCallback((msgId, text) => {
    if (playingMsgId === msgId) { stopSpeaking(); setPlayingMsgId(null); return; }
    const hasGhomala = /[ɔɛəŋ]/.test(text);
    const ttsLang = hasGhomala ? 'bbj' : (lang === 'en' ? 'en' : 'fr');
    ttsSpeak(text, ttsLang, {
      onStart: () => setPlayingMsgId(msgId),
      onDone: () => setPlayingMsgId(null),
      onError: () => setPlayingMsgId(null),
    });
  }, [playingMsgId, lang]);

  // Scroll to bottom
  useEffect(() => {
    if (messages.length > 0) {
      setTimeout(() => flatListRef.current?.scrollToEnd({ animated: true }), 100);
    }
  }, [messages]);

  // Render message
  const renderMessage = ({ item }) => {
    const isUser = item.role === 'user';
    const isSpeaking = playingMsgId === item.id;

    return (
      <View style={[styles.bubbleRow, isUser ? styles.bubbleRowUser : styles.bubbleRowAssistant]}>
        {!isUser && <Ionicons name="sunny" size={18} color={Colors.secondary} style={styles.avatar} />}
        <View style={[styles.bubble, isUser ? styles.userBubble : styles.assistantBubble, item.isError && styles.errorBubble]}>
          <Text style={[styles.bubbleText, isUser ? styles.userText : styles.assistantText]}>{item.text}</Text>
          {!item.isError && item.id !== 'welcome' && (
            <TouchableOpacity
              style={[styles.speakerBtn, isUser && styles.speakerBtnUser]}
              onPress={() => handlePlayTTS(item.id, item.text)}
              hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
            >
              <Ionicons
                name={isSpeaking ? 'volume-high' : 'volume-medium-outline'}
                size={15} color={isUser ? 'rgba(255,255,255,0.7)' : Colors.textMuted}
              />
            </TouchableOpacity>
          )}
        </View>
      </View>
    );
  };

  return (
    <KeyboardAvoidingView
      style={[styles.container]}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      {/* Header */}
      <View style={[styles.header, { paddingTop: insets.top + Spacing.xs }]}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={20} color={Colors.textPrimary} />
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          <Text style={styles.headerTitle}>NAM SA'</Text>
          <Text style={styles.headerSub}>{t('liveConversation')}</Text>
        </View>
        <View style={{ width: 40 }} />
      </View>

      {/* Messages */}
      <FlatList
        ref={flatListRef}
        data={messages}
        renderItem={renderMessage}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.messageList}
        showsVerticalScrollIndicator={false}
      />

      {/* Input Bar — always visible */}
      <View style={[styles.inputBar, { paddingBottom: insets.bottom + Spacing.xs }]}>
        <TextInput
          style={styles.textField}
          value={textInput}
          onChangeText={setTextInput}
          placeholder={t('typeMessage')}
          placeholderTextColor={Colors.textMuted}
          multiline
          maxLength={500}
          returnKeyType="send"
          onSubmitEditing={() => handleSend(textInput)}
          editable={!sending}
        />
        {sending ? (
          <View style={styles.sendBtn}><ActivityIndicator color={Colors.textOnPrimary} size="small" /></View>
        ) : (
          <TouchableOpacity
            style={[styles.sendBtn, !textInput.trim() && styles.sendBtnDisabled]}
            onPress={() => handleSend(textInput)}
            disabled={!textInput.trim()}
          >
            <Ionicons name="send" size={20} color={Colors.textOnPrimary} />
          </TouchableOpacity>
        )}
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  // Header
  header: {
    flexDirection: 'row', alignItems: 'center',
    paddingHorizontal: Spacing.md, paddingBottom: Spacing.sm,
    backgroundColor: Colors.warmWhite, borderBottomWidth: 1, borderBottomColor: Colors.sand,
  },
  backBtn: {
    width: 38, height: 38, borderRadius: 19,
    backgroundColor: Colors.card, justifyContent: 'center', alignItems: 'center', ...Shadows.sm,
  },
  headerCenter: { flex: 1, alignItems: 'center' },
  headerTitle: { ...Typography.h3, color: Colors.primary },
  headerSub: { ...Typography.caption, color: Colors.textMuted },
  // Messages
  messageList: { paddingHorizontal: Spacing.md, paddingVertical: Spacing.md, flexGrow: 1 },
  bubbleRow: { flexDirection: 'row', marginBottom: Spacing.md, alignItems: 'flex-end' },
  bubbleRowUser: { justifyContent: 'flex-end' },
  bubbleRowAssistant: { justifyContent: 'flex-start' },
  avatar: { marginRight: Spacing.xs, marginBottom: 4 },
  bubble: {
    maxWidth: SCREEN_W * 0.75, paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm + 2, borderRadius: BorderRadius.lg,
  },
  userBubble: {
    backgroundColor: Colors.primary, borderBottomRightRadius: 4, marginLeft: 'auto',
  },
  assistantBubble: {
    backgroundColor: Colors.card, borderBottomLeftRadius: 4,
    borderWidth: 1, borderColor: Colors.sand,
  },
  errorBubble: { borderColor: Colors.error, borderWidth: 1 },
  bubbleText: { ...Typography.body, lineHeight: 22 },
  userText: { color: Colors.textOnPrimary },
  assistantText: { color: Colors.textPrimary },
  speakerBtn: {
    alignSelf: 'flex-end', marginTop: 4, padding: 3, borderRadius: 10,
    backgroundColor: Colors.backgroundAlt,
  },
  speakerBtnUser: { backgroundColor: 'rgba(255,255,255,0.15)' },
  // Input bar
  inputBar: {
    flexDirection: 'row', alignItems: 'flex-end', gap: Spacing.sm,
    paddingHorizontal: Spacing.md, paddingTop: Spacing.sm,
    backgroundColor: Colors.warmWhite, borderTopWidth: 1, borderTopColor: Colors.sand,
  },
  textField: {
    flex: 1, backgroundColor: Colors.card, borderRadius: BorderRadius.xl,
    paddingHorizontal: Spacing.md,
    paddingVertical: Platform.OS === 'ios' ? Spacing.sm + 2 : Spacing.sm,
    ...Typography.body, color: Colors.textPrimary, maxHeight: 100,
    borderWidth: 1, borderColor: Colors.sand,
  },
  sendBtn: {
    width: 44, height: 44, borderRadius: 22,
    backgroundColor: Colors.primary, justifyContent: 'center', alignItems: 'center',
  },
  sendBtnDisabled: { backgroundColor: Colors.stone },
});
