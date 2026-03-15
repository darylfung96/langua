import { useState, useEffect } from 'react';
import { Sparkles, BookOpen } from 'lucide-react';
import './VisualMemory.css';
import { apiFetch } from '../../utils/apiClient';
import { useSessionStorage } from '../../hooks/useSessionStorage';
import { useToast } from '../../hooks/useToast';
import { SESSION_KEYS } from '../../utils/sessionKeys';
import type { ImageResponse, SavedVisual, VisualDetail } from './types';
import ImageGenerator from './components/ImageGenerator';
import ImageGrid from './components/ImageGrid';
import VisualLibrary from './components/VisualLibrary';

const VisualMemory = () => {
  const [word, setWord] = useState('');
  const [language, setLanguage] = useState('en');
  const [loading, setLoading] = useState(false);
  const [imageData, setImageData] = useState<ImageResponse | null>(null);
  const [view, setView] = useSessionStorage<'generator' | 'library'>(SESSION_KEYS.visualMemory.view, 'generator');
  const [savedVisuals, setSavedVisuals] = useState<SavedVisual[]>([]);
  const [selectedVisualId, setSelectedVisualId] = useSessionStorage<string | null>(SESSION_KEYS.visualMemory.selectedVisualId, null);
  const [selectedVisual, setSelectedVisual] = useState<VisualDetail | null>(null);
  const [loadingLibrary, setLoadingLibrary] = useState(false);
  const [saving, setSaving] = useState(false);
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null);
  const { success: successMessage, error, setSuccess: setSuccessMessage, setError } = useToast(2500);

  useEffect(() => {
    if (view === 'library') {
      loadVisuals();
    }
  }, [view]);

  useEffect(() => {
    if (selectedVisualId) {
      loadVisualDetail(selectedVisualId);
    }
  }, []);

  const loadVisuals = async () => {
    setLoadingLibrary(true);
    try {
      const response = await apiFetch('/visuals');
      const data = await response.json();
      setSavedVisuals(data.visuals || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load visuals');
    } finally {
      setLoadingLibrary(false);
    }
  };

  const loadVisualDetail = async (visualId: string) => {
    try {
      const response = await apiFetch(`/visuals/${visualId}`);
      const data = await response.json();
      setSelectedVisual(data);
      setSelectedVisualId(visualId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load visual details');
    }
  };

  const handleGenerateImage = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!word.trim()) {
      setError('Please enter a word');
      return;
    }

    setLoading(true);
    setError('');
    setImageData(null);

    try {
      const params = new URLSearchParams({ word: word.trim(), language });
      const response = await apiFetch(`/generate-image?${params}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      }, 200_000);

      const data: ImageResponse = await response.json();
      if (data.success) {
        setImageData(data);
      } else {
        setError('Failed to generate image. Please try again.');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate image');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveVisual = async () => {
    if (!imageData) return;

    setSaving(true);
    setError('');

    try {
      await apiFetch('/visuals', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          word: imageData.word,
          language: imageData.language,
          images: JSON.stringify(imageData.images),
          prompt: imageData.prompt,
          explanation: imageData.text_response,
        }),
      });

      setImageData(null);
      setWord('');
      setError('');
      setSuccessMessage('Visual saved successfully!');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save visual');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteVisual = async (visualId: string) => {
    try {
      await apiFetch(`/visuals/${visualId}`, { method: 'DELETE' });

      setSavedVisuals(savedVisuals.filter((v) => v.id !== visualId));
      if (selectedVisual?.id === visualId) {
        setSelectedVisual(null);
        setSelectedVisualId(null);
      }
      setPendingDeleteId(null);
      setSuccessMessage('Visual deleted!');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete visual');
    }
  };

  return (
    <div className="page-container animate-fade-in">
      <header className="page-header">
        <h2>Visual Memory</h2>
        <p>Create memorable images to never forget a word!</p>
      </header>
      <div className="page-content">
        <div className="visual-memory-container">
          <div className="view-tabs">
            <button
              className={`tab-btn ${view === 'generator' ? 'active' : ''}`}
              onClick={() => setView('generator')}
            >
              <Sparkles size={18} />
              Generator
            </button>
            <button
              className={`tab-btn ${view === 'library' ? 'active' : ''}`}
              onClick={() => setView('library')}
            >
              <BookOpen size={18} />
              Library
            </button>
          </div>

          {view === 'generator' ? (
            <>
              <ImageGenerator
                word={word}
                setWord={setWord}
                language={language}
                setLanguage={setLanguage}
                loading={loading}
                error={error}
                successMessage={successMessage}
                hasImageData={imageData !== null}
                onSubmit={handleGenerateImage}
              />
              {imageData && (
                <ImageGrid
                  imageData={imageData}
                  saving={saving}
                  onSave={handleSaveVisual}
                />
              )}
            </>
          ) : (
            <VisualLibrary
              savedVisuals={savedVisuals}
              selectedVisual={selectedVisual}
              loadingLibrary={loadingLibrary}
              error={error}
              pendingDeleteId={pendingDeleteId}
              setPendingDeleteId={setPendingDeleteId}
              onLoadVisual={loadVisualDetail}
              onDeleteVisual={handleDeleteVisual}
              onClearSelectedVisual={() => setSelectedVisual(null)}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default VisualMemory;
