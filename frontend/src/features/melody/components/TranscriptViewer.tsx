import type { RefObject } from 'react';
import { Loader2, Music, Play } from 'lucide-react';
import type { TranscriptSection } from '../../../utils/YoutubeTranscript';

interface Props {
  transcript: TranscriptSection[];
  isLoading: boolean;
  activeIndex: number;
  transcriptScrollRef: RefObject<HTMLDivElement | null>;
  onJumpToTime: (seconds: number) => void;
}

const formatTime = (seconds: number) => {
  const min = Math.floor(seconds / 60);
  const sec = Math.floor(seconds % 60);
  return `${min}:${sec.toString().padStart(2, '0')}`;
};

const TranscriptViewer = ({ transcript, isLoading, activeIndex, transcriptScrollRef, onJumpToTime }: Props) => {
  return (
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
              onClick={() => onJumpToTime(line.start)}
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
  );
};

export default TranscriptViewer;
