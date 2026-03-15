import { useState, useEffect, useRef, useCallback } from 'react';
import { Mic2, Volume2 } from 'lucide-react';
import { useSpeechRecognition } from '../../hooks/useSpeechRecognition';
import { useSpeechSynthesis } from '../../hooks/useSpeechSynthesis';
import { useSessionStorage } from '../../hooks/useSessionStorage';
import { apiFetch } from '../../utils/apiClient';
import { SESSION_KEYS } from '../../utils/sessionKeys';
import './Shadowing.css';
import PhraseGenerator from './components/PhraseGenerator';
import PhraseDisplay from './components/PhraseDisplay';
import AccuracyFeedback from './components/AccuracyFeedback';

interface PhraseWord {
  text: string;
  difficulty?: 'easy' | 'medium' | 'hard';
}

interface Phrase {
  text: string;
  translation: string;
  words: PhraseWord[];
}

interface WordMatch {
  index: number;
  status: 'pending' | 'current' | 'matched' | 'missed';
  confidence?: number;
}

export default function Shadowing() {
  const [theme, setTheme] = useSessionStorage(SESSION_KEYS.shadowing.theme, '');
  const [language, setLanguage] = useSessionStorage(SESSION_KEYS.shadowing.language, 'en');
  const [phrases, setPhrases] = useSessionStorage<Phrase[]>(SESSION_KEYS.shadowing.phrases, []);
  const [currentPhraseIndex, setCurrentPhraseIndex] = useSessionStorage(SESSION_KEYS.shadowing.currentIndex, 0);

  const [wordMatches, setWordMatches] = useState<WordMatch[]>([]);
  const [isListening, setIsListening] = useState(false);
  const [accuracy, setAccuracy] = useState<number | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const phraseRef = useRef<HTMLDivElement>(null);

  const { transcript, interim, start, stop, error: speechError, isSupported } = useSpeechRecognition({
    language: language,
    continuous: true,
    interimResults: true
  });

  const { speak: speakPhrase, stop: stopSpeaking, isSpeaking: isTTSPlaying, supported: ttsSupported } = useSpeechSynthesis();

  useEffect(() => {
    if (!transcript || phrases.length === 0) return;

    const currentPhrase = phrases[currentPhraseIndex];
    if (!currentPhrase) return;

    const targetWords = currentPhrase.words.map(w => w.text.toLowerCase());
    const spokenWords = transcript.toLowerCase()
      .split(/\s+/)
      .filter(Boolean)
      .slice(-50);

    const matches = computeWordMatches(targetWords, spokenWords);
    setWordMatches(matches);

    const matched = matches.filter(m => m.status === 'matched').length;
    const score = Math.round((matched / targetWords.length) * 100);
    setAccuracy(score);

    if (score >= 90 && spokenWords.length >= targetWords.length) {
      setTimeout(() => {
        if (accuracy !== null && accuracy >= 90) {
          handleNextPhrase();
        }
      }, 1000);
    }
  }, [transcript, currentPhraseIndex, phrases]);

  useEffect(() => {
    stopSpeaking();
  }, [currentPhraseIndex, language, phrases, stopSpeaking]);

  const computeWordMatches = useCallback((targetWords: string[], spokenWords: string[]): WordMatch[] => {
    const matches: WordMatch[] = targetWords.map((_, idx) => ({
      index: idx,
      status: 'pending' as const
    }));

    const usedSpokenIndices = new Set<number>();

    for (let sIdx = 0; sIdx < spokenWords.length; sIdx++) {
      if (usedSpokenIndices.has(sIdx)) continue;

      const spoken = spokenWords[sIdx];
      let bestMatchIdx = -1;
      let bestSimilarity = 0;

      for (let tIdx = 0; tIdx < targetWords.length; tIdx++) {
        if (matches[tIdx].status === 'matched') continue;

        const target = targetWords[tIdx];
        const similarity = calculateSimilarity(spoken, target);

        if (similarity > bestSimilarity && similarity > 0.6) {
          bestSimilarity = similarity;
          bestMatchIdx = tIdx;
        }
      }

      if (bestMatchIdx !== -1) {
        matches[bestMatchIdx].status = 'matched';
        matches[bestMatchIdx].confidence = bestSimilarity;
        usedSpokenIndices.add(sIdx);
      }
    }

    if (interim && interim.trim()) {
      const interimWords = interim.toLowerCase().split(/\s+/).filter(Boolean);
      const lastInterim = interimWords[interimWords.length - 1];
      if (lastInterim) {
        for (let tIdx = 0; tIdx < targetWords.length; tIdx++) {
          if (matches[tIdx].status === 'pending') {
            const similarity = calculateSimilarity(lastInterim, targetWords[tIdx]);
            if (similarity > 0.4) {
              matches[tIdx].status = 'current';
            }
            break;
          }
        }
      }
    }

    return matches;
  }, [interim]);

  const calculateSimilarity = (a: string, b: string): number => {
    a = a.toLowerCase().replace(/[^a-z0-9]/g, '');
    b = b.toLowerCase().replace(/[^a-z0-9]/g, '');

    if (a === b) return 1.0;
    if (a.length === 0 || b.length === 0) return 0;

    const distance = levenshteinDistance(a, b);
    const maxLen = Math.max(a.length, b.length);
    return 1 - distance / maxLen;
  };

  const levenshteinDistance = (a: string, b: string): number => {
    const matrix = Array(b.length + 1).fill(null).map(() => Array(a.length + 1).fill(null));

    for (let i = 0; i <= a.length; i++) matrix[0][i] = i;
    for (let j = 0; j <= b.length; j++) matrix[j][0] = j;

    for (let j = 1; j <= b.length; j++) {
      for (let i = 1; i <= a.length; i++) {
        const cost = a[i - 1] === b[j - 1] ? 0 : 1;
        matrix[j][i] = Math.min(
          matrix[j][i - 1] + 1,
          matrix[j - 1][i] + 1,
          matrix[j - 1][i - 1] + cost
        );
      }
    }

    return matrix[b.length][a.length];
  };

  const handleGenerate = async () => {
    if (!theme.trim()) {
      setError('Please enter a theme');
      return;
    }

    setIsGenerating(true);
    setError(null);
    setPhrases([]);
    setCurrentPhraseIndex(0);
    setWordMatches([]);
    setAccuracy(null);

    try {
      const response = await apiFetch('/shadowing/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ theme, language, num_phrases: 10 })
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: 'Failed to generate phrases' }));
        throw new Error(err.detail || 'Failed to generate phrases');
      }

      const data = await response.json();
      setPhrases(data.phrases);
      startSession();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'An error occurred while generating phrases');
    } finally {
      setIsGenerating(false);
    }
  };

  const startSession = async () => {
    try {
      const response = await apiFetch('/shadowing/start-session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ theme, language })
      });

      if (response.ok) {
        const data = await response.json();
        setSessionId(data.session_id);
      }
    } catch (err) {
      console.error('Failed to create session:', err);
    }
  };

  const toggleListening = () => {
    if (isListening) {
      stop();
    } else {
      stopSpeaking();
      start();
    }
    setIsListening(!isListening);
  };

  const handleSpeakPhrase = () => {
    if (phrases.length === 0 || currentPhraseIndex >= phrases.length) return;
    const currentPhrase = phrases[currentPhraseIndex];
    if (currentPhrase) {
      if (isTTSPlaying) {
        stopSpeaking();
      } else {
        speakPhrase(currentPhrase.text, language);
      }
    }
  };

  const handleNextPhrase = async () => {
    stopSpeaking();

    if (sessionId && phrases.length > 0 && currentPhraseIndex < phrases.length) {
      const currentPhrase = phrases[currentPhraseIndex];
      const matchedCount = wordMatches.filter(m => m.status === 'matched').length;

      try {
        await apiFetch('/shadowing/record-attempt', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: sessionId,
            phrase_index: currentPhraseIndex,
            phrase_text: currentPhrase.text,
            accuracy_score: accuracy || 0,
            words_matched: matchedCount,
            total_words: currentPhrase.words.length
          })
        });
      } catch (err) {
        console.error('Failed to record attempt:', err);
      }
    }

    if (currentPhraseIndex < phrases.length - 1) {
      setCurrentPhraseIndex(currentPhraseIndex + 1);
      setWordMatches([]);
      setAccuracy(null);
      if (phraseRef.current) {
        phraseRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    } else {
      stop();
      setIsListening(false);
      setSessionId(null);
    }
  };

  const handlePhraseClick = (idx: number) => {
    setCurrentPhraseIndex(idx);
    setWordMatches([]);
    setAccuracy(null);
    setIsListening(false);
    stop();
    stopSpeaking();
  };

  const handleStartOver = () => {
    if (window.confirm('Start over from the first phrase?')) {
      setCurrentPhraseIndex(0);
      setWordMatches([]);
      setAccuracy(null);
      setIsListening(false);
      stop();
      stopSpeaking();
      setPhrases([]);
    }
  };

  return (
    <div className="page-container shadowing-page animate-fade-in">
      <header className="page-header">
        <h2><Mic2 size={32} className="header-icon" /> Shadowing Practice</h2>
        <p>Listen. Repeat. Improve.</p>
      </header>

      {!isSupported && (
        <div className="error-banner">
          Speech recognition is not supported in your browser. Please use Chrome or Edge for the best experience.
        </div>
      )}

      {error && (
        <div className="error-message" style={{ color: '#ff6b6b', marginBottom: '1rem', padding: '0.75rem', background: 'rgba(255,107,107,0.1)', borderRadius: '0.5rem' }}>
          {error}
        </div>
      )}

      {speechError && (
        <div className="error-message" style={{ color: '#ffa726', marginBottom: '1rem', padding: '0.75rem', background: 'rgba(255,167,38,0.1)', borderRadius: '0.5rem' }}>
          Speech recognition error: {speechError}
        </div>
      )}

      {phrases.length === 0 && (
        <PhraseGenerator
          theme={theme}
          setTheme={setTheme}
          language={language}
          setLanguage={setLanguage}
          isGenerating={isGenerating}
          onGenerate={handleGenerate}
        />
      )}

      {phrases.length > 0 && (
        <div className="shadowing-main" ref={phraseRef}>
          <div className="phrase-container glass-panel">
            <div className="phrase-header">
              <span className="phrase-counter">{currentPhraseIndex + 1} / {phrases.length}</span>
              <span className="phrase-theme">{theme}</span>
            </div>

            <PhraseDisplay
              phrases={phrases}
              currentPhraseIndex={currentPhraseIndex}
              wordMatches={wordMatches}
            />

            <AccuracyFeedback
              accuracy={accuracy}
              interim={interim}
              isListening={isListening}
              transcript={transcript}
              onClearRetry={() => { setWordMatches([]); setAccuracy(null); }}
            />
          </div>

          <div className="controls-panel">
            <button
              className={`mic-control-btn ${isListening ? 'listening' : ''}`}
              onClick={toggleListening}
              disabled={!isSupported}
              title={isListening ? 'Stop listening' : 'Start speaking'}
            >
              <Mic2 size={24} />
              <span>{isListening ? 'Listening...' : 'Speak'}</span>
            </button>

            <button
              className={`listen-btn ${isTTSPlaying ? 'playing' : ''}`}
              onClick={handleSpeakPhrase}
              disabled={!ttsSupported || phrases.length === 0}
              title={isTTSPlaying ? 'Stop' : 'Listen to phrase'}
            >
              <Volume2 size={24} />
              <span>{isTTSPlaying ? 'Playing...' : 'Listen'}</span>
            </button>

            <button
              className="next-btn"
              onClick={handleNextPhrase}
              disabled={currentPhraseIndex >= phrases.length - 1 && accuracy !== null && accuracy >= 90}
              title="Move to next phrase"
            >
              Next →
            </button>

            <button
              className="start-over-btn"
              onClick={handleStartOver}
              title="Start over from the beginning"
            >
              Start Over
            </button>
          </div>

          <div className="phrase-navigation">
            <h4>Phrase List</h4>
            <div className="phrase-items">
              {phrases.map((phrase, idx) => (
                <div
                  key={idx}
                  className={`phrase-item ${idx === currentPhraseIndex ? 'active' : ''}
                    ${idx < currentPhraseIndex ? 'completed' : ''}`}
                  onClick={() => handlePhraseClick(idx)}
                >
                  <span className="phrase-num">{idx + 1}.</span>
                  <span className="phrase-preview">{phrase.text}</span>
                  {wordMatches[idx] && idx === currentPhraseIndex && (
                    <span className="mini-accuracy">{accuracy !== null ? `${accuracy}%` : '-'}</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
