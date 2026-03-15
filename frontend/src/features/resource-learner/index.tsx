import React, { useState, useRef, useEffect } from 'react';
import './ResourceLearner.css';
import { apiFetch } from '../../utils/apiClient';
import { useSessionStorage } from '../../hooks/useSessionStorage';
import { useToast } from '../../hooks/useToast';
import { SESSION_KEYS } from '../../utils/sessionKeys';
import FileUploader from './components/FileUploader';
import TranscriptEditor from './components/TranscriptEditor';

const ALLOWED_MIME_TYPES = new Set([
  'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/x-wav', 'audio/wave',
  'audio/ogg', 'audio/flac', 'video/mp4', 'video/webm', 'video/ogg',
]);
const MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024;

function validateFile(f: File): string | null {
  const baseMime = f.type.split(';')[0].trim().toLowerCase();
  if (!ALLOWED_MIME_TYPES.has(baseMime)) {
    return `File type "${f.type}" is not supported. Please upload an audio or video file (MP3, WAV, MP4, etc.).`;
  }
  if (f.size > MAX_FILE_SIZE_BYTES) {
    return `File is too large (${(f.size / (1024 * 1024)).toFixed(1)} MB). Maximum allowed size is 50 MB.`;
  }
  return null;
}

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
  const [status, setStatus] = useSessionStorage(SESSION_KEYS.resourceLearner.status, '');
  const [transcript, setTranscript] = useSessionStorage<TranscriptSegment[]>(SESSION_KEYS.resourceLearner.transcript, []);
  const [currentTime, setCurrentTime] = useState(0);
  const [language, setLanguage] = useSessionStorage(SESSION_KEYS.resourceLearner.language, '');
  const [isSaving, setIsSaving] = useState(false);
  const [savedResources, setSavedResources] = useState<SavedResource[]>([]);
  const [isLoadingSavedResources, setIsLoadingSavedResources] = useState(false);
  const [mediaFileType, setMediaFileType] = useSessionStorage<string | null>(SESSION_KEYS.resourceLearner.mediaFileType, null);
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null);
  const [selectedResourceId, setSelectedResourceId] = useSessionStorage<string | null>(SESSION_KEYS.resourceLearner.selectedResourceId, null);
  const { success, error, setSuccess, setError } = useToast();

  const videoRef = useRef<HTMLVideoElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);

  useEffect(() => {
    loadSavedResources();
  }, []);

  useEffect(() => {
    if (!selectedResourceId) return;
    let blobUrl: string | null = null;
    let cancelled = false;
    apiFetch(`/resources/media/${selectedResourceId}`)
      .then(res => res.ok ? res.blob() : null)
      .then(blob => {
        if (cancelled) { if (blobUrl) URL.revokeObjectURL(blobUrl); return; }
        if (blob) { blobUrl = URL.createObjectURL(blob); setMediaUrl(blobUrl); }
      })
      .catch(() => {});
    return () => {
      cancelled = true;
      if (blobUrl) URL.revokeObjectURL(blobUrl);
    };
  }, []);

  const loadSavedResources = async () => {
    setIsLoadingSavedResources(true);
    try {
      const response = await apiFetch('/resources');
      if (response.ok) {
        const data = await response.json();
        setSavedResources(data.resources);
      }
    } catch {
      // silently fail
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

      const saveResponse = await apiFetch('/resources', {
        method: 'POST',
        body: formData,
      });

      await saveResponse.json();
      setSuccess('Resource saved successfully!');
      loadSavedResources();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save resource');
    } finally {
      setIsSaving(false);
    }
  };

  const loadResourceFromSaved = async (resourceId: string) => {
    setSelectedResourceId(resourceId);
    try {
      const response = await apiFetch(`/resources/${resourceId}`);
      const data = await response.json();
      setTranscript(data.transcript);
      setLanguage(data.language);
      setFile(null);
      setMediaFileType(data.file_type);
      setStatus(`Loaded: ${data.file_name}`);
      setError(null);

      if (data.media_file_path) {
        try {
          const mediaResponse = await apiFetch(`/resources/media/${resourceId}`);
          if (mediaResponse.ok) {
            const blob = await mediaResponse.blob();
            const url = URL.createObjectURL(blob);
            setMediaUrl(url);
          }
        } catch {
          // Continue anyway, transcript is still available
        }
      } else {
        setMediaUrl(null);
      }
    } catch (err: unknown) {
      setError(`Failed to load resource: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const deleteResource = async (resourceId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (pendingDeleteId !== resourceId) {
      setPendingDeleteId(resourceId);
      return;
    }
    setPendingDeleteId(null);
    try {
      await apiFetch(`/resources/${resourceId}`, { method: 'DELETE' });
      setSuccess('Resource deleted!');
      loadSavedResources();
    } catch {
      setError('Failed to delete resource');
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      const validationError = validateFile(selectedFile);
      if (validationError) {
        setError(validationError);
        return;
      }
      if (mediaUrl) URL.revokeObjectURL(mediaUrl);
      setSelectedResourceId(null);
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
    if (droppedFile) {
      const validationError = validateFile(droppedFile);
      if (validationError) {
        setError(validationError);
        return;
      }
      if (mediaUrl) URL.revokeObjectURL(mediaUrl);
      setSelectedResourceId(null);
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

      // Use a 5-minute timeout to match the backend's TRANSCRIBE_TIMEOUT
      const response = await apiFetch(`/transcribe?language=${language}`, {
        method: 'POST',
        body: formData,
      }, 300_000);

      const data: TranscribeResponse = await response.json();

      if (data && data.segments && data.segments.length > 0) {
        setTranscript(data.segments);
        setStatus('Transcription complete!');
      } else if (data && data.segments) {
        setStatus('Transcription returned no speech segments. Try a different file.');
      } else {
        throw new Error('Invalid response format from server.');
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unknown error';
      setError(`Transcription failed: ${msg}`, 10_000); // show for 10 seconds
      setStatus('Transcription failed.');
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
        <FileUploader
          file={file}
          language={language}
          setLanguage={setLanguage}
          isTranscribing={isTranscribing}
          status={status}
          isSaving={isSaving}
          error={error}
          success={success}
          transcript={transcript}
          savedResources={savedResources}
          isLoadingSavedResources={isLoadingSavedResources}
          pendingDeleteId={pendingDeleteId}
          setPendingDeleteId={setPendingDeleteId}
          onFileChange={handleFileChange}
          onDrop={onDrop}
          onTranscribe={runTranscription}
          onSave={saveResource}
          onLoadResource={loadResourceFromSaved}
          onDeleteResource={deleteResource}
        />

        <TranscriptEditor
          mediaUrl={mediaUrl}
          file={file}
          mediaFileType={mediaFileType}
          videoRef={videoRef}
          audioRef={audioRef}
          transcript={transcript}
          activeSegmentIndex={activeSegmentIndex}
          onJumpToTime={jumpToTime}
        />
      </div>
    </div>
  );
};

export default ResourceLearner;
