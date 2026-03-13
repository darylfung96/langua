import React, { useState, useRef, useEffect, useMemo } from 'react';
import { Sparkles, Play, Pause, BookOpen, Volume2, Loader2, Save, Trash2, Brain, RefreshCw, CheckCircle2, XCircle, Trophy } from 'lucide-react';
import './StoryWeaver.css';
import { apiFetch } from '../utils/apiClient';

const AUDIO_SAMPLE_RATE = 24000;
const TOAST_TIMEOUT_MS = 2000;

interface VocabWord {
  word: string;
  meaning_in_target: string;
  equivalent_in_english: string;
}

interface StoryResponse {
  title: string;
  story: string;
  vocabulary: VocabWord[];
}

interface SavedStory {
  id: string;
  title: string;
  language: string;
  created_at: string;
}

interface QuizQuestion {
  id: number;
  type: 'multiple_choice' | 'fill_blank' | 'true_false';
  question: string;
  options?: string[];
  correct_answer: string;
  explanation: string;
  word: string;
}

interface QuizData {
  questions: QuizQuestion[];
}

const createWavUrl = (base64Data: string, sampleRate = AUDIO_SAMPLE_RATE) => {
  const binaryString = atob(base64Data);
  const pcmData = new Uint8Array(binaryString.length);
  for (let i = 0; i < binaryString.length; i++) {
    pcmData[i] = binaryString.charCodeAt(i);
  }

  const numChannels = 1;
  const bitsPerSample = 16;
  const header = new ArrayBuffer(44);
  const view = new DataView(header);

  const writeString = (v: DataView, offset: number, str: string) => {
    for (let i = 0; i < str.length; i++) {
      v.setUint8(offset + i, str.charCodeAt(i));
    }
  };

  writeString(view, 0, 'RIFF');
  view.setUint32(4, 36 + pcmData.length, true);
  writeString(view, 8, 'WAVE');

  writeString(view, 12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true); // PCM
  view.setUint16(22, numChannels, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * numChannels * (bitsPerSample / 8), true);
  view.setUint16(32, numChannels * (bitsPerSample / 8), true);
  view.setUint16(34, bitsPerSample, true);

  writeString(view, 36, 'data');
  view.setUint32(40, pcmData.length, true);

  const wavArray = new Uint8Array(44 + pcmData.length);
  wavArray.set(new Uint8Array(header), 0);
  wavArray.set(pcmData, 44);

  const blob = new Blob([wavArray], { type: 'audio/wav' });
  return URL.createObjectURL(blob);
};

const LANGUAGES = {
  'es': 'Spanish',
  'fr': 'French',
  'de': 'German',
  'it': 'Italian',
  'ja': 'Japanese',
  'ko': 'Korean',
  'zh-CN': 'Chinese (Simplified)',
  'zh-TW': 'Chinese (Traditional)',
  'ru': 'Russian',
  'pt': 'Portuguese',
  'ar': 'Arabic',
} as const;

