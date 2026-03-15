import type { RefObject } from 'react';
import { FileAudio, Languages, CheckCircle2, Upload } from 'lucide-react';

interface TranscriptSegment {
  id: number;
  start: number;
  end: number;
  text: string;
}

interface Props {
  mediaUrl: string | null;
  file: File | null;
  mediaFileType: string | null;
  videoRef: RefObject<HTMLVideoElement | null>;
  audioRef: RefObject<HTMLAudioElement | null>;
  transcript: TranscriptSegment[];
  activeSegmentIndex: number;
  onJumpToTime: (time: number) => void;
}

const TranscriptEditor = ({
  mediaUrl, file, mediaFileType, videoRef, audioRef, transcript, activeSegmentIndex, onJumpToTime,
}: Props) => {
  return (
    <main className="main-content-section">
      {mediaUrl && (
        <div className="player-card glass-panel">
          <div className="media-container">
            {(file?.type || mediaFileType)?.startsWith('video/') ? (
              <video ref={videoRef} src={mediaUrl} controls />
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2rem', width: '100%' }}>
                <FileAudio size={80} style={{ opacity: 0.3 }} />
                <audio ref={audioRef} src={mediaUrl} controls style={{ width: '80%' }} />
              </div>
            )}
          </div>
        </div>
      )}

      {transcript.length > 0 ? (
        <div className="transcript-card glass-panel">
          <div className="transcript-header">
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Languages size={20} /> Interactive Transcript
            </h3>
            {transcript.length > 0 && (
              <span style={{ fontSize: '0.8rem', opacity: 0.6 }}>
                <CheckCircle2 size={14} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'middle', color: '#10b981' }} />
                Timestamped
              </span>
            )}
          </div>

          <div className="transcript-content">
            {transcript.map((chunk, i) => (
              <span
                key={chunk.id}
                className={`transcript-item ${i === activeSegmentIndex ? 'active' : ''}`}
                onClick={() => onJumpToTime(chunk.start)}
              >
                {chunk.text.trim()}{' '}
              </span>
            ))}
          </div>
        </div>
      ) : mediaUrl ? null : (
        <div className="glass-panel" style={{ height: '400px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', padding: '2rem' }}>
          <div style={{ marginTop: 'auto', marginBottom: 'auto' }}>
            <Upload size={60} style={{ opacity: 0.1, marginBottom: '1.5rem' }} />
            <h3 style={{ opacity: 0.5 }}>No Media Selected</h3>
            <p style={{ opacity: 0.3, maxWidth: '300px', margin: '1rem auto' }}>
              Upload an audio or video file to start learning from your favorite resources.
            </p>
          </div>
        </div>
      )}
    </main>
  );
};

export default TranscriptEditor;
