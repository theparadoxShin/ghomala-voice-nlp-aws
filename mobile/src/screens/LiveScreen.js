/**
 * LiveScreen — NAM SA'
 * Fluid voice conversation with Gemini via WebSocket.
 * Tap mic to start/stop conversation. Silence auto-detection sends audio.
 * Continuous flow: speak → auto-detect silence → agent responds → auto-listen again.
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, FlatList,
  Animated, Dimensions, Platform,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import {
  useAudioRecorder, useAudioRecorderState,
  RecordingPresets, requestRecordingPermissionsAsync,
} from 'expo-audio';
import { useLanguage } from '../context/LanguageContext';
import { Colors, Typography, Spacing, BorderRadius, Shadows } from '../theme';
import Constants from 'expo-constants';

const PROD_URL = 'https://nam-sa-976647416990.us-central1.run.app';
const API_BASE = __DEV__
  ? (Constants.expoConfig?.extra?.API_URL || 'http://192.168.1.100:8080')
  : (Constants.expoConfig?.extra?.API_URL || PROD_URL);
const WS_BASE = API_BASE.replace(/^http/, 'ws');

// Recording with metering enabled for silence detection
const RECORDING_OPTIONS = {
  ...RecordingPresets.HIGH_QUALITY,
  extension: '.m4a',
  sampleRate: 16000,
  numberOfChannels: 1,
  bitRate: 64000,
  isMeteringEnabled: true,
  android: { outputFormat: 'mpeg4', audioEncoder: 'aac' },
  ios: {
    outputFormat: 'aac', audioQuality: 'high',
    linearPCMBitDepth: 16, linearPCMIsBigEndian: false, linearPCMIsFloat: false,
  },
};

// Silence detection config
const SILENCE_THRESHOLD = -35;       // dB — below this is "silence"
const SILENCE_DURATION_MS = 1800;    // ms of silence before auto-send
const MIN_RECORDING_MS = 800;        // ignore very short recordings
const MAX_RECORDING_MS = 6000;       // force auto-send after 6s (fallback if metering is null)

const STATES = {
  IDLE: 'idle',
  CONNECTING: 'connecting',
  READY: 'ready',
  LISTENING: 'listening',
  PROCESSING: 'processing',
  RESPONDING: 'responding',
};

const { width: SCREEN_W } = Dimensions.get('window');

export default function LiveScreen({ navigation }) {
  const insets = useSafeAreaInsets();
  const { t, lang } = useLanguage();

  const [status, setStatus] = useState(STATES.IDLE);
  const [messages, setMessages] = useState([]);
  const [conversationActive, setConversationActive] = useState(false);

  const wsRef = useRef(null);
  const playerRef = useRef(null);
  const flatListRef = useRef(null);
  const statusRef = useRef(STATES.IDLE);
  const silenceStartRef = useRef(null);
  const conversationActiveRef = useRef(false);
  const autoRestartRef = useRef(false);

  // Keep refs in sync with state
  useEffect(() => { statusRef.current = status; }, [status]);
  useEffect(() => { conversationActiveRef.current = conversationActive; }, [conversationActive]);

  // Audio recorder with metering
  const recorder = useAudioRecorder(RECORDING_OPTIONS);
  const recorderState = useAudioRecorderState(recorder, 150);

  // Animations
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const waveAnim = useRef(new Animated.Value(0)).current;

  // ── Silence Detection via Metering + Timer Fallback ──
  useEffect(() => {
    if (statusRef.current !== STATES.LISTENING) {
      silenceStartRef.current = null;
      return;
    }

    // Timer fallback: force auto-send after MAX_RECORDING_MS
    // This ensures audio is ALWAYS sent even if metering is null
    if (recorderState.durationMillis >= MAX_RECORDING_MS) {
      console.log('[Live] Max recording time reached, auto-sending...');
      silenceStartRef.current = null;
      autoRestartRef.current = true;
      stopAndSend();
      return;
    }

    if (recorderState.metering == null) return;

    const now = Date.now();
    const isSilent = recorderState.metering < SILENCE_THRESHOLD;

    if (isSilent) {
      if (!silenceStartRef.current) {
        silenceStartRef.current = now;
      } else if (
        now - silenceStartRef.current >= SILENCE_DURATION_MS &&
        recorderState.durationMillis >= MIN_RECORDING_MS
      ) {
        console.log('[Live] Silence detected, auto-sending...');
        silenceStartRef.current = null;
        autoRestartRef.current = true;
        stopAndSend();
      }
    } else {
      silenceStartRef.current = null;
    }
  }, [recorderState.metering, recorderState.durationMillis]);

  // Pulse animation when listening
  useEffect(() => {
    if (status === STATES.LISTENING) {
      const anim = Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, { toValue: 1.12, duration: 600, useNativeDriver: true }),
          Animated.timing(pulseAnim, { toValue: 1, duration: 600, useNativeDriver: true }),
        ])
      );
      anim.start();
      return () => anim.stop();
    } else {
      pulseAnim.setValue(1);
    }
  }, [status]);

  // Connect WebSocket on mount
  useEffect(() => {
    connectWebSocket();
    return () => {
      wsRef.current?.close();
      cleanupPlayer();
    };
  }, []);

  // Auto-scroll transcript
  useEffect(() => {
    if (messages.length > 0) {
      setTimeout(() => flatListRef.current?.scrollToEnd({ animated: true }), 100);
    }
  }, [messages]);

  const connectWebSocket = useCallback(() => {
    setStatus(STATES.CONNECTING);
    const ws = new WebSocket(`${WS_BASE}/ws/live`);

    ws.onopen = () => {
      console.log('[Live] WS connected');
      ws.send(JSON.stringify({ type: 'config', language: lang }));
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        console.log('[Live] WS msg:', msg.type, msg.text?.substring(0, 50) || '');

        switch (msg.type) {
          case 'status':
            if (msg.status === 'ready') setStatus(STATES.READY);
            break;

          case 'user_transcript':
            setMessages(prev => [...prev, {
              id: `u_${Date.now()}`, role: 'user', text: msg.text,
            }]);
            break;

          case 'transcript':
            setMessages(prev => [...prev, {
              id: `a_${Date.now()}`, role: 'assistant', text: msg.text,
            }]);
            break;

          case 'audio_response':
            setStatus(STATES.RESPONDING);
            playResponseAudio(msg.data, msg.format);
            break;

          case 'turn_complete':
            if (autoRestartRef.current && conversationActiveRef.current) {
              autoRestartRef.current = false;
              setTimeout(() => {
                if (conversationActiveRef.current && statusRef.current !== STATES.RESPONDING) {
                  startListening();
                }
              }, 400);
            }
            break;

          case 'error':
            console.warn('[Live] Error from server:', msg.message);
            if (conversationActiveRef.current) {
              setTimeout(() => startListening(), 500);
            } else {
              setStatus(STATES.READY);
            }
            break;
        }
      } catch (e) {
        console.warn('[Live] WS parse error:', e);
      }
    };

    ws.onerror = (e) => {
      console.warn('[Live] WS error', e.message);
      setStatus(STATES.IDLE);
      setConversationActive(false);
    };

    ws.onclose = (e) => {
      console.log('[Live] WS closed', e.code);
      setStatus(STATES.IDLE);
      setConversationActive(false);
    };

    wsRef.current = ws;
  }, [lang]);

  // ── Start Listening (begin recording) ──
  const startListening = useCallback(async () => {
    try {
      const perm = await requestRecordingPermissionsAsync();
      if (!perm.granted) {
        console.warn('[Live] Mic permission denied');
        return;
      }
      cleanupPlayer();
      silenceStartRef.current = null;
      recorder.record();
      console.log('[Live] Listening started');
      setStatus(STATES.LISTENING);
    } catch (e) {
      console.warn('[Live] Start listening error:', e.message);
    }
  }, [recorder]);

  // ── Stop Recording & Send Audio ──
  const stopAndSend = useCallback(async () => {
    try {
      await recorder.stop();
      const fileUri = recorder.uri;

      if (!fileUri) {
        if (conversationActiveRef.current) startListening();
        else setStatus(STATES.READY);
        return;
      }

      setStatus(STATES.PROCESSING);

      const FileSystem = require('expo-file-system/legacy');
      const base64Audio = await FileSystem.readAsStringAsync(fileUri, {
        encoding: FileSystem.EncodingType.Base64,
      });
      console.log('[Live] Audio captured, base64 length:', base64Audio.length);

      if (base64Audio.length < 500) {
        console.log('[Live] Audio too short, skipping');
        if (conversationActiveRef.current) {
          setTimeout(() => startListening(), 200);
        } else {
          setStatus(STATES.READY);
        }
        return;
      }

      if (wsRef.current?.readyState === WebSocket.OPEN) {
        console.log('[Live] Sending audio to server...');
        wsRef.current.send(JSON.stringify({
          type: 'audio',
          data: base64Audio,
          mime_type: 'audio/mp4',
        }));
      } else {
        console.warn('[Live] WS not open, cannot send');
        setStatus(STATES.IDLE);
        setConversationActive(false);
      }
    } catch (e) {
      console.warn('[Live] Stop/send error:', e.message);
      if (conversationActiveRef.current) {
        setTimeout(() => startListening(), 500);
      } else {
        setStatus(STATES.READY);
      }
    }
  }, [recorder, startListening]);

  // ── Play Response Audio ──
  const playResponseAudio = useCallback(async (base64Audio, format) => {
    try {
      const FileSystem = require('expo-file-system/legacy');
      const { createAudioPlayer } = require('expo-audio');

      const ext = format === 'wav' ? 'wav' : 'mp3';
      const fileUri = `${FileSystem.cacheDirectory}live_resp_${Date.now()}.${ext}`;
      await FileSystem.writeAsStringAsync(fileUri, base64Audio, {
        encoding: FileSystem.EncodingType.Base64,
      });

      cleanupPlayer();

      const player = createAudioPlayer(fileUri);
      playerRef.current = player;

      const sub = player.addListener('playbackStatusUpdate', (s) => {
        if (s.didJustFinish) {
          sub.remove();
          cleanupPlayer();
          if (conversationActiveRef.current) {
            setTimeout(() => startListening(), 300);
          } else {
            setStatus(STATES.READY);
          }
        }
      });

      player.play();
    } catch (e) {
      console.warn('[Live] Playback error:', e.message);
      if (conversationActiveRef.current) {
        setTimeout(() => startListening(), 300);
      } else {
        setStatus(STATES.READY);
      }
    }
  }, [startListening]);

  const cleanupPlayer = () => {
    if (playerRef.current) {
      try { playerRef.current.pause(); } catch {}
      try { playerRef.current.release(); } catch {}
      playerRef.current = null;
    }
  };

  // ── Toggle Conversation (single tap) ──
  const toggleConversation = useCallback(() => {
    if (status === STATES.IDLE) {
      connectWebSocket();
      return;
    }

    if (conversationActive) {
      console.log('[Live] Stopping conversation');
      setConversationActive(false);
      autoRestartRef.current = false;
      if (statusRef.current === STATES.LISTENING) {
        recorder.stop().catch(() => {});
      }
      cleanupPlayer();
      setStatus(STATES.READY);
    } else {
      console.log('[Live] Starting conversation');
      setConversationActive(true);
      autoRestartRef.current = true;
      startListening();
    }
  }, [status, conversationActive, recorder, connectWebSocket, startListening]);

  // ── Status Text ──
  const getStatusText = () => {
    if (conversationActive) {
      const texts = {
        [STATES.LISTENING]: lang === 'en' ? "I'm listening..." : "Je t'écoute...",
        [STATES.PROCESSING]: lang === 'en' ? "NAM SA' is thinking..." : "NAM SA' réfléchit...",
        [STATES.RESPONDING]: lang === 'en' ? "NAM SA' is speaking..." : "NAM SA' parle...",
      };
      return texts[status] || (lang === 'en' ? 'Conversation active' : 'Conversation active');
    }
    const texts = {
      [STATES.IDLE]: lang === 'en' ? 'Tap to reconnect' : 'Appuie pour reconnecter',
      [STATES.CONNECTING]: lang === 'en' ? 'Connecting...' : 'Connexion...',
      [STATES.READY]: lang === 'en' ? 'Tap to start talking' : 'Appuie pour commencer',
    };
    return texts[status] || '';
  };

  const getStatusColor = () => {
    switch (status) {
      case STATES.LISTENING: return '#4CAF50';
      case STATES.PROCESSING: return Colors.secondary;
      case STATES.RESPONDING: return Colors.primary;
      case STATES.READY: return Colors.textMuted;
      default: return Colors.textMuted;
    }
  };

  // Metering bar height (0-1)
  const getMeterLevel = () => {
    if (status !== STATES.LISTENING || recorderState.metering == null) return 0;
    const db = recorderState.metering;
    return Math.max(0, Math.min(1, (db + 50) / 50));
  };

  const renderMessage = ({ item }) => {
    const isUser = item.role === 'user';
    return (
      <View style={[styles.msgRow, isUser ? styles.msgRowUser : styles.msgRowAssistant]}>
        {!isUser && (
          <View style={styles.avatar}>
            <Ionicons name="sunny" size={14} color={Colors.secondary} />
          </View>
        )}
        <View style={[styles.msgBubble, isUser ? styles.userBubble : styles.assistantBubble]}>
          <Text style={[styles.msgText, isUser ? styles.userText : styles.assistantText]}>
            {item.text}
          </Text>
        </View>
      </View>
    );
  };

  const meterLevel = getMeterLevel();

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={20} color={Colors.textPrimary} />
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          <Text style={styles.headerTitle}>NAM SA' Live</Text>
          <View style={styles.statusRow}>
            <View style={[styles.statusDot, {
              backgroundColor: conversationActive ? '#4CAF50' : (status === STATES.IDLE ? '#999' : Colors.secondary)
            }]} />
            <Text style={styles.headerSub}>
              {conversationActive
                ? (lang === 'en' ? 'Active' : 'Active')
                : (status === STATES.IDLE
                  ? (lang === 'en' ? 'Offline' : 'Hors ligne')
                  : (lang === 'en' ? 'Ready' : 'Prêt'))}
            </Text>
          </View>
        </View>
        <TouchableOpacity
          onPress={() => navigation.navigate('Chat')}
          style={styles.chatBtn}
        >
          <Ionicons name="chatbubble-ellipses-outline" size={20} color={Colors.textSecondary} />
        </TouchableOpacity>
      </View>

      {/* Transcript */}
      {messages.length > 0 ? (
        <FlatList
          ref={flatListRef}
          data={messages}
          renderItem={renderMessage}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.transcriptList}
          showsVerticalScrollIndicator={false}
          style={styles.transcriptContainer}
        />
      ) : (
        <View style={styles.emptyTranscript}>
          <Ionicons name="mic-circle-outline" size={72} color={Colors.sand} />
          <Text style={styles.emptyTitle}>
            {lang === 'en' ? 'Voice Conversation' : 'Conversation Vocale'}
          </Text>
          <Text style={styles.emptyText}>
            {lang === 'en'
              ? "Tap the mic to start a natural conversation.\nSpeak freely — NAM SA' will respond when you pause."
              : "Appuie sur le micro pour démarrer.\nParle librement — NAM SA' répond quand tu fais une pause."}
          </Text>
        </View>
      )}

      {/* Mic Area */}
      <View style={[styles.micArea, { paddingBottom: insets.bottom + Spacing.md }]}>
        {/* Metering visualization */}
        {status === STATES.LISTENING && (
          <View style={styles.meterRow}>
            {[0, 1, 2, 3, 4, 5, 6].map((i) => (
              <View
                key={i}
                style={[
                  styles.meterBar,
                  {
                    height: 4 + Math.max(0, meterLevel * 28 - Math.abs(i - 3) * 4),
                    backgroundColor: meterLevel > 0.3 ? '#4CAF50' : Colors.sand,
                    opacity: meterLevel > 0.05 ? 0.5 + meterLevel * 0.5 : 0.3,
                  },
                ]}
              />
            ))}
          </View>
        )}

        <Text style={[styles.statusText, { color: getStatusColor() }]}>
          {getStatusText()}
        </Text>

        <View style={styles.micContainer}>
          <Animated.View style={{ transform: [{ scale: pulseAnim }] }}>
            <TouchableOpacity
              style={[
                styles.micBtn,
                conversationActive && status === STATES.LISTENING && styles.micBtnListening,
                status === STATES.PROCESSING && styles.micBtnProcessing,
                status === STATES.RESPONDING && styles.micBtnResponding,
              ]}
              onPress={toggleConversation}
              activeOpacity={0.7}
              disabled={status === STATES.CONNECTING}
            >
              <Ionicons
                name={
                  conversationActive
                    ? (status === STATES.LISTENING ? 'mic'
                      : status === STATES.PROCESSING ? 'hourglass-outline'
                      : status === STATES.RESPONDING ? 'volume-high'
                      : 'mic')
                    : 'mic-outline'
                }
                size={36}
                color={Colors.textOnPrimary}
              />
            </TouchableOpacity>
          </Animated.View>

          {conversationActive && (
            <Text style={styles.tapStop}>
              {lang === 'en' ? 'Tap to stop' : 'Appuie pour arrêter'}
            </Text>
          )}
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },

  header: {
    flexDirection: 'row', alignItems: 'center',
    paddingHorizontal: Spacing.md, paddingVertical: Spacing.sm,
    backgroundColor: Colors.warmWhite,
    borderBottomWidth: 1, borderBottomColor: Colors.sand,
  },
  backBtn: {
    width: 38, height: 38, borderRadius: 19,
    backgroundColor: Colors.card, justifyContent: 'center', alignItems: 'center',
    ...Shadows.sm,
  },
  headerCenter: { flex: 1, alignItems: 'center' },
  headerTitle: { ...Typography.h3, color: Colors.primary },
  statusRow: { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: 2 },
  statusDot: { width: 8, height: 8, borderRadius: 4 },
  headerSub: { ...Typography.caption, color: Colors.textMuted },
  chatBtn: {
    width: 38, height: 38, borderRadius: 19,
    backgroundColor: Colors.card, justifyContent: 'center', alignItems: 'center',
    ...Shadows.sm,
  },

  transcriptContainer: { flex: 1 },
  transcriptList: {
    paddingHorizontal: Spacing.md, paddingVertical: Spacing.md, flexGrow: 1,
  },
  emptyTranscript: {
    flex: 1, justifyContent: 'center', alignItems: 'center',
    paddingHorizontal: Spacing.xl,
  },
  emptyTitle: { ...Typography.h3, color: Colors.textPrimary, marginTop: Spacing.md },
  emptyText: {
    ...Typography.body, color: Colors.textMuted,
    textAlign: 'center', marginTop: Spacing.sm, lineHeight: 22,
  },

  msgRow: { flexDirection: 'row', marginBottom: Spacing.sm, alignItems: 'flex-end' },
  msgRowUser: { justifyContent: 'flex-end' },
  msgRowAssistant: { justifyContent: 'flex-start' },
  avatar: {
    width: 26, height: 26, borderRadius: 13,
    backgroundColor: Colors.sand, justifyContent: 'center', alignItems: 'center',
    marginRight: Spacing.xs, marginBottom: 2,
  },
  msgBubble: {
    maxWidth: SCREEN_W * 0.75, paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm, borderRadius: BorderRadius.lg,
  },
  userBubble: { backgroundColor: Colors.primary, borderBottomRightRadius: 4 },
  assistantBubble: {
    backgroundColor: Colors.card, borderBottomLeftRadius: 4,
    borderWidth: 1, borderColor: Colors.sand,
  },
  msgText: { ...Typography.body, lineHeight: 22 },
  userText: { color: Colors.textOnPrimary },
  assistantText: { color: Colors.textPrimary },

  micArea: {
    alignItems: 'center', paddingTop: Spacing.sm,
    backgroundColor: Colors.warmWhite,
    borderTopWidth: 1, borderTopColor: Colors.sand,
  },
  meterRow: {
    flexDirection: 'row', alignItems: 'center', gap: 3,
    height: 32, marginBottom: Spacing.xs,
  },
  meterBar: { width: 4, borderRadius: 2 },
  statusText: { ...Typography.label, marginBottom: Spacing.sm },
  micContainer: { alignItems: 'center' },
  micBtn: {
    width: 88, height: 88, borderRadius: 44,
    backgroundColor: Colors.secondary, justifyContent: 'center', alignItems: 'center',
    ...Shadows.glow,
  },
  micBtnListening: { backgroundColor: '#4CAF50' },
  micBtnProcessing: { backgroundColor: Colors.stone },
  micBtnResponding: { backgroundColor: Colors.primary },
  tapStop: {
    ...Typography.caption, color: Colors.textMuted,
    marginTop: Spacing.xs,
  },
});
