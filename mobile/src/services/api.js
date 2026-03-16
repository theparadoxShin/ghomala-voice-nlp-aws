/**
 * NAM SA' — API Service
 * Handles REST API calls and WebSocket connection to the backend.
 *
 * Configuration:
 *   Set API_URL in app.json → expo.extra.API_URL
 *   or override with env var EXPO_PUBLIC_API_URL
 */
import Constants from 'expo-constants';

// AWS ALB — deployed backend
const PROD_URL = 'http://nam-sa-alb-1826409243.us-east-1.elb.amazonaws.com';

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

/**
 * Create a WebSocket connection for voice streaming.
 * @param {'voice'|'live'|'sonic'} endpoint - Which backend WS endpoint to use
 * @returns {WebSocket}
 */
export function createVoiceWebSocket(endpoint = 'live') {
  const path = `/ws/${endpoint}`;
  return new WebSocket(`${WS_BASE}${path}`);
}
