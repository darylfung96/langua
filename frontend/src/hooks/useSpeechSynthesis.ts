import { useCallback, useRef, useEffect, useState } from 'react';
import { apiPost, ApiError } from '../utils/apiClient';

interface SpeechSynthesisHook {
  speak: (text: string, lang?: string) => void;
  stop: () => void;
  isSpeaking: boolean;
  supported: boolean;
  voices: SpeechSynthesisVoice[];
}

// Only attempt Google Cloud TTS when explicitly enabled via env var.
// Set VITE_GOOGLE_TTS_ENABLED=true in frontend/.env once you have an API key.
const GOOGLE_TTS_ENABLED = import.meta.env.VITE_GOOGLE_TTS_ENABLED === 'true';

function playBase64Audio(base64: string): HTMLAudioElement {
  const audio = new Audio(`data:audio/mp3;base64,${base64}`);
  audio.play();
  return audio;
}

export function useSpeechSynthesis(): SpeechSynthesisHook {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    if (!('speechSynthesis' in window)) return;

    const loadVoices = () => setVoices(window.speechSynthesis.getVoices());
    loadVoices();
    if (window.speechSynthesis.onvoiceschanged !== undefined) {
      window.speechSynthesis.onvoiceschanged = loadVoices;
    }
    return () => { window.speechSynthesis.cancel(); };
  }, []);

  const stop = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    setIsSpeaking(false);
    utteranceRef.current = null;
  }, []);

  const speakWithBrowser = useCallback((text: string, lang: string) => {
    if (!('speechSynthesis' in window)) return;

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utteranceRef.current = utterance;

    const matchingVoice = voices.find(v => v.lang.startsWith(lang) || v.lang === lang);
    if (matchingVoice) {
      utterance.voice = matchingVoice;
      utterance.lang = matchingVoice.lang;
    } else {
      utterance.lang = lang;
    }
    utterance.rate = 0.9;
    utterance.pitch = 1;
    utterance.volume = 1;
    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => { setIsSpeaking(false); utteranceRef.current = null; };
    utterance.onerror = () => { setIsSpeaking(false); utteranceRef.current = null; };
    window.speechSynthesis.speak(utterance);
  }, [voices]);

  const speak = useCallback((text: string, lang: string = 'en-US') => {
    stop();

    if (!GOOGLE_TTS_ENABLED) {
      speakWithBrowser(text, lang);
      return;
    }

    // Google TTS is enabled — try it first, fall back to browser on any failure
    setIsSpeaking(true);
    apiPost<{ audioContent: string }>('/shadowing/tts', { text, language: lang })
      .then(({ audioContent }) => {
        const audio = playBase64Audio(audioContent);
        audioRef.current = audio;
        audio.onended = () => { setIsSpeaking(false); audioRef.current = null; };
        audio.onerror = () => { setIsSpeaking(false); audioRef.current = null; };
      })
      .catch((err: unknown) => {
        setIsSpeaking(false);
        if (!(err instanceof ApiError && err.status === 503)) {
          console.warn('Google TTS failed, falling back to browser TTS:', err);
        }
        speakWithBrowser(text, lang);
      });
  }, [stop, speakWithBrowser]);

  return {
    speak,
    stop,
    isSpeaking,
    supported: 'speechSynthesis' in window,
    voices,
  };
}
