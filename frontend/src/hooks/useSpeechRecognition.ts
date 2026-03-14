import { useState, useEffect, useCallback, useRef } from 'react';

interface SpeechRecognitionHook {
  transcript: string;
  interim: string;
  start: () => void;
  stop: () => void;
  error: string | null;
  isListening: boolean;
  isSupported: boolean;
}

// Augment the global Window type for the vendor-prefixed Web Speech API.
declare global {
  interface Window {
    SpeechRecognition?: typeof SpeechRecognition;
    webkitSpeechRecognition?: typeof SpeechRecognition;
  }
}

type SpeechRecognitionInstance = InstanceType<typeof SpeechRecognition>;

export function useSpeechRecognition(options: {
  language: string;
  continuous: boolean;
  interimResults: boolean;
}): SpeechRecognitionHook {
  const [transcript, setTranscript] = useState('');
  const [interim, setInterim] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);

  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        try { recognitionRef.current.stop(); } catch { /* already stopped */ }
        recognitionRef.current = null;
      }
    };
  }, []);

  const start = useCallback(() => {
    const SpeechRecognitionCtor = window.SpeechRecognition ?? window.webkitSpeechRecognition;
    if (!SpeechRecognitionCtor) {
      setError('Speech recognition not supported');
      return;
    }

    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch { /* ignore */ }
      recognitionRef.current = null;
    }

    const recognition = new SpeechRecognitionCtor();
    recognition.lang = options.language;
    recognition.continuous = options.continuous;
    recognition.interimResults = options.interimResults;

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let final = '';
      let interimResult = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const content = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          final += content;
        } else {
          interimResult += content;
        }
      }

      if (final) setTranscript(prev => prev + ' ' + final);
      setInterim(interimResult);
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      setError(event.error);
      setIsListening(false);
      recognitionRef.current = null;
    };

    recognition.onend = () => {
      setIsListening(false);
      recognitionRef.current = null;
    };

    setTranscript('');
    setInterim('');
    setError(null);

    try {
      recognition.start();
      recognitionRef.current = recognition;
      setIsListening(true);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to start speech recognition');
      recognitionRef.current = null;
    }
  }, [options.language, options.continuous, options.interimResults]);

  const stop = useCallback(() => {
    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch { /* ignore */ }
      recognitionRef.current = null;
    }
    setIsListening(false);
  }, []);

  return {
    transcript,
    interim,
    start,
    stop,
    error,
    isListening,
    isSupported: !!(window.SpeechRecognition ?? window.webkitSpeechRecognition),
  };
}