const StoryWeaver = () => {
  const [language, setLanguage] = useState('fr');
  const [inputWords, setInputWords] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [storyData, setStoryData] = useState<StoryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [savedStories, setSavedStories] = useState<SavedStory[]>([]);
  const [isLoadingSavedStories, setIsLoadingSavedStories] = useState(false);
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null);

  // Quiz state
  const [quizData, setQuizData] = useState<QuizData | null>(null);
  const [isGeneratingQuiz, setIsGeneratingQuiz] = useState(false);
  const [userAnswers, setUserAnswers] = useState<Record<number, string>>({});
  const [fillBlankInputs, setFillBlankInputs] = useState<Record<number, string>>({});
  const [quizSubmitted, setQuizSubmitted] = useState(false);
  const [quizScore, setQuizScore] = useState(0);

  // Audio state
  const [isPlaying, setIsPlaying] = useState(false);
  const [isGeneratingAudio, setIsGeneratingAudio] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Load saved stories on mount
  useEffect(() => {
    loadSavedStories();
  }, []);

  const loadSavedStories = async () => {
    setIsLoadingSavedStories(true);
    try {
      const response = await apiFetch('/stories');
      if (response.ok) {
        const data = await response.json();
        setSavedStories(data.stories);
      }
    } catch {
      // silently fail — saved stories list is a convenience
    } finally {
      setIsLoadingSavedStories(false);
    }
  };

  const saveStory = async () => {
    if (!storyData) return;

    setIsSaving(true);
    setError(null);
    setSuccess(null);

    try {
      let audioData = null;

      // Extract base64 audio if available
      if (audioUrl) {
        if (audioUrl.startsWith('data:')) {
          audioData = audioUrl.split(',')[1];
        } else if (audioUrl.startsWith('blob:')) {
          const response = await fetch(audioUrl);
          const blob = await response.blob();
          audioData = await new Promise<string>((resolve) => {
            const reader = new FileReader();
            reader.onloadend = () => {
              const base64 = (reader.result as string).split(',')[1];
              resolve(base64);
            };
            reader.readAsDataURL(blob);
          });
        }
      }

      const saveResponse = await apiFetch('/stories', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: `${storyData.title} (${inputWords})`,
          story_content: storyData.story,
          language: language,
          vocabulary: JSON.stringify(storyData.vocabulary),
          quiz: quizData ? JSON.stringify(quizData) : null,
          audio: audioData
        })
      });

      if (!saveResponse.ok) {
        throw new Error('Failed to save story');
      }

      await saveResponse.json();
      setSuccess('Story saved successfully!');
      setTimeout(() => setSuccess(null), TOAST_TIMEOUT_MS);

      // Reload saved stories
      loadSavedStories();
    } catch (err) {
      setError((err as Error).message || 'Failed to save story');
    } finally {
      setIsSaving(false);
    }
  };

  const loadStoryFromSaved = async (storyId: string) => {
    try {
      const response = await apiFetch(`/stories/${storyId}`);
      if (!response.ok) throw new Error('Failed to load story');
      const data = await response.json();
      setStoryData({
        title: data.title,
        story: data.story_content,
        vocabulary: data.vocabulary
      });
      // Set language to match the saved story
      setLanguage(data.language);
      // Load quiz if saved
      if (data.quiz) {
        setQuizData(data.quiz);
        setUserAnswers({});
        setFillBlankInputs({});
        setQuizSubmitted(false);
        setQuizScore(0);
      } else {
        setQuizData(null);
      }
      // Set audio URL from saved data if available
      if (data.audio_file_path) {
        apiFetch(`/${data.audio_file_path}`)
          .then(res => {
            if (!res.ok) throw new Error('Failed to load audio');
            return res.blob();
          })
          .then(blob => setAudioUrl(URL.createObjectURL(blob)))
          .catch(() => setAudioUrl(null));
      } else {
        setAudioUrl(null);
      }
      setIsPlaying(false);
      setCurrentTime(0);
      setDuration(0);
    } catch (err) {
      setError('Failed to load story');
    }
  };

  const deleteStory = async (storyId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (pendingDeleteId !== storyId) {
      setPendingDeleteId(storyId);
      return;
    }
    setPendingDeleteId(null);
    try {
      await apiFetch(`/stories/${storyId}`, { method: 'DELETE' });
      loadSavedStories();
    } catch (err) {
      setError('Failed to delete story');
    }
  };

  useEffect(() => {
    // Cleanup dynamic URL if needed (we'll use base64 mostly, but good practice)
    return () => {
      if (audioUrl && audioUrl.startsWith('blob:')) {
        URL.revokeObjectURL(audioUrl);
      }
    };
  }, [audioUrl]);

  // Handle Playback State
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleEnded = () => setIsPlaying(false);
    const handlePause = () => setIsPlaying(false);
    const handlePlay = () => setIsPlaying(true);
    const handleTimeUpdate = () => setCurrentTime(audio.currentTime);
    const handleLoadedMetadata = () => setDuration(audio.duration);

    audio.addEventListener('ended', handleEnded);
    audio.addEventListener('pause', handlePause);
    audio.addEventListener('play', handlePlay);
    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('loadedmetadata', handleLoadedMetadata);

    return () => {
      audio.removeEventListener('ended', handleEnded);
      audio.removeEventListener('pause', handlePause);
      audio.removeEventListener('play', handlePlay);
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
    };
  }, [audioUrl]);

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const time = parseFloat(e.target.value);
    if (audioRef.current) {
      audioRef.current.currentTime = time;
      setCurrentTime(time);
    }
  };

  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const storyWords = useMemo(() => {
    if (!storyData) return [];

    const result: { text: string; index: number; isHighlight: boolean; title?: string }[] = [];
    let currentIdx = 0;

    const parts = storyData.story.split(/(<span[^>]*>.*?<\/span>)/g);

    parts.forEach(part => {
      if (part.startsWith('<span')) {
        const titleMatch = part.match(/title='([^']+)'/);
        const contentMatch = part.match(/>([^<]+)<\//);
        const title = titleMatch ? titleMatch[1] : undefined;
        const content = contentMatch ? contentMatch[1] : '';

        const words = content.split(/\s+/).filter(Boolean);
        words.forEach(w => {
          currentIdx++;
          result.push({ text: w, index: currentIdx, isHighlight: true, title });
        });
      } else {
        const words = part.split(/\s+/).filter(Boolean);
        words.forEach(w => {
          currentIdx++;
          result.push({ text: w, index: currentIdx, isHighlight: false });
        });
      }
    });

    return result;
  }, [storyData]);

  const jumpToWord = (index: number, total: number) => {
    if (audioRef.current && duration) {
      const time = (index / total) * duration;
      audioRef.current.currentTime = time;
      if (!isPlaying) {
        audioRef.current.play().catch(e => console.error("Error playing audio on jump:", e));
      }
    }
  };

  const jumpToVocab = (word: string) => {
    const found = storyWords.find(w => w.text.toLowerCase().includes(word.toLowerCase()));
    if (found) {
      jumpToWord(found.index, storyWords.length);
    }
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputWords.trim()) return;

    setIsGenerating(true);
    setStoryData(null);
    setAudioUrl(null);
    setIsPlaying(false);
    setError(null);
    setQuizData(null);
    setUserAnswers({});
    setFillBlankInputs({});
    setQuizSubmitted(false);
    setQuizScore(0);

    try {
      const response = await apiFetch('/gemini/generate-story', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ language, words: inputWords }),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to generate story.');
      }

      const parsedData = await response.json();
      setStoryData(parsedData);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'An error occurred while generating the story.');
    } finally {
      setIsGenerating(false);
    }
  };

  const generateAudio = async () => {
    if (!storyData || isGeneratingAudio) return;

    setIsGeneratingAudio(true);
    setError(null);

    try {
      const response = await apiFetch('/gemini/generate-audio', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          language,
          title: storyData.title,
          story: storyData.story,
        }),
      }, 200_000);

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to generate audio.');
      }

      const { audio_data, mime_type } = await response.json();

      let url = '';
      if (mime_type.includes('pcm')) {
        url = createWavUrl(audio_data);
      } else {
        url = `data:${mime_type};base64,${audio_data}`;
      }
      setAudioUrl(url);
      if (audioRef.current) {
        setTimeout(() => {
          audioRef.current?.play().catch(e => console.error("Error playing audio:", e));
        }, 0);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'An error occurred while generating audio.');
    } finally {
      setIsGeneratingAudio(false);
    }
  };

  const toggleAudio = () => {
    if (!audioUrl) {
      // First time clicking listen, generate the audio
      generateAudio();
    } else if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play().catch(e => console.error("Error playing audio:", e));
      }
    }
  };

  const generateQuiz = async () => {
    if (!storyData || isGeneratingQuiz) return;

    setIsGeneratingQuiz(true);
    setQuizSubmitted(false);
    setUserAnswers({});
    setFillBlankInputs({});
    setQuizScore(0);
    setError(null);

    try {
      const response = await apiFetch('/gemini/generate-quiz', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          language,
          story: storyData.story,
          vocabulary: storyData.vocabulary,
        }),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to generate quiz.');
      }

      const parsed: QuizData = await response.json();
      setQuizData(parsed);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to generate quiz.');
    } finally {
      setIsGeneratingQuiz(false);
    }
  };

  const handleAnswerSelect = (questionId: number, answer: string) => {
    if (quizSubmitted) return;
    setUserAnswers(prev => ({ ...prev, [questionId]: answer }));
  };

  const handleFillBlankChange = (questionId: number, value: string) => {
    if (quizSubmitted) return;
    setFillBlankInputs(prev => ({ ...prev, [questionId]: value }));
  };

  const submitQuiz = () => {
    if (!quizData) return;
    let score = 0;
    quizData.questions.forEach(q => {
      if (q.type === 'fill_blank') {
        const userAnswer = (fillBlankInputs[q.id] || '').trim().toLowerCase();
        if (userAnswer === q.correct_answer.toLowerCase()) score++;
      } else {
        if ((userAnswers[q.id] || '').toLowerCase() === q.correct_answer.toLowerCase()) score++;
      }
    });
    setQuizScore(score);
    setQuizSubmitted(true);
  };

  const retakeQuiz = () => {
    setUserAnswers({});
    setFillBlankInputs({});
    setQuizSubmitted(false);
    setQuizScore(0);
  };

  const isAnswerCorrect = (q: QuizQuestion): boolean => {
    if (q.type === 'fill_blank') {
      return (fillBlankInputs[q.id] || '').trim().toLowerCase() === q.correct_answer.toLowerCase();
    }
    return (userAnswers[q.id] || '').toLowerCase() === q.correct_answer.toLowerCase();
  };

  return (
    <div className="page-container animate-fade-in story-weaver-page">
      <header className="page-header text-center">
        <h2 className="title-gradient">Story Weaver</h2>
        <p className="subtitle">Enter a few words and we'll weave them into a memorable story.</p>
      </header>

      <div className="story-weaver-grid">
        <div className="input-section glass-panel">
          <form onSubmit={handleGenerate}>
            <div className="input-group">
              <label htmlFor="language">Target Language</label>
              <select
                id="language"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  borderRadius: '0.5rem',
                  background: 'rgba(255,255,255,0.05)',
                  border: '1px solid rgba(255,255,255,0.1)',
                  color: 'white',
                  fontFamily: 'inherit',
                  marginBottom: '1rem',
                  outline: 'none',
                  cursor: 'pointer'
                }}
              >
                <option value="es" style={{ color: 'black' }}>Spanish</option>
                <option value="fr" style={{ color: 'black' }}>French</option>
                <option value="de" style={{ color: 'black' }}>German</option>
                <option value="it" style={{ color: 'black' }}>Italian</option>
                <option value="ja" style={{ color: 'black' }}>Japanese</option>
                <option value="ko" style={{ color: 'black' }}>Korean</option>
                <option value="zh-CN" style={{ color: 'black' }}>Chinese (Simplified)</option>
                <option value="ru" style={{ color: 'black' }}>Russian</option>
                <option value="pt" style={{ color: 'black' }}>Portuguese</option>
              </select>
            </div>
            <div className="input-group">
              <label htmlFor="words">Vocabulary Words</label>
              <textarea
                id="words"
                placeholder="e.g. gato, leche, rápido..."
                value={inputWords}
                onChange={(e) => setInputWords(e.target.value)}
                rows={4}
              />
              <p className="input-hint">Separate words with commas for best results.</p>
            </div>

            {error && <div className="error-message" style={{ color: '#ff6b6b', marginBottom: '1rem', fontSize: '0.875rem', padding: '0.5rem', background: 'rgba(255,107,107,0.1)', borderRadius: '0.25rem' }}>{error}</div>}
            {success && <div className="success-message" style={{ color: '#51cf66', marginBottom: '1rem', fontSize: '0.875rem', padding: '0.5rem', background: 'rgba(81,207,102,0.1)', borderRadius: '0.25rem' }}>{success}</div>}

            <button
              type="submit"
              className={`generate-btn ${isGenerating ? 'generating' : ''}`}
              disabled={isGenerating || !inputWords.trim()}
            >
              {isGenerating ? (
                <>
                  <div className="spinner"></div>
                  Weaving Magic...
                </>
              ) : (
                <>
                  <Sparkles size={20} />
                  Weave Story
                </>
              )}
            </button>
          </form>

          {!isLoadingSavedStories && savedStories.length > 0 && (
            <div style={{ marginTop: '2rem', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '1.5rem' }}>
              <h3 style={{ marginBottom: '1rem', fontSize: '1rem', fontWeight: '600' }}>📚 Saved Stories</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', maxHeight: '300px', overflowY: 'auto' }}>
                {savedStories.map(story => (
                  <button
                    key={story.id}
                    onClick={() => loadStoryFromSaved(story.id)}
                    style={{
                      padding: '0.75rem',
                      background: 'rgba(255,255,255,0.05)',
                      border: '1px solid rgba(255,255,255,0.1)',
                      borderRadius: '0.5rem',
                      color: 'white',
                      textAlign: 'left',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center'
                    }}
                    onMouseEnter={(e) => {
                      (e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.1)';
                    }}
                    onMouseLeave={(e) => {
                      (e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.05)';
                    }}
                  >
                    <div>
                      <div style={{ fontSize: '0.9rem', fontWeight: '500' }}>{story.title}</div>
                      <div style={{ fontSize: '0.75rem', opacity: 0.6 }}>
                        {LANGUAGES[story.language as keyof typeof LANGUAGES] || story.language}
                      </div>
                    </div>
                    <button
                      onClick={(e) => deleteStory(story.id, e)}
                      style={{
                        background: pendingDeleteId === story.id ? 'rgba(255,107,107,0.5)' : 'rgba(255,107,107,0.2)',
                        border: 'none',
                        borderRadius: '0.25rem',
                        padding: '0.25rem 0.5rem',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        color: '#ff6b6b',
                        fontSize: pendingDeleteId === story.id ? '0.7rem' : undefined,
                      }}
                      title={pendingDeleteId === story.id ? 'Click again to confirm delete' : 'Delete'}
                    >
                      {pendingDeleteId === story.id ? 'Confirm?' : <Trash2 size={14} />}
                    </button>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {storyData && (
          <div className="result-section animate-fade-in">
            <div className="story-card glass-panel">
              <div className="card-header">
                <h3><BookOpen size={20} /> {storyData.title}</h3>

                <div style={{ display: 'flex', gap: '0.75rem' }}>
                  <button className="audio-btn" onClick={toggleAudio} disabled={isGeneratingAudio}>
                    {isGeneratingAudio ? (
                      <Loader2 size={18} className="spinner" />
                    ) : isPlaying ? (
                      <Pause size={18} />
                    ) : (
                      <Play size={18} />
                    )}
                    <span>{isGeneratingAudio ? 'Generating...' : isPlaying ? 'Pause' : 'Listen'}</span>
                    {isPlaying && <div className="audio-waves">
                      <span></span><span></span><span></span>
                    </div>}
                  </button>

                  <button className="audio-btn" onClick={saveStory} disabled={isSaving} style={{ background: isSaving ? 'rgba(99, 102, 241, 0.5)' : undefined }}>
                    <Save size={18} />
                    <span>{isSaving ? 'Saving...' : 'Save'}</span>
                  </button>
                </div>
              </div>

              {audioUrl && (
                <div className="audio-controls-container" style={{ padding: '0 1.5rem 1.5rem' }}>
                  <audio ref={audioRef} src={audioUrl} />
                  <div className="audio-seekbar-row" style={{ display: 'flex', alignItems: 'center', gap: '1rem', width: '100%' }}>
                    <span style={{ fontSize: '0.75rem', opacity: 0.6, minWidth: '35px' }}>{formatTime(currentTime)}</span>
                    <input
                      type="range"
                      min="0"
                      max={duration || 0}
                      step="0.1"
                      value={currentTime}
                      onChange={handleSeek}
                      style={{
                        flex: 1,
                        accentColor: '#6366f1',
                        cursor: 'pointer',
                        height: '4px',
                        borderRadius: '2px'
                      }}
                    />
                    <span style={{ fontSize: '0.75rem', opacity: 0.6, minWidth: '35px' }}>{formatTime(duration)}</span>
                  </div>
                </div>
              )}

              <div className="story-content">
                <p>
                  {storyWords.map((w, i) => (
                    <React.Fragment key={i}>
                      <span
                        onClick={() => jumpToWord(w.index, storyWords.length)}
                        className={`${w.isHighlight ? 'highlight' : ''} clickable-word`}
                        title={w.title}
                      >
                        {w.text}
                      </span>
                      {' '}
                    </React.Fragment>
                  ))}
                </p>
              </div>
            </div>

            <div className="vocab-table-container glass-panel">
              <div className="card-header border-bottom">
                <h3>Vocabulary Breakdown</h3>
              </div>
              <div className="table-responsive">
                <table className="vocab-table">
                  <thead>
                    <tr>
                      <th>Original Word</th>
                      <th>Meaning in {LANGUAGES[language as keyof typeof LANGUAGES] || language}</th>
                      <th>Equivalent Word in English</th>
                    </tr>
                  </thead>
                  <tbody>
                    {storyData.vocabulary.map((vocab, i) => (
                      <tr key={i}>
                        <td className="vocab-word">
                          <Volume2
                            size={16}
                            className="word-audio"
                            onClick={() => jumpToVocab(vocab.word)}
                          />
                          {vocab.word}
                        </td>
                        <td>{vocab.meaning_in_target}</td>
                        <td className="vocab-mnemonic">{vocab.equivalent_in_english}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Quiz Section */}
            <div className="quiz-container glass-panel">
              <div className="card-header border-bottom">
                <h3><Brain size={20} /> Vocabulary Quiz</h3>
                <button
                  className="quiz-generate-btn"
                  onClick={generateQuiz}
                  disabled={isGeneratingQuiz}
                >
                  {isGeneratingQuiz ? (
                    <><Loader2 size={16} className="spinner" /> Crafting Quiz...</>
                  ) : quizData ? (
                    <><RefreshCw size={16} /> New Quiz</>
                  ) : (
                    <><Sparkles size={16} /> Generate Quiz</>
                  )}
                </button>
              </div>

              {!quizData && !isGeneratingQuiz && (
                <div className="quiz-empty-state">
                  <Brain size={48} className="quiz-empty-icon" />
                  <p>Test your memory! Generate a quiz based on the vocabulary words.</p>
                  <button className="quiz-start-btn" onClick={generateQuiz}>
                    <Sparkles size={18} /> Generate Quiz
                  </button>
                </div>
              )}

              {isGeneratingQuiz && (
                <div className="quiz-loading">
                  <div className="quiz-loading-dots">
                    <span></span><span></span><span></span>
                  </div>
                  <p>Crafting your personalized quiz...</p>
                </div>
              )}

              {quizData && !isGeneratingQuiz && (
                <div className="quiz-content">
                  {quizSubmitted && (
                    <div className={`quiz-score-banner ${quizScore === quizData.questions.length ? 'perfect' : quizScore >= quizData.questions.length * 0.7 ? 'great' : 'keep-trying'}`}>
                      <Trophy size={28} />
                      <div>
                        <div className="quiz-score-number">{quizScore} / {quizData.questions.length}</div>
                        <div className="quiz-score-message">
                          {quizScore === quizData.questions.length ? '🎉 Perfect! You nailed it!' :
                            quizScore >= quizData.questions.length * 0.7 ? '🌟 Great job! Keep it up!' :
                              '💪 Keep practicing — you\'ve got this!'}
                        </div>
                      </div>
                      <button className="quiz-retake-btn" onClick={retakeQuiz}>
                        <RefreshCw size={16} /> Retake
                      </button>
                    </div>
                  )}

                  <div className="quiz-questions">
                    {quizData.questions.map((q, idx) => {
                      const answered = q.type === 'fill_blank'
                        ? !!fillBlankInputs[q.id]?.trim()
                        : !!userAnswers[q.id];
                      const correct = quizSubmitted ? isAnswerCorrect(q) : null;

                      return (
                        <div
                          key={q.id}
                          className={`quiz-question ${quizSubmitted ? (correct ? 'correct' : 'incorrect') : answered ? 'answered' : ''}`}
                        >
                          <div className="quiz-question-header">
                            <span className="quiz-q-number">Q{idx + 1}</span>
                            <span className={`quiz-type-badge quiz-type-${q.type}`}>
                              {q.type === 'multiple_choice' ? 'Multiple Choice' :
                                q.type === 'fill_blank' ? 'Fill in the Blank' : 'True / False'}
                            </span>
                            {quizSubmitted && (
                              correct
                                ? <CheckCircle2 size={20} className="quiz-result-icon correct-icon" />
                                : <XCircle size={20} className="quiz-result-icon incorrect-icon" />
                            )}
                          </div>

                          <p className="quiz-question-text">{q.question}</p>

                          {q.type === 'fill_blank' ? (
                            <div className="quiz-fill-blank">
                              <input
                                type="text"
                                placeholder="Type your answer..."
                                value={fillBlankInputs[q.id] || ''}
                                onChange={(e) => handleFillBlankChange(q.id, e.target.value)}
                                disabled={quizSubmitted}
                                className={`quiz-fill-input ${quizSubmitted ? (correct ? 'input-correct' : 'input-incorrect') : ''}`}
                              />
                              {quizSubmitted && !correct && (
                                <div className="quiz-correct-answer">
                                  ✓ Correct: <strong>{q.correct_answer}</strong>
                                </div>
                              )}
                            </div>
                          ) : (
                            <div className="quiz-options">
                              {q.options?.map((option) => {
                                const isSelected = userAnswers[q.id] === option;
                                const isCorrectOption = option.toLowerCase() === q.correct_answer.toLowerCase();
                                let optionClass = 'quiz-option';
                                if (quizSubmitted) {
                                  if (isCorrectOption) optionClass += ' option-correct';
                                  else if (isSelected && !isCorrectOption) optionClass += ' option-wrong';
                                } else if (isSelected) {
                                  optionClass += ' option-selected';
                                }

                                return (
                                  <button
                                    key={option}
                                    className={optionClass}
                                    onClick={() => handleAnswerSelect(q.id, option)}
                                    disabled={quizSubmitted}
                                  >
                                    <span className="quiz-option-dot"></span>
                                    {option}
                                    {quizSubmitted && isCorrectOption && <CheckCircle2 size={16} className="option-check" />}
                                    {quizSubmitted && isSelected && !isCorrectOption && <XCircle size={16} className="option-x" />}
                                  </button>
                                );
                              })}
                            </div>
                          )}

                          {quizSubmitted && (
                            <div className={`quiz-explanation ${correct ? 'explanation-correct' : 'explanation-incorrect'}`}>
                              💡 {q.explanation}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>

                  {!quizSubmitted && (
                    <button
                      className="quiz-submit-btn"
                      onClick={submitQuiz}
                      disabled={quizData.questions.filter(q => q.type === 'fill_blank' ? !fillBlankInputs[q.id]?.trim() : !userAnswers[q.id]).length > 0}
                    >
                      <CheckCircle2 size={18} /> Check Answers
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default StoryWeaver;
