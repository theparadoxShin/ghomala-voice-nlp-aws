/**
 * ConversationScreen — NAM SA'
 * Voice-first conversation interface.
 * Shows: status indicator, message bubbles, voice waveform, controls.
 * Adapts to all screen sizes.
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Animated,
  FlatList,
  Dimensions,
  Platform,
  KeyboardAvoidingView,
  TextInput,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { Colors, Typography, Spacing, BorderRadius, Shadows } from '../theme';
import { sendChat, fetchTTS } from '../services/api';
import { useAudioPlayer } from 'expo-audio';
import * as FileSystem from 'expo-file-system';

const { width: SCREEN_W, height: SCREEN_H } = Dimensions.get('window');
const isSmallScreen = SCREEN_H < 700;

// Voice states
const VoiceState = {
  IDLE: 'idle',
  LISTENING: 'listening',
  THINKING: 'thinking',
  SPEAKING: 'speaking',
};

const STATUS_CONFIG = {
  [VoiceState.IDLE]: { text: 'Appuie pour parler', color: Colors.stone, iconName: 'mic-outline' },
  [VoiceState.LISTENING]: { text: 'Je t\'écoute...', color: Colors.accent, iconName: 'ear-outline' },
  [VoiceState.THINKING]: { text: 'Je réfléchis...', color: Colors.secondary, iconName: 'cloud-outline' },
  [VoiceState.SPEAKING]: { text: 'Je parle...', color: Colors.primary, iconName: 'volume-high-outline' },
};

export default function ConversationScreen({ navigation, route }) {
  const insets = useSafeAreaInsets();
  const { mode = 'tutor', initialMessage } = route.params || {};

  const [voiceState, setVoiceState] = useState(VoiceState.IDLE);
  const [messages, setMessages] = useState([]);
  const [textInput, setTextInput] = useState('');
  const [showTextInput, setShowTextInput] = useState(false);
  const [sessionId, setSessionId] = useState(null);

  const flatListRef = useRef(null);
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const waveAnims = useRef(
    Array.from({ length: 7 }, () => new Animated.Value(0.3))
  ).current;
  const [playingMsgId, setPlayingMsgId] = useState(null);
  const player = useAudioPlayer();

  // === TTS Playback ===
  const handlePlayTTS = useCallback(
    async (messageId, text) => {
      if (playingMsgId === messageId) {
        player.pause();
        setPlayingMsgId(null);
        return;
      }

      setPlayingMsgId(messageId);
      try {
        // Detect language: if text has Ghomala' diacritics, it's likely bbj
        const hasGhomalaDiacritics = /[ɔɛəŋ]|[àáâǎèéêěòóôǒùúûǔ]/.test(text);
        const lang = hasGhomalaDiacritics ? 'bbj' : 'fr';

        const result = await fetchTTS(text, lang);
        if (result.audio) {
          // Write base64 audio to a temp file for reliable playback
          const ext = (result.mime_type || '').includes('wav') ? 'wav' : 'mp3';
          const fileUri = `${FileSystem.cacheDirectory}tts_${messageId}.${ext}`;
          await FileSystem.writeAsStringAsync(fileUri, result.audio, {
            encoding: FileSystem.EncodingType.Base64,
          });
          player.replace({ uri: fileUri });
          player.play();
        }
      } catch (error) {
        console.warn('TTS playback failed:', error.message);
      } finally {
        setPlayingMsgId(null);
      }
    },
    [playingMsgId, player]
  );

  // === Animations ===
  useEffect(() => {
    if (voiceState === VoiceState.LISTENING) {
      // Waveform animation
      waveAnims.forEach((anim, i) => {
        Animated.loop(
          Animated.sequence([
            Animated.timing(anim, {
              toValue: 0.3 + Math.random() * 0.7,
              duration: 200 + i * 80,
              useNativeDriver: true,
            }),
            Animated.timing(anim, {
              toValue: 0.2 + Math.random() * 0.3,
              duration: 200 + i * 60,
              useNativeDriver: true,
            }),
          ])
        ).start();
      });
    } else {
      waveAnims.forEach((anim) => {
        Animated.timing(anim, {
          toValue: 0.3,
          duration: 300,
          useNativeDriver: true,
        }).start();
      });
    }
  }, [voiceState]);

  useEffect(() => {
    if (voiceState === VoiceState.THINKING) {
      Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.15,
            duration: 600,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 600,
            useNativeDriver: true,
          }),
        ])
      ).start();
    } else {
      pulseAnim.setValue(1);
    }
  }, [voiceState]);

  // === Welcome message ===
  useEffect(() => {
    const welcomeMessages = {
      tutor: 'Bienvenue ! Je suis NAM SA\', ton guide pour apprendre le Ghomala\'. Pose-moi une question ou dis un mot à traduire !',
      conversation: 'Salut ! Parlons ensemble en Ghomala\' et en Français. N\'hésite pas à mélanger les langues !',
      proverb: 'La sagesse des ancêtres Bamiléké est infinie. Demande-moi un proverbe sur un thème qui t\'intéresse.',
      translate: 'Je traduis entre Ghomala\', Français et Anglais. Dis ou écris ce que tu veux traduire !',
    };

    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        text: welcomeMessages[mode] || welcomeMessages.tutor,
        timestamp: new Date(),
      },
    ]);

    // If there's an initial message, send it
    if (initialMessage) {
      setTimeout(() => handleSendText(initialMessage), 500);
    }
  }, [mode]);

  // === Send text message ===
  const handleSendText = useCallback(
    async (text) => {
      if (!text.trim()) return;

      const userMsg = {
        id: Date.now().toString(),
        role: 'user',
        text: text.trim(),
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMsg]);
      setTextInput('');
      setVoiceState(VoiceState.THINKING);

      try {
        const response = await sendChat(text.trim(), mode, sessionId);
        setSessionId(response.session_id);

        const assistantMsg = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          text: response.response,
          timestamp: new Date(),
        };

        setMessages((prev) => [...prev, assistantMsg]);
      } catch (error) {
        const errorMsg = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          text: 'Désolé, je n\'ai pas pu répondre. Vérifie ta connexion et réessaie.',
          timestamp: new Date(),
          isError: true,
        };
        setMessages((prev) => [...prev, errorMsg]);
      }

      setVoiceState(VoiceState.IDLE);
    },
    [mode, sessionId]
  );

  // === Voice recording (placeholder — integrate expo-av) ===
  const handleVoicePress = () => {
    if (voiceState === VoiceState.IDLE) {
      setVoiceState(VoiceState.LISTENING);
      // TODO: Start recording with expo-av
      // In production: stream audio chunks to WebSocket
    } else if (voiceState === VoiceState.LISTENING) {
      setVoiceState(VoiceState.THINKING);
      // TODO: Stop recording, send audio
      // For now, simulate with text
      setTimeout(() => {
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now().toString(),
            role: 'assistant',
            text: 'J\'ai bien entendu ! Pour l\'instant, utilise le mode texte en bas. Le mode vocal complet arrive bientôt avec Gemini Live !',
            timestamp: new Date(),
          },
        ]);
        setVoiceState(VoiceState.IDLE);
      }, 1500);
    }
  };

  // === Scroll to bottom on new message ===
  useEffect(() => {
    if (messages.length > 0) {
      setTimeout(() => {
        flatListRef.current?.scrollToEnd({ animated: true });
      }, 100);
    }
  }, [messages]);

  // === Render message bubble ===
  const renderMessage = ({ item }) => {
    const isUser = item.role === 'user';
    const isSpeaking = playingMsgId === item.id;

    return (
      <View
        style={[
          styles.messageBubbleContainer,
          isUser ? styles.userBubbleContainer : styles.assistantBubbleContainer,
        ]}
      >
        {!isUser && <Ionicons name="sunny" size={20} color={Colors.secondary} style={styles.avatarIcon} />}
        <View
          style={[
            styles.messageBubble,
            isUser ? styles.userBubble : styles.assistantBubble,
            item.isError && styles.errorBubble,
          ]}
        >
          <Text
            style={[
              styles.messageText,
              isUser ? styles.userText : styles.assistantText,
            ]}
          >
            {item.text}
          </Text>
          {/* Speaker button for all messages */}
          {!item.isError && item.id !== 'welcome' && (
            <TouchableOpacity
              style={[
                styles.speakerButton,
                isUser ? styles.speakerButtonUser : styles.speakerButtonAssistant,
                isSpeaking && styles.speakerButtonActive,
              ]}
              onPress={() => handlePlayTTS(item.id, item.text)}
              hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
            >
              <Ionicons
                name={isSpeaking ? 'volume-high' : 'volume-medium-outline'}
                size={16}
                color={isUser ? 'rgba(255,255,255,0.8)' : Colors.textMuted}
              />
            </TouchableOpacity>
          )}
        </View>
      </View>
    );
  };

  const statusConfig = STATUS_CONFIG[voiceState];

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      {/* === HEADER === */}
      <View style={[styles.header, { paddingTop: insets.top + Spacing.sm }]}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => navigation.goBack()}
        >
          <Ionicons name="arrow-back" size={20} color={Colors.textPrimary} />
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          <Text style={styles.headerTitle}>NAM SA'</Text>
          <Ionicons name={statusConfig.iconName} size={14} color={Colors.textMuted} />
          <Text style={[styles.headerMode, { marginLeft: 4 }]}>{statusConfig.text}</Text>
        </View>
        <TouchableOpacity
          style={styles.textToggle}
          onPress={() => setShowTextInput(!showTextInput)}
        >
          <Ionicons
            name={showTextInput ? 'mic-outline' : 'keypad-outline'}
            size={18}
            color={Colors.textPrimary}
          />
        </TouchableOpacity>
      </View>

      {/* === MESSAGES === */}
      <FlatList
        ref={flatListRef}
        data={messages}
        renderItem={renderMessage}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.messageList}
        showsVerticalScrollIndicator={false}
      />

      {/* === BOTTOM CONTROLS === */}
      <View style={[styles.bottomBar, { paddingBottom: insets.bottom + Spacing.sm }]}>
        {showTextInput ? (
          /* Text input mode */
          <View style={styles.textInputRow}>
            <TextInput
              style={styles.textInputField}
              value={textInput}
              onChangeText={setTextInput}
              placeholder="Écris ton message..."
              placeholderTextColor={Colors.textMuted}
              multiline
              maxLength={500}
              returnKeyType="send"
              onSubmitEditing={() => handleSendText(textInput)}
            />
            <TouchableOpacity
              style={[
                styles.sendButton,
                !textInput.trim() && styles.sendButtonDisabled,
              ]}
              onPress={() => handleSendText(textInput)}
              disabled={!textInput.trim() || voiceState === VoiceState.THINKING}
            >
              <Ionicons name="send" size={20} color={Colors.textOnPrimary} />
            </TouchableOpacity>
          </View>
        ) : (
          /* Voice mode */
          <View style={styles.voiceControls}>
            {/* Waveform visualization */}
            <View style={styles.waveformContainer}>
              {waveAnims.map((anim, i) => (
                <Animated.View
                  key={i}
                  style={[
                    styles.waveBar,
                    {
                      backgroundColor:
                        voiceState === VoiceState.LISTENING
                          ? Colors.accent
                          : voiceState === VoiceState.SPEAKING
                          ? Colors.primary
                          : Colors.stone,
                      transform: [{ scaleY: anim }],
                    },
                  ]}
                />
              ))}
            </View>

            {/* Main voice button */}
            <Animated.View style={{ transform: [{ scale: pulseAnim }] }}>
              <TouchableOpacity
                style={[
                  styles.voiceBtn,
                  voiceState === VoiceState.LISTENING && styles.voiceBtnActive,
                  voiceState === VoiceState.THINKING && styles.voiceBtnThinking,
                ]}
                onPress={handleVoicePress}
                activeOpacity={0.7}
                disabled={voiceState === VoiceState.THINKING}
              >
                <Ionicons
                  name={voiceState === VoiceState.LISTENING
                    ? 'stop-circle'
                    : voiceState === VoiceState.THINKING
                    ? 'hourglass-outline'
                    : 'mic'}
                  size={isSmallScreen ? 26 : 30}
                  color={Colors.textOnPrimary}
                />
              </TouchableOpacity>
            </Animated.View>

            {/* Waveform right side (mirror) */}
            <View style={styles.waveformContainer}>
              {waveAnims
                .slice()
                .reverse()
                .map((anim, i) => (
                  <Animated.View
                    key={i}
                    style={[
                      styles.waveBar,
                      {
                        backgroundColor:
                          voiceState === VoiceState.LISTENING
                            ? Colors.accent
                            : voiceState === VoiceState.SPEAKING
                            ? Colors.primary
                            : Colors.stone,
                        transform: [{ scaleY: anim }],
                      },
                    ]}
                  />
                ))}
            </View>
          </View>
        )}
      </View>
    </KeyboardAvoidingView>
  );
}

