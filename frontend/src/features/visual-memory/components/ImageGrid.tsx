import ReactMarkdown from 'react-markdown';
import type { ImageResponse } from '../types';

interface Props {
  imageData: ImageResponse;
  saving: boolean;
  onSave: () => void;
}

const ImageGrid = ({ imageData, saving, onSave }: Props) => {
  return (
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
          onClick={onSave}
          disabled={saving}
        >
          {saving ? 'Saving...' : '💾 Save Visual'}
        </button>
      </div>
    </div>
  );
};

export default ImageGrid;
