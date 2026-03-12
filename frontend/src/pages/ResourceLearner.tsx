import React, { useState, useRef, useEffect } from 'react';
import { Upload, FileAudio, FileVideo, Languages, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import './ResourceLearner.css';

interface TranscriptSegment {
  id: number;
  start: number;
  end: number;
  text: string;
}

interface TranscribeResponse {
  filename: string;
  text: string;
  segments: TranscriptSegment[];
}

const ResourceLearner = () => {
  const [file, setFile] = useState<File | null>(null);
  const [mediaUrl, setMediaUrl] = useState<string | null>(null);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [status, setStatus] = useState<string>('');
  const [transcript, setTranscript] = useState<TranscriptSegment[]>([]);
  const [currentTime, setCurrentTime] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [language, setLanguage] = useState('');

  const videoRef = useRef<HTMLVideoElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Handle file selection
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      if (mediaUrl) URL.revokeObjectURL(mediaUrl);
      setFile(selectedFile);
      setMediaUrl(URL.createObjectURL(selectedFile));
      setTranscript([]);
      setError(null);
      setStatus('File loaded. Ready to transcribe.');
    }
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && (droppedFile.type.startsWith('audio/') || droppedFile.type.startsWith('video/'))) {
      if (mediaUrl) URL.revokeObjectURL(mediaUrl);
      setFile(droppedFile);
      setMediaUrl(URL.createObjectURL(droppedFile));
      setTranscript([]);
      setError(null);
      setStatus('File loaded. Ready to transcribe.');
    }
  };

  const runTranscription = async () => {
    if (!file) return;

    setIsTranscribing(true);
    setError(null);
    setStatus('Uploading and transcribing...');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`http://localhost:8000/transcribe?language=${language}`, {
        method: 'POST',
        headers: {
          'X-API-Key': import.meta.env.VITE_TRANSCRIBE_API_KEY
        },
        body: formData
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.statusText}`);
      }

      const data: TranscribeResponse = await response.json();
      console.log('Transcription Result:', data);

      if (data && data.segments) {
        setTranscript(data.segments);
        setStatus('Transcription complete!');
      } else {
        throw new Error('Invalid response format from server.');
      }

    } catch (err: any) {
      console.error('Transcription error:', err);
      setError(`Transcription failed: ${err.message}. Please ensure the backend is running at http://localhost:8000`);
    } finally {
      setIsTranscribing(false);
    }
  };

  const jumpToTime = (time: number) => {
    const media = videoRef.current || audioRef.current;
    if (media) {
      media.currentTime = time;
      media.play();
    }
  };

  // Sync current highlight with time
  useEffect(() => {
    const media = videoRef.current || audioRef.current;
    if (!media) return;

    const handleTimeUpdate = () => {
      setCurrentTime(media.currentTime);
    };


    media.addEventListener('timeupdate', handleTimeUpdate);

    return () => {
      media.removeEventListener('timeupdate', handleTimeUpdate);
    };
  }, [mediaUrl]);

  const activeSegmentIndex = transcript.findIndex(
    seg => currentTime >= seg.start && currentTime < seg.end
  );

  return (
    <div className="page-container resource-learner-page animate-fade-in">
      <header className="page-header text-center">
        <h2 className="title-gradient">Resource Learner</h2>
        <p className="subtitle">Upload audio or video and get a smart, interactive transcript.</p>
      </header>

      <div className="resource-learner-grid">
        <aside className="upload-section glass-panel">
          <div
            className="dropzone"
            onDragOver={(e) => { e.preventDefault(); e.currentTarget.classList.add('dragging'); }}
            onDragLeave={(e) => { e.preventDefault(); e.currentTarget.classList.remove('dragging'); }}
            onDrop={(e) => { onDrop(e); e.currentTarget.classList.remove('dragging'); }}
            onClick={() => fileInputRef.current?.click()}
          >
            <Upload size={40} className="dropzone-icon" />
            <div>
              <p style={{ fontWeight: 600, marginBottom: '0.25rem' }}>Click or drop media</p>
              <p style={{ fontSize: '0.8rem', opacity: 0.6 }}>MP3, MP4, WAV supported</p>
            </div>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept="audio/*,video/*"
              style={{ display: 'none' }}
            />
          </div>

          {file && (
            <div className="file-info">
              {file.type.startsWith('video/') ? <FileVideo size={20} /> : <FileAudio size={20} />}
              <div style={{ overflow: 'hidden' }}>
                <p style={{ fontWeight: 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{file.name}</p>
                <p style={{ fontSize: '0.75rem', opacity: 0.6 }}>{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
              </div>
            </div>
          )}

          <div className="language-selector-container">
            <label htmlFor="language-select">Target Language</label>
            <select
              id="language-select"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="language-dropdown"
            >
              <option value="">Auto-detect</option>
              <option value="es">Spanish</option>
              <option value="fr">French</option>
              <option value="de">German</option>
              <option value="it">Italian</option>
              <option value="ja">Japanese</option>
              <option value="ko">Korean</option>
              <option value="zh">Chinese</option>
              <option value="ru">Russian</option>
              <option value="pt">Portuguese</option>
              <option value="en">English</option>
            </select>
          </div>

          <button
            className="transcribe-btn"
            disabled={!file || isTranscribing}
            onClick={runTranscription}
          >
            {isTranscribing ? (
              <>
                <Loader2 size={20} className="spinner" />
                Transcribing...
              </>
            ) : (
              <>
                <Languages size={20} />
                Generate Transcript
              </>
            )}
          </button>

          {(isTranscribing || status) && (
            <div className="progress-container">
              <div className="progress-header">
                <span>{status}</span>
              </div>
              <div className="progress-bar-bg">
                <div
                  className="progress-bar-fill"
                  style={{ width: isTranscribing ? '50%' : '100%', transition: 'width 2s' }}
                ></div>
              </div>
            </div>
          )}

          {error && (
            <div className="error-message" style={{ display: 'flex', gap: '0.5rem', color: '#ff6b6b', padding: '1rem', background: 'rgba(255,107,107,0.1)', borderRadius: '0.5rem', fontSize: '0.9rem' }}>
              <AlertCircle size={18} />
              <span>{error}</span>
            </div>
          )}
        </aside>

        <main className="main-content-section">
          {mediaUrl ? (
            <>
              <div className="player-card glass-panel">
                <div className="media-container">
                  {file?.type.startsWith('video/') ? (
                    <video ref={videoRef} src={mediaUrl} controls />
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2rem', width: '100%' }}>
                      <FileAudio size={80} style={{ opacity: 0.3 }} />
                      <audio ref={audioRef} src={mediaUrl} controls style={{ width: '80%' }} />
                    </div>
                  )}
                </div>
              </div>

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
                  {transcript.length > 0 ? (
                    transcript.map((chunk, i) => (
                      <span
                        key={chunk.id}
                        className={`transcript-item ${i === activeSegmentIndex ? 'active' : ''}`}
                        onClick={() => jumpToTime(chunk.start)}
                      >
                        {chunk.text.trim()}{' '}
                      </span>
                    ))
                  ) : (
                    <div className="empty-state">
                      {isTranscribing ? (
                        <>
                          <Loader2 size={40} className="spinner" />
                          <p>Transcribing via backend...</p>
                        </>
                      ) : (
                        <>
                          <Languages size={40} className="empty-state-icon" />
                          <p>Click "Generate Transcript" to see the magic happen.</p>
                        </>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </>
          ) : (
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
      </div>
    </div>
  );
};

export default ResourceLearner;
