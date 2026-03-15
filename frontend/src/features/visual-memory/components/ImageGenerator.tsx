import React from 'react';
import { Sparkles, Loader, AlertCircle } from 'lucide-react';
import { LANGUAGE_OPTIONS } from '../../../utils/languages';

interface Props {
  word: string;
  setWord: (v: string) => void;
  language: string;
  setLanguage: (v: string) => void;
  loading: boolean;
  error: string | null;
  successMessage: string | null;
  hasImageData: boolean;
  onSubmit: (e: React.FormEvent) => void;
}

const ImageGenerator = ({
  word, setWord, language, setLanguage, loading, error, successMessage, hasImageData, onSubmit,
}: Props) => {
  return (
    <>
      <form onSubmit={onSubmit} className="word-input-form">
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

      {!hasImageData && !loading && !error && (
        <div className="empty-state">
          <Sparkles size={48} />
          <p>Enter a word and generate an unforgettable visual!</p>
        </div>
      )}
    </>
  );
};

export default ImageGenerator;
