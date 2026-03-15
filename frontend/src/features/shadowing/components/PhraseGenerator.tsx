import { Loader2, Mic2 } from 'lucide-react';
import { LANGUAGE_OPTIONS } from '../../../utils/languages';

interface Props {
  theme: string;
  setTheme: (v: string) => void;
  language: string;
  setLanguage: (v: string) => void;
  isGenerating: boolean;
  onGenerate: () => void;
}

const PhraseGenerator = ({ theme, setTheme, language, setLanguage, isGenerating, onGenerate }: Props) => {
  return (
    <div className="glass-panel theme-input">
      <div className="input-group">
        <label htmlFor="theme">Practice Theme</label>
        <input
          id="theme"
          type="text"
          value={theme}
          onChange={e => setTheme(e.target.value)}
          placeholder="e.g., travel, restaurant ordering, daily conversations"
          disabled={isGenerating}
        />
      </div>
      <div className="input-group">
        <label htmlFor="language">Target Language</label>
        <select
          id="language"
          value={language}
          onChange={e => setLanguage(e.target.value)}
          disabled={isGenerating}
        >
          {LANGUAGE_OPTIONS.map(lang => (
            <option key={lang.value} value={lang.value}>{lang.label}</option>
          ))}
        </select>
      </div>
      <button
        className="generate-btn"
        onClick={onGenerate}
        disabled={isGenerating || !theme.trim()}
      >
        {isGenerating ? (
          <>
            <Loader2 size={20} className="spinner" />
            Generating Phrases...
          </>
        ) : (
          <>
            <Mic2 size={20} />
            Begin Practice
          </>
        )}
      </button>
    </div>
  );
};

export default PhraseGenerator;
