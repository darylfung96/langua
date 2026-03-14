
import { useState, useEffect } from 'react';
import { Sparkles, Loader, AlertCircle, BookOpen, Trash2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import './VisualMemory.css';
import { apiFetch } from '../utils/apiClient';
import { LANGUAGE_OPTIONS } from '../utils/languages';
import { useSessionStorage } from '../hooks/useSessionStorage';
import { useToast } from '../hooks/useToast';
import { SESSION_KEYS } from '../utils/sessionKeys';

interface GeneratedImage {
  id: number;
  type: string;
  url: string;
  base64: string;
}

interface ImageResponse {
  word: string;
  language: string;
  prompt: string;
  images: GeneratedImage[];
  text_response: string;
  success: boolean;
}

interface SavedVisual {
  id: string;
  word: string;
  language: string;
  created_at: string;
  updated_at: string;
}

interface VisualDetail extends SavedVisual {
  images: GeneratedImage[];
  prompt: string;
  explanation: string;
}

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

  // When view changes, load library if needed
  useEffect(() => {
    if (view === 'library') {
      loadVisuals();
    }
  }, [view]);

  // On mount: restore the previously selected visual
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
      }, 200_000); // 200s timeout — image generation can take a while

      const data: ImageResponse = await response.json();
      if (data.success) {
        setImageData(data);
      } else {
        setError('Failed to generate image. Please try again.');
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to generate image'
      );
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
      setError(
        err instanceof Error ? err.message : 'Failed to save visual'
      );
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
      setError(
        err instanceof Error ? err.message : 'Failed to delete visual'
      );
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
              <form onSubmit={handleGenerateImage} className="word-input-form">
                <div className="form-group">
                  <label htmlFor="word">Word to Remember</label>
                  <input
                    id="word"
                    type="text"
                    value={word}
                    onChange={(e) => setWord(e.target.value)}
                    placeholder="Enter a word..."
                    disabled={loading}
                    className="word-input"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="language">Language</label>
                  <select
                    id="language"
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    disabled={loading}
                    className="language-select"
                  >
                    {LANGUAGE_OPTIONS.map(lang => (
                      <option key={lang.value} value={lang.value}>{lang.label}</option>
                    ))}
                  </select>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="generate-btn"
                >
                  {loading ? (
                    <>
                      <Loader className="spinner" size={20} />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Sparkles size={20} />
                      Generate Image
                    </>
                  )}
                </button>
              </form>

              {error && (
                <div className="error-message">
                  <AlertCircle size={20} />
                  {error}
                </div>
              )}
              {successMessage && (
                <div className="success-toast">
                  {successMessage}
                </div>
              )}

              {imageData && (
                <div className="image-result">
                  <div className="result-header">
                    <h3>
                      {imageData.word}
                      <span className="language-tag">{imageData.language}</span>
                    </h3>
                  </div>

                  {imageData.images && imageData.images.length > 0 && (
                    <div className="image-container">
                      <img
                        src={`data:image/png;base64,${imageData.images[0].base64}`}
                        alt={imageData.word}
                        className="generated-image"
                      />
                    </div>
                  )}

                  <div className="image-description">
                    <h4>Memory Aid</h4>
                    <ReactMarkdown>{imageData.text_response}</ReactMarkdown>
                  </div>

                  <div className="image-prompt">
                    <h4>Visual Prompt</h4>
                    <p>{imageData.prompt}</p>
                  </div>

                  <div className="image-actions">
                    <button
                      className="save-btn"
                      onClick={handleSaveVisual}
                      disabled={saving}
                    >
                      {saving ? 'Saving...' : '💾 Save Visual'}
                    </button>
                  </div>
                </div>
              )}

              {!imageData && !loading && !error && (
                <div className="empty-state">
                  <Sparkles size={48} />
                  <p>Enter a word and generate an unforgettable visual!</p>
                </div>
              )}
            </>
          ) : (
            <>
              {loadingLibrary ? (
                <div className="loading-state">
                  <Loader className="spinner" size={40} />
                  <p>Loading your visuals...</p>
                </div>
              ) : selectedVisual ? (
                <div className="visual-detail">
                  <button
                    className="back-btn"
                    onClick={() => setSelectedVisual(null)}
                  >
                    ← Back to Library
                  </button>
                  <div className="detail-header">
                    <h3>{selectedVisual.word}</h3>
                    <span className="language-tag">{selectedVisual.language}</span>
                  </div>

                  {selectedVisual.images && selectedVisual.images.length > 0 && (
                    <div className="image-container">
                      <img
                        src={`data:image/png;base64,${selectedVisual.images[0].base64}`}
                        alt={selectedVisual.word}
                        className="generated-image"
                      />
                    </div>
                  )}

                  {selectedVisual.explanation && (
                    <div className="image-description">
                      <h4>Memory Aid</h4>
                      <ReactMarkdown>{selectedVisual.explanation}</ReactMarkdown>
                    </div>
                  )}

                  <div className="image-prompt">
                    <h4>Visual Prompt</h4>
                    <p>{selectedVisual.prompt}</p>
                  </div>

                  <div className="detail-footer">
                    <p className="created-date">
                      Created: {new Date(selectedVisual.created_at).toLocaleDateString()}
                    </p>
                    {pendingDeleteId === selectedVisual.id ? (
                      <div className="confirm-delete-inline">
                        <span>Delete this visual?</span>
                        <button className="confirm-yes-btn" onClick={() => handleDeleteVisual(selectedVisual.id)}>Yes, delete</button>
                        <button className="confirm-no-btn" onClick={() => setPendingDeleteId(null)}>Cancel</button>
                      </div>
                    ) : (
                      <button
                        className="delete-btn"
                        onClick={() => setPendingDeleteId(selectedVisual.id)}
                      >
                        <Trash2 size={18} />
                        Delete
                      </button>
                    )}
                  </div>
                </div>
              ) : (
                <>
                  {error && (
                    <div className="error-message">
                      <AlertCircle size={20} />
                      {error}
                    </div>
                  )}
                  {savedVisuals.length === 0 ? (
                    <div className="empty-state">
                      <BookOpen size={48} />
                      <p>No saved visuals yet. Create some in the Generator!</p>
                    </div>
                  ) : (
                    <div className="visuals-grid">
                      {savedVisuals.map((visual) => (
                        <div
                          key={visual.id}
                          className="visual-card"
                          onClick={() => loadVisualDetail(visual.id)}
                        >
                          <div className="card-header">
                            <h4>{visual.word}</h4>
                            <span className="language-tag">{visual.language}</span>
                          </div>
                          <p className="card-date">
                            {new Date(visual.created_at).toLocaleDateString()}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default VisualMemory;
