/**
 * TTS Helper — NAM SA'
 * Shared Text-to-Speech playback using backend Cloud TTS API + expo-audio.
 * Returns base64 MP3 from /api/tts, saves to cache, plays via createAudioPlayer.
 * All native imports are lazy to avoid splash screen crashes.
 */

import { fetchTTS } from '../services/api';

let _currentPlayer = null;
let _statusSub = null;

/**
 * Play text via backend Cloud TTS.
 * @param {string} text - Text to speak
 * @param {string} lang - Language code: 'fr', 'en', or 'bbj'
 * @param {object} callbacks - { onStart, onDone, onError }
 */
export async function speak(text, lang = 'fr', { onStart, onDone, onError } = {}) {
  try {
    // Stop any currently playing audio
    await stopSpeaking();

    onStart?.();

    const result = await fetchTTS(text, lang);
    if (!result.audio) {
      throw new Error('No audio returned');
    }

    // Lazy imports to avoid crash at app boot
    const FileSystem = require('expo-file-system/legacy');
    const { createAudioPlayer } = require('expo-audio');

    // Save base64 audio to temp file
    const fileUri = `${FileSystem.cacheDirectory}tts_${Date.now()}.mp3`;
    await FileSystem.writeAsStringAsync(fileUri, result.audio, {
      encoding: FileSystem.EncodingType.Base64,
    });

    // Create player and play
    const player = createAudioPlayer(fileUri);
    _currentPlayer = player;

    // Listen for completion
    _statusSub = player.addListener('playbackStatusUpdate', (status) => {
      if (status.didJustFinish) {
        _cleanup();
        onDone?.();
      }
    });

    player.play();
  } catch (e) {
    console.warn('TTS error:', e.message);
    _cleanup();
    onError?.(e);
  }
}

function _cleanup() {
  if (_statusSub) {
    _statusSub.remove();
    _statusSub = null;
  }
  if (_currentPlayer) {
    try { _currentPlayer.release(); } catch { /* ignore */ }
    _currentPlayer = null;
  }
}

/**
 * Stop currently playing TTS audio.
 */
export async function stopSpeaking() {
  if (_currentPlayer) {
    try { _currentPlayer.pause(); } catch { /* ignore */ }
    _cleanup();
  }
}

/**
 * Check if audio is currently playing.
 */
export function isSpeaking() {
  return _currentPlayer !== null;
}
