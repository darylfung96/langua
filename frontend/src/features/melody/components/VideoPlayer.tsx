import type { RefObject } from 'react';
import ReactPlayer from 'react-player';
import { Search, Loader2, Youtube, ExternalLink } from 'lucide-react';
import { LANGUAGE_OPTIONS } from '../../../utils/languages';
import type { TranscriptSection } from '../../../utils/YoutubeTranscript';

interface Props {
  url: string;
  setUrl: (v: string) => void;
  language: string;
  setLanguage: (v: string) => void;
  isLoading: boolean;
  videoId: string | null;
  isPlaying: boolean;
  setIsPlaying: (v: boolean) => void;
  playerRef: RefObject<ReactPlayer | null>;
  onFetch: () => void;
  onProgress: (state: { playedSeconds: number }) => void;
  transcript: TranscriptSection[];
}

const VideoPlayer = ({
  url, setUrl, language, setLanguage, isLoading, videoId, isPlaying, setIsPlaying,
  playerRef, onFetch, onProgress, transcript: _transcript,
}: Props) => {
  return (
    <div className="player-section card-wrapper">
      <div className="video-search-container glass-panel" style={{ marginBottom: '1rem' }}>
        <input
          type="text"
          className="video-input"
          placeholder="Paste YouTube video URL here..."
          aria-label="YouTube video URL"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && onFetch()}
        />
        <select
          className="language-select"
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          title="Select transcript language"
          aria-label="Transcript language"
        >
          {LANGUAGE_OPTIONS.map(lang => (
            <option key={lang.value} value={lang.value}>{lang.label}</option>
          ))}
        </select>
        <button
          className="fetch-btn"
          onClick={onFetch}
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
            onProgress={onProgress}
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
  );
};

export default VideoPlayer;
