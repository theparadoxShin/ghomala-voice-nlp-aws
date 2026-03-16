/**
 * NAM SA' — API Service
 * Handles REST API calls and WebSocket connection to the backend.
 *
 * Configuration:
 *   Set API_URL in app.json → expo.extra.API_URL
 *   or override with env var EXPO_PUBLIC_API_URL
 */
import Constants from 'expo-constants';

// Cloud Run URL — deployed backend
const PROD_URL = 'https://nam-sa-976647416990.us-central1.run.app';

const API_BASE = __DEV__
  ? (Constants.expoConfig?.extra?.API_URL || 'http://192.168.1.100:8080')
  : (Constants.expoConfig?.extra?.API_URL || PROD_URL);

const WS_BASE = API_BASE.replace(/^http/, 'ws');

// ============================================================================
// REST API
// ============================================================================

export async function sendChat(message, mode = 'tutor', sessionId = null) {
  const response = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      mode,
      session_id: sessionId,
    }),
  });

  if (!response.ok) {
    throw new Error(`Chat API error: ${response.status}`);
  }

  return response.json();
}

export async function translate(text, sourceLang = 'fr', targetLang = 'bbj') {
  const response = await fetch(`${API_BASE}/api/translate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      text,
      source_lang: sourceLang,
      target_lang: targetLang,
    }),
  });

  if (!response.ok) {
    throw new Error(`Translate API error: ${response.status}`);
  }

  return response.json();
}

export async function checkHealth() {
  const response = await fetch(`${API_BASE}/health`);
  return response.json();
}

/**
 * Text-to-Speech — returns base64 audio for a given text.
 * @param {string} text - Text to speak
 * @param {string} language - 'fr', 'en', or 'bbj' (Ghomala')
 * @returns {{ audio: string, mime_type: string }} base64-encoded audio
 */
export async function fetchTTS(text, language = 'fr') {
  const response = await fetch(`${API_BASE}/api/tts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, language }),
  });

  if (!response.ok) {
    throw new Error(`TTS API error: ${response.status}`);
  }

  return response.json();
}


// ============================================================================
// WEBSOCKET — Voice Streaming
// ============================================================================

export class VoiceConnection {
  /**
   * @param {Object} opts
   * @param {boolean} opts.useLive - Use Gemini Live API endpoint (real-time speech-to-speech)
   */
  constructor({ useLive = false } = {}) {
    this.ws = null;
    this.listeners = {};
    this.sessionId = null;
    this.isConnected = false;
    this.endpoint = useLive ? '/ws/live' : '/ws/voice';
  }

  connect(config = {}) {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(`${WS_BASE}${this.endpoint}`);

      this.ws.onopen = () => {
        this.isConnected = true;
        // Send initial config
        this.ws.send(JSON.stringify({
          type: 'config',
          language: config.language || 'fr',
          mode: config.mode || 'tutor',
        }));
        resolve();
      };

      this.ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        this._emit(msg.type, msg);
      };

      this.ws.onerror = (error) => {
        this.isConnected = false;
        this._emit('error', { message: 'Connection error' });
        reject(error);
      };

      this.ws.onclose = () => {
        this.isConnected = false;
        this._emit('disconnected', {});
      };
    });
  }

  sendAudio(base64Audio) {
    if (this.ws && this.isConnected) {
      this.ws.send(JSON.stringify({
        type: 'audio',
        data: base64Audio,
      }));
    }
  }

  updateConfig(config) {
    if (this.ws && this.isConnected) {
      this.ws.send(JSON.stringify({
        type: 'config',
        ...config,
      }));
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.send(JSON.stringify({ type: 'stop' }));
      this.ws.close();
      this.ws = null;
      this.isConnected = false;
    }
  }

  on(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
    return () => {
      this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
    };
  }

  _emit(event, data) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(cb => cb(data));
    }
  }
}

// Singleton instances
export const voiceConnection = new VoiceConnection();
export const liveConnection = new VoiceConnection({ useLive: true });
