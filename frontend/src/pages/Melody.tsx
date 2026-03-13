import { useState, useRef, useEffect } from 'react';
import ReactPlayer from 'react-player';
import { YoutubeTranscript } from '../utils/YoutubeTranscript';
import type { TranscriptSection } from '../utils/YoutubeTranscript';
import { Search, Loader2, Music, Youtube, Play, ExternalLink, Save, Trash2 } from 'lucide-react';
import { apiFetch } from '../utils/apiClient';
import './Melody.css';

const TOAST_TIMEOUT_MS = 2000;

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
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [savedLyrics, setSavedLyrics] = useState<SavedLyric[]>([]);
  const [videoTitle, setVideoTitle] = useState('');
  const [language, setLanguage] = useState('en');
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null);

  const playerRef = useRef<ReactPlayer>(null);
  const transcriptScrollRef = useRef<HTMLDivElement>(null);

  // Load saved lyrics on mount
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
    } catch (err) {
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
        setSuccess(`No ${requestedLang.toUpperCase()} subtitles found — showing ${data.language.toUpperCase()} instead.`);
        setTimeout(() => setSuccess(null), TOAST_TIMEOUT_MS * 3);
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
      setTimeout(() => setSuccess(null), TOAST_TIMEOUT_MS);

      // Reload saved lyrics
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
    } catch (err) {
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
      setTimeout(() => setSuccess(null), 2000);
      loadSavedLyrics();
    } catch (err) {
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

  // Find the active transcript line
  const activeIndex = transcript.findIndex((line, i) => {
    const nextLine = transcript[i + 1];
    return currentTime >= line.start && (!nextLine || currentTime < nextLine.start);
  });

  // Scroll active line into view
  useEffect(() => {
    if (activeIndex !== -1 && transcriptScrollRef.current) {
      const container = transcriptScrollRef.current;
      const activeEl = container.children[activeIndex] as HTMLElement;
      if (activeEl) {
        const scrollTop = activeEl.offsetTop - (container.clientHeight / 2) + (activeEl.clientHeight / 2);
        container.scrollTo({
          top: scrollTop,
          behavior: 'smooth'
        });
      }
    }
  }, [activeIndex]);

  const formatTime = (seconds: number) => {
    const min = Math.floor(seconds / 60);
    const sec = Math.floor(seconds % 60);
    return `${min}:${sec.toString().padStart(2, '0')}`;
  };

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
        <div className="video-search-container glass-panel">
          <input
            type="text"
            className="video-input"
            placeholder="Paste YouTube video URL here..."
            aria-label="YouTube video URL"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleFetch()}
          />
          <select
            className="language-select"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            title="Select transcript language"
            aria-label="Transcript language"
          >
            <option value="en">English</option>
            <option value="fr">French</option>
            <option value="ja">Japanese</option>
            <option value="zh-TW">Chinese (Traditional)</option>
            <option value="zh-CN">Chinese (Simplified)</option>
            <option value="ko">Korean</option>
            <option value="es">Spanish</option>
            <option value="de">German</option>
            <option value="it">Italian</option>
            <option value="pt">Portuguese</option>
            <option value="ru">Russian</option>
            <option value="ar">Arabic</option>
          </select>
          <button
            className="fetch-btn"
            onClick={handleFetch}
            disabled={isLoading || !url}
          >
            {isLoading ? (
              <Loader2 size={18} className="spinner" />
            ) : (
              <Search size={18} />
            )}
            {isLoading ? 'Fetching...' : 'Load Video'}
          </button>
        </div>

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
          {/* Player Section */}
          <div className="player-section card-wrapper">
            <div className="player-wrapper glass-panel shadow-2xl">
              {videoId ? (
                <ReactPlayer
                  key={videoId}
                  ref={playerRef}
                  url={`https://www.youtube.com/watch?v=${videoId}`}
                  width="100%"
                  height="100%"
                  controls
                  playing={isPlaying}
                  onPlay={() => setIsPlaying(true)}
                  onPause={() => setIsPlaying(false)}
                  onProgress={handleProgress as any}
                />
              ) : (
                <div className="empty-state">
                  <Youtube size={64} style={{ opacity: 0.1 }} />
                  <p>Paste a link to get started</p>
                </div>
              )}
            </div>
            {videoId && (
              <div style={{ marginTop: '1rem', display: 'flex', justifyContent: 'flex-end' }}>
                <a
                  href={`https://www.youtube.com/watch?v=${videoId}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs opacity-50 hover:opacity-100 transition-opacity flex items-center gap-1"
                >
                  Watch on YouTube <ExternalLink size={12} />
                </a>
              </div>
            )}
          </div>

          {/* Transcript Section */}
          <div className="transcript-section glass-panel">
            <div className="transcript-header">
              <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', margin: 0 }}>
                <Play size={18} /> Lyrics & Transcript
              </h3>
              {transcript.length > 0 && (
                <span className="badge">{transcript.length} lines</span>
              )}
            </div>

            <div className="transcript-scroll" ref={transcriptScrollRef}>
              {transcript.length > 0 ? (
                transcript.map((line, i) => (
                  <div
                    key={i}
                    className={`transcript-line ${i === activeIndex ? 'active' : ''}`}
                    onClick={() => jumpToTime(line.start)}
                  >
                    <span className="timestamp">{formatTime(line.start)}</span>
                    <span className="text">{line.text}</span>
                  </div>
                ))
              ) : (
                <div className="empty-state">
                  {isLoading ? (
                    <>
                      <Loader2 size={40} className="spinner" />
                      <p>Grabbing subtitles...</p>
                    </>
                  ) : (
                    <>
                      <Music size={40} style={{ opacity: 0.1 }} />
                      <p>Load a video to see interactive lyrics</p>
                    </>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Saved Lyrics Section */}
        {savedLyrics.length > 0 && (
          <div className="saved-lyrics-section glass-panel" style={{ marginTop: '2rem', padding: '1rem' }}>
            <h3 style={{ marginTop: 0, marginBottom: '1rem' }}>Saved Lyrics</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '1rem' }}>
              {savedLyrics.map((lyric) => (
                <div
                  key={lyric.id}
                  onClick={() => loadLyricFromSaved(lyric.id)}
                  style={{
                    padding: '1rem',
                    background: 'rgba(99, 102, 241, 0.1)',
                    borderRadius: '0.5rem',
                    cursor: 'pointer',
                    transition: 'background 0.2s',
                    border: '1px solid rgba(99, 102, 241, 0.3)'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(99, 102, 241, 0.2)'}
                  onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(99, 102, 241, 0.1)'}
                >
                  <h4 style={{ margin: '0 0 0.5rem 0', color: 'var(--accent-primary)' }}>{lyric.title}</h4>
                  <p style={{ margin: '0.5rem 0', fontSize: '0.875rem', opacity: 0.7 }}>Language: {lyric.language}</p>
                  <p style={{ margin: '0.5rem 0', fontSize: '0.75rem', opacity: 0.5 }}>
                    {new Date(lyric.created_at).toLocaleDateString()}
                  </p>
                  {pendingDeleteId === lyric.id ? (
                    <div style={{ marginTop: '0.5rem', display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
                      <span style={{ fontSize: '0.75rem' }}>Delete this lyric?</span>
                      <button
                        onClick={(e) => deleteLyric(lyric.id, e)}
                        style={{ background: '#ef4444', color: 'white', border: 'none', padding: '0.25rem 0.5rem', borderRadius: '0.25rem', cursor: 'pointer', fontSize: '0.75rem' }}
                      >Yes, delete</button>
                      <button
                        onClick={(e) => { e.stopPropagation(); setPendingDeleteId(null); }}
                        style={{ background: 'rgba(255,255,255,0.2)', color: 'white', border: 'none', padding: '0.25rem 0.5rem', borderRadius: '0.25rem', cursor: 'pointer', fontSize: '0.75rem' }}
                      >Cancel</button>
                    </div>
                  ) : (
                    <button
                      onClick={(e) => deleteLyric(lyric.id, e)}
                      style={{
                        marginTop: '0.5rem',
                        background: '#ef4444',
                        color: 'white',
                        border: 'none',
                        padding: '0.25rem 0.5rem',
                        borderRadius: '0.25rem',
                        cursor: 'pointer',
                        fontSize: '0.75rem',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.25rem'
                      }}
                    >
                      <Trash2 size={12} />
                      Delete
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Melody;
