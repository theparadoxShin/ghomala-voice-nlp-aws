/**
 * NAM SA' — API Service
 * Handles REST API calls and WebSocket connection to the backend.
 */

const API_BASE = __DEV__
  ? 'http://192.168.1.100:8000'  // Change to your local IP
  : 'https://your-production-url.amazonaws.com';

const WS_BASE = __DEV__
  ? 'ws://192.168.1.100:8000'
  : 'wss://your-production-url.amazonaws.com';

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


// ============================================================================
// WEBSOCKET — Voice Streaming
// ============================================================================

export class VoiceConnection {
  constructor() {
    this.ws = null;
    this.listeners = {};
    this.sessionId = null;
    this.isConnected = false;
  }

  connect(config = {}) {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(`${WS_BASE}/ws/voice`);

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

// Singleton instance
export const voiceConnection = new VoiceConnection();
