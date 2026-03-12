
import { useState } from 'react';
import { Sparkles, Loader, AlertCircle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import './VisualMemory.css';

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

const VisualMemory = () => {
  const [word, setWord] = useState('');
  const [language, setLanguage] = useState('en');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [imageData, setImageData] = useState<ImageResponse | null>(null);

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
      const apiKey = import.meta.env.VITE_TRANSCRIBE_API_KEY;
      if (!apiKey) {
        setError('API key not found. Please set it in settings.');
        setLoading(false);
        return;
      }

      const params = new URLSearchParams({
        word: word.trim(),
        language,
      });

      const response = await fetch(
        `http://localhost:8000/generate-image?${params}`,
        {
          method: 'POST',
          headers: {
            'X-API-Key': apiKey,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }

      const data: ImageResponse = await response.json();
      console.log(data)
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

  return (
    <div className="page-container animate-fade-in">
      <header className="page-header">
        <h2>Visual Memory</h2>
        <p>Create memorable images to never forget a word!</p>
      </header>
      <div className="page-content">
        <div className="visual-memory-container">
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
                <option value="en">English</option>
                <option value="es">Spanish</option>
                <option value="fr">French</option>
                <option value="de">German</option>
                <option value="it">Italian</option>
                <option value="pt">Portuguese</option>
                <option value="ja">Japanese</option>
                <option value="zh-CN">Chinese (Simplified)</option>
                <option value="zh-TW">Chinese (Traditional)</option>
                <option value="ko">Korean</option>
                <option value="ru">Russian</option>
                <option value="ar">Arabic</option>
                <option value="hi">Hindi</option>
                <option value="nl">Dutch</option>
                <option value="pl">Polish</option>
                <option value="tr">Turkish</option>
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
            </div>
          )}

          {!imageData && !loading && !error && (
            <div className="empty-state">
              <Sparkles size={48} />
              <p>Enter a word and generate an unforgettable visual!</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default VisualMemory;
