import { Loader, AlertCircle, BookOpen, Trash2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import type { SavedVisual, VisualDetail } from '../types';

interface Props {
  savedVisuals: SavedVisual[];
  selectedVisual: VisualDetail | null;
  loadingLibrary: boolean;
  error: string | null;
  pendingDeleteId: string | null;
  setPendingDeleteId: (id: string | null) => void;
  onLoadVisual: (visualId: string) => void;
  onDeleteVisual: (visualId: string) => void;
  onClearSelectedVisual: () => void;
}

const VisualLibrary = ({
  savedVisuals,
  selectedVisual,
  loadingLibrary,
  error,
  pendingDeleteId,
  setPendingDeleteId,
  onLoadVisual,
  onDeleteVisual,
  onClearSelectedVisual,
}: Props) => {
  if (loadingLibrary) {
    return (
      <div className="loading-state">
        <Loader className="spinner" size={40} />
        <p>Loading your visuals...</p>
      </div>
    );
  }

  if (selectedVisual) {
    return (
      <div className="visual-detail">
        <button className="back-btn" onClick={onClearSelectedVisual}>
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
              <button className="confirm-yes-btn" onClick={() => onDeleteVisual(selectedVisual.id)}>Yes, delete</button>
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
    );
  }

  return (
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
              onClick={() => onLoadVisual(visual.id)}
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
  );
};

export default VisualLibrary;
