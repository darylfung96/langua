import { Sparkles } from 'lucide-react';
import { LANGUAGE_OPTIONS } from '../../../utils/languages';

interface Props {
  language: string;
  setLanguage: (v: string) => void;
  inputWords: string;
  setInputWords: (v: string) => void;
  isGenerating: boolean;
  error: string | null;
  success: string | null;
  onSubmit: (e: React.FormEvent) => void;
}

const StoryGenerator = ({
  language, setLanguage, inputWords, setInputWords, isGenerating, error, success, onSubmit,
}: Props) => {
  return (
    <form onSubmit={onSubmit}>
      <div className="input-group">
        <label htmlFor="language">Target Language</label>
        <select
          id="language"
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          style={{
            width: '100%',
            padding: '0.75rem',
            borderRadius: '0.5rem',
            background: 'rgba(255,255,255,0.05)',
            border: '1px solid rgba(255,255,255,0.1)',
            color: 'white',
            fontFamily: 'inherit',
            marginBottom: '1rem',
            outline: 'none',
            cursor: 'pointer'
          }}
        >
          {LANGUAGE_OPTIONS.map(lang => (
            <option key={lang.value} value={lang.value} style={{ color: 'black' }}>{lang.label}</option>
          ))}
        </select>
      </div>
      <div className="input-group">
        <label htmlFor="words">Vocabulary Words</label>
        <textarea
          id="words"
          placeholder="e.g. gato, leche, rápido..."
          value={inputWords}
          onChange={(e) => setInputWords(e.target.value)}
          rows={4}
        />
        <p className="input-hint">Separate words with commas for best results.</p>
      </div>

      {error && <div className="error-message" style={{ color: '#ff6b6b', marginBottom: '1rem', fontSize: '0.875rem', padding: '0.5rem', background: 'rgba(255,107,107,0.1)', borderRadius: '0.25rem' }}>{error}</div>}
      {success && <div className="success-message" style={{ color: '#51cf66', marginBottom: '1rem', fontSize: '0.875rem', padding: '0.5rem', background: 'rgba(81,207,102,0.1)', borderRadius: '0.25rem' }}>{success}</div>}

      <button
        type="submit"
        className={`generate-btn ${isGenerating ? 'generating' : ''}`}
        disabled={isGenerating || !inputWords.trim()}
      >
        {isGenerating ? (
          <>
            <div className="spinner"></div>
            Weaving Magic...
          </>
        ) : (
          <>
            <Sparkles size={20} />
            Weave Story
          </>
        )}
      </button>
    </form>
  );
};

export default StoryGenerator;
