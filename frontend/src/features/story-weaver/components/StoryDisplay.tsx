import React from 'react';
import type { RefObject } from 'react';
import { BookOpen, Play, Pause, Loader2, Save } from 'lucide-react';
import type { StoryResponse } from '../types';

interface StoryWord {
  text: string;
  index: number;
  isHighlight: boolean;
  title?: string;
}

interface Props {
  storyData: StoryResponse;
  storyWords: StoryWord[];
  isPlaying: boolean;
  isGeneratingAudio: boolean;
  audioUrl: string | null;
  currentTime: number;
  duration: number;
  audioRef: RefObject<HTMLAudioElement | null>;
  isSaving: boolean;
  onToggleAudio: () => void;
  onSave: () => void;
  onSeek: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onJumpToWord: (index: number, total: number) => void;
}

const formatTime = (time: number) => {
  const minutes = Math.floor(time / 60);
  const seconds = Math.floor(time % 60);
  return `${minutes}:${seconds.toString().padStart(2, '0')}`;
};

const StoryDisplay = ({
  storyData, storyWords, isPlaying, isGeneratingAudio, audioUrl, currentTime, duration,
  audioRef, isSaving, onToggleAudio, onSave, onSeek, onJumpToWord,
}: Props) => {
  return (
    <div className="story-card glass-panel">
      <div className="card-header">
        <h3><BookOpen size={20} /> {storyData.title}</h3>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button className="audio-btn" onClick={onToggleAudio} disabled={isGeneratingAudio}>
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

          <button className="audio-btn" onClick={onSave} disabled={isSaving} style={{ background: isSaving ? 'rgba(99, 102, 241, 0.5)' : undefined }}>
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
              onChange={onSeek}
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
                onClick={() => onJumpToWord(w.index, storyWords.length)}
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
  );
};

export default StoryDisplay;
