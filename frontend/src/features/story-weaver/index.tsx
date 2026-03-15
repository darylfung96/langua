import React, { useState, useRef, useEffect, useMemo } from 'react';
import './StoryWeaver.css';
import { apiFetch } from '../../utils/apiClient';
import { useSessionStorage } from '../../hooks/useSessionStorage';
import { useToast } from '../../hooks/useToast';
import { SESSION_KEYS } from '../../utils/sessionKeys';
import type { StoryResponse, QuizData } from './types';
import StoryGenerator from './components/StoryGenerator';
import StoryDisplay from './components/StoryDisplay';
import VocabularyList from './components/VocabularyList';
import QuizPanel from './components/QuizPanel';
import SavedStoriesList from './components/SavedStoriesList';

const AUDIO_SAMPLE_RATE = 24000;

const AUDIO_PATH_RE = /^uploads\/[0-9a-f]{16}_[\w\- ]{0,50}\.[a-z0-9]{2,5}$/;

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
  view.setUint16(20, 1, true);
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

const StoryWeaver = () => {
  const [language, setLanguage] = useSessionStorage(SESSION_KEYS.storyWeaver.language, 'fr');
  const [inputWords, setInputWords] = useSessionStorage(SESSION_KEYS.storyWeaver.inputWords, '');
  const [isGenerating, setIsGenerating] = useState(false);
  const [storyData, setStoryData] = useSessionStorage<StoryResponse | null>(SESSION_KEYS.storyWeaver.storyData, null);
  const [isSaving, setIsSaving] = useState(false);
  const [savedStories, setSavedStories] = useState<{ id: string; title: string; language: string; created_at: string }[]>([]);
  const [isLoadingSavedStories, setIsLoadingSavedStories] = useState(false);
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null);
  const { success, error, setSuccess, setError } = useToast();

  const [quizData, setQuizData] = useSessionStorage<QuizData | null>(SESSION_KEYS.storyWeaver.quizData, null);
  const [isGeneratingQuiz, setIsGeneratingQuiz] = useState(false);
  const [userAnswers, setUserAnswers] = useSessionStorage<Record<number, string>>(SESSION_KEYS.storyWeaver.userAnswers, {});
  const [fillBlankInputs, setFillBlankInputs] = useSessionStorage<Record<number, string>>(SESSION_KEYS.storyWeaver.fillBlankInputs, {});
  const [quizSubmitted, setQuizSubmitted] = useSessionStorage(SESSION_KEYS.storyWeaver.quizSubmitted, false);
  const [quizScore, setQuizScore] = useSessionStorage(SESSION_KEYS.storyWeaver.quizScore, 0);
  const [selectedStoryId, setSelectedStoryId] = useSessionStorage<string | null>(SESSION_KEYS.storyWeaver.selectedStoryId, null);

  const [isPlaying, setIsPlaying] = useState(false);
  const [isGeneratingAudio, setIsGeneratingAudio] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    loadSavedStories();
  }, []);

  useEffect(() => {
    if (!selectedStoryId) return;
    let blobUrl: string | null = null;
    let cancelled = false;
    apiFetch(`/stories/${selectedStoryId}`)
      .then(res => res.ok ? res.json() : null)
      .then(data => {
        if (data?.audio_file_path && AUDIO_PATH_RE.test(data.audio_file_path)) {
          return apiFetch(`/${data.audio_file_path}`)
            .then(r => r.ok ? r.blob() : null)
            .then(blob => {
              if (cancelled) { if (blobUrl) URL.revokeObjectURL(blobUrl); return; }
              if (blob) { blobUrl = URL.createObjectURL(blob); setAudioUrl(blobUrl); }
            });
        }
      })
      .catch(() => {});
    return () => {
      cancelled = true;
      if (blobUrl) URL.revokeObjectURL(blobUrl);
    };
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
      // silently fail
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
      loadSavedStories();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save story');
    } finally {
      setIsSaving(false);
    }
  };

  const loadStoryFromSaved = async (storyId: string) => {
    setSelectedStoryId(storyId);
    try {
      const response = await apiFetch(`/stories/${storyId}`);
      if (!response.ok) throw new Error('Failed to load story');
      const data = await response.json();
      setStoryData({
        title: data.title,
        story: data.story_content,
        vocabulary: data.vocabulary
      });
      setLanguage(data.language);
      if (data.quiz) {
        setQuizData(data.quiz);
        setUserAnswers({});
        setFillBlankInputs({});
        setQuizSubmitted(false);
        setQuizScore(0);
      } else {
        setQuizData(null);
      }
      if (data.audio_file_path && AUDIO_PATH_RE.test(data.audio_file_path)) {
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
    } catch {
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
    } catch {
      setError('Failed to delete story');
    }
  };

  useEffect(() => {
    return () => {
      if (audioUrl && audioUrl.startsWith('blob:')) {
        URL.revokeObjectURL(audioUrl);
      }
    };
  }, [audioUrl]);

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
      const titleWordCount = storyData ? storyData.title.split(/\s+/).filter(Boolean).length / 2 : 0;
      const time = ((titleWordCount + index) / (titleWordCount + total)) * duration;
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

    setSelectedStoryId(null);
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
        throw new Error((err as { detail?: string }).detail || 'Failed to generate story.');
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
        throw new Error((err as { detail?: string }).detail || 'Failed to generate audio.');
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
        throw new Error((err as { detail?: string }).detail || 'Failed to generate quiz.');
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

  return (
    <div className="page-container animate-fade-in story-weaver-page">
      <header className="page-header text-center">
        <h2 className="title-gradient">Story Weaver</h2>
        <p className="subtitle">Enter a few words and we'll weave them into a memorable story.</p>
      </header>

      <div className="story-weaver-grid">
        <div className="input-section glass-panel">
          <StoryGenerator
            language={language}
            setLanguage={setLanguage}
            inputWords={inputWords}
            setInputWords={setInputWords}
            isGenerating={isGenerating}
            error={error}
            success={success}
            onSubmit={handleGenerate}
          />

          {!isLoadingSavedStories && (
            <SavedStoriesList
              savedStories={savedStories}
              pendingDeleteId={pendingDeleteId}
              onLoad={loadStoryFromSaved}
              onDelete={deleteStory}
            />
          )}
        </div>

        {storyData && (
          <div className="result-section animate-fade-in">
            <StoryDisplay
              storyData={storyData}
              storyWords={storyWords}
              isPlaying={isPlaying}
              isGeneratingAudio={isGeneratingAudio}
              audioUrl={audioUrl}
              currentTime={currentTime}
              duration={duration}
              audioRef={audioRef}
              isSaving={isSaving}
              onToggleAudio={toggleAudio}
              onSave={saveStory}
              onSeek={handleSeek}
              onJumpToWord={jumpToWord}
            />

            <VocabularyList
              vocabulary={storyData.vocabulary}
              language={language}
              onJumpToVocab={jumpToVocab}
            />

            <QuizPanel
              quizData={quizData}
              isGeneratingQuiz={isGeneratingQuiz}
              userAnswers={userAnswers}
              fillBlankInputs={fillBlankInputs}
              quizSubmitted={quizSubmitted}
              quizScore={quizScore}
              onGenerateQuiz={generateQuiz}
              onAnswerSelect={handleAnswerSelect}
              onFillBlankChange={handleFillBlankChange}
              onSubmitQuiz={submitQuiz}
              onRetakeQuiz={retakeQuiz}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default StoryWeaver;
