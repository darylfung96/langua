import { useState, useRef, useEffect } from 'react';
import ReactPlayer from 'react-player';
import { YoutubeTranscript } from '../utils/YoutubeTranscript';
import type { TranscriptSection } from '../utils/YoutubeTranscript';
import { Search, Loader2, Music, Youtube, Play, ExternalLink } from 'lucide-react';
import './Melody.css';

const Melody = () => {
  const [url, setUrl] = useState('');
  const [videoId, setVideoId] = useState<string | null>(null);
  const [transcript, setTranscript] = useState<TranscriptSection[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  const playerRef = useRef<any>(null); // Use any for ReactPlayer ref until types are fully sorted
  const transcriptScrollRef = useRef<HTMLDivElement>(null);

  const handleFetch = async () => {
    const id = YoutubeTranscript.extractVideoId(url);
    console.log("VIDEO ID:", id);   // add this

    if (!id) {
      setError('Invalid YouTube URL');
      return;
    }

    setIsLoading(true);
    setError(null);
    setVideoId(id);

    try {
      const data = await YoutubeTranscript.fetchTranscript(id);
      setTranscript(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch transcript. Ensure the video has subtitles.');
      setTranscript([]);
    } finally {
      setIsLoading(false);
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
      const activeEl = transcriptScrollRef.current.children[activeIndex] as HTMLElement;
      if (activeEl) {
        activeEl.scrollIntoView({
          behavior: 'smooth',
          block: 'center'
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
            <h2 className="title-gradient">Lyric Learner</h2>
            <p className="subtitle">Master vocabulary and rhythm through your favorite YouTube tracks.</p>
          </div>
        </div>
      </header>

      <div className="page-content">
        <div className="video-search-container glass-panel">
          <input
            type="text"
            className="video-input"
            placeholder="Paste YouTube video URL here..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleFetch()}
          />
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
          <div className="error-card glass-panel" style={{ color: '#ef4444', marginBottom: '2rem', padding: '1rem' }}>
            <p>{error}</p>
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
      </div>
    </div>
  );
};

export default Melody;