// ============================================================================
// STYLES
// ============================================================================
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },

  // --- Header ---
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: Spacing.md,
    paddingBottom: Spacing.sm,
    backgroundColor: Colors.warmWhite,
    borderBottomWidth: 1,
    borderBottomColor: Colors.sand,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: Colors.card,
    justifyContent: 'center',
    alignItems: 'center',
    ...Shadows.sm,
  },
  headerCenter: {
    flex: 1,
    alignItems: 'center',
  },
  headerTitle: {
    ...Typography.h3,
    color: Colors.primary,
  },
  headerMode: {
    ...Typography.caption,
    color: Colors.textMuted,
  },
  textToggle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: Colors.card,
    justifyContent: 'center',
    alignItems: 'center',
    ...Shadows.sm,
  },

  // --- Messages ---
  messageList: {
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.md,
    flexGrow: 1,
  },
  messageBubbleContainer: {
    flexDirection: 'row',
    marginBottom: Spacing.md,
    alignItems: 'flex-end',
  },
  userBubbleContainer: {
    justifyContent: 'flex-end',
  },
  assistantBubbleContainer: {
    justifyContent: 'flex-start',
  },
  avatarIcon: {
    marginRight: Spacing.xs,
    marginBottom: 4,
  },
  messageBubble: {
    maxWidth: SCREEN_W * 0.75,
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm + 2,
    borderRadius: BorderRadius.lg,
  },
  userBubble: {
    backgroundColor: Colors.primary,
    borderBottomRightRadius: 4,
    marginLeft: 'auto',
  },
  assistantBubble: {
    backgroundColor: Colors.card,
    borderBottomLeftRadius: 4,
    borderWidth: 1,
    borderColor: Colors.sand,
  },
  errorBubble: {
    borderColor: Colors.error,
    borderWidth: 1,
  },
  messageText: {
    ...Typography.body,
    lineHeight: 22,
  },
  userText: {
    color: Colors.textOnPrimary,
  },
  assistantText: {
    color: Colors.textPrimary,
  },
  speakerButton: {
    alignSelf: 'flex-end',
    marginTop: 6,
    padding: 4,
    borderRadius: 12,
  },
  speakerButtonUser: {
    backgroundColor: 'rgba(255,255,255,0.15)',
  },
  speakerButtonAssistant: {
    backgroundColor: Colors.backgroundAlt,
  },
  speakerButtonActive: {
    backgroundColor: Colors.voicePulse,
  },

  // --- Bottom Bar ---
  bottomBar: {
    backgroundColor: Colors.warmWhite,
    borderTopWidth: 1,
    borderTopColor: Colors.sand,
    paddingTop: Spacing.md,
    paddingHorizontal: Spacing.md,
  },

  // --- Voice Controls ---
  voiceControls: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: Spacing.sm,
  },
  waveformContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    height: 50,
    gap: 3,
    flex: 1,
    justifyContent: 'center',
  },
  waveBar: {
    width: isSmallScreen ? 3 : 4,
    height: 40,
    borderRadius: 2,
  },
  voiceBtn: {
    width: isSmallScreen ? 64 : 72,
    height: isSmallScreen ? 64 : 72,
    borderRadius: 50,
    backgroundColor: Colors.secondary,
    justifyContent: 'center',
    alignItems: 'center',
    marginHorizontal: Spacing.md,
    ...Shadows.md,
  },
  voiceBtnActive: {
    backgroundColor: Colors.error,
    ...Shadows.glow,
  },
  voiceBtnThinking: {
    backgroundColor: Colors.stone,
  },

  // --- Text Input ---
  textInputRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: Spacing.sm,
  },
  textInputField: {
    flex: 1,
    backgroundColor: Colors.card,
    borderRadius: BorderRadius.xl,
    paddingHorizontal: Spacing.md,
    paddingVertical: Platform.OS === 'ios' ? Spacing.sm + 2 : Spacing.sm,
    ...Typography.body,
    color: Colors.textPrimary,
    maxHeight: 100,
    borderWidth: 1,
    borderColor: Colors.sand,
  },
  sendButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: Colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendButtonDisabled: {
    backgroundColor: Colors.stone,
  },
});
