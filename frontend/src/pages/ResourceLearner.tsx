import React, { useState, useRef, useEffect } from 'react';
import { Upload, FileAudio, FileVideo, Languages, Loader2, CheckCircle2, AlertCircle, Save, Trash2 } from 'lucide-react';
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

interface SavedResource {
  id: string;
  title: string;
  file_name: string;
  language: string;
  created_at: string;
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
  const [isSaving, setIsSaving] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [savedResources, setSavedResources] = useState<SavedResource[]>([]);
  const [isLoadingSavedResources, setIsLoadingSavedResources] = useState(false);
  const [mediaFileType, setMediaFileType] = useState<string | null>(null);

  const videoRef = useRef<HTMLVideoElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
  const backendApiKey = import.meta.env.VITE_BACKEND_API_KEY;

  // Load saved resources on mount
  useEffect(() => {
    loadSavedResources();
  }, []);

  const loadSavedResources = async () => {
    setIsLoadingSavedResources(true);
    try {
      const response = await fetch(`${backendUrl}/resources`, {
        headers: { 'X-API-Key': backendApiKey }
      });
      if (response.ok) {
        const data = await response.json();
        console.log('Loaded saved resources:', data);
        setSavedResources(data.resources);
      } else {
        console.error('Failed to fetch resources:', response.status);
      }
    } catch (err) {
      console.error('Failed to load saved resources:', err);
    } finally {
      setIsLoadingSavedResources(false);
    }
  };

  const saveResource = async () => {
    if (!file || transcript.length === 0) return;

    setIsSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const formData = new FormData();
      formData.append('title', file.name.split('.')[0]);
      formData.append('file_name', file.name);
      formData.append('file_type', file.type);
      formData.append('language', language || 'auto-detect');
      formData.append('transcript', JSON.stringify(transcript));
      formData.append('media_file', file);

      const saveResponse = await fetch(`${backendUrl}/resources`, {
        method: 'POST',
        headers: {
          'X-API-Key': backendApiKey
        },
        body: formData
      });

      if (!saveResponse.ok) {
        const errorText = await saveResponse.text();
        console.error('Save error:', saveResponse.status, errorText);
        throw new Error('Failed to save resource');
      }

      const saveData = await saveResponse.json();
      console.log('Resource saved:', saveData);
      
      setSuccess('Resource saved successfully!');
      setTimeout(() => setSuccess(null), 2000);

      // Reload saved resources
      loadSavedResources();
    } catch (err) {
      console.error('Error saving resource:', err);
      setError((err as Error).message || 'Failed to save resource');
    } finally {
      setIsSaving(false);
    }
  };

  const loadResourceFromSaved = async (resourceId: string) => {
    try {
      const response = await fetch(`${backendUrl}/resources/${resourceId}`, {
        headers: { 'X-API-Key': backendApiKey }
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Backend error:', response.status, errorText);
        throw new Error(`Failed to load resource: ${response.statusText}`);
      }

      const data = await response.json();
      console.log('Loaded resource data:', data);
      
      setTranscript(data.transcript);
      setLanguage(data.language);
      setFile(null);
      setMediaFileType(data.file_type);
      setStatus(`Loaded: ${data.file_name}`);
      setError(null);
      
      // Load media file if available
      if (data.media_file_path) {
        try {
          const mediaResponse = await fetch(`${backendUrl}/resources/media/${resourceId}`, {
            headers: { 'X-API-Key': backendApiKey }
          });
          if (mediaResponse.ok) {
            const blob = await mediaResponse.blob();
            const mediaUrl = URL.createObjectURL(blob);
            setMediaUrl(mediaUrl);
            console.log('Media loaded from resource');
          }
        } catch (err) {
          console.warn('Could not load media file:', err);
          // Continue anyway, transcript is still available
        }
      } else {
        setMediaUrl(null);
      }
    } catch (err: any) {
      console.error('Error loading resource:', err);
      setError(`Failed to load resource: ${err.message}`);
    }
  };

  const deleteResource = async (resourceId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this resource?')) return;

    try {
      const response = await fetch(`${backendUrl}/resources/${resourceId}`, {
        method: 'DELETE',
        headers: { 'X-API-Key': backendApiKey }
      });

      if (!response.ok) {
        throw new Error('Failed to delete resource');
      }

      loadSavedResources();
    } catch (err) {
      setError('Failed to delete resource');
    }
  };

  // Handle file selection
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      if (mediaUrl) URL.revokeObjectURL(mediaUrl);
      setFile(selectedFile);
      setMediaFileType(null);
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
      setMediaFileType(null);
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

      const response = await fetch(`${backendUrl}/transcribe?language=${language}`, {
        method: 'POST',
        headers: {
          'X-API-Key': import.meta.env.VITE_BACKEND_API_KEY
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

          {transcript.length > 0 && (
            <button
              className="transcribe-btn"
              disabled={isSaving}
              onClick={saveResource}
              style={{ background: '#10b981' }}
            >
              {isSaving ? (
                <>
                  <Loader2 size={20} className="spinner" />
                  Saving...
                </>
              ) : (
                <>
                  <Save size={20} />
                  Save Resource
                </>
              )}
            </button>
          )}

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

          {success && (
            <div className="success-message" style={{ display: 'flex', gap: '0.5rem', color: '#10b981', padding: '1rem', background: 'rgba(16,185,129,0.1)', borderRadius: '0.5rem', fontSize: '0.9rem' }}>
              <CheckCircle2 size={18} />
              <span>{success}</span>
            </div>
          )}

          {!isLoadingSavedResources && savedResources.length > 0 && (
            <div style={{ marginTop: '2rem', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '1.5rem' }}>
              <h3 style={{ marginBottom: '1rem', fontSize: '1rem', fontWeight: '600' }}>💾 Saved Resources</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', maxHeight: '300px', overflowY: 'auto' }}>
                {savedResources.map(resource => (
                  <button
                    key={resource.id}
                    onClick={() => loadResourceFromSaved(resource.id)}
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
                      <div style={{ fontSize: '0.9rem', fontWeight: '500' }}>{resource.title}</div>
                      <div style={{ fontSize: '0.75rem', opacity: 0.6 }}>{resource.file_name}</div>
                    </div>
                    <button
                      onClick={(e) => deleteResource(resource.id, e)}
                      style={{
                        background: 'rgba(255,107,107,0.2)',
                        border: 'none',
                        borderRadius: '0.25rem',
                        padding: '0.25rem 0.5rem',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        color: '#ff6b6b'
                      }}
                    >
                      <Trash2 size={14} />
                    </button>
                  </button>
                ))}
              </div>
            </div>
          )}
        </aside>

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
                    onClick={() => jumpToTime(chunk.start)}
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
      </div>
    </div>
  );
};

export default ResourceLearner;
