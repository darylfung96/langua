import React, { useRef } from 'react';
import { Upload, FileAudio, FileVideo, Languages, Loader2, CheckCircle2, AlertCircle, Save } from 'lucide-react';
import { LANGUAGE_OPTIONS } from '../../../utils/languages';
import SavedResourcesList from './SavedResourcesList';

interface TranscriptSegment {
  id: number;
  start: number;
  end: number;
  text: string;
}

interface SavedResource {
  id: string;
  title: string;
  file_name: string;
  language: string;
  created_at: string;
}

interface Props {
  file: File | null;
  language: string;
  setLanguage: (v: string) => void;
  isTranscribing: boolean;
  status: string;
  isSaving: boolean;
  error: string | null;
  success: string | null;
  transcript: TranscriptSegment[];
  savedResources: SavedResource[];
  isLoadingSavedResources: boolean;
  pendingDeleteId: string | null;
  setPendingDeleteId: (id: string | null) => void;
  onFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onDrop: (e: React.DragEvent) => void;
  onTranscribe: () => void;
  onSave: () => void;
  onLoadResource: (resourceId: string) => void;
  onDeleteResource: (resourceId: string, e: React.MouseEvent) => void;
}

const FileUploader = ({
  file, language, setLanguage, isTranscribing, status, isSaving, error, success,
  transcript, savedResources, isLoadingSavedResources, pendingDeleteId, setPendingDeleteId,
  onFileChange, onDrop, onTranscribe, onSave, onLoadResource, onDeleteResource,
}: Props) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  return (
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
          onChange={onFileChange}
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
          {LANGUAGE_OPTIONS.map(lang => (
            <option key={lang.value} value={lang.value}>{lang.label}</option>
          ))}
        </select>
      </div>

      <button
        className="transcribe-btn"
        disabled={!file || isTranscribing}
        onClick={onTranscribe}
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
          onClick={onSave}
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

      <SavedResourcesList
        savedResources={savedResources}
        isLoadingSavedResources={isLoadingSavedResources}
        pendingDeleteId={pendingDeleteId}
        setPendingDeleteId={setPendingDeleteId}
        onLoad={onLoadResource}
        onDelete={onDeleteResource}
      />
    </aside>
  );
};

export default FileUploader;
