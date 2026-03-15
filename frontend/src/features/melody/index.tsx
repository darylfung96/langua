import { useState, useRef, useEffect } from 'react';
import ReactPlayer from 'react-player';
import { YoutubeTranscript } from '../../utils/YoutubeTranscript';
import type { TranscriptSection } from '../../utils/YoutubeTranscript';
import { Music, Save } from 'lucide-react';
import { apiFetch } from '../../utils/apiClient';
import { useToast, TOAST_TIMEOUT_MS } from '../../hooks/useToast';
import './Melody.css';
import VideoPlayer from './components/VideoPlayer';
import TranscriptViewer from './components/TranscriptViewer';
import SavedLyricsList from './components/SavedLyricsList';

interface SavedLyric {
  id: string;
  title: string;
  language: string;
  created_at: string;
}

const Melody = () => {
  const [url, setUrl] = useState('');
  const [videoId, setVideoId] = useState<string | null>(null);
  const [transcript, setTranscript] = useState<TranscriptSection[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [savedLyrics, setSavedLyrics] = useState<SavedLyric[]>([]);
  const [videoTitle, setVideoTitle] = useState('');
  const [language, setLanguage] = useState('en');
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null);
  const { success, error, setSuccess, setError } = useToast();

  const playerRef = useRef<ReactPlayer>(null);
  const transcriptScrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadSavedLyrics();
  }, []);

  const loadSavedLyrics = async () => {
    try {
      const response = await apiFetch('/lyrics');
      if (response.ok) {
        const data = await response.json();
        setSavedLyrics(data.lyrics);
      }
    } catch {
      setError('Failed to load saved lyrics');
    }
  };

  const handleFetch = async () => {
    const id = YoutubeTranscript.extractVideoId(url);

    if (!id) {
      setError('Invalid YouTube URL');
      return;
    }

    setIsLoading(true);
    setError(null);
    setSuccess(null);
    setVideoId(id);

    try {
      const requestedLang = language;
      const data = await YoutubeTranscript.fetchTranscript(id, requestedLang);
      setTranscript(data.segments);
      setLanguage(data.language);
      if (data.language !== requestedLang) {
        setSuccess(`No ${requestedLang.toUpperCase()} subtitles found — showing ${data.language.toUpperCase()} instead.`, TOAST_TIMEOUT_MS * 3);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to fetch transcript. Ensure the video has subtitles.');
      setTranscript([]);
    } finally {
      setIsLoading(false);
    }
  };

  const saveLyric = async () => {
    if (!videoId || transcript.length === 0) return;

    setIsSaving(true);
    setError(null);
    setSuccess(null);

    try {
      await apiFetch('/lyrics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: videoTitle || `Video ${videoId}`,
          video_id: videoId,
          language: language,
          transcript: JSON.stringify(transcript),
        }),
      });

      setSuccess('Lyrics saved successfully!');
      loadSavedLyrics();
    } catch (err) {
      setError((err as Error).message || 'Failed to save lyric');
    } finally {
      setIsSaving(false);
    }
  };

  const loadLyricFromSaved = async (lyricId: string) => {
    try {
      const response = await apiFetch(`/lyrics/${lyricId}`);
      const data = await response.json();
      setVideoId(data.video_id);
      setTranscript(data.transcript);
      setVideoTitle(data.title);
      setLanguage(data.language);
      setIsPlaying(false);
      setCurrentTime(0);
    } catch {
      setError('Failed to load lyric');
    }
  };

  const deleteLyric = async (lyricId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (pendingDeleteId !== lyricId) {
      setPendingDeleteId(lyricId);
      return;
    }
    setPendingDeleteId(null);
    try {
      await apiFetch(`/lyrics/${lyricId}`, { method: 'DELETE' });
      setSuccess('Lyric deleted!');
      loadSavedLyrics();
    } catch {
      setError('Failed to delete lyric');
    }
  };

  const jumpToTime = (seconds: number) => {
    playerRef.current?.seekTo(seconds, 'seconds');
    setIsPlaying(true);
  };

  const handleProgress = (state: { playedSeconds: number }) => {
    setCurrentTime(state.playedSeconds);
  };

  const activeIndex = transcript.findIndex((line, i) => {
    const nextLine = transcript[i + 1];
    return currentTime >= line.start && (!nextLine || currentTime < nextLine.start);
  });

  useEffect(() => {
    if (activeIndex !== -1 && transcriptScrollRef.current) {
      const container = transcriptScrollRef.current;
      const activeEl = container.children[activeIndex] as HTMLElement;
      if (activeEl) {
        const scrollTop = activeEl.offsetTop - (container.clientHeight / 2) + (activeEl.clientHeight / 2);
        container.scrollTo({ top: scrollTop, behavior: 'smooth' });
      }
    }
  }, [activeIndex]);

  return (
    <div className="page-container melody-page animate-fade-in">
      <header className="page-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div className="icon-badge" style={{ background: 'var(--accent-secondary)' }}>
            <Music size={24} />
          </div>
          <div>
            <h2 className="title-gradient">YouTube Learner</h2>
            <p className="subtitle">Master vocabulary and rhythm through your favorite YouTube tracks/videos.</p>
          </div>
        </div>
      </header>

      <div className="page-content">
        {error && (
          <div className="error-card glass-panel" style={{ color: '#ff6b6b', marginBottom: '2rem', padding: '1rem' }}>
            <p>{error}</p>
          </div>
        )}
        {success && (
          <div className="success-card glass-panel" style={{ color: '#51cf66', marginBottom: '2rem', padding: '1rem' }}>
            <p>{success}</p>
          </div>
        )}

        {videoId && transcript.length > 0 && (
          <div className="save-section glass-panel" style={{ marginBottom: '2rem', padding: '1rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
            <input
              type="text"
              placeholder="Give this lyric a title (optional)"
              aria-label="Lyric title"
              value={videoTitle}
              onChange={(e) => setVideoTitle(e.target.value)}
              style={{ flex: 1, padding: '0.5rem', borderRadius: '0.25rem', border: '1px solid rgba(255,255,255,0.2)', background: 'rgba(0,0,0,0.2)', color: 'white' }}
            />
            <button
              className="save-btn"
              onClick={saveLyric}
              disabled={isSaving}
              style={{ background: isSaving ? 'rgba(99, 102, 241, 0.5)' : 'var(--accent-primary)', color: 'white', border: 'none', padding: '0.5rem 1rem', borderRadius: '0.25rem', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
            >
              <Save size={18} />
              {isSaving ? 'Saving...' : 'Save Lyrics'}
            </button>
          </div>
        )}

        <div className="lyrics-learner-grid">
          <VideoPlayer
            url={url}
            setUrl={setUrl}
            language={language}
            setLanguage={setLanguage}
            isLoading={isLoading}
            videoId={videoId}
            isPlaying={isPlaying}
            setIsPlaying={setIsPlaying}
            playerRef={playerRef}
            onFetch={handleFetch}
            onProgress={handleProgress}
            transcript={transcript}
          />
          <TranscriptViewer
            transcript={transcript}
            isLoading={isLoading}
            activeIndex={activeIndex}
            transcriptScrollRef={transcriptScrollRef}
            onJumpToTime={jumpToTime}
          />
        </div>

        <SavedLyricsList
          savedLyrics={savedLyrics}
          pendingDeleteId={pendingDeleteId}
          setPendingDeleteId={setPendingDeleteId}
          onLoad={loadLyricFromSaved}
          onDelete={deleteLyric}
        />
      </div>
    </div>
  );
};

export default Melody;
